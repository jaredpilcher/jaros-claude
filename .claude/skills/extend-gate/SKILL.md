---
name: extend-gate
description: Use when a new capability changes what the execution plane is allowed to do — adding, tightening, or loosening a rule in the deterministic gate (.claude/hooks/policy.py). Examples: "block <pattern>", "allow <command> through the gate", "turn on the strict no-egress posture", "the gate is refusing X and it shouldn't / it should". Treats the gate as governance: spec the change, add a verifiable rule, commit code + spec — never quietly widen the gate.
---

# Changing the gate the jarify way

The PreToolUse gate (`.claude/hooks/gate.py`, policy in `.claude/hooks/policy.py`) is
the deterministic control of PRIME-001 Tenet 1. Changing what it allows or refuses is
a **governance change**, not a routine edit. Make it deliberately and conformantly.

## Before you edit: which direction?
- **Tightening** (refuse more) — usually safe; still spec it so the refusal is
  documented and testable.
- **Loosening** (allow something now refused) — this *reduces* control. STOP and
  confirm it does not weaken Tenet 1 to satisfy a lower tenet. If it does, flag the
  conflict instead of editing. Loosening is the change to be most careful with.

## Procedure
1. **Spec it first** (Tenet 4). Add/extend a `.jarify` requirement (EXT-001 owns the
   gate) describing the new rule as a *testable* statement: "the gate refuses X",
   "the gate allows Y". Use the **add-capability** skill / `spec-author` subagent.
2. **Edit only `policy.py`** — the single tuning point. Keep its functions pure and
   deterministic (no I/O, no side effects); the gate must stay a total function of
   the proposed tool call.
   - destructive/privileged shell → extend `_DESTRUCTIVE`
   - remote-content-into-shell → extend `_REMOTE_PIPE`
   - all network egress (strict jaros-code posture) → flip `BLOCK_ALL_EGRESS = True`
   - credential/system write targets → extend `_SENSITIVE_PATH`
   - a genuinely new class → add a pattern and have `bash_reason` / `write_reason`
     (or a new `*_reason`) return a clear refusal string.
3. **Prove it deterministically.** Run the gate against representative inputs and
   confirm the verdict — this is exactly the kind of check that belongs on the
   execution plane:
   ```bash
   echo '{"tool_name":"Bash","tool_input":{"command":"<should be DENIED>"}}' | python3 .claude/hooks/gate.py; echo "exit=$?"   # expect 2
   echo '{"tool_name":"Bash","tool_input":{"command":"<should be ALLOWED>"}}' | python3 .claude/hooks/gate.py; echo "exit=$?"  # expect 0
   ```
4. **Commit code + spec together.** The denylist and its requirement never drift.

## Guardrails
- Never weaken the gate just to make a feature pass. If a feature can't run within the
  gate, that is a signal to redesign the feature, not to open the gate.
- Never move enforcement out of `policy.py`/`gate.py` into ad-hoc places — one gate,
  one tuning point, fully auditable.
- The decision log (PostToolUse) and session binding (SessionStart) stay intact; do
  not disable them to "simplify" a change.
