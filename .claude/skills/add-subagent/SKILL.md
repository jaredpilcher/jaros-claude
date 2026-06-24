---
name: add-subagent
description: Use when the new capability's core is a JUDGEMENT (classify, pick, transform-by-example, read a result) and needs a new single-purpose subagent in a jaros-claude-governed project. Scaffolds a conformant .claude/agents/<name>.md — one narrow judgement, a minimal tool grant, proposes effects rather than performing them, traces to a .jarify spec. Invoke from the add-capability loop's plane-placement step, or whenever someone says "add an agent that ...".
---

# Adding a single-purpose subagent the jarify way

A new subagent is how you add a new *judgement* to the reasoning plane (PRIME-001
Tenet 2). It must stay single-purpose and confined — capability comes from many
small agents, never one generalist.

## Conformance rules (non-negotiable)
1. **One narrow judgement.** If you can't state the agent's job in a single sentence,
   it's two agents. Split it.
2. **Minimal tool grant.** Grant only the tools the judgement needs. A reviewer is
   read-only (`Read, Glob, Grep, Bash`); an author writes specs (`Read, Write, Edit`);
   a builder may need `Edit, Write, Bash`. Never grant `*`.
3. **Proposes, never bypasses.** The subagent's effects are ordinary tool calls that
   pass the PreToolUse gate like everything else. It must not try to route around the
   gate or the decision log.
4. **Traces to a spec.** A new subagent is new capability → it needs a `.jarify`
   requirement (use the **add-capability** skill, or the `spec-author` subagent).

## Procedure
1. Read an existing agent (e.g. `.claude/agents/architect.md`) and the template at
   `${CLAUDE_SKILL_DIR}/templates/subagent.md` to match the house style.
2. Copy the template to `.claude/agents/<name>.md`. The file/`name` is the subagent's
   identity; keep it lowercase-hyphenated.
3. Write a `description` that says **when to use it** (and "use PROACTIVELY" if it
   should auto-delegate before a step). This is what makes it auto-invoke.
4. List the minimal `tools`.
5. In the body: state the ONE job, the procedure, and the honesty/stop-and-flag rule.
6. Add/extend the `.jarify` spec (EXT-002 covers the fleet) so `index.json` maps the
   new agent to its requirement. Commit code + spec together.

## Anti-patterns to refuse
- A "do-everything" agent, or one whose description lists many unrelated triggers.
- Granting broad tools "just in case."
- An agent that performs a host effect described as if it were a judgement — that
  belongs on the execution plane (a gated tool call), see the **extend-gate** skill.
