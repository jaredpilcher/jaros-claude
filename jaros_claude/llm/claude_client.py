"""Claude reasoning client (the Anthropic Messages API behind the LlmClient contract).

This is the one place the harness talks to a model. It uses the official
``anthropic`` SDK and Claude Opus 4.8 (`claude-opus-4-8`) by default, with
adaptive thinking — the recommended configuration for capable agentic reasoning.

Two-plane discipline holds regardless of how capable the model is: this client
returns **only inert text/data**. It never performs a side effect, holds a host
handle, or drives execution. Whatever Claude proposes becomes a ``Decision`` that
the deterministic gate validates before any tool runs. The model is powerful, but
its authority stops at the boundary — that is the control this template exists to
apply to Claude.

Configuration (env, all optional except the key):
  ANTHROPIC_API_KEY     # required — your Anthropic API key
  JCLAUDE_MODEL         # model id (default: claude-opus-4-8)
  JCLAUDE_EFFORT        # low | medium | high | xhigh | max (default: high)
  JCLAUDE_MAX_TOKENS    # output cap (default: 16000)
"""

from __future__ import annotations

import os

from jaros_claude.llm.client import LlmRequest, LlmResponse

DEFAULT_MODEL = "claude-opus-4-8"
DEFAULT_EFFORT = "high"
DEFAULT_MAX_TOKENS = 16000


class ClaudeClient:
    """Anthropic Messages API adapter satisfying the :class:`LlmClient` contract."""

    def __init__(
        self,
        model: str | None = None,
        *,
        effort: str | None = None,
        max_tokens: int | None = None,
        api_key: str | None = None,
    ) -> None:
        self.model = model or os.environ.get("JCLAUDE_MODEL", DEFAULT_MODEL)
        self.effort = effort or os.environ.get("JCLAUDE_EFFORT", DEFAULT_EFFORT)
        self.max_tokens = max_tokens or int(
            os.environ.get("JCLAUDE_MAX_TOKENS", str(DEFAULT_MAX_TOKENS))
        )
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._client = None  # lazily constructed so import never requires the SDK

    def _ensure_client(self):
        if self._client is not None:
            return self._client
        try:
            import anthropic
        except ImportError as exc:  # honest failure (Tenet 3) — never fabricate
            raise RuntimeError(
                "The 'anthropic' package is required for the Claude client. "
                "Install it with `pip install anthropic`."
            ) from exc
        if not self._api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Export your Anthropic API key before "
                "running the harness."
            )
        self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def complete(self, req: LlmRequest) -> LlmResponse:
        """Send one prompt to Claude and return its text as inert data.

        Per-request overrides may be passed via ``req.params`` (``effort``,
        ``max_tokens``). Errors are surfaced, never hidden or faked (Tenet 3).
        """
        client = self._ensure_client()
        params = req.params if isinstance(req.params, dict) else {}
        effort = params.get("effort", self.effort)
        max_tokens = int(params.get("max_tokens", self.max_tokens))

        try:
            message = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                thinking={"type": "adaptive"},
                output_config={"effort": effort},
                messages=[{"role": "user", "content": req.prompt}],
            )
        except Exception as exc:  # surfaced to the caller, never swallowed
            raise RuntimeError(f"Claude request failed ({self.model}): {exc}") from exc

        if getattr(message, "stop_reason", None) == "refusal":
            details = getattr(message, "stop_details", None)
            reason = getattr(details, "explanation", None) or "model declined the request"
            raise RuntimeError(f"Claude refused the request: {reason}")

        text = "".join(
            block.text for block in message.content if getattr(block, "type", None) == "text"
        ).strip()
        return LlmResponse(text=text, model=getattr(message, "model", self.model))


def health(model: str | None = None) -> dict:
    """Probe reachability: returns {ok, model, error?}. Used by `/status`."""
    try:
        client = ClaudeClient(model=model)
        resp = client.complete(LlmRequest(prompt="Reply with the single word: ok"))
        return {"ok": True, "model": resp.model, "sample": resp.text[:40]}
    except Exception as exc:  # noqa: BLE001 — reported honestly
        return {"ok": False, "model": model or DEFAULT_MODEL, "error": str(exc)}
