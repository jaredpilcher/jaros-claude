---
id: EXT-003
title: Orchestration — Runtime, Decision Log, and the Agentic Loop
status: implemented
priority: high
serves: PRIME-001 Tenet 1 & 3 (gate→execute→record; reproducible & honest)
---

This spec serves **Tenets 1 and 3** of PRIME-001: the single choke point through
which every Decision flows, and the durable record that makes any run replayable.

## Requirements

- **REQ-1 Runtime** — `Runtime.apply(decision)`: validate at the gate, record the
  accepted Decision in the hash-chained log *before* the effect is observable,
  then dispatch to the matching tool. The one path nothing reaches the host
  without. (`harness/runtime.py`)
- **REQ-2 Agentic loop** — plan → act → observe → replan over the verb set, with
  an injectable planner so the loop is testable without a model. Every step's
  side effect routes through `Runtime.apply`. (`harness/agent_loop.py`)
- **REQ-3 Operator surface** — a Claude-Code-like CLI (REPL + one-shot) exposing
  `/status /read /list /edit /write /run /plan /agent /log`, and routing plain
  requests through the orchestrator. (`harness/cli.py`)
- **REQ-4 Decision log** — a durable, append-only, hash-chained log; `replay`
  re-executes recorded decisions through the deterministic executor with zero
  model calls; `verify_chain` detects any tampering.
  (`jaros_claude/state/decision_log.py`)
