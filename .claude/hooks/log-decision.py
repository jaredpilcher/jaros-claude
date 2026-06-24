#!/usr/bin/env python3
"""The durable decision log — PostToolUse hook (PRIME-001 Tenet 3).

Reproducible & honest: every tool call that the gate accepted and the execution
plane ran is recorded here, in commit order, as a hash-chained record. Each record
links to the previous one's checksum, so any insertion, deletion, reorder, or edit
anywhere in the log is detectable — it is the auditable truth of what the harness
did. Fires automatically on every tool (see .claude/settings.json); never blocks.

The log lives at .claude/audit/decisions.jsonl (gitignored runtime state). Use
`/jarify-status` to see the recent decisions and verify chain integrity.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time

GENESIS_PREV = "0" * 64


def _checksum(index: int, prev: str, record: dict) -> str:
    payload = json.dumps({"index": index, "prev": prev, "record": record},
                         sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _tail(path: str) -> tuple[int, str]:
    """Return (last_index, last_checksum) from the existing log, or (0, GENESIS)."""
    if not os.path.exists(path):
        return 0, GENESIS_PREV
    last_index, last_sum = 0, GENESIS_PREV
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                last_index = obj.get("index", last_index)
                last_sum = obj.get("checksum", last_sum)
            except Exception:
                continue
    return last_index, last_sum


def _target(tool: str, ti: dict) -> str:
    if tool == "Bash":
        return ti.get("command", "")[:500]
    for k in ("file_path", "notebook_path", "path", "pattern", "url"):
        if k in ti:
            return str(ti[k])[:500]
    return ""


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    project = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    audit_dir = os.path.join(project, ".claude", "audit")
    os.makedirs(audit_dir, exist_ok=True)
    path = os.path.join(audit_dir, "decisions.jsonl")

    tool = data.get("tool_name", "")
    ti = data.get("tool_input") or {}
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "session": data.get("session_id", ""),
        "tool": tool,
        "target": _target(tool, ti),
    }

    index, prev = _tail(path)
    index += 1
    checksum = _checksum(index, prev, record)
    line = json.dumps({"index": index, "prev": prev, "record": record, "checksum": checksum},
                      sort_keys=True, separators=(",", ":"))
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
