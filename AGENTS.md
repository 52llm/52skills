# Repository Guidelines

## Project Structure & Module Organization

This repository contains reusable AI-agent skills. Each skill package is a top-level directory with a `SKILL.md` entry point plus optional `references/`, `agents/`, `scripts/`, and `tests/` subdirectories.

- `forge/` contains a multi-skill workflow suite. The hub is `forge/forge/SKILL.md`; stage skills live in `forge/forge-spec/`, `forge/forge-plan/`, `forge/forge-build/`, `forge/forge-review/`, `forge/forge-debug/`, and `forge/forge-compound/`.
- `shuo-renhua/` contains Chinese/English prose quality rules and a Python checker in `shuo-renhua/scripts/`.
- `ui-taste/` contains frontend design review guidance and a Python checker in `ui-taste/scripts/`.
- Tests are colocated under each package’s `tests/` directory.

## Build, Test, and Development Commands

Use Python 3 and the standard library only unless a package explicitly documents otherwise.

```bash
python3 -m py_compile forge/forge/scripts/forge.py
python3 -m unittest discover -s forge/tests -v
python3 -m unittest discover -s shuo-renhua/tests -v
python3 -m unittest discover -s ui-taste/tests -v
bash forge/forge/scripts/forge --help
```

The `py_compile` command catches syntax errors in the Forge CLI. The unittest commands run package regression tests. The `forge --help` command verifies the executable wrapper still starts.

## Coding Style & Naming Conventions

Keep Python scripts dependency-free, executable with `python3`, and compatible with direct script usage from the repository root. Existing Python uses two-space indentation, `snake_case` functions, uppercase constants, and short helper functions. Keep markdown concise: skill descriptions should explain trigger conditions, while detailed procedures belong in `references/`.

## Testing Guidelines

Add or update tests when changing scripts, generated templates, structural budgets, or rule heuristics. Name test files `test_*.py` and place them in the matching package’s `tests/` directory. Prefer deterministic fixture strings over external files or network calls.

## Commit & Pull Request Guidelines

This repository currently has no committed history, so no project-specific commit convention is established. Use concise imperative commit messages such as `Add ui-taste contrast tests` or `Tighten forge template checks`. Pull requests should include a short behavior summary, changed packages, commands run, and any known follow-up work. Include screenshots only when changing visual assets or rendered documentation.

## Agent-Specific Instructions

Before editing, check whether target files already exist and prefer surgical changes over rewrites. Do not modify generated target-project `.forge/` outputs unless the task explicitly concerns those artifacts.
