# Safety contract

`jaros-claude` puts the Claude Code harness behind a deterministic gate. The control
is enforced by Claude Code's own hooks, so it is active by construction once the
template is copied in — the operator does not switch it on.

## What the gate enforces (deterministically, before a tool runs)

The PreToolUse gate (`.claude/hooks/gate.py`, policy in `.claude/hooks/policy.py`)
refuses, by default:

1. **Destructive / privileged shell** — `rm -rf`/`-fr`, `dd if=`, `mkfs`, `shred`,
   writing to `/dev/sd*`, fork bombs, `shutdown`/`reboot`/`halt`/`poweroff`,
   `sudo`/`doas`/`su`/`runas`, `chmod -R 777`, `Remove-Item -Recurse`, `del /s`.
2. **Remote-code-execution pattern** — piping downloaded content straight into a
   shell (`curl ... | sh`, `wget ... | bash`, `iwr ... | iex`).
3. **Writes into credential/system locations** — `~/.ssh`, `~/.aws`, `~/.gnupg`,
   `~/.config/gh`, shell rc/profile files, `.netrc`/`.npmrc`/`.git-credentials`,
   and `/etc`, `/usr`, `/bin`, `/sbin`, `/boot`.

A refused call **never executes**; the reason is shown to Claude, which adapts.

## What it deliberately allows (and how to change that)

The default is an **interactive safety floor**: it does not block ordinary
development — plain `git`, `curl`, and package installs are allowed so the harness
stays usable for hands-on work. To run the strict **jaros-code unattended posture**
— refuse *all* network egress (curl/wget/ssh/`git push|pull|clone|fetch`, package
installs, raw URLs) — set `BLOCK_ALL_EGRESS = True` in `.claude/hooks/policy.py`.

`policy.py` is the **single tuning point**. Tightening or loosening the gate is a
governance change (PRIME-001 Tenet 1): make it in a commit, against the spec, not
as a quiet edit. Widening the gate to permit something dangerous should be
surfaced, not silently resolved.

## What is guaranteed by construction

- **Capability-safety.** Claude never gets ungated authority — every effect is a
  tool call the PreToolUse gate accepted. A bad step cannot reach a capability the
  policy did not grant.
- **Auditability.** Every executed tool call is recorded, in commit order, in a
  hash-chained log (`.claude/audit/decisions.jsonl`). Each record links to the
  previous checksum, so any insertion, deletion, reorder, or edit is detectable.
  `python3 .claude/hooks/verify-chain.py` (or `/jarify-status`) verifies it.
- **Honesty.** Refusals, failures, and skips are recorded and reported as
  themselves — never hidden or fabricated (Tenet 3).

## Limits to understand

- The gate is a **policy filter on tool calls**, not a sandbox. It refuses the
  patterns in `policy.py`; it does not contain a process that has already started,
  and a sufficiently obfuscated command can evade a regex. For untrusted or
  unattended use, combine it with OS-level isolation and turn on `BLOCK_ALL_EGRESS`.
- The audit log is **runtime state** (gitignored). It records what ran in *this*
  working copy; it is not a substitute for your VCS history.
- Calling the model is Claude Code's own operation, not a model-generated command —
  that is how the harness works, by design, and is outside the command denylist.
