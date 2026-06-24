---
id: EXT-001
title: The Decision Gate (PreToolUse hook)
status: implemented
priority: high
serves: PRIME-001 Tenet 1 (two-plane discipline)
---

This spec serves **Tenet 1** of PRIME-001: every effect Claude proposes passes a
deterministic gate before it touches the host. On the Claude Code harness the gate
is a **PreToolUse hook** that fires automatically — the operator runs Claude Code
normally and the discipline just operates.

## Requirements

- **REQ-1 Gate hook** — a PreToolUse hook that receives each proposed tool call and
  decides deterministically whether it may run, denying with exit code 2 (the
  reason is shown to Claude) and allowing with exit 0.
  (`.claude/hooks/gate.py`)
- **REQ-2 Policy (single tuning point)** — pure, deterministic policy functions the
  gate consults: refuse destructive/privileged shell, refuse piping remote content
  into a shell, and refuse writes into credential/system locations; with a
  `BLOCK_ALL_EGRESS` switch for the strict jaros-code unattended posture. This is
  the one file an adopting project edits to tighten/loosen the execution plane — a
  governance change, made deliberately. (`.claude/hooks/policy.py`)
- **REQ-3 Automatic wiring** — the gate is registered in `.claude/settings.json` for
  `Bash|Write|Edit|MultiEdit|NotebookEdit`, so it fires with no operator action.
  (`.claude/settings.json`)
- **REQ-4 Fail open to logging, never crash the session** — a malformed hook
  payload must not break the harness; the gate allows and lets the audit log record.
  (`.claude/hooks/gate.py`)

A refused call never executes; the model sees the reason and adapts. Widening the
policy is a structural change — surface it against this tenet rather than quietly
relaxing the gate.
