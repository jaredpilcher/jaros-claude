"""The deterministic decision validation gate.

Every Decision passes this total, deterministic gate before any executor acts.
Built-in structural checks always run first and cannot be removed; each tool
registers an additional pure validator that runs, in registration order,
afterwards. The first rejection short-circuits and no decision is accepted.

This is where **control** lives: a malformed, unsafe, or unauthorized proposal
from the model is rejected here, deterministically, before it can touch the host.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from jaros_claude.core.decision import Decision
from jaros_claude.core.json_value import NotSerializableError, assert_serializable


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of the gate: either an accepted decision or a typed rejection.

    Attributes:
        ok: True if the decision passed every validator.
        value: The normalized decision when ``ok`` is True, else None.
        reason: A human-readable rejection reason when ``ok`` is False, else None.
    """

    ok: bool
    value: Decision | None
    reason: str | None

    @staticmethod
    def accept(value: Decision) -> "ValidationResult":
        return ValidationResult(ok=True, value=value, reason=None)

    @staticmethod
    def reject(reason: str) -> "ValidationResult":
        return ValidationResult(ok=False, value=None, reason=reason)


# A registered validator is a pure function of the Decision returning either an
# accept (value carries the possibly-normalized decision) or a typed rejection.
Validator = Callable[[Decision], ValidationResult]

_validators: list[Validator] = []


def register_validator(fn: Validator) -> Validator:
    """Register an additional deterministic validator.

    Validators run after the built-in structural checks, in registration order.
    A validator must be a pure function of the decision (no side effects) so the
    gate stays deterministic. Returns ``fn`` so it may be used as a decorator.
    """
    _validators.append(fn)
    return fn


def reset_validators() -> None:
    """Clear all registered validators. Intended for test isolation."""
    _validators.clear()


def _structural_check(d: Decision) -> ValidationResult:
    """Built-in structural validation. Always runs first; cannot be removed."""
    if not isinstance(d, Decision):
        return ValidationResult.reject("decision is not a Decision instance")
    if not isinstance(d.id, str) or not d.id:
        return ValidationResult.reject("decision id must be a non-empty string")
    if not isinstance(d.source, str) or not d.source:
        return ValidationResult.reject("decision source must be a non-empty string")
    if not isinstance(d.type, str) or not d.type:
        return ValidationResult.reject("decision type must be a non-empty string")
    try:
        assert_serializable(d.payload)
    except NotSerializableError as exc:
        return ValidationResult.reject(f"decision payload is not serializable: {exc}")
    return ValidationResult.accept(d)


def validate_decision(d: Decision) -> ValidationResult:
    """Validate ``d`` deterministically and totally.

    Built-in structural checks run first; if they pass, every registered
    validator runs in registration order. The first rejection short-circuits and
    returns its reason. Returns a normalized accepted decision otherwise.
    """
    structural = _structural_check(d)
    if not structural.ok:
        return structural
    current = structural.value
    assert current is not None
    for validator in _validators:
        result = validator(current)
        if not result.ok:
            return result
        if result.value is not None:
            current = result.value
    return ValidationResult.accept(current)
