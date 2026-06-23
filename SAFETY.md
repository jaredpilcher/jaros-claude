# Safety contract

`jaros-claude` puts a capable model behind a deterministic gate. These bounds are
enforced deterministically where possible (two-plane safety: the model only
proposes; deterministic gates/tools decide).

## What is guaranteed by construction

1. **Capability-safety.** Reasoning agents hold no host handles. Every host effect
   is a deterministic tool the execution plane runs. A bug — or a bad generation —
   cannot reach a capability the gate did not grant.

2. **No network egress from generated commands.** The `shell.exec` gate
   (`_codesafety.unsafe_command_reason`) **refuses** any network command: `curl`,
   `wget`, `ssh`/`scp`, `git push/pull/clone/fetch`, `pip/npm/conda/apt install`,
   raw `http(s)://`, `Invoke-WebRequest`, etc. A refused command never executes.
   (Calling the Anthropic API is the harness's own outbound path, not a
   model-generated command — that is how Claude is reached, by design.)

3. **No destructive or privileged commands.** The same gate refuses `rm -rf`,
   `del /`, `Remove-Item -Recurse`, `format`, `mkfs`, `dd`, `shutdown`/`reboot`,
   `sudo`/`runas`, `chmod 777`. Ordinary build/test commands (e.g.
   `python -m pytest -q`) are allowed.

4. **No dangerous generated code lands.** `code.write_file` refuses content that
   contains sockets, process spawning, or dynamic exec
   (`_codesafety.unsafe_code_reason`).

5. **Unambiguous edits only.** `code.apply_patch` refuses an edit whose `old`
   snippet does not appear exactly once — a model-proposed edit cannot silently
   hit the wrong location.

6. **Auditable and replayable.** Every accepted Decision is hash-chain logged
   before its effect is observable. `verify_chain` detects tampering; `replay`
   reconstructs the run with zero model calls.

## Why confine a capable model

The point of this template is that a frontier model's correctness does not earn it
ungated authority. Safety, reproducibility, and auditability come from the planes,
not from the model — so even Claude stays on the reasoning side of the gate.

## Tuning the bounds for your project

When you adopt this template, the denylists in `_codesafety.py` are the place to
tighten or (carefully) widen what the execution plane will run. Widening a
denylist is a structural change — surface it against PRIME-001 Tenet 1 rather than
quietly relaxing the gate.
