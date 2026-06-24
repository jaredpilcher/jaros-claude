---
id: EXT-002
title: Single-Purpose Subagent Fleet (.claude/agents)
status: implemented
priority: high
serves: PRIME-001 Tenet 2 (Claude confined; capability by composition)
---

This spec serves **Tenet 2** of PRIME-001: capability comes from composing many
small, single-purpose subagents — each making ONE narrow judgement — not from one
big agent with unguarded power. On the Claude Code harness these are
`.claude/agents/*.md` subagents, which auto-delegate by their `description`, so the
operator gets the decomposition without invoking anything.

The fleet mirrors the jarify roles (the spec-first loop, all the way down).

## Requirements

- **REQ-1 `spec-author`** — captures intent as a `.jarify` requirement/design and
  index.json traceability; does not implement. (`.claude/agents/spec-author.md`)
- **REQ-2 `task-decomposer`** — breaks one requirement into small, ordered,
  individually-verifiable tasks, applying plane-placement triage (judgement →
  subagent, deterministic op → gated tool). (`.claude/agents/task-decomposer.md`)
- **REQ-3 `builder`** — implements EXACTLY ONE scoped task, verifies it, updates
  traceability, and stops. Its effects pass the gate. (`.claude/agents/builder.md`)
- **REQ-4 `architect`** — read-only reviewer: validates a task against its
  requirement and checks no higher tenet is weakened, before commit.
  (`.claude/agents/architect.md`)

Each subagent is genuinely single-purpose with a minimal tool grant. Add capability
by adding more small subagents — never by widening one into a generalist.
