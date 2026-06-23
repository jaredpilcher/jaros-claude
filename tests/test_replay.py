"""Reproducible & honest: the decision log is a tamper-evident, replayable record.

These prove Tenet 3 without a model: recorded decisions replay through the
deterministic executor to the same state, and any tampering with the log is
detected by the hash chain.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from jaros_claude.core import create_decision  # noqa: E402
from jaros_claude.execution import executor  # noqa: E402
from jaros_claude.state import (  # noqa: E402
    DecisionLog,
    read_decisions,
    record_decision,
    replay,
    verify_chain,
)


def test_record_and_replay_reconstructs_writes(tmp_path):
    executor.reset_handlers()
    written = []
    executor.register_handler(
        "code.write_file", lambda d, **_: written.append(d.payload["path"]))

    log = DecisionLog(tmp_path)
    log.ensure()
    d = create_decision(id="w1", source="t", type="code.write_file",
                        payload={"path": "a.py", "content": "x = 1\n"})
    record_decision(log, d)

    # Replay with ZERO model calls reproduces the same effect.
    written.clear()
    replay(log, executor.apply)
    assert written == ["a.py"]


def test_chain_detects_tampering(tmp_path):
    log = DecisionLog(tmp_path)
    log.ensure()
    record_decision(log, create_decision(id="1", source="t", type="advance",
                                         payload={"events": ["start"], "n": 1}))
    record_decision(log, create_decision(id="2", source="t", type="advance",
                                         payload={"events": ["start"], "n": 2}))
    assert verify_chain(log).ok

    # Tamper with a recorded line.
    text = log.path.read_text().splitlines()
    text[0] = text[0].replace('"n":1', '"n":999')
    log.path.write_text("\n".join(text) + "\n")
    assert not verify_chain(log).ok


def test_decisions_round_trip(tmp_path):
    log = DecisionLog(tmp_path)
    log.ensure()
    orig = create_decision(id="abc", source="editor", type="code.apply_patch",
                           payload={"path": "f.py", "old": "a", "new": "b"})
    record_decision(log, orig)
    [back] = read_decisions(log)
    assert back.id == orig.id and back.type == orig.type and back.payload == orig.payload
