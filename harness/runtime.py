"""The faithful two-plane execution path: gate -> executor -> hash-chained log.

`Runtime.apply` is the single choke point every Decision passes through. It
validates at the deterministic gate, dispatches to the matching tool, and records
the accepted Decision in the hash-chained log *before* the effect is observable.
Nothing reaches the host except through here — that is the control this template
applies to Claude.

`build_llm` returns the Claude reasoning client. `load_agent` loads a
single-purpose agent and wires it to that client. Agents propose; the Runtime
disposes.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from jaros_claude.core.decision_gate import validate_decision
from jaros_claude.execution import executor
from jaros_claude.execution.tools import load_custom_tools
from jaros_claude.state import DecisionLog, record_decision

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / ".jaros-data"
AGENTS_DIR = DATA_DIR / "agents"
TOOLS_DIR = DATA_DIR / "tools"
STATE_DIR = DATA_DIR / "state"


def _advance_handler(decision, **_collaborators):
    """Handler for inert ``advance`` Decisions (judgements/routes that carry no host effect).

    Recording them keeps the decision log a complete, replayable transcript of what
    every agent decided — even the steps that only produced data, not a side effect.
    """
    return {"tool": "advance", "payload": decision.payload}


class Runtime:
    """Faithful execution path: gate -> executor -> decision log."""

    _bootstrapped = False

    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        state_dir = data_dir / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        if not Runtime._bootstrapped:
            executor.register_handler("advance", _advance_handler)
            load_custom_tools(data_dir / "tools")  # registers fs.*, code.*, shell.exec
            Runtime._bootstrapped = True
        self._dlog = DecisionLog(state_dir)
        self._dlog.ensure()

    def apply(self, decision):
        """Validate at the gate, record the accepted Decision, then execute."""
        gated = validate_decision(decision)
        if not gated.ok:
            raise RuntimeError(f"gate rejected {decision.type}: {gated.reason}")
        outcome = executor.apply(
            decision, on_accept=lambda d: record_decision(self._dlog, d)
        )
        if not outcome.applied:
            raise RuntimeError(f"executor refused {decision.type}: {outcome.reason}")
        return outcome.output

    @property
    def log(self) -> DecisionLog:
        return self._dlog


def build_llm():
    """Return the Claude reasoning client (the only model the harness ever calls)."""
    from jaros_claude.llm import ClaudeClient

    return ClaudeClient()


def load_agent(filename: str, llm):
    """Load a single-purpose agent module and build it against ``llm``."""
    path = AGENTS_DIR / filename
    spec = importlib.util.spec_from_file_location(f"jaros_claude_agent_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build(llm)
