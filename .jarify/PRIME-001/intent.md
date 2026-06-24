# Intent

**jaros-claude** is a template repository. Its purpose is to make the **Claude Code
harness itself** operate under the same **control over agent decisions** that Jaros
and jaros-code apply to a small local model — the **two-plane discipline** — without
building any new harness and without asking the operator to run extra commands. You
copy this repository's contents into a project, and from then on Claude Code *just
operates that way*: the model proposes, a deterministic gate decides, and every
decision is recorded.

This is the deliberate inversion of jaros-code. jaros-code's wager is *"a small
model becomes useful when the harness is strong."* jaros-claude's wager is *"a
strong model becomes safe, reproducible, and auditable when the harness is in
control."* The discipline never depended on the model being weak — it is a
governance property, and it is exactly as valuable when the reasoning is done by a
frontier model driving its own harness.

**The harness is Claude Code. We do not replace it; we govern it** through its own
native extension points — `CLAUDE.md`, `.claude/agents`, `.claude/settings.json`
hooks, and `.jarify` specs. The control is enforced by hooks that fire on their
own, so the operator uses Claude Code normally; the discipline is authentic, not a
mode the operator has to switch on.

These commitments are ordered. A lower-numbered commitment is never weakened to
satisfy a higher-numbered one. When any specification, agent, hook, or change would
violate one, **STOP and flag the conflict** rather than silently resolving it.

1. **Two-plane discipline (inherited from the Jaros prime directive).**
   Claude (the model driving Claude Code) only ever *proposes* an effect — a tool
   call. A deterministic gate decides whether that call may touch the host before
   it runs. The reasoning plane never gets ungated authority: no shell command, no
   file write executes until the gate accepts it. On the Claude Code harness the
   gate is a **PreToolUse hook** (`.claude/hooks/gate.py`); the execution plane is
   Claude Code's built-in tools. **This is the control. It does not relax because
   the model is capable, and it fires automatically — the operator does nothing.**

2. **Claude is the reasoning model — and it stays on the reasoning side of the
   gate.** All reasoning is Claude driving Claude Code. But its proposals are
   inert until the gate accepts them, and capability is added by *composition* —
   many small, single-purpose subagents (`.claude/agents`), each making one narrow
   judgement — not by handing one agent unguarded power. Where jaros-code says
   "decompose instead of escalating to a bigger model," jaros-claude says
   **"decompose for control and auditability, not to compensate for the model."**

3. **Reproducible & honest.**
   Every tool call the gate accepts and the execution plane runs is recorded, in
   commit order, in a hash-chained decision log (`.claude/hooks/log-decision.py` →
   `.claude/audit/decisions.jsonl`). Each record links to the previous one's
   checksum, so any insertion, deletion, reorder, or edit anywhere in the log is
   detectable. It is the auditable, tamper-evident truth of what the harness did.
   The harness never hides, rounds away, or fabricates a result: a failing test is
   reported as failing; a gate refusal is reported as a refusal; a skip as a skip.

4. **Spec-first, the jarify way — all the way down.**
   Behavior is governed by `.jarify` specifications. Code traces back to
   requirements through `index.json`. When specified behavior changes, the spec and
   the code change in the same commit. Stale specs are defects. Because this is a
   *template*, the reflexive loop is the product: when you adopt jaros-claude into
   your project, you capture *your* intent as that project's prime directive,
   decompose it into requirements / design / tasks (the `spec-author` and
   `task-decomposer` subagents do this), implement one scoped task at a time (the
   `builder`), and validate each against its requirement before commit (the
   `architect`) — the identical loop that governs this template.

5. **Claude-Code-like experience.**
   The operator-facing experience is Claude Code itself — already familiar and
   transparent. The discipline must not degrade it: it adds no required commands,
   no friction, no ceremony. It shows what the gate refused and what the log
   recorded, and otherwise stays out of the way. UX is the last tier: it never
   overrides the two-plane confinement, reproducibility, or spec-first discipline
   above it.

**The method, stated once:** capability comes from a capable model *under control*
— composed of many small, single-purpose subagents, every proposed effect passed
through a deterministic gate, every executed effect recorded in a tamper-evident
log. The intelligence is Claude's; the *authority* is the harness's.

**Plane-placement is still the craft.** For every grain ask: *is its core a
judgement Claude should make, or a deterministic operation the host should
perform?* A judgement → a tiny single-purpose **subagent**. A deterministic
operation → a **tool call**, which runs only through the gate. Even when Claude
could do the deterministic part, routing it through a gated tool is what makes the
run auditable and safe.

**Why confine a capable model at all?** Three reasons, each a tenet above:
*safety* (the gate refuses dangerous effects deterministically, so a bad step
cannot reach a capability policy didn't grant), *reproducibility* (every executed
effect is recorded, so any run is replayable and auditable), and *auditability*
(the hash-chained log is the complete, tamper-evident account of what the harness
did). None of these depend on the model being weak — they are the reason to keep
even a frontier model behind the gate.
