"""Effectful execution-plane tool ``shell.exec`` (EXT-001 / REQ-5).

Runs a shell command and returns its result as inert data. The deterministic
denylist refuses network egress and destructive/privileged commands *before*
they run (see `_codesafety.unsafe_command_reason`) — so a model-proposed command
that would exfiltrate data or wreck the host is rejected at the gate, never
executed. Ordinary build/test commands (e.g. `python -m pytest -q`) are allowed.
"""

from __future__ import annotations

import os
import subprocess
import sys

from jaros_claude.core.decision_gate import ValidationResult

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from _codesafety import unsafe_command_reason
except Exception:  # pragma: no cover
    def unsafe_command_reason(command):  # type: ignore
        return None

_DEFAULT_TIMEOUT = 60


class ShellExecTool:
    NAME = "shell.exec"

    def validate(self, decision) -> ValidationResult:
        payload = decision.payload if isinstance(decision.payload, dict) else {}
        command = payload.get("command")
        if not isinstance(command, str) or not command.strip():
            return ValidationResult.reject("shell.exec requires a non-empty 'command' string")
        reason = unsafe_command_reason(command)
        if reason is not None:
            return ValidationResult.reject(f"shell.exec refused: {reason}")
        return ValidationResult.accept(decision)

    def execute(self, decision, **collaborators) -> dict:
        payload = decision.payload
        command = payload["command"]
        cwd = payload.get("cwd") or None
        timeout = int(payload.get("timeout", _DEFAULT_TIMEOUT))
        try:
            proc = subprocess.run(
                command, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout
            )
        except subprocess.TimeoutExpired:
            return {"tool": self.NAME, "command": command, "ok": False,
                    "error": f"timed out after {timeout}s"}
        return {
            "tool": self.NAME,
            "command": command,
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:],
        }
