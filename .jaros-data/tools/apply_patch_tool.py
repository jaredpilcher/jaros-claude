"""Effectful execution-plane tool ``code.apply_patch`` (EXT-001 / REQ-4).

Applies one surgical old->new edit to a file. The deterministic part is the
*uniqueness check*: the ``old`` snippet must appear EXACTLY once, or the edit is
refused. This is the control that keeps a model-proposed edit from silently
hitting the wrong location — the model proposes the edit, the tool proves it is
unambiguous before applying it.
"""

from __future__ import annotations

import os

from jaros_claude.core.decision_gate import ValidationResult


class ApplyPatchTool:
    NAME = "code.apply_patch"

    def validate(self, decision) -> ValidationResult:
        payload = decision.payload if isinstance(decision.payload, dict) else {}
        path = payload.get("path")
        old = payload.get("old")
        new = payload.get("new")
        if not isinstance(path, str) or not path:
            return ValidationResult.reject("code.apply_patch requires a 'path' string")
        if not isinstance(old, str) or old == "":
            return ValidationResult.reject("code.apply_patch requires a non-empty 'old' string")
        if not isinstance(new, str):
            return ValidationResult.reject("code.apply_patch requires a 'new' string")
        if not os.path.isfile(path):
            return ValidationResult.reject(f"code.apply_patch: {path} does not exist")
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read()
        count = content.count(old)
        if count == 0:
            return ValidationResult.reject("code.apply_patch: 'old' snippet not found")
        if count > 1:
            return ValidationResult.reject(
                f"code.apply_patch: 'old' snippet is ambiguous (appears {count} times)"
            )
        return ValidationResult.accept(decision)

    def execute(self, decision, **collaborators) -> dict:
        payload = decision.payload
        path, old, new = payload["path"], payload["old"], payload["new"]
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read()
        updated = content.replace(old, new, 1)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(updated)
        return {"tool": self.NAME, "path": path, "applied": True}
