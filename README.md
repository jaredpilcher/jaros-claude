# jaros-claude

**The jaros-code discipline, running on the Claude Code harness you already use.**
A copy-in template that makes **Claude Code itself** operate under the two-plane
control of Jaros and jaros-code — the model proposes, a deterministic gate decides,
every decision is recorded — **without a new harness and without any extra commands
to run.** You drop its contents into a project and Claude Code just operates that
way.

## The idea

jaros-code's bet is that a *small* model becomes useful when the harness is strong.
jaros-claude flips the motivation: a *strong* model becomes **safe, reproducible,
and auditable** when the harness is in control. And the harness here is not
something new — it is **Claude Code**, governed through its own native extension
points (`CLAUDE.md`, `.claude/agents`, `.claude/settings.json` hooks, `.jarify`).

The two planes map cleanly onto Claude Code:

```
you (Claude) propose a tool call ─► PreToolUse gate decides ─► Claude Code's tools run it ─► PostToolUse hook hash-chains it to the audit log
```

| Jaros / jaros-code concept | Claude Code mechanism |
|---|---|
| reasoning plane (the model) | Claude driving Claude Code |
| single-purpose agents | `.claude/agents/*.md` subagents (auto-delegated) |
| the decision **gate** | a **PreToolUse hook** (`.claude/hooks/gate.py` + `policy.py`) |
| deterministic execution tools | Claude Code's built-in Bash / Write / Edit / Read |
| hash-chained decision log | a **PostToolUse hook** → `.claude/audit/decisions.jsonl` |
| spec-first governance | `.jarify/` (PRIME-001 + EXT specs) + `index.json` |
| the jarify roles | `spec-author`, `task-decomposer`, `builder`, `architect` |

## It just operates that way (authentic, no ceremony)

Nothing to switch on. Three hooks make the discipline passive:

- **SessionStart** binds every session to the Prime Directive (injects the
  governance as standing context).
- **PreToolUse** runs the **gate** on every Bash/Write/Edit and deterministically
  refuses the unsafe ones — destructive/privileged commands, piping remote content
  into a shell, writes into credential/system locations. A refusal is shown to
  Claude, and the call never executes.
- **PostToolUse** records every executed call to a tamper-evident, hash-chained
  decision log.

You use Claude Code exactly as you always do; the control rides along.

## What's in the box

```
.claude/
  settings.json          wires the three hooks so the discipline is active on copy-in
  hooks/
    gate.py              PreToolUse — the deterministic decision gate
    policy.py            the denylist / safety policy (the single tuning point)
    log-decision.py      PostToolUse — appends a hash-chained record per tool call
    session-init.py      SessionStart — binds the session to PRIME-001
    verify-chain.py      read-only chain verifier (used by /jarify-status)
  agents/                single-purpose subagents: spec-author, task-decomposer,
                         builder, architect (the jarify roles)
  commands/
    jarify-status.md     optional, read-only: specs + gate posture + chain integrity
  skills/                conformant "how to add capability" (auto-triggered)
    add-capability/      master loop: spec → decompose → build → verify → commit
    add-subagent/        scaffold a new single-purpose subagent (+ template)
    extend-gate/         spec'd, tested change to the gate policy
.jarify/                 governance: PRIME-001 (Prime Directive) + EXT-001..004,
                         with index.json traceability
CLAUDE.md                the working agreement Claude Code loads every session
SAFETY.md                what the gate guarantees, allows, and how to harden it
```

## Try the gate

The hooks are plain stdlib Python 3 — no dependencies, no `jq`. You can exercise the
gate directly:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | python3 .claude/hooks/gate.py   # exit 2 (blocked)
echo '{"tool_name":"Bash","tool_input":{"command":"python -m pytest -q"}}' | python3 .claude/hooks/gate.py   # exit 0 (allowed)
python3 .claude/hooks/verify-chain.py   # decision-log status + chain integrity
```

In a Claude Code session, `/jarify-status` summarizes the specs, the gate posture,
and the chain integrity.

## Governance

The repo is governed by `.jarify/`; **`PRIME-001` is the Prime Directive**. Its five
ordered, non-negotiable tenets: (1) two-plane discipline, (2) Claude confined /
capability by composition, (3) reproducible & honest, (4) spec-first, (5)
Claude-Code-like UX — a lower tenet is never weakened for a higher one. See
`CLAUDE.md` for the working agreement and `.jarify/PRIME-001/` for the full intent
and the architecture mapping.

## Adopting it

Copy the contents into your project. Capture your intent as that project's PRIME
directive, then run the jarify loop with the subagents — one scoped task at a time,
every effect through the gate, code traced to the spec. Tune the gate in
`.claude/hooks/policy.py` (e.g. flip `BLOCK_ALL_EGRESS` on for the strict
jaros-code unattended posture) — and treat that as a governance change.

---

*Claude Code does the reasoning. The gate keeps the authority. No new harness, no
extra commands — it just operates that way.*
