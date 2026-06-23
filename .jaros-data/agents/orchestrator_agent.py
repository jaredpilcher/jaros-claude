"""Single-purpose agent ``orchestrator`` (EXT-002 / REQ-1).

Given a user's natural-language request, it decides WHICH action should serve it
and emits an inert routing Decision. The model decides *what* the user wants; the
deterministic CLI decides *how* to carry it out (dispatching to the matching
tool). One narrow judgement, a tiny output contract — never a side effect.
"""

from __future__ import annotations

import re
import uuid

from jaros_claude.core import create_decision
from jaros_claude.llm import LlmRequest

NAME = "orchestrator"

ACTIONS = ("read", "list", "edit", "write", "run", "plan", "help")

_PROMPT = (
    "You route a developer's request to exactly ONE action and give its argument.\n"
    "Output EXACTLY two lines and nothing else:\n"
    "ACTION: <one of: read | list | edit | write | run | plan | help>\n"
    "ARG: <the file path, command, or instruction — or empty>\n\n"
    "Guide: showing a file = read; listing a directory = list; changing a file = edit; "
    "creating/replacing a file = write; running a command/tests = run; breaking a task "
    "into steps = plan.\n\n"
    "REQUEST: {request}\n"
)

_ACTION_RE = re.compile(r"ACTION:\s*([a-zA-Z]+)", re.I)
_ARG_RE = re.compile(r"ARG:\s*(.*)", re.I)


def parse_route(text: str):
    a = _ACTION_RE.search(text)
    g = _ARG_RE.search(text)
    action = (a.group(1).lower() if a else "")
    if action not in ACTIONS:
        for cand in ACTIONS:
            if re.search(rf"\b{cand}\b", text.lower()):
                action = cand
                break
        else:
            action = "help"
    arg = (g.group(1).strip() if g else "").strip().strip("`'\"")
    return action, arg


class OrchestratorBoundary:
    def __init__(self, llm) -> None:
        self._llm = llm

    def decide(self, context) -> list:
        ctx = context if isinstance(context, dict) else {}
        request = ctx.get("request", str(context))
        reply = self._llm.complete(LlmRequest(prompt=_PROMPT.format(request=request))).text
        action, arg = parse_route(reply)
        return [create_decision(
            id=f"orch-{uuid.uuid4().hex}", source=NAME, type="advance",
            payload={"events": ["start", "complete"], "action": action, "arg": arg,
                     "note": f"orchestrator: route -> {action} {arg}".strip()})]


def build(llm) -> OrchestratorBoundary:
    return OrchestratorBoundary(llm)
