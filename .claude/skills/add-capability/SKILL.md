---
name: add-capability
description: Use when adding ANY new capability, feature, or behavior change to a jaros-claude-governed project (this repo or one that copied the template in). Drives the conformant jarify loop end-to-end — capture intent as a .jarify spec, decompose into scoped tasks, build one task at a time behind the gate, validate against the spec, and commit code + spec together. Invoke for "add X", "make it do Y", "build Z", or any request that introduces or changes behavior. Keeps extension easy AND conformant with the Prime Directive.
---

# Adding capability the jarify way

You are extending a project governed by `.jarify/PRIME-001`. New capability is added
by *composition under control*, not by free-form coding. Follow this loop — it keeps
the addition easy and keeps it conformant. Do not skip the spec; do not let one step
balloon into the whole feature.

First, read `.jarify/PRIME-001/intent.md` if you have not this session. Then:

## 1. Capture intent → a spec (spec-first, Tenet 4)
A change with no spec is a defect waiting to happen. Delegate to the **spec-author**
subagent (or do its job): write/extend one `.jarify/EXT-00N/` requirement — frontmatter
(`id`, `title`, `status`, `priority`, `serves: PRIME-001 Tenet N`), a few numbered,
*testable* REQ-x, an `index.json` mapping each REQ-x to the file(s) that will satisfy
it, and a `design.md` if non-trivial. State which tenet the capability serves. If the
intent conflicts with a higher tenet, STOP and flag it.

## 2. Decompose → scoped tasks (composition, Tenet 2)
Delegate to **task-decomposer**: break the requirement into small, ordered,
individually-verifiable `[TASK-x]` items in `tasks.md`. Apply **plane-placement
triage** to each:
- the grain's core is a **judgement** (classify, pick, transform-by-example, read a
  result) → an `[agent]` task — a single-purpose subagent. If a new subagent is
  needed, use the **add-subagent** skill.
- the grain's core is a **deterministic operation** (compute, search, apply, enforce a
  rule) → a `[tool]` task — a Claude Code tool call, which runs through the gate. If it
  changes what the gate allows/refuses, use the **extend-gate** skill.

## 3. Build one task at a time (Tenet 1)
For each `[TASK-x]`, delegate to **builder** (one task, then stop). Its writes and
commands pass the PreToolUse gate automatically — a refusal is the control working;
adapt the approach, never try to bypass the hook. Verify with the narrowest real
check and report the true result.

## 4. Validate before commit (Tenets 3 & 4)
Delegate to **architect** (read-only): confirm the code actually satisfies its REQ-x,
that `index.json` traces it, that tests really pass, and that no higher tenet was
weakened. APPROVED or CHANGES NEEDED — be honest.

## 5. Commit code + spec together (Tenet 4)
One commit contains both the implementation and the `.jarify` spec it traces to.
Stale specs are defects, so they never lag the code. Footer:
`Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

## Guardrails (do not violate)
- Never add a capability that gives the reasoning plane ungated authority — every
  effect stays a gated tool call.
- Never disable, weaken, or route around the gate or the decision log to make a
  feature work. If a feature seems to require that, STOP and flag the conflict.
- Keep each subagent single-purpose and each task atomic. More capability = more
  small pieces, not bigger ones.
