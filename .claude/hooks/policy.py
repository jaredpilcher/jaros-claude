"""Deterministic policy for the two-plane gate (the single tuning point).

This module is pure data + pure functions. The PreToolUse gate (`gate.py`) imports
it to decide, deterministically, whether a tool call Claude proposed may touch the
host. Editing the patterns here is how an adopting project tightens or loosens the
execution plane — that is a governance change (PRIME-001 Tenet 1), so make it
deliberately, in a commit, against the spec.

The default is an INTERACTIVE safety floor: it blocks the genuinely destructive and
the classic remote-code-execution pattern, and confines writes away from
credential/system locations — without getting in the way of ordinary development
(plain git, curl, package installs are allowed by default). To run the strict
jaros-code "unattended, no egress" posture instead, enable BLOCK_ALL_EGRESS below.
"""

from __future__ import annotations

import os
import re

# Flip to True for the strict jaros-code unattended posture: refuse ALL network
# egress (curl/wget/ssh/git push|pull|clone|fetch, package installs, raw URLs).
BLOCK_ALL_EGRESS = False

# Destructive / privilege-escalating shell — always refused.
_DESTRUCTIVE = re.compile(
    r"\brm\s+-[a-z]*r[a-z]*f\b|\brm\s+-[a-z]*f[a-z]*r\b"      # rm -rf / -fr
    r"|\bdd\s+if=|\bmkfs\b|\bshred\b"
    r"|>\s*/dev/sd|\bof=/dev/sd"
    r"|:\s*\(\s*\)\s*\{\s*:\s*\|\s*:\s*&\s*\}"                 # fork bomb
    r"|\bshutdown\b|\breboot\b|\bhalt\b|\bpoweroff\b"
    r"|\bsudo\b|\bdoas\b|\bsu\s|\brunas\b"
    r"|\bchmod\s+-R?\s*0?777\b"
    r"|\bRemove-Item\b[^\n]*-Recurse|\bdel\s+/[sq]",
    re.I,
)

# Piping remote content straight into a shell — refused (RCE / exfil-and-run).
_REMOTE_PIPE = re.compile(
    r"\b(curl|wget|Invoke-WebRequest|iwr)\b[^|]*\|\s*(sudo\s+)?[a-z]*sh\b", re.I
)

# Any network egress — only consulted when BLOCK_ALL_EGRESS is True.
_EGRESS = re.compile(
    r"\b(curl|wget|nc|ncat|telnet|ssh|scp|sftp|rsync|ftp)\b"
    r"|https?://"
    r"|\bgit\s+(push|pull|clone|fetch|remote)\b"
    r"|\b(pip|pip3|npm|pnpm|yarn|conda|apt|apt-get|brew)\s+install\b"
    r"|Invoke-WebRequest|Invoke-RestMethod",
    re.I,
)

# Sensitive locations writes are refused into (credentials, system, shell rc).
_SENSITIVE_PATH = re.compile(
    r"(^|/)\.ssh/|(^|/)\.aws/|(^|/)\.gnupg/|(^|/)\.config/gh/"
    r"|(^|/)\.(bash|zsh)rc$|(^|/)\.(bash_profile|zprofile|profile)$"
    r"|(^|/)\.netrc$|(^|/)\.npmrc$|(^|/)\.git-credentials$"
    r"|^/etc/|^/usr/|^/bin/|^/sbin/|^/boot/",
    re.I,
)


def bash_reason(command: str) -> str | None:
    """Return a refusal reason for a Bash command, or None if allowed."""
    if not isinstance(command, str):
        return None
    if _DESTRUCTIVE.search(command):
        return "destructive/privileged command refused by the two-plane gate"
    if _REMOTE_PIPE.search(command):
        return "piping remote content into a shell is refused by the two-plane gate"
    if BLOCK_ALL_EGRESS and _EGRESS.search(command):
        return "network egress refused by the two-plane gate (BLOCK_ALL_EGRESS)"
    return None


def write_reason(file_path: str) -> str | None:
    """Return a refusal reason for a write target, or None if allowed."""
    if not isinstance(file_path, str) or not file_path:
        return None
    expanded = os.path.expanduser(file_path)
    if _SENSITIVE_PATH.search(expanded) or _SENSITIVE_PATH.search(file_path):
        return f"write to a credential/system location refused by the two-plane gate: {file_path}"
    return None
