---
id: EXT-005
title: Capability-Extension Skills (conformant "how to add to the harness")
status: implemented
priority: high
serves: PRIME-001 Tenet 4 (spec-first) and Tenet 5 (Claude-Code-like UX)
---

This spec serves **Tenets 4 and 5** of PRIME-001: adding new capability to a
jaros-claude-governed project must stay *easy* and must *conform* to the discipline
by construction. On the Claude Code harness the mechanism is **Agent Skills**
(`.claude/skills/<name>/SKILL.md`) — auto-discovered, model-triggered procedures
that encode the conformant way to extend the harness, so a contributor falls into
the jarify loop rather than around it.

## Requirements

- **REQ-1 `add-capability`** — the master workflow skill: drives the full
  conformant loop for any new feature (capture intent → spec-author →
  task-decomposer → builder → architect → commit code+spec together), with
  plane-placement triage and gate-awareness. The entry point for "add X".
  (`.claude/skills/add-capability/SKILL.md`)
- **REQ-2 `add-subagent`** — the conformant way to add a new single-purpose
  subagent when the new grain is a *judgement*: one judgement, minimal tool grant,
  proposes effects (never performs them), traces to a spec. Ships a template.
  (`.claude/skills/add-subagent/SKILL.md`, `.../templates/subagent.md`)
- **REQ-3 `extend-gate`** — the conformant way to change what the execution plane
  may do: editing `.claude/hooks/policy.py` is a governance change (Tenet 1) —
  spec it, add a verifiable rule, commit code+spec, never quietly widen the gate.
  (`.claude/skills/extend-gate/SKILL.md`)

Each skill is self-contained, references PRIME-001, and reinforces (never
circumvents) the gate, the decision log, and spec-first traceability. Adding the
skills themselves followed this spec — the loop is reflexive.
