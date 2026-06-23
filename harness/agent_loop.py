"""Agentic master loop: plan -> act -> observe -> replan.

From one natural-language request the planner lays out a TODO; the loop executes
each step with the DETERMINISTIC tools (routed through `Runtime.apply`), OBSERVES
the result, and REPLANS when a step fails. Two-plane discipline: Claude only
PLANS/REPLANS and proposes edits (inert Decisions); every side effect goes through
the gate and the tools. The planner is INJECTABLE so the loop is testable without
a model.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

_SKIP = {".git", "__pycache__", ".venv", "node_modules", ".jaros-data"}


@dataclass
class Step:
    action: str
    arg: str = ""
    status: str = "pending"          # pending | done | failed
    observation: str = ""


def repo_files(cwd: str, limit: int = 40) -> list[str]:
    """The repo's .py files (relative) — grounding so the planner references real files."""
    root = Path(cwd)
    out = []
    for p in root.rglob("*.py"):
        if any(s in p.parts for s in _SKIP):
            continue
        try:
            out.append(p.relative_to(root).as_posix())
        except ValueError:
            out.append(p.name)
    return sorted(out)[:limit]


def _ground(request: str, cwd: str) -> str:
    files = repo_files(cwd)
    return (f"Files in the repo: {', '.join(files)}\n\n{request}") if files else request


def _default_planner(request: str) -> list[Step]:
    from harness.runtime import build_llm, load_agent

    [d] = load_agent("planner_agent.py", build_llm()).decide({"request": request})
    return [Step(s.get("action", ""), s.get("arg", "")) for s in d.payload.get("plan", [])]


def execute_step(step: Step, cwd: str) -> tuple[bool, str]:
    """Run one step's tool through the two-plane Runtime. Returns (ok, observation)."""
    from jaros_claude.core import create_decision
    from harness.runtime import Runtime, build_llm, load_agent

    a, arg = step.action, (step.arg or "").strip()
    rt = Runtime()

    if a == "read":
        out = rt.apply(create_decision(
            id=f"read-{abs(hash((cwd, arg)))}", source="agent_loop", type="fs.read",
            payload={"path": str(Path(cwd) / arg)}))
        return (bool(out.get("ok")), f"read {arg} ({out.get('lines', 0)} lines)"
                if out.get("ok") else f"{arg}: {out.get('error')}")

    if a == "find":
        out = rt.apply(create_decision(
            id=f"list-{abs(hash(cwd))}", source="agent_loop", type="fs.list",
            payload={"path": cwd}))
        return (bool(out.get("ok")), f"listed {len(out.get('entries', []))} entries")

    if a == "run":
        out = rt.apply(create_decision(
            id=f"run-{abs(hash((cwd, arg)))}", source="agent_loop", type="shell.exec",
            payload={"command": arg or "python -m pytest -q", "cwd": cwd}))
        if not out.get("ok") and out.get("error"):
            return (False, out["error"])
        return (bool(out.get("ok")), "tests pass" if out.get("ok") else "tests fail")

    if a == "edit":
        if ":" not in arg:
            return (False, "edit needs '<file>: <instruction>'")
        fname, _, instr = arg.partition(":")
        fname, instr = fname.strip(), instr.strip()
        p = Path(cwd) / fname
        content = p.read_text(encoding="utf-8") if p.is_file() else ""
        [d] = load_agent("editor_agent.py", build_llm()).decide(
            {"path": str(p), "content": content, "instruction": instr})
        if d.type != "code.apply_patch":
            return (False, "editor produced no edit")
        rt.apply(d)
        return (True, f"edited {fname}")

    if a == "write":
        if ":" not in arg:
            return (False, "write needs '<file>: <intent>'")
        fname, _, intent = arg.partition(":")
        return (False, f"write of {fname.strip()} not auto-implemented in template "
                       f"(wire a builder agent here)")

    return (False, f"unknown action '{a}'")


def agent_loop(request: str, cwd: str, *, planner: Callable[[str], list[Step]] | None = None,
               max_steps: int = 8, verbose: bool = False) -> dict:
    """plan -> act -> observe -> replan, with a TODO working-memory."""
    plan = planner or _default_planner
    todo: list[Step] = plan(_ground(request, cwd))
    if not todo:
        return {"todo": [], "done": False, "steps_run": 0, "note": "planner produced no plan"}
    steps_run = 0
    while steps_run < max_steps:
        pending = next((s for s in todo if s.status == "pending"), None)
        if pending is None:
            break
        ok, obs = execute_step(pending, cwd)
        pending.status = "done" if ok else "failed"
        pending.observation = obs
        steps_run += 1
        if verbose:
            print(f"  [{pending.status}] {pending.action} {pending.arg} -> {obs}", flush=True)
        if not ok and steps_run < max_steps:
            progress = "; ".join(f"{s.action} {s.arg}: {s.observation}"
                                 for s in todo if s.status != "pending")
            todo.extend(plan(_ground(
                f"{request}\nProgress: {progress}\nThe last step failed; plan the "
                f"remaining steps to finish the request.", cwd)))
    return {"todo": [asdict(s) for s in todo],
            "done": all(s.status == "done" for s in todo), "steps_run": steps_run}
