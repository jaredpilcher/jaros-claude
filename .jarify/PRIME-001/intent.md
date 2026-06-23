# Intent

**jaros-claude** is a template repository. Its purpose is to apply the same
**control over agent decisions** that Jaros and jaros-code apply to a small local
model — the **two-plane discipline** — to **Claude**. You copy this repository's
contents into another project and that project inherits the discipline: every
reasoning call is Claude, and **every side effect Claude wants is mediated by a
deterministic gate and deterministic tools.** The model proposes; the harness
disposes.

This is the deliberate inversion of jaros-code. jaros-code's wager is *"a small
model becomes useful when the harness is strong."* jaros-claude's wager is *"a
strong model becomes safe, reproducible, and auditable when the harness is in
control."* The architecture is identical; only the motivation generalizes. The
discipline never depended on the model being weak — it is a governance property,
and it is exactly as valuable when the reasoning is done by a frontier model.

These commitments are ordered. A lower-numbered commitment is never weakened to
satisfy a higher-numbered one. When any specification, agent, tool, or change
would violate one, **STOP and flag the conflict** rather than silently resolving it.

1. **Two-plane discipline (inherited from the Jaros prime directive).**
   The model only ever writes recommendations on slips of paper: inert,
   JSON-serializable `Decision` data. A deterministic execution plane — a gate
   that validates and tools that act — decides whether and how each decision
   actually runs. The reasoning plane never performs a side effect directly: no
   file write, no shell command, no network call originates from a model output.
   Everything the harness *does* is a deterministic tool the clerk runs. **This
   is the control. It is non-negotiable and it does not relax because the model is
   capable.**

2. **Claude is the reasoning model — and it is always confined to the reasoning
   plane.** All reasoning is served by Claude (the Anthropic Messages API),
   defaulting to Claude Opus 4.8 with adaptive thinking. But Claude holds **no
   host handles** and drives **no execution**. Its only output is a `Decision`
   that must pass the gate before any tool runs. Where jaros-code says "decompose
   instead of escalating to a bigger model," jaros-claude says **"decompose for
   control and auditability, not to compensate for the model."** A capable model
   does not earn ungated authority; even a correct proposal is executed only
   through the deterministic plane. No tool reaches the host except via the gate.

3. **Reproducible & honest.**
   Every accepted Decision is hash-chain logged before its effect is observable,
   and the log replays through the deterministic executor — with **zero model
   calls** — to reconstruct the run. Claude's live generation is not
   bit-reproducible, but the *decision log is*: it is the auditable, tamper-evident
   truth of what the system did and why, and any completed run can be replayed
   from it without calling the model again. The harness never hides, rounds away,
   or fabricates a result. A failing test is reported as failing; a refusal is
   reported as a refusal; a skipped step is reported as skipped.

4. **Spec-first, the jarify way — all the way down.**
   Behavior is governed by `.jarify` specifications. Code traces back to
   requirements through `index.json`. When specified behavior changes, the spec
   and the code change in the same commit. Stale specs are defects. Because this
   is a *template*, the reflexive loop is the product: when you adopt jaros-claude
   into your project, you first capture *your* intent as that project's prime
   directive, decompose it into requirements / design / tasks, implement one
   scoped task at a time with single-purpose agents, and trace the resulting code
   back to the spec — the identical loop that governs this template.

5. **Claude-Code-like experience.**
   The operator-facing experience should feel familiar and transparent: a terminal
   harness that shows what it is doing, what each agent decided, and what each tool
   ran. But UX is the last tier: it never overrides correctness, reproducibility,
   or the two-plane confinement above it.

**The method, stated once:** capability comes from a capable model *under control*
— many small, single-purpose agents each making one narrow judgement, every
judgement emitted as inert data, every effect performed by a deterministic tool
behind a gate. The intelligence is Claude's; the *authority* is the harness's.

**Plane-placement is still the craft.** For every grain ask: *is its core a
judgement Claude should make, or a deterministic operation the host should
perform?* Classify, pick, transform-by-example, read a result → a tiny **agent**
emitting a Decision. Apply a patch, run a command, write bytes, check uniqueness,
enforce a denylist → a deterministic **tool** behind the gate. Even when Claude
could do the deterministic part, routing it to a tool is what makes the system
auditable and safe — the model's role shrinks to the judgement, and the judgement
is all that is recorded as non-deterministic input.

**Why confine a capable model at all?** Three reasons, each a tenet above:
*safety* (a bug or a bad generation cannot reach a capability the gate didn't
grant — capability-safety by construction), *reproducibility* (the only
non-deterministic input is the recorded Decision, so any run replays), and
*auditability* (the hash-chained log is the complete account of what every agent
decided and what every tool did). None of these depend on the model being weak.
They are the reason to keep even a frontier model on the reasoning side of the gate.
