#!/usr/bin/env python3
"""The decision gate — PreToolUse hook (PRIME-001 Tenet 1).

This is the two-plane control, ported onto the Claude Code harness. Claude (the
reasoning plane) proposes a tool call; this deterministic gate decides whether it
may touch the host (the execution plane) *before* it runs. A refused call never
executes — the model is told why and adapts.

It fires automatically on every Bash / Write / Edit (see .claude/settings.json),
so the discipline just operates — the user runs Claude Code normally. The policy
itself lives in policy.py, the single place an adopting project tunes the gate.

Deny mechanism: exit code 2 with the reason on stderr (the robust, unambiguous
form). Exit 0 allows.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import policy  # noqa: E402


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # never break the session on a malformed payload; fail open to logging

    tool = data.get("tool_name", "")
    ti = data.get("tool_input") or {}

    reason = None
    if tool == "Bash":
        reason = policy.bash_reason(ti.get("command", ""))
    elif tool in ("Write", "Edit", "MultiEdit"):
        reason = policy.write_reason(ti.get("file_path", ""))
    elif tool == "NotebookEdit":
        reason = policy.write_reason(ti.get("notebook_path", ""))

    if reason:
        # stderr is shown to Claude as the deny reason; exit 2 blocks the call.
        print(f"BLOCKED by jaros-claude gate: {reason}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
