---
description: Show jaros-claude governance status — the .jarify specs, the gate policy, and the decision-log hash-chain integrity.
allowed-tools: Bash(python3 .claude/hooks/verify-chain.py), Bash(ls .jarify/*), Read, Glob
---

Report the current state of the two-plane discipline in this project. This is a
read-only status view — it does not change anything.

1. List the `.jarify/` specs (PRIME-001 and each EXT-* with its title/status from
   the requirements.md frontmatter).
2. State whether the gate is active by confirming `.claude/settings.json` registers
   the PreToolUse/PostToolUse/SessionStart hooks, and summarize what the gate
   currently refuses (read `.claude/hooks/policy.py`: destructive/privileged,
   remote-pipe-to-shell, sensitive-path writes, and whether BLOCK_ALL_EGRESS is on).
3. Run the decision-log verifier and report its output:

!`python3 .claude/hooks/verify-chain.py`

Summarize in a few lines: specs present, gate posture, and chain integrity.
