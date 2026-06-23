---
id: EXT-002
title: Single-Purpose Claude Agent Fleet
status: implemented
priority: high
serves: PRIME-001 Tenet 2 (Claude confined to the reasoning plane)
---

This spec serves **Tenet 2** of PRIME-001: all reasoning is Claude, and each
agent makes ONE narrow judgement and emits inert `Decision` data only. Agents
hold no host handles; capability comes from composing many small agents behind
the gate, not from one big agent.

## Requirements

- **REQ-1 `orchestrator`** — route a natural-language request to exactly one
  action (read | list | edit | write | run | plan | help), emitting an inert
  routing Decision. (`.jaros-data/agents/orchestrator_agent.py`)
- **REQ-2 `editor`** — given a file and an instruction, propose ONE exact old→new
  edit and emit a `code.apply_patch` Decision (or an honest no-op if it cannot).
  (`.jaros-data/agents/editor_agent.py`)
- **REQ-3 `planner`** — break a request into an ordered, inert plan of steps over
  the verb set. (`.jaros-data/agents/planner_agent.py`)
- **REQ-4 `test-reader`** — read raw test output and emit a PASS/FAIL verdict with
  the salient failure. (`.jaros-data/agents/test_reader_agent.py`)

Every agent exposes `build(llm)` and a `decide(context) -> [Decision]` boundary.
The Decision is the only thing it emits — never a side effect. Adding capability
means adding more small agents, each behind the same gate.
