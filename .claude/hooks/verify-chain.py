#!/usr/bin/env python3
"""Verify the decision log's hash chain and print a short status.

Read-only. Walks .claude/audit/decisions.jsonl confirming index continuity,
per-record checksums, and that each record's `prev` matches the previous record's
checksum. Reports the first break, or that the chain is intact. Used by
`/jarify-status`; safe to run any time.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

GENESIS_PREV = "0" * 64


def _checksum(index: int, prev: str, record: dict) -> str:
    payload = json.dumps({"index": index, "prev": prev, "record": record},
                         sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> int:
    project = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    path = os.path.join(project, ".claude", "audit", "decisions.jsonl")
    if not os.path.exists(path):
        print("decision log: empty (no tool calls recorded yet)")
        return 0

    prev, expected, count, recent = GENESIS_PREV, 1, 0, []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                print(f"decision log: BROKEN — unparseable line at record {count + 1}")
                return 1
            count += 1
            if o.get("index") != expected:
                print(f"decision log: BROKEN at record {count} — index discontinuity")
                return 1
            if o.get("checksum") != _checksum(o["index"], o["prev"], o["record"]):
                print(f"decision log: BROKEN at record {count} — checksum mismatch (edited)")
                return 1
            if o.get("prev") != prev:
                print(f"decision log: BROKEN at record {count} — prev mismatch (insert/reorder)")
                return 1
            prev = o["checksum"]
            expected += 1
            r = o["record"]
            recent.append(f"  {r.get('tool', '?'):<14} {r.get('target', '')[:70]}")

    print(f"decision log: {count} records, hash-chain INTACT")
    if recent:
        print("recent decisions:")
        print("\n".join(recent[-15:]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
