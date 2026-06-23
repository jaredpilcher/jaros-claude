# jaros-claude

**Claude under two-plane control — as a copy-in template.** A software-development
agent harness that gives Claude the same disciplined control over agent decisions
that **Jaros** and **jaros-code** apply to a small local model: the model only
emits inert `Decision` data, and a deterministic execution plane — a gate that
validates and tools that act — performs every side effect.

You copy this repository's contents into another project, and that project
inherits the discipline: every reasoning call is Claude, every effect is gated,
every decision is recorded and replayable.

## The idea

jaros-code's bet is that a *small* model becomes useful when the harness is
strong. jaros-claude flips the motivation: a *strong* model becomes **safe,
reproducible, and auditable** when the harness is in control. The architecture is
identical — only the reason changes.

- **Two-plane discipline.** Claude emits inert `Decision` data; a deterministic,
  gate-checked execution plane (tools) performs every side effect. A wrong or
  unsafe proposal is rejected at the gate, never executed.
- **Confine the capable model.** Claude holds no host handles and drives no
  execution. Even a correct proposal runs only through the deterministic plane.
- **Record and replay.** Every accepted Decision is hash-chain logged before its
  effect is observable; the log replays through the deterministic executor with
  **zero model calls**, reconstructing any run. Tampering is detectable.

The control is a governance property — safety, reproducibility, auditability — and
none of it depends on the model being weak.

```
request ─► Claude (inert Decision) ─► gate/validate ─► deterministic tools (effects) ─► hash-chained, replayable log
```

## What's in the box

| Piece | What it is |
|---|---|
| `jaros_claude/` | A self-contained, stdlib-only two-plane runtime: `Decision`, the gate, the executor, the tool loader, and the hash-chained decision log. |
| `jaros_claude/llm/` | The narrow `LlmClient` contract and the `ClaudeClient` adapter (Anthropic Messages API, Claude Opus 4.8, adaptive thinking). |
| `.jaros-data/agents/` | Single-purpose Claude agents: `orchestrator`, `planner`, `editor`, `test-reader`. Each makes one judgement and emits a Decision. |
| `.jaros-data/tools/` | Deterministic tools: `fs.read`, `fs.list`, `code.write_file`, `code.apply_patch`, `shell.exec` — each with `validate()` + `execute()` and a safety gate. |
| `harness/` | The Claude-Code-like CLI, the gate→execute→record `Runtime`, and a plan→act→observe→replan loop. |
| `.jarify/` | The governance: `PRIME-001` (the Prime Directive) plus `EXT-001..004`, with `index.json` traceability. |
| `tests/` | Proofs that the control holds — run offline with a fake LLM, no API key needed. |

## CLI

```
export ANTHROPIC_API_KEY=sk-ant-...
python -m harness.cli                 # interactive REPL
python -m harness.cli /status         # one command and exit
python -m harness.cli "fix foo.py"    # one plain request (orchestrator routes it)
```

Slash commands: `/status /read /list /edit /write /run /plan /agent /log /help /quit`.
A plain request is routed by the `orchestrator` agent (Claude) to one action;
the action runs through the gate and tools, and every decision lands in the log.

## Try the control without a key

```
python -m pytest -q
```

The tests prove the discipline offline (a fake LLM stands in for Claude): the
gate rejects malformed and unsafe proposals, the decision log replays
byte-for-byte with zero model calls, tampering is detected, and agents emit only
inert Decisions.

## Governance

The repo is governed by `.jarify/` specifications; **`PRIME-001` is the Prime
Directive**. Its five ordered, non-negotiable tenets: (1) two-plane discipline,
(2) Claude confined to the reasoning plane, (3) reproducible & honest,
(4) spec-first, (5) Claude-Code-like UX — a lower tenet is never weakened for a
higher one. See `CLAUDE.md` for the working agreement and `.jarify/PRIME-001/` for
the full intent and architecture.

## Requirements

- Python 3.10+
- `anthropic` (`pip install anthropic`) — only needed to actually call Claude; the
  runtime and tests are stdlib-only.
- `ANTHROPIC_API_KEY` in the environment.

---

*Claude does the reasoning. The harness keeps the authority. That's the whole point.*
