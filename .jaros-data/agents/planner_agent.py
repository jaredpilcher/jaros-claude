"""Single-purpose agent ``planner`` (EXT-002 / REQ-3).

Given a request (optionally grounded with the repo's file list), emits an inert
plan: an ordered list of {action, arg} steps over the known verb set. The plan is
pure data — the agent_loop executes each step through the deterministic tools and
specialist agents. The model decides the steps; the tools do the work.
"""

from __future__ import annotations

import re
import uuid

from jaros_claude.core import create_decision
from jaros_claude.llm import LlmRequest

NAME = "planner"

VERBS = ("read", "find", "edit", "write", "run")

_PROMPT = (
    "Break the developer's REQUEST into a short ordered plan of concrete steps.\n"
    "Each step is one line: ACTION: ARG\n"
    "ACTION is one of: read | find | edit | write | run\n"
    "  read <file>            — read a file\n"
    "  find <symbol>          — locate where a symbol is used\n"
    "  edit <file>: <change>  — change a file\n"
    "  write <file>: <intent> — create/replace a file\n"
    "  run <command>          — run a command (e.g. tests)\n"
    "Output ONLY the step lines, at most 8, no commentary.\n\n"
    "REQUEST: {request}\n"
)

_STEP_RE = re.compile(r"^\s*(read|find|edit|write|run)\s*:?\s*(.*)$", re.I)


def parse_plan(text: str) -> list[dict]:
    steps = []
    for line in text.splitlines():
        m = _STEP_RE.match(line)
        if not m:
            continue
        action = m.group(1).lower()
        arg = m.group(2).strip().strip("`'\"")
        if action in VERBS:
            steps.append({"action": action, "arg": arg})
    return steps


class PlannerBoundary:
    def __init__(self, llm) -> None:
        self._llm = llm

    def decide(self, context) -> list:
        ctx = context if isinstance(context, dict) else {}
        request = ctx.get("request", str(context))
        reply = self._llm.complete(LlmRequest(prompt=_PROMPT.format(request=request))).text
        plan = parse_plan(reply)
        return [create_decision(
            id=f"plan-{uuid.uuid4().hex}", source=NAME, type="advance",
            payload={"events": ["start", "complete"], "plan": plan,
                     "note": f"planner: {len(plan)} step(s)"})]


def build(llm) -> PlannerBoundary:
    return PlannerBoundary(llm)
