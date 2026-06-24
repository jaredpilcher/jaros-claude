---
id: EXT-004
title: Governance Binding (CLAUDE.md, settings.json, .jarify scaffold)
status: implemented
priority: high
serves: PRIME-001 Tenet 4 (spec-first) and Tenet 5 (Claude-Code-like UX)
---

This spec serves **Tenets 4 and 5** of PRIME-001: the discipline is bound into the
Claude Code harness through its own configuration, spec-first and unobtrusively.

## Requirements

- **REQ-1 Working agreement** — `CLAUDE.md` binds every session to the Prime
  Directive: the two-plane discipline, plane-placement, spec-first commits, and the
  stop-and-flag-on-conflict rule. It is the project-level instruction Claude Code
  loads automatically. (`CLAUDE.md`)
- **REQ-2 Hook + permission configuration** — `.claude/settings.json` registers the
  gate, the decision log, and the session binding so the control is active by
  construction when the template is copied in. (`.claude/settings.json`)
- **REQ-3 Spec-first scaffold** — `.jarify/` holds PRIME-001 and the EXT specs with
  `index.json` traceability; the `spec-author`/`task-decomposer` subagents extend it
  for the adopting project's own features. (`.jarify/`)
- **REQ-4 Honest safety contract** — `SAFETY.md` states what the gate guarantees,
  what it deliberately allows, and how to harden it (the `policy.py` /
  `BLOCK_ALL_EGRESS` tuning point). (`SAFETY.md`)

The binding must never force the operator into extra ceremony — Claude Code stays
itself; the discipline rides on its native config.
