"""jaros-claude CLI — the Claude-Code-like operator surface over the two planes.

Type a slash command or a plain request. A plain request is routed by the
`orchestrator` agent (Claude) to one action; the action runs through the
deterministic gate and tools. Everything the model decides is recorded in the
hash-chained decision log, so any run is auditable and replayable.

Usage:
  python -m harness.cli                  # interactive REPL
  python -m harness.cli /status          # one command and exit
  python -m harness.cli "fix foo.py"     # one plain request (orchestrator routes it)
"""

from __future__ import annotations

import sys
from pathlib import Path

from jaros_claude.core import create_decision
from jaros_claude.state import verify_chain

CWD = str(Path.cwd())

_BANNER = "\033[1m jaros-claude \033[0m  Claude under two-plane control"
_DIM = "\033[2m"
_RESET = "\033[0m"
_CYAN = "\033[36m"


def _rt():
    from harness.runtime import Runtime
    return Runtime()


def _llm():
    from harness.runtime import build_llm
    return build_llm()


def cmd_status() -> None:
    from jaros_claude.llm import health
    print(_BANNER)
    h = health()
    if h["ok"]:
        print(f"   model    : {h['model']}  (Anthropic, reachable)")
    else:
        print(f"   model    : {h['model']}  \033[31m(unreachable: {h['error']})\033[0m")
    rt = _rt()
    chain = verify_chain(rt.log)
    state = "intact" if chain.ok else f"BROKEN at {chain.position}: {chain.reason}"
    print(f"   decisions: {chain.length} recorded, hash-chain {state}")
    print(f"   planes   : model proposes inert Decisions -> gate validates -> tools act")


def cmd_read(arg: str) -> None:
    out = _rt().apply(create_decision(
        id="cli-read", source="cli", type="fs.read", payload={"path": arg}))
    if out.get("ok"):
        print(out["content"])
    else:
        print(f"read failed: {out.get('error')}")


def cmd_list(arg: str) -> None:
    out = _rt().apply(create_decision(
        id="cli-list", source="cli", type="fs.list", payload={"path": arg or "."}))
    if out.get("ok"):
        for e in out["entries"]:
            print(("📁 " if e["dir"] else "   ") + e["name"])
    else:
        print(f"list failed: {out.get('error')}")


def cmd_run(arg: str) -> None:
    out = _rt().apply(create_decision(
        id="cli-run", source="cli", type="shell.exec",
        payload={"command": arg or "python -m pytest -q", "cwd": CWD}))
    if out.get("error"):
        print(f"refused/failed: {out['error']}")
        return
    print(out.get("stdout", ""), end="")
    if out.get("stderr"):
        print(out["stderr"], end="")
    print(f"\n{_DIM}exit {out.get('returncode')}{_RESET}")


def cmd_edit(arg: str) -> None:
    if ":" not in arg:
        print("usage: /edit <file>: <instruction>")
        return
    from harness.runtime import load_agent
    fname, _, instr = arg.partition(":")
    fname, instr = fname.strip(), instr.strip()
    p = Path(CWD) / fname
    content = p.read_text(encoding="utf-8") if p.is_file() else ""
    [d] = load_agent("editor_agent.py", _llm()).decide(
        {"path": str(p), "content": content, "instruction": instr})
    if d.type != "code.apply_patch":
        print(f"editor produced no edit: {d.payload.get('note', '')}")
        return
    try:
        _rt().apply(d)
        print(f"{_CYAN}edited{_RESET} {fname}")
    except RuntimeError as exc:
        print(f"edit refused at gate: {exc}")


def cmd_write(arg: str) -> None:
    if ":" not in arg:
        print("usage: /write <file>: <full content intent>")
        return
    print("note: /write in this template expects you to wire a builder agent that "
          "emits a code.write_file Decision. The tool and gate are ready.")


def cmd_plan(arg: str) -> None:
    from harness.runtime import load_agent
    [d] = load_agent("planner_agent.py", _llm()).decide({"request": arg})
    plan = d.payload.get("plan", [])
    if not plan:
        print("planner produced no plan")
        return
    for i, step in enumerate(plan, 1):
        print(f"  {i}. {step['action']} {step['arg']}")


def cmd_agent(arg: str) -> None:
    from harness.agent_loop import agent_loop
    result = agent_loop(arg, CWD, verbose=True)
    print(f"{_DIM}done={result['done']} steps={result['steps_run']}{_RESET}")


def cmd_log() -> None:
    from jaros_claude.state import read_decisions
    rt = _rt()
    decisions = read_decisions(rt.log)
    if not decisions:
        print("no decisions recorded yet")
        return
    for d in decisions[-20:]:
        note = d.payload.get("note", "") if isinstance(d.payload, dict) else ""
        print(f"  {d.source:>14} -> {d.type:<18} {note}")
    chain = verify_chain(rt.log)
    print(f"{_DIM}{chain.length} records, chain {'intact' if chain.ok else 'BROKEN'}{_RESET}")


def cmd_help() -> None:
    print(_BANNER)
    print("""
  /status            model + decision-log health
  /read <file>       read a file            (fs.read)
  /list [dir]        list a directory       (fs.list)
  /edit <f>: <how>   propose+apply one edit (editor -> code.apply_patch)
  /write <f>: <what> create/replace a file  (code.write_file)
  /run [command]     run a command/tests    (shell.exec, denylist-gated)
  /plan <request>    show an inert plan     (planner)
  /agent <request>   plan -> act -> observe -> replan loop
  /log               recent recorded decisions + chain integrity
  /help              this help
  /quit              exit

  Or just type a plain request — the orchestrator (Claude) routes it.
""")


def route_plain(request: str) -> None:
    """Route a plain-language request via the orchestrator agent, then dispatch."""
    from harness.runtime import load_agent
    [d] = load_agent("orchestrator_agent.py", _llm()).decide({"request": request})
    action = d.payload.get("action", "help")
    arg = d.payload.get("arg", "")
    print(f"{_DIM}-> {action} {arg}{_RESET}")
    _dispatch(action, arg)


def _dispatch(cmd: str, arg: str) -> None:
    table = {
        "status": lambda a: cmd_status(), "read": cmd_read, "list": cmd_list,
        "run": cmd_run, "edit": cmd_edit, "write": cmd_write, "plan": cmd_plan,
        "agent": cmd_agent, "log": lambda a: cmd_log(), "help": lambda a: cmd_help(),
    }
    fn = table.get(cmd)
    if fn is None:
        cmd_help()
    else:
        fn(arg)


def handle(line: str) -> bool:
    """Handle one input line. Returns False to quit."""
    line = line.strip()
    if not line:
        return True
    if line in ("/quit", "/exit", "quit", "exit"):
        return False
    if line.startswith("/"):
        cmd, _, arg = line[1:].partition(" ")
        _dispatch(cmd.strip().lower(), arg.strip())
    else:
        route_plain(line)
    return True


def repl() -> None:
    cmd_status()
    print(f"{_DIM}type /help for commands, /quit to exit{_RESET}")
    while True:
        try:
            line = input(f"{_CYAN}jaros-claude>{_RESET} ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not handle(line):
            break


def main(argv: list[str]) -> int:
    if not argv:
        repl()
        return 0
    handle(" ".join(argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
