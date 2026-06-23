"""Execution-plane tool ``fs.read`` (EXT-001 / REQ-1).

Reads a file's exact bytes and returns them as inert data. Deterministic: given
the same file, the same content. The reasoning plane never opens a file itself —
it proposes an ``fs.read`` Decision and the clerk runs this tool.
"""

from __future__ import annotations

import os

from jaros_claude.core.decision_gate import ValidationResult

_MAX_BYTES = 1_000_000


class FsReadTool:
    NAME = "fs.read"

    def validate(self, decision) -> ValidationResult:
        payload = decision.payload if isinstance(decision.payload, dict) else {}
        path = payload.get("path")
        if not isinstance(path, str) or not path:
            return ValidationResult.reject("fs.read requires a 'path' string")
        return ValidationResult.accept(decision)

    def execute(self, decision, **collaborators) -> dict:
        path = decision.payload["path"]
        if not os.path.isfile(path):
            return {"tool": self.NAME, "path": path, "ok": False, "error": "not found"}
        size = os.path.getsize(path)
        if size > _MAX_BYTES:
            return {"tool": self.NAME, "path": path, "ok": False, "error": "file too large"}
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()
        return {
            "tool": self.NAME,
            "path": path,
            "ok": True,
            "content": content,
            "lines": content.count("\n") + 1,
        }
