"""The deterministic executor — the only thing that acts on a Decision.

The executor acts only after the gate accepts a Decision, dispatching it to a
handler registered for the decision's ``type``. Unknown types are refused with a
reason and cause no side effect. This module never imports the LLM side: the
boundary is structural — the reasoning plane proposes, the execution plane acts.

The accepted decision is the run's *sole* replayable input: :func:`apply` offers
an ``on_accept`` hook that fires after the gate accepts and **before** the handler
runs, so the durable decision log can record each accepted decision before its
effects are observable. ``apply`` performs no model call, so a recorded run can
be re-executed from decisions alone.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from jaros_claude.core.decision import Decision
from jaros_claude.core.decision_gate import validate_decision

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExecutionResult:
    """Outcome of an :func:`apply` call.

    Attributes:
        applied: True iff a handler ran and acted on the decision.
        reason: Why the decision was refused (None when ``applied`` is True).
        output: Whatever the handler returned (None when not applied).
        accepted: The gate-accepted decision, surfaced for durable recording.
    """

    applied: bool
    reason: str | None = None
    output: Any = None
    accepted: "Decision | None" = None


# A handler is a deterministic function of the validated decision plus
# execution-plane collaborators (granted handles). It never receives the LLM side.
Handler = Callable[..., Any]

_handlers: dict[str, Handler] = {}


def register_handler(decision_type: str, fn: Handler) -> Handler:
    """Register the handler the executor dispatches to for ``decision_type``."""
    _handlers[decision_type] = fn
    return fn


def reset_handlers() -> None:
    """Clear all registered handlers. Intended for test isolation."""
    _handlers.clear()


def apply(
    d: Decision,
    *,
    on_accept: "Callable[[Decision], None] | None" = None,
    **collaborators: Any,
) -> ExecutionResult:
    """Validate ``d`` via the gate, then dispatch to its ``type`` handler.

    On gate rejection the reason is logged and a non-applied result is returned
    with no state mutation. If the decision's ``type`` has no registered handler
    the decision is refused with a clear reason and no side effect. Otherwise the
    handler runs with the validated decision and any execution-plane
    ``collaborators`` — never the reasoning side.

    ``on_accept`` fires once with the gate-accepted decision *before* the handler
    runs, so a caller can durably record it for replay before its effects are
    observable.
    """
    result = validate_decision(d)
    if not result.ok:
        logger.warning("decision %r rejected by gate: %s", getattr(d, "id", "?"), result.reason)
        return ExecutionResult(applied=False, reason=result.reason)

    validated = result.value
    assert validated is not None

    handler = _handlers.get(validated.type)
    if handler is None:
        reason = f"no handler registered for decision type {validated.type!r}"
        logger.warning("decision %r refused: %s", validated.id, reason)
        return ExecutionResult(applied=False, reason=reason, accepted=validated)

    if on_accept is not None:
        on_accept(validated)

    output = handler(validated, **collaborators)
    return ExecutionResult(applied=True, output=output, accepted=validated)
