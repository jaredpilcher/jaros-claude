"""jaros-claude — the two-plane control discipline, applied to Claude.

The model (Claude) only ever emits inert ``Decision`` data. A deterministic
execution plane — a gate that validates and tools that act — performs every side
effect. Capability comes from a capable model *under control*, not from letting
the model touch the host directly.

This package is the vendored runtime: import it, drop in agents and tools, and
you have the same disciplined control over agent decisions that Jaros and
jaros-code apply to a small local model — but with Claude doing the reasoning.
"""

from jaros_claude.core import (
    Decision,
    ValidationResult,
    create_decision,
    validate_decision,
)

__all__ = [
    "Decision",
    "ValidationResult",
    "create_decision",
    "validate_decision",
]
