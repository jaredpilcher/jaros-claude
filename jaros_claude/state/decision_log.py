"""Durable decision log + deterministic replay.

Reproducibility is record-and-replay of non-determinism. The only
non-deterministic input to a run is the model's output, captured as an inert,
serializable ``Decision``. This module records each *accepted* decision, in
commit order, before its effects are observable, and replays the recorded
decisions through the deterministic executor — with **no model call** — to
reconstruct the run to byte-identical state.

With Claude, live generation is not bit-reproducible; the decision log is what
makes a *completed* run honestly replayable: re-execute the recorded decisions
and you reconstruct exactly what the harness did, without calling the model again.

The log is newline-delimited JSON, one record per line, durable by ``os.fsync``
on append, and each record is hash-chained to the previous one (``prev`` = the
previous record's checksum) so any insertion, deletion, reorder, or edit anywhere
in the log is detectable — the auditable truth of what the system did and why.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator

from jaros_claude.core.decision import Decision, create_decision


def _decision_to_dict(decision: Decision) -> dict[str, Any]:
    return {
        "id": decision.id,
        "source": decision.source,
        "type": decision.type,
        "payload": decision.payload,
    }


def _decision_from_dict(data: dict[str, Any]) -> Decision:
    return create_decision(
        id=data["id"], source=data["source"], type=data["type"], payload=data["payload"]
    )


GENESIS_PREV = "0" * 64


@dataclass(frozen=True)
class DecisionRecord:
    """A single durable record of one accepted decision, chained to the prior one."""

    index: int
    decision: dict[str, Any]
    checksum: str
    prev: str = GENESIS_PREV

    @staticmethod
    def compute_checksum(index: int, prev: str, decision: dict[str, Any]) -> str:
        payload = json.dumps(
            {"index": index, "prev": prev, "decision": decision},
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @classmethod
    def make(cls, index: int, decision: dict[str, Any], prev: str = GENESIS_PREV) -> "DecisionRecord":
        return cls(
            index=index,
            decision=decision,
            prev=prev,
            checksum=cls.compute_checksum(index, prev, decision),
        )

    def checksum_ok(self) -> bool:
        return self.checksum == self.compute_checksum(self.index, self.prev, self.decision)

    def to_json(self) -> str:
        return json.dumps(
            {"index": self.index, "prev": self.prev, "decision": self.decision, "checksum": self.checksum},
            sort_keys=True,
            separators=(",", ":"),
        )


class DecisionLog:
    """A durable, append-only, newline-delimited JSON decision log."""

    def __init__(self, dir: str | os.PathLike[str], filename: str = "decisions.log") -> None:
        self.dir: Path = Path(dir)
        self.filename: str = filename
        self.path: Path = self.dir / filename
        self._lock = threading.Lock()
        self._count: int | None = None
        self._last_checksum: str | None = None

    def ensure(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.flush()
                os.fsync(fh.fileno())

    def _write_raw(self, record: DecisionRecord) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        line = record.to_json() + "\n"
        with open(self.path, "a", encoding="utf-8", newline="") as fh:
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())

    def _load_tail_locked(self) -> None:
        if self._count is not None:
            return
        count = 0
        last = GENESIS_PREV
        for rec in self.read():
            count += 1
            last = rec.checksum
        self._count = count
        self._last_checksum = last

    def append_decision(self, decision: dict[str, Any]) -> "DecisionRecord":
        """Atomically append the next chained record (amortized O(1)), thread-safe."""
        with self._lock:
            self._load_tail_locked()
            assert self._count is not None
            index = self._count + 1
            prev = self._last_checksum or GENESIS_PREV
            record = DecisionRecord.make(index, decision, prev=prev)
            self._write_raw(record)
            self._count = index
            self._last_checksum = record.checksum
            return record

    def read(self) -> Iterator[DecisionRecord]:
        """Yield records in append order, tolerating a torn trailing line."""
        if not self.path.exists():
            return
        with open(self.path, "r", encoding="utf-8") as fh:
            raw = fh.read()
        if not raw:
            return
        ends_with_newline = raw.endswith("\n")
        lines = raw.split("\n")
        if ends_with_newline and lines and lines[-1] == "":
            lines.pop()
        for line in lines:
            if line == "":
                continue
            try:
                obj = json.loads(line)
                yield DecisionRecord(
                    index=obj["index"],
                    decision=obj["decision"],
                    checksum=obj["checksum"],
                    prev=obj.get("prev", GENESIS_PREV),
                )
            except (json.JSONDecodeError, KeyError, TypeError):
                continue

    def length(self) -> int:
        return sum(1 for _ in self.read())


def record_decision(log: DecisionLog, decision: Decision) -> DecisionRecord:
    """Durably append ``decision`` as the next chained record (executor ``on_accept`` hook)."""
    return log.append_decision(_decision_to_dict(decision))


def read_decisions(log: DecisionLog) -> list[Decision]:
    """Return recorded decisions in order, dropping a torn/corrupt trailing record."""
    records = list(log.read())
    decisions: list[Decision] = []
    expected = 1
    for pos, rec in enumerate(records):
        is_last = pos == len(records) - 1
        if rec.index == expected and rec.checksum_ok():
            decisions.append(_decision_from_dict(rec.decision))
            expected += 1
            continue
        if is_last:
            break
        raise ValueError(f"corrupt decision record at position {pos} (index={rec.index!r})")
    return decisions


@dataclass(frozen=True)
class ChainResult:
    """Outcome of verifying the decision log's hash chain."""

    ok: bool
    length: int
    position: int | None = None
    reason: str | None = None


def verify_chain(log: DecisionLog) -> ChainResult:
    """Verify the log is an untampered, append-only hash chain. Returns the first break."""
    prev = GENESIS_PREV
    expected = 1
    count = 0
    for rec in log.read():
        count += 1
        if rec.index != expected:
            return ChainResult(False, count, expected,
                               f"index discontinuity: expected {expected}, found {rec.index}")
        if not rec.checksum_ok():
            return ChainResult(False, count, expected, "record checksum mismatch (record was edited)")
        if rec.prev != prev:
            return ChainResult(False, count, expected, "broken hash chain: prev mismatch")
        prev = rec.checksum
        expected += 1
    return ChainResult(True, count)


def replay(decision_log: DecisionLog, apply: Callable[..., Any], **collaborators: Any) -> list[Any]:
    """Re-execute recorded decisions through the deterministic executor — no model call.

    Because ``apply`` is a pure function of the decision plus collaborators,
    replaying the same log reconstructs the run to byte-identical state.
    """
    results: list[Any] = []
    for decision in read_decisions(decision_log):
        results.append(apply(decision, **collaborators))
    return results
