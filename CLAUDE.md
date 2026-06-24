# jaros-claude

A **template** that makes the **Claude Code harness itself** operate under the
**two-plane control discipline** of Jaros and jaros-code — without building a new
harness and without asking you to run extra commands. Copy this repository's
contents into a project and Claude Code *just operates that way*: the model
proposes, a deterministic gate decides, and every decision is recorded.

The harness is Claude Code. We do not replace it — we **govern it** through its own
native extension points: this `CLAUDE.md`, `.claude/agents`, `.claude/settings.json`
hooks, and the `.jarify` specs.

## Governance (binds every run)

This repo is governed by `.jarify/`. **`PRIME-001` is the Prime Directive** — read
`.jarify/PRIME-001/intent.md` before any structural change. Its five ordered
tenets are non-negotiable; a lower tenet is never weakened for a higher one:

1. **Two-plane discipline** — you (Claude) only *propose* effects (tool calls); a
   deterministic gate decides whether each may run before it does. On this harness
   the gate is a **PreToolUse hook** (`.claude/hooks/gate.py` + `policy.py`); the
   execution plane is Claude Code's built-in tools. A gate refusal is the control
   working — adapt, don't try to bypass it.
2. **Claude confined; capability by composition** — reasoning is Claude, but
   capability is added with many small, single-purpose subagents
   (`.claude/agents`), not one big agent with unguarded power. Decompose for
   control and auditability, not to compensate for the model.
3. **Reproducible & honest** — every executed tool call is hash-chain logged
   (`.claude/hooks/log-decision.py` → `.claude/audit/decisions.jsonl`); the chain
   is tamper-evident. Report failures, refusals, and skips as themselves; never
   hide or fabricate a result.
4. **Spec-first** — behavior traces to `.jarify` requirements via `index.json`;
   spec + code change in the SAME commit; stale specs are defects.
5. **Claude-Code-like UX** — the experience is Claude Code itself; the discipline
   adds no required commands and no friction. UX never overrides the tenets above.

When a change would violate a tenet, **STOP and flag the conflict** — do not
silently resolve it.

## How the discipline operates (automatically)

You do not turn anything on. Three hooks (registered in `.claude/settings.json`)
make it passive:

- **SessionStart** injects this directive as standing context, so you operate under
  it from your first turn.
- **PreToolUse** runs `gate.py` on every Bash/Write/Edit and refuses the unsafe
  ones deterministically (destructive/privileged commands, piping remote content
  into a shell, writes into credential/system locations). `policy.py` is the single
  place that policy is tuned.
- **PostToolUse** runs `log-decision.py` on every tool call and appends a
  hash-chained record to the audit log.

## The jarify loop (use the subagents)

This is reflexive: you build the user's project the same way this template is
governed. The fleet mirrors the jarify roles and auto-delegates:

- **`spec-author`** — capture intent as a `.jarify` requirement (before building).
- **`task-decomposer`** — break one requirement into small, ordered tasks, with
  plane-placement triage (judgement → subagent, deterministic op → gated tool).
- **`builder`** — implement EXACTLY ONE task, verify it, update traceability, stop.
- **`architect`** — validate the task against its requirement before commit.

## Adding capability stays easy — use the skills

Extending the harness must stay conformant by construction. Agent Skills
(`.claude/skills`) encode the conformant way to add, and auto-trigger by their
description:

- **`add-capability`** — the master loop for any new feature: spec → decompose →
  build one task → validate → commit code+spec together. Start here for "add X".
- **`add-subagent`** — when the new grain is a judgement: scaffold a new
  single-purpose subagent (one job, minimal tools, proposes-not-bypasses), with a
  template.
- **`extend-gate`** — when a change alters what the gate allows/refuses: a spec'd,
  tested edit of `.claude/hooks/policy.py` (a governance change, never a quiet one).

Capability grows by adding more small, gated, spec-traced pieces — never by widening
one into a generalist or routing around the gate.

## Design rules

- **Subagents are single-purpose.** Each makes ONE narrow judgement. Capability
  comes from composing many small ones, not from one generalist.
- **Effects are gated.** Every host effect is a Claude Code tool call that the
  PreToolUse gate has accepted. Nothing reaches the host another way.
- **Plane-placement triage.** For each grain ask: is its core a judgement you
  should make (→ a tiny subagent) or a deterministic operation the host should
  perform (→ a gated tool call)? Even when you *could* do the deterministic part,
  route it through a gated tool — that is what makes the run auditable and safe.

## Adopting this template into your project

Copy the contents in. Capture *your* intent as that project's PRIME directive
(`.jarify/PRIME-001`), then run the jarify loop with the subagents above: one
scoped task at a time, every effect through the gate, code traced back to the spec.
Tune `.claude/hooks/policy.py` if your project needs a tighter or looser gate — and
treat that as a governance change (Tenet 1), made in a commit against the spec.

## Commit discipline

Commit often: after each verified logical unit, commit code + spec together with a
descriptive message. Never commit `.env`, secrets, or runtime state (`.gitignore`
covers `.claude/audit/`). Footer:
`Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
