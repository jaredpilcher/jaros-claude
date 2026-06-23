---
id: EXT-004
title: Claude Reasoning Adapter behind the LlmClient Contract
status: implemented
priority: high
serves: PRIME-001 Tenet 2 (Claude is the reasoning model, confined to data-in/data-out)
---

This spec serves **Tenet 2** of PRIME-001: all reasoning is Claude, accessed
through one narrow, provider-neutral contract. The model returns inert data only;
it holds no handles and drives no execution.

## Requirements

- **REQ-1 `LlmClient` contract** — a provider-neutral `complete(LlmRequest) ->
  LlmResponse` Protocol. `LlmRequest`/`LlmResponse` carry inert JSON-serializable
  data only — no callbacks, sockets, or client instances cross the boundary.
  (`jaros_claude/llm/client.py`)
- **REQ-2 Claude adapter** — `ClaudeClient` implements the contract over the
  Anthropic Messages API, defaulting to `claude-opus-4-8` with adaptive thinking
  and configurable effort. It reads `ANTHROPIC_API_KEY` from the environment,
  surfaces errors and refusals honestly (Tenet 3), and never performs a side
  effect. A `health()` probe reports reachability for `/status`.
  (`jaros_claude/llm/claude_client.py`)

Model selection is configured in `.jaros-data/config/llm.json` and overridable
via `JCLAUDE_MODEL` / `JCLAUDE_EFFORT` / `JCLAUDE_MAX_TOKENS`.
