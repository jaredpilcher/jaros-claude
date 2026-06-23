---
id: EXT-001
title: Deterministic Execution-Plane Tool Primitives
status: implemented
priority: high
serves: PRIME-001 Tenet 1 (two-plane discipline)
---

This spec serves **Tenet 1 (two-plane discipline)** of PRIME-001: every host
effect the harness performs is a deterministic tool with `validate()` +
`execute()`, registered into the gate and the executor. Claude never performs an
effect; it proposes a Decision and one of these tools runs it.

## Requirements

- **REQ-1 `fs.read`** — read a file's exact bytes and return them as inert data.
  Read-only, deterministic, size-capped. (`.jaros-data/tools/fs_read_tool.py`)
- **REQ-2 `fs.list`** — list a directory's entries as inert data. Read-only.
  (`.jaros-data/tools/fs_list_tool.py`)
- **REQ-4 `code.apply_patch`** — apply ONE old→new edit, refusing it unless the
  `old` snippet appears EXACTLY once (the deterministic uniqueness guard that
  keeps a model-proposed edit from hitting the wrong place).
  (`.jaros-data/tools/apply_patch_tool.py`)
- **REQ-5 `shell.exec`** — run a shell command, refusing network egress and
  destructive/privileged commands at the gate via a deterministic denylist before
  execution. (`.jaros-data/tools/shell_exec_tool.py`)
- **REQ-6 `code.write_file`** — overwrite a file with full content, refusing
  content that contains dangerous constructs (sockets, process spawning, dynamic
  exec) via the code-safety gate. (`.jaros-data/tools/write_file_tool.py`)
- **REQ-7 Safety gate** — pure functions `unsafe_command_reason` /
  `unsafe_code_reason` that the effectful tools call to refuse dangerous actions
  before they run. (`.jaros-data/tools/_codesafety.py`)

Each tool contributes its `validate()` to the gate and its `execute()` to the
executor via the dynamic loader. A rejected Decision never executes.
