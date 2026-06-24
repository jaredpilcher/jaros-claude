#!/usr/bin/env python3
"""Session binding — SessionStart hook (PRIME-001 Tenets 4 & 5).

Makes the discipline *authentic*: every Claude Code session in this project starts
already bound to the two-plane / jarify governance, with no command for the user to
run. It injects a short standing context (the tenets and how the harness is wired)
so Claude operates that way from its first turn, and ensures the audit dir exists.
"""

from __future__ import annotations

import json
import os
import sys

CONTEXT = """\
[jaros-claude is active in this project — the two-plane discipline governs this session.]

You are Claude Code operating under jaros-claude's control (.jarify/PRIME-001 is the
Prime Directive). The harness enforces the two planes automatically:
- REASONING PLANE (you): you propose tool calls; you never get ungated authority.
- DECISION GATE: a PreToolUse hook deterministically refuses unsafe tool calls
  (.claude/hooks/policy.py). A refusal is the gate working — adapt, don't fight it.
- EXECUTION PLANE: Claude Code's built-in tools perform every effect.
- DURABLE LOG: a PostToolUse hook hash-chains every tool call to
  .claude/audit/decisions.jsonl, so the run is auditable and tamper-evident.

Operating rules (do these without being told):
1. Spec-first: behavior traces to .jarify requirements. When you change specified
   behavior, change the spec and the code in the SAME commit. Stale specs are defects.
2. Plane-placement: a judgement → a single-purpose subagent (.claude/agents); a
   deterministic operation → a tool. Compose many small agents, not one big prompt.
3. Honest & reproducible: report failures, refusals, and skips as themselves; never
   hide or fabricate a result.
4. If a change would violate a tenet, STOP and flag the conflict — don't silently
   resolve it.
"""


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    project = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    try:
        os.makedirs(os.path.join(project, ".claude", "audit"), exist_ok=True)
    except Exception:
        pass
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": CONTEXT,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
