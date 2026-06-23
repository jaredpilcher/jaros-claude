"""The inert Decision contract — the only thing the Reasoning Plane may emit.

A Decision is immutable, JSON-serializable data: it carries intent (``type``) and
inert ``payload`` data, never callbacks, closures, or handles. It records its
``source`` (the emitting agent) and a discriminated ``type`` so the deterministic
executor can dispatch on it. This is the heart of the two-plane discipline:
**Claude proposes a Decision; it never performs the effect itself.**
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from jaros_claude.core.json_value import JsonValue, assert_serializable


@dataclass(frozen=True)
class Decision:
    """An immutable, JSON-serializable proposal emitted by the Reasoning Plane.

    Attributes:
        id: Unique identifier for this decision.
        source: Identifier of the emitting agent/source.
        type: Discriminator used for deterministic executor dispatch.
        payload: Inert, JSON-serializable data only.
    """

    id: str
    source: str
    type: str
    payload: JsonValue


def create_decision(*, id: str, source: str, type: str, payload: JsonValue) -> Decision:
    """Construct a validated, frozen :class:`Decision`.

    The payload is asserted to be inert JSON data and proven round-trippable
    (serialize -> deserialize -> identical), guaranteeing the Decision carries no
    executable side effect.

    Raises:
        NotSerializableError: if the payload contains non-serializable values.
        ValueError: if the payload is not JSON round-trippable.
    """
    assert_serializable(payload)
    if json.loads(json.dumps(payload)) != payload:
        raise ValueError("payload is not JSON round-trippable")
    return Decision(id=id, source=source, type=type, payload=payload)
