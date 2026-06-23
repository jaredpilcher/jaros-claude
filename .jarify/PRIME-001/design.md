# PRIME-001 — System Architecture

`jaros-claude` is a fleet of single-purpose reasoning agents (each calling
**Claude**) whose only output is inert `Decision` data, executed by a
deterministic tool plane on top of a vendored two-plane runtime. This document
maps the architecture the Intent demands. It is a **template**: the same shape is
what you adopt into a project to put Claude under control.

## The two planes

```text
        ┌──────────────────────── REASONING PLANE ────────────────────────────┐
        │  single-purpose agents — each makes ONE narrow judgement via Claude   │
        │  and emits inert JSON Decisions only (no side effects, no handles)    │
        │                                                                       │
        │   [orchestrator]   [planner]   [editor]   [test-reader]   …           │
        └───────────────────────────────┬───────────────────────────────────────┘
                                        │  Decision data (slips of paper)
                                        ▼
        ┌──────────────────────── DECISION GATE ───────────────────────────────┐
        │  deterministic validate() per tool — accept / reject the proposal      │
        │  (structural checks + per-tool safety: uniqueness, denylist, size)     │
        └───────────────────────────────┬───────────────────────────────────────┘
                                        ▼
        ┌──────────────────────── EXECUTION PLANE ─────────────────────────────┐
        │  deterministic tools (the clerk) run the host effect, then record it   │
        │   fs.read   fs.list   code.write_file   code.apply_patch   shell.exec   │
        └───────────────────────────────┬───────────────────────────────────────┘
                                        ▼
        ┌──────────── DURABLE STATE: hash-chained decision log ─────────────────┐
        │  every accepted Decision recorded before its effect is observable →    │
        │  replay reconstructs state with ZERO model calls (Tenet 3)             │
        └────────────────────────────────────────────────────────────────────────┘
```

The arrow only ever points down. Nothing in the reasoning plane holds a handle to
the file system, the shell, or the network — those exist solely as harness-granted
capabilities the execution plane uses. **Claude is capable, but it sits entirely
above the gate.**

## Why confine a capable model

A frontier model could, in principle, be handed a shell and told to go. The cost
of that convenience is everything this template exists to provide:

```text
   property            how the two planes provide it
   ─────────────────   ────────────────────────────────────────────────────────
   safety              agents hold no handles; a bad generation cannot reach a
                       capability the gate didn't grant (capability-safety)
   reproducibility     the only non-deterministic input is the recorded Decision,
                       so any run replays byte-for-byte with no model call
   auditability        the hash-chained log is the complete account of what every
                       agent decided and what every tool did
   honesty             refusals, failures, and skips are reported as themselves;
                       nothing is hidden or fabricated
```

None of these depend on the model being weak. That is the whole point of the
inversion from jaros-code: the discipline is a governance property, valuable
*because* the model is capable, not in spite of it.

## Plane placement: route each grain to the plane that should own it

```text
   for each grain, ask: is its CORE a judgement Claude should make?
   ─────────────────────────────────────────────────────────────────────────
   YES → tiny AGENT (reasoning plane)      NO → deterministic TOOL (exec plane)
   • route a request to an action          • apply a patch / write bytes
   • plan the steps                        • run a command (denylist-gated)
   • propose one old→new edit              • prove a snippet is unique
   • read a PASS/FAIL result               • enforce size / safety limits
```

Even when Claude *could* do the deterministic part, routing it to a tool is what
makes the system auditable: the model's role shrinks to the judgement, and the
judgement is all that is recorded as non-deterministic input.

## What is in this template

```text
  jaros_claude/            vendored two-plane runtime (self-contained, stdlib-only)
    core/                  Decision, the gate, the JSON-value guard
    execution/            the executor + the dynamic tool loader
    state/                the hash-chained decision log + replay
    llm/                  the LlmClient contract + the Claude adapter
  .jaros-data/
    agents/               single-purpose agents (orchestrator, planner, editor, …)
    tools/                deterministic tools (fs.*, code.*, shell.exec) + safety gate
    config/llm.json       model selection (Claude Opus 4.8, adaptive thinking)
  harness/                the Claude-Code-like CLI + Runtime + agent loop
  tests/                  proofs of the control (gate, replay, agent contracts)
```

## Spec map

```text
  PRIME-001  ── north star (this document; intent.md + design.md)
     ├── EXT-001  deterministic tool plane (fs.read, fs.list, write_file, apply_patch, shell.exec)
     ├── EXT-002  single-purpose Claude agent fleet (orchestrator, planner, editor, test-reader)
     ├── EXT-003  orchestration: gate→executor→log Runtime + the plan→act→observe→replan loop
     └── EXT-004  Claude reasoning adapter behind the narrow LlmClient contract
```

Every `EXT` serves exactly one tenet of the Intent and must never contradict a
higher tenet. New capability is added by widening the fleet and sharpening the
tools — and always behind the gate.

## Adopting this template into your project

`jaros-claude` is a code-building scaffold. When you copy it into a project, you
operate that project with the **same** jarify loop that governs this template:

```text
   how jaros-claude is governed        how you build your project with it
   ────────────────────────────        ──────────────────────────────────
   PRIME-001 (this directive)    ⇄     your project's PRIME directive (your intent)
   EXT-00x requirements/design   ⇄     feature requirements/design for your project
   single-purpose agents +       ⇄     same single-purpose agents + deterministic
     deterministic tools                 tools implement one task at a time
   index.json traceability       ⇄     your code traced back to your spec
```

Capture your intent first, decompose it, implement one scoped task at a time, and
keep every effect behind the gate. Claude does the reasoning; the harness keeps
the authority.
