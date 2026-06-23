"""Execution-plane tool ``fs.list`` (EXT-001 / REQ-2).

Lists a directory's entries as inert data. Deterministic and read-only.
"""

from __future__ import annotations

import os

from jaros_claude.core.decision_gate import ValidationResult


class FsListTool:
    NAME = "fs.list"

    def validate(self, decision) -> ValidationResult:
        payload = decision.payload if isinstance(decision.payload, dict) else {}
        path = payload.get("path", ".")
        if not isinstance(path, str):
            return ValidationResult.reject("fs.list 'path' must be a string")
        return ValidationResult.accept(decision)

    def execute(self, decision, **collaborators) -> dict:
        path = decision.payload.get("path", ".") if isinstance(decision.payload, dict) else "."
        if not os.path.isdir(path):
            return {"tool": self.NAME, "path": path, "ok": False, "error": "not a directory"}
        entries = []
        for name in sorted(os.listdir(path)):
            full = os.path.join(path, name)
            entries.append({"name": name, "dir": os.path.isdir(full)})
        return {"tool": self.NAME, "path": path, "ok": True, "entries": entries}
