"""Deterministic safety gates for the execution plane (shared helper, not a tool).

These are pure functions used by the effectful tools to refuse dangerous actions
*before* they run. They are part of the control discipline: the model may propose
anything, but a deterministic gate decides what is allowed to touch the host.

`unsafe_command_reason` mirrors jaros-code's shell denylist (no network egress, no
destructive/privileged commands). `unsafe_code_reason` rejects obviously dangerous
constructs in generated file content. Both return a short reason string when the
input should be refused, or ``None`` when it is allowed.
"""

from __future__ import annotations

import re

# Network egress — refused so an unattended run cannot exfiltrate or fetch.
_NETWORK = re.compile(
    r"\b(curl|wget|nc|ncat|telnet|ssh|scp|sftp|rsync|ftp)\b"
    r"|https?://"
    r"|\bgit\s+(push|pull|clone|fetch|remote)\b"
    r"|\b(pip|pip3|npm|pnpm|yarn|conda|apt|apt-get|brew)\s+install\b"
    r"|Invoke-WebRequest|Invoke-RestMethod",
    re.I,
)

# Destructive / privilege-escalating — refused so a bad generation can't wreck the host.
_DESTRUCTIVE = re.compile(
    r"\brm\s+-rf\b|\brm\s+-fr\b"
    r"|\bdel\s+/|Remove-Item\s+.*-Recurse"
    r"|\bmkfs\b|\bdd\s+if=|\b:\(\)\s*\{|\bformat\b"
    r"|\bshutdown\b|\breboot\b|\bhalt\b"
    r"|\bsudo\b|\brunas\b|\bchmod\s+777\b",
    re.I,
)

# Dangerous constructs in generated source content.
_CODE = re.compile(
    r"\bos\.system\b|\bsubprocess\.|\b__import__\b|\beval\(|\bexec\("
    r"|\bsocket\.|\burllib\b|\brequests\.|\bshutil\.rmtree\b",
    re.I,
)


def unsafe_command_reason(command: str) -> str | None:
    """Return a refusal reason if ``command`` hits the denylist, else None."""
    if not isinstance(command, str):
        return "command must be a string"
    if _NETWORK.search(command):
        return "network/egress command refused"
    if _DESTRUCTIVE.search(command):
        return "destructive/privileged command refused"
    return None


def unsafe_code_reason(code: str) -> str | None:
    """Return a refusal reason if ``code`` contains a dangerous construct, else None."""
    if not isinstance(code, str):
        return "content must be a string"
    m = _CODE.search(code)
    return m.group(0) if m else None


# Back-compat alias mirroring jaros-code's helper name.
def unsafe_reason(code):  # type: ignore[no-untyped-def]
    return unsafe_code_reason(code)
