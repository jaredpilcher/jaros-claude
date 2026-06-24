# PRIME-001 — System Architecture

`jaros-claude` does not add a harness. It **governs the Claude Code harness** so
that Claude — driving its own tools — operates under the two-plane discipline. The
mapping from the Jaros architecture onto Claude Code's native extension points is
the whole design.

## The two planes, mapped onto Claude Code

```text
        ┌──────────────────────── REASONING PLANE ────────────────────────────┐
        │  Claude (driving Claude Code) + single-purpose subagents in           │
        │  .claude/agents — each makes ONE narrow judgement and PROPOSES a       │
        │  tool call. No subagent holds ungated authority.                       │
        └───────────────────────────────┬───────────────────────────────────────┘
                                        │  proposed tool call (the "Decision")
                                        ▼
        ┌──────────────────────── DECISION GATE ───────────────────────────────┐
        │  PreToolUse hook  (.claude/hooks/gate.py + policy.py)                   │
        │  deterministically ACCEPTS or REFUSES the call BEFORE it runs.          │
        │  A refusal (exit 2) is shown to Claude; the call never executes.        │
        └───────────────────────────────┬───────────────────────────────────────┘
                                        ▼
        ┌──────────────────────── EXECUTION PLANE ─────────────────────────────┐
        │  Claude Code's built-in tools (Bash, Write, Edit, Read, …) perform the │
        │  effect. They are the deterministic clerk; the model never bypasses    │
        │  them.                                                                  │
        └───────────────────────────────┬───────────────────────────────────────┘
                                        ▼
        ┌──────────── DURABLE STATE: hash-chained decision log ─────────────────┐
        │  PostToolUse hook (.claude/hooks/log-decision.py) records every        │
        │  executed call to .claude/audit/decisions.jsonl, each record chained   │
        │  to the previous checksum → tamper-evident, auditable (Tenet 3).       │
        └────────────────────────────────────────────────────────────────────────┘

        SessionStart hook (.claude/hooks/session-init.py) binds every session to
        this directive automatically — no command for the operator to run.
```

The arrow only ever points down. Nothing in the reasoning plane reaches the host
except by proposing a tool call that the gate accepts. **Claude is capable, but it
sits entirely above the gate** — and the gate is enforced by Claude Code's own hook
mechanism, not by a wrapper we built.

## What maps to what

```text
   Jaros / jaros-code concept        Claude Code native mechanism
   ──────────────────────────        ──────────────────────────────────────────
   reasoning plane (the model)        Claude driving Claude Code
   single-purpose agents              .claude/agents/*.md subagents (auto-delegated)
   the decision gate                  PreToolUse hook (gate.py + policy.py)
   deterministic execution tools      Claude Code built-in tools (Bash/Write/Edit/…)
   hash-chained decision log          PostToolUse hook → .claude/audit/decisions.jsonl
   capability-safety / denylist       policy.py (the single tuning point)
   spec-first governance              .jarify/ (PRIME-001 + EXT-*) + index.json
   operator surface (Claude-Code-like) Claude Code itself + optional /jarify-status
   the jarify roles (spec/task/build/  spec-author, task-decomposer, builder,
     architect)                         architect subagents
```

## Authentic by construction

The control must not make the operator do more. Three hooks make it passive:

- **SessionStart** injects the standing governance context, so Claude operates
  under the discipline from its first turn — the operator never "turns it on."
- **PreToolUse** gates every dangerous tool call automatically; the operator only
  notices it when something genuinely unsafe is refused.
- **PostToolUse** records every call automatically; the audit trail accrues with no
  ceremony.

Subagents auto-delegate by their `description`. The one optional convenience,
`/jarify-status`, is read-only and never required for the discipline to function.

## Why confine a capable model

```text
   property            how the mapped two planes provide it
   ─────────────────   ────────────────────────────────────────────────────────
   safety              the PreToolUse gate refuses destructive/privileged/exfil
                       effects deterministically, before they run
   reproducibility     every executed effect is recorded in commit order, so a run
                       is auditable and can be reconstructed
   auditability        the hash-chained log is the tamper-evident account of what
                       the harness did
   honesty             refusals, failures, and skips are surfaced as themselves
```

None of these depend on the model being weak. That is the inversion from
jaros-code: the discipline is a governance property, valuable *because* the model
is capable.

## Spec map

```text
  PRIME-001  ── north star (this document; intent.md + design.md)
     ├── EXT-001  the decision gate (PreToolUse hook + policy) — Tenet 1
     ├── EXT-002  single-purpose subagent fleet (.claude/agents) — Tenet 2
     ├── EXT-003  durable decision log + session binding (PostToolUse/SessionStart) — Tenet 3
     └── EXT-004  governance binding (CLAUDE.md, settings.json, .jarify scaffold) — Tenets 4 & 5
```

## Adopting this template into your project

Copy the contents in. From then on, operate your project with the **same** jarify
loop that governs this template — and Claude Code does it through the subagents:

```text
   how jaros-claude is governed        how you build your project with it
   ────────────────────────────        ──────────────────────────────────
   PRIME-001 (this directive)    ⇄     your project's PRIME directive (your intent)
   EXT-00x requirements/design   ⇄     spec-author drafts your feature specs
   tasks.md ([TASK-x])           ⇄     task-decomposer breaks them into scoped tasks
   single-purpose agents +       ⇄     builder implements one task at a time; every
     gated tools                         effect passes the gate
   index.json traceability       ⇄     architect validates each task against its spec
```

Capture your intent first, decompose it, implement one scoped task at a time, and
let the gate keep authority. Claude Code does the reasoning; the harness — governed
by these hooks and specs — keeps the control.
