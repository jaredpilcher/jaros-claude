"""Single-purpose agent ``test-reader`` (EXT-002 / REQ-4).

Reads raw test output and makes ONE narrow judgement: did the suite pass, and if
not, what is the single most salient failure? Emits an inert verdict Decision.
Reading a PASS/FAIL result is exactly the kind of bounded judgement a model is
reliable at — and it stays in the reasoning plane, emitting data only.
"""

from __future__ import annotations

import re
import uuid

from jaros_claude.core import create_decision
from jaros_claude.llm import LlmRequest

NAME = "test-reader"

_MAX_OUTPUT = 6000

_PROMPT = (
    "You read test-runner output and judge the result. Output EXACTLY two lines:\n"
    "VERDICT: <pass | fail>\n"
    "REASON: <one short sentence — the key failure, or 'all tests passed'>\n\n"
    "TEST OUTPUT:\n{output}\n"
)

_VERDICT_RE = re.compile(r"VERDICT:\s*(pass|fail)", re.I)
_REASON_RE = re.compile(r"REASON:\s*(.*)", re.I)


def parse_verdict(text: str):
    v = _VERDICT_RE.search(text)
    r = _REASON_RE.search(text)
    verdict = (v.group(1).lower() if v else "fail")
    reason = (r.group(1).strip() if r else "")
    return verdict, reason


class TestReaderBoundary:
    def __init__(self, llm) -> None:
        self._llm = llm

    def decide(self, context) -> list:
        ctx = context if isinstance(context, dict) else {}
        output = (ctx.get("output", "") or "")[-_MAX_OUTPUT:]
        reply = self._llm.complete(LlmRequest(prompt=_PROMPT.format(output=output))).text
        verdict, reason = parse_verdict(reply)
        return [create_decision(
            id=f"test-{uuid.uuid4().hex}", source=NAME, type="advance",
            payload={"events": ["start", "complete"], "verdict": verdict, "reason": reason,
                     "note": f"test-reader: {verdict} — {reason}"})]


def build(llm) -> TestReaderBoundary:
    return TestReaderBoundary(llm)
