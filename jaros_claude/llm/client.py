"""The single, provider-agnostic LLM interface.

All model access in the Reasoning Plane goes through one narrow contract,
:class:`LlmClient`, with a single entry point: ``complete``. Callers depend only
on this interface and the provider-neutral request/response dataclasses — no
concrete provider type ever leaks to a caller.

The LLM decides *what* to propose, never *how* the system runs. What crosses this
boundary is **data only**: an :class:`LlmRequest` in, an :class:`LlmResponse` out.
The response carries inert ``text``/``structured``/``model`` data and nothing
that can perform a side effect or drive a state transition. Reasoning consumes
the response and may emit a ``Decision`` (which the gate validates); the LLM
itself never executes anything.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from jaros_claude.core.json_value import JsonValue


@dataclass(frozen=True)
class LlmRequest:
    """A provider-neutral request to an :class:`LlmClient`.

    Attributes:
        prompt: The input text the model should reason over.
        params: Optional, inert JSON-serializable tuning parameters
            (e.g. ``{"effort": "high", "max_tokens": 4096}``).
    """

    prompt: str
    params: dict[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True)
class LlmResponse:
    """A provider-neutral, data-only response from an :class:`LlmClient`.

    Attributes:
        text: The primary textual output of the model.
        model: Identifier of the model that produced this response.
        structured: Optional structured output as inert JSON data.
    """

    text: str
    model: str
    structured: JsonValue = None


@runtime_checkable
class LlmClient(Protocol):
    """The single, narrow interface every model adapter satisfies.

    Callers depend only on this Protocol — never on a concrete provider. The sole
    entry point, :meth:`complete`, takes inert data in and returns inert data out;
    it must not perform side effects, hold system handles, or drive execution.
    """

    def complete(self, req: LlmRequest) -> LlmResponse:
        """Produce a data-only :class:`LlmResponse` for ``req``."""
        ...
