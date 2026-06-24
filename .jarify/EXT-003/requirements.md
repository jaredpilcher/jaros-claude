---
id: EXT-003
title: Durable Decision Log + Session Binding (PostToolUse / SessionStart hooks)
status: implemented
priority: high
serves: PRIME-001 Tenet 3 (reproducible & honest) and Tenet 5 (authentic UX)
---

This spec serves **Tenet 3** of PRIME-001 (and Tenet 5): every executed effect is
recorded in a tamper-evident log, and every session is bound to the discipline
without the operator doing anything. Both are Claude Code hooks that fire on their
own.

## Requirements

- **REQ-1 Decision log hook** — a PostToolUse hook (matcher `*`) that appends every
  executed tool call to `.claude/audit/decisions.jsonl` as a hash-chained record
  (index + prev-checksum + record + sha256), and never blocks.
  (`.claude/hooks/log-decision.py`)
- **REQ-2 Tamper-evidence + verifier** — each record links to the previous
  checksum, so any insertion, deletion, reorder, or edit is detectable; a read-only
  verifier walks the chain and reports the first break or that it is intact.
  (`.claude/hooks/verify-chain.py`)
- **REQ-3 Session binding** — a SessionStart hook (matcher `startup|resume|clear|
  compact`) injects the standing governance context so Claude operates under the
  two-plane discipline from its first turn, and ensures the audit dir exists. No
  operator command required. (`.claude/hooks/session-init.py`)
- **REQ-4 Status surface** — an optional, read-only `/jarify-status` command shows
  the specs, the gate posture, and the chain integrity. Convenience only; the
  discipline operates without it. (`.claude/commands/jarify-status.md`)

The log is runtime state (gitignored). Honesty is the rule: refusals, failures, and
skips are recorded and reported as themselves.
