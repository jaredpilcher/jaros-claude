"""Single-purpose agent ``editor`` (EXT-002 / REQ-2).

Given a file's content and an instruction, proposes ONE exact old->new edit and
emits a ``code.apply_patch`` Decision. Uses a delimited-block contract so the
edit is unambiguous to parse. Emits inert data only — the deterministic
``code.apply_patch`` tool applies it (and proves the snippet is unique first).
"""

from __future__ import annotations

import re
import uuid

from jaros_claude.core import create_decision
from jaros_claude.llm import LlmRequest

NAME = "editor"

_MAX_CONTENT = 12000

_PROMPT = (
    "You are a precise code-editing tool. You are given a FILE and an INSTRUCTION.\n"
    "Output EXACTLY ONE edit as these two blocks and NOTHING else:\n"
    "<<<OLD\n"
    "(snippet copied character-for-character from the FILE; it must appear EXACTLY once)\n"
    "OLD>>>\n"
    "<<<NEW\n"
    "(the replacement text)\n"
    "NEW>>>\n"
    "Keep the edit as small as possible. Do not explain.\n\n"
    "INSTRUCTION: {instruction}\n\n"
    "FILE ({path}):\n{content}\n"
)

_OLD_RE = re.compile(r"<<<OLD\r?\n(.*?)\r?\nOLD>>>", re.S)
_NEW_RE = re.compile(r"<<<NEW\r?\n(.*?)\r?\nNEW>>>", re.S)


def parse_edit(text: str):
    old = _OLD_RE.search(text)
    new = _NEW_RE.search(text)
    if not old or not new:
        return None
    old_text = old.group(1)
    if "copied character-for-character" in old_text or not old_text.strip():
        return None
    return old_text, new.group(1)


class EditorBoundary:
    def __init__(self, llm) -> None:
        self._llm = llm

    def decide(self, context) -> list:
        ctx = context if isinstance(context, dict) else {}
        path = ctx.get("path", "")
        content = (ctx.get("content", "") or "")[:_MAX_CONTENT]
        instruction = ctx.get("instruction", "")

        reply = self._llm.complete(LlmRequest(prompt=_PROMPT.format(
            instruction=instruction, path=path, content=content))).text
        parsed = parse_edit(reply)

        if parsed is None:
            return [create_decision(
                id=f"edit-{uuid.uuid4().hex}", source=NAME, type="advance",
                payload={"events": ["start", "fail"],
                         "note": f"editor: could not parse an edit ({reply[:60]!r})"})]

        old, new = parsed
        return [create_decision(
            id=f"edit-{uuid.uuid4().hex}", source=NAME, type="code.apply_patch",
            payload={"path": path, "old": old, "new": new})]


def build(llm) -> EditorBoundary:
    return EditorBoundary(llm)
