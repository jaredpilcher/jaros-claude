# jaros-claude

A **template** that applies the **two-plane control discipline** of Jaros and
jaros-code to **Claude**. Copy this repository's contents into another project and
that project inherits the discipline: Claude does the reasoning, but **every side
effect Claude wants is mediated by a deterministic gate and deterministic tools**.
The model proposes inert `Decision` data; the harness performs the effects.

Reasoning is served by **Claude (Anthropic Messages API)**, default
`claude-opus-4-8` with adaptive thinking. Set `ANTHROPIC_API_KEY`; override with
`JCLAUDE_MODEL` / `JCLAUDE_EFFORT` / `JCLAUDE_MAX_TOKENS`.

## Governance (binds every run)

This repo is governed by `.jarify/`. **`PRIME-001` is the Prime Directive** — read
`.jarify/PRIME-001/intent.md` before any structural change. Its five ordered
tenets are non-negotiable; a lower tenet is never weakened for a higher one:

1. **Two-plane discipline** — the model emits only inert `Decision` data; a
   deterministic execution plane (gate + tools) performs every side effect. This
   is the control, and it does not relax because the model is capable.
2. **Claude, confined to the reasoning plane** — all reasoning is Claude, but
   Claude holds no host handles and drives no execution; every effect passes the
   gate. Decompose for control and auditability, not to compensate for the model.
3. **Reproducible & honest** — every accepted Decision is hash-chain logged before
   its effect is observable; the log replays with zero model calls; refusals,
   failures, and skips are reported as themselves, never hidden or fabricated.
4. **Spec-first** — code traces to `.jarify` requirements; spec + code change in
   the same commit; stale specs are defects.
5. **Claude-Code-like UX** — familiar, transparent terminal feel, but UX never
   overrides the tenets above it.

When a change would violate a tenet, **STOP and flag the conflict** — do not
silently resolve it.

## The inversion (why this template exists)

jaros-code's wager: *a small model becomes useful when the harness is strong.*
jaros-claude's wager: *a strong model becomes safe, reproducible, and auditable
when the harness is in control.* Same architecture; the motivation generalizes.
The discipline never depended on the model being weak — it is a governance
property (safety, reproducibility, auditability), and it is exactly as valuable
with a frontier model doing the reasoning.

## Design rules

- **Agents are single-purpose.** Each agent makes ONE narrow judgement and emits
  inert Decisions. Capability comes from composing many small agents behind the
  gate, not one big agent.
- **Tools are deterministic.** Every host effect (read, write, shell, patch) is a
  tool with `validate()` + `execute()`. Agents never touch the host.
- **Plane-placement triage.** For each grain ask: is its core a judgement Claude
  should make (→ a tiny agent emitting a Decision) or a deterministic operation
  the host should perform (→ a tool behind the gate)? Even when Claude *could* do
  the deterministic part, route it to a tool — that is what makes the run
  auditable and safe.

## Layout

```
jaros_claude/        vendored two-plane runtime (self-contained, stdlib-only)
  core/              Decision, the gate, the JSON-value guard
  execution/         the executor + the dynamic tool loader
  state/             the hash-chained decision log + replay
  llm/               the LlmClient contract + the Claude adapter
.jaros-data/
  agents/            single-purpose agents (orchestrator, planner, editor, test-reader)
  tools/             deterministic tools (fs.*, code.*, shell.exec) + the safety gate
  config/llm.json    model selection
harness/             the Claude-Code-like CLI + Runtime + agent loop
tests/               proofs of the control (gate, replay, agent contracts)
```

## Running

```
export ANTHROPIC_API_KEY=sk-ant-...
bash scripts/jclaude.sh                 # interactive REPL (POSIX)
pwsh scripts/jclaude.ps1                # interactive REPL (Windows)
python -m harness.cli /status           # one command and exit
python -m harness.cli "fix foo.py"      # one plain request (orchestrator routes it)
python -m pytest -q                     # the control tests (no API key needed)
```

In the REPL, type `/help` for slash commands, or just type a plain request — the
`orchestrator` agent (Claude) routes it. `/quit` exits. The control tests run
offline with a fake LLM, so you can verify the discipline without spending a token.

## Adopting this template into your project

Copy the contents in, then run your project with the **same** jarify loop that
governs this template: capture *your* intent as that project's PRIME directive,
decompose it into requirements/design/tasks, implement one scoped task at a time
with single-purpose agents, and keep every effect behind the gate. Claude does the
reasoning; the harness keeps the authority. Add capability by widening the agent
fleet and sharpening the tools — always behind the gate.

## Commit discipline

Commit often: after each verified logical unit, commit code + spec together with a
descriptive message. Never commit `.env`, secrets, logs, or runtime state
(`.gitignore` covers `.jaros-data` runtime dirs). Footer:
`Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
