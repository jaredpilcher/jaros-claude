"""Agents emit inert Decisions and never touch the host — proven with a fake LLM.

A `FakeLlm` stands in for Claude so these run offline and deterministically. The
point is the *contract*: given a model reply, the agent emits a well-formed inert
Decision (or an honest no-op), and nothing executes inside the agent.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from jaros_claude.core import Decision  # noqa: E402
from jaros_claude.llm import LlmResponse  # noqa: E402
from harness.runtime import load_agent  # noqa: E402


class FakeLlm:
    def __init__(self, reply: str) -> None:
        self._reply = reply

    def complete(self, req) -> LlmResponse:
        return LlmResponse(text=self._reply, model="fake")


def test_orchestrator_routes_to_one_action():
    agent = load_agent("orchestrator_agent.py", FakeLlm("ACTION: read\nARG: foo.py"))
    [d] = agent.decide({"request": "show me foo.py"})
    assert isinstance(d, Decision)
    assert d.payload["action"] == "read"
    assert d.payload["arg"] == "foo.py"


def test_editor_emits_apply_patch():
    reply = "<<<OLD\nx = 1\nOLD>>>\n<<<NEW\nx = 2\nNEW>>>"
    agent = load_agent("editor_agent.py", FakeLlm(reply))
    [d] = agent.decide({"path": "f.py", "content": "x = 1\n", "instruction": "bump"})
    assert d.type == "code.apply_patch"
    assert d.payload == {"path": "f.py", "old": "x = 1", "new": "x = 2"}


def test_editor_honest_noop_when_unparseable():
    agent = load_agent("editor_agent.py", FakeLlm("I cannot do that"))
    [d] = agent.decide({"path": "f.py", "content": "x = 1\n", "instruction": "?"})
    assert d.type == "advance"  # honest no-op, not a fabricated edit


def test_planner_emits_inert_plan():
    reply = "read foo.py\nedit foo.py: fix the bug\nrun python -m pytest -q"
    agent = load_agent("planner_agent.py", FakeLlm(reply))
    [d] = agent.decide({"request": "fix foo"})
    plan = d.payload["plan"]
    assert [s["action"] for s in plan] == ["read", "edit", "run"]


def test_test_reader_reads_verdict():
    agent = load_agent("test_reader_agent.py", FakeLlm("VERDICT: fail\nREASON: assert 1 == 2"))
    [d] = agent.decide({"output": "E assert 1 == 2"})
    assert d.payload["verdict"] == "fail"
