"""Dynamic execution-plane tool loader and registry.

Each tool is a small class with ``NAME``, a deterministic ``validate()`` (which
contributes to the gate) and an ``execute()`` (which the executor dispatches to).
This loader scans a directory, imports each module, and wires its tool into both
the gate and the executor — so adding a capability is dropping in one file.

Capability-safety is structural: agents (the reasoning plane) hold no host
handles; every host effect exists solely as a tool the execution plane runs.
"""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from typing import Any, Callable

from jaros_claude.core.decision import Decision
from jaros_claude.core.decision_gate import ValidationResult, register_validator
from jaros_claude.execution import executor

logger = logging.getLogger(__name__)

_loaded_tools: set[str] = set()


def load_custom_tools(tools_dir: Path) -> list[str]:
    """Scan ``tools_dir``, import each module, and register its tool.

    Idempotent: tools already imported are skipped, permitting repeated scans.
    Files beginning with ``_`` are treated as private helpers and skipped.
    """
    loaded_names: list[str] = []
    tools_dir = Path(tools_dir)

    if not tools_dir.exists():
        tools_dir.mkdir(parents=True, exist_ok=True)
        return loaded_names

    for path in sorted(tools_dir.glob("*.py")):
        if path.name.startswith("_"):
            continue
        abs_path = str(path.resolve())
        if abs_path in _loaded_tools:
            continue
        try:
            module_name = f"jaros_claude_tool_{path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            tool_class = None
            for name in dir(module):
                obj = getattr(module, name)
                if (
                    isinstance(obj, type)
                    and hasattr(obj, "NAME")
                    and hasattr(obj, "validate")
                    and hasattr(obj, "execute")
                ):
                    tool_class = obj
                    break
            if tool_class is None:
                logger.warning("No valid tool class found in %s", path.name)
                continue

            tool_instance = tool_class()
            action_name = tool_instance.NAME

            def make_validator(inst: Any) -> Callable[[Decision], ValidationResult]:
                def validator(d: Decision) -> ValidationResult:
                    if d.type == inst.NAME:
                        return inst.validate(d)
                    return ValidationResult.accept(d)

                return validator

            register_validator(make_validator(tool_instance))
            executor.register_handler(action_name, tool_instance.execute)

            _loaded_tools.add(abs_path)
            loaded_names.append(action_name)
            logger.info("Registered execution-plane tool: %s", action_name)
        except Exception as exc:  # fault isolation: a bad tool never crashes the loader
            logger.error("Failed to load custom tool from %s: %s", path.name, exc)

    return loaded_names


def reset_tools_registry() -> None:
    """Clear the registered-tools tracker. Intended for tests."""
    _loaded_tools.clear()
