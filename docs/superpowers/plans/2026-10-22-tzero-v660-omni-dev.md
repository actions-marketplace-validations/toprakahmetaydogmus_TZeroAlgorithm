# T-Zero v6.6.0 Omni-Dev & Graph-Prune Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade T-Zero to v6.6.0 Master Edition with Cross-Module AST Reachability (Zero-Waste Prompt Context), CLI Stdin/Stdout Pipeline (`tzero --pipe`), Git Pre-Commit Zero-Leak & Token Guard (`tzero --init-hooks`), and 3 new native MCP tools (total 42 tools).

**Architecture:** Pure Python 3 AST graph analysis calculates symbol reachability from workspace entrypoints to prune unreferenced functions and dead code before LLM context ingestion. A zero-dependency streaming pipe module enables UNIX-style stdin/stdout token compression for developer CLI pipelines. An automated git hook generator installs a local pre-commit guard that halts commits on secret leaks and uncompressed token bloat.

**Tech Stack:** Python 3.11+ standard library (`ast`, `re`, `sys`, `os`, `hashlib`, `subprocess`), pytest/unittest, MCP stdio protocol. 100% offline, zero-cost, zero cloud dependencies.

**Spec:** Offline, zero-leak enterprise AI context optimization engine.

## Global Constraints

- Zero cost: 100% offline local algorithms, no paid external APIs or subscriptions.
- Zero leaks: Strictly eliminate and prohibit any hardcoded personal emails, tokens, or passwords.
- Backward compatibility: All existing 39 MCP tools and CLI arguments must continue functioning without breaking changes.
- Test coverage: Every module must have complete unit tests executed via `python -m unittest discover tests -v`.

## Review Focus

- Entrypoint reachability cycle handling: Circular imports and recursive function calls must not cause infinite loops.
- Empty stdin handling: `tzero --pipe` with empty or whitespace-only input must gracefully output empty string without throwing exceptions.
- Git hook execution on non-git directories: `tzero --init-hooks` must detect when `.git` is absent and return a clear user warning without crashing.
- Multi-language AST fallback in pipe: Non-Python code piped without extension hint should fallback gracefully to polyglot regex compression.
- MCP tool registration count: `tests/test_mcp.py` must strictly verify exactly 42 registered tools.

---

### Task 1: Cross-Module AST Call-Graph Reachability Engine (`tzero_reachability.py`)

**Files:**
- Create: `tzero_reachability.py`
- Test: `tests/test_reachability.py`

**Interfaces:**
- Consumes: `ast`, `os`, `re`
- Produces: `CallGraphReachabilityEngine(workspace_root: str)`, `build_reachability_graph(entrypoints: list[str]) -> dict`, `generate_zero_waste_prompt(entrypoints: list[str]) -> dict`

- [ ] **Step 1: Write failing test in `tests/test_reachability.py`**
Verify graph extraction, reachable symbol filtering, dead-code identification, and prompt synthesis across multi-file synthetic codebases.

- [ ] **Step 2: Run test to verify it fails**
Run: `python -m unittest tests/test_reachability.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tzero_reachability'`

- [ ] **Step 3: Implement `tzero_reachability.py`**
Implement `CallGraphReachabilityEngine` to parse Python AST across workspace files, detect defined symbols (functions, classes) and function calls/instantiations, perform graph reachability traversal from entrypoints, and construct zero-waste pruned prompt contexts.

- [ ] **Step 4: Run test to verify it passes**
Run: `python -m unittest tests/test_reachability.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add tzero_reachability.py tests/test_reachability.py
git commit -m "feat(reachability): add cross-module call-graph reachability engine"
```

---

### Task 2: CLI Stdin/Stdout Pipeline & Token Streamer (`tzero_pipe.py`)

**Files:**
- Create: `tzero_pipe.py`
- Modify: `tzero_v3.py:7720-7760` (add `--pipe` argument handling)
- Test: `tests/test_pipe.py`

**Interfaces:**
- Consumes: `TokenReducer` from `tzero_v3.py`, `sys.stdin`, `sys.stdout`
- Produces: `PipeCompressor.compress_stream(content: str, filename_hint: str = "", tier: str = "T-3") -> str`

- [ ] **Step 1: Write failing test in `tests/test_pipe.py`**
Test piping Python, JavaScript, SQL, and Markdown text through `PipeCompressor.compress_stream` and verify accurate compression without data loss or exceptions.

- [ ] **Step 2: Run test to verify it fails**
Run: `python -m unittest tests/test_pipe.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tzero_pipe'`

- [ ] **Step 3: Implement `tzero_pipe.py` & wire `--pipe` into `tzero_v3.py`**
Implement `PipeCompressor` with format autodetection and safe stdin buffering. Add `--pipe` CLI flag in `tzero_v3.py` `main()` for instant terminal UNIX piping.

- [ ] **Step 4: Run test to verify it passes**
Run: `python -m unittest tests/test_pipe.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add tzero_pipe.py tzero_v3.py tests/test_pipe.py
git commit -m "feat(pipe): add stdin/stdout CLI pipeline compression engine"
```

---

### Task 3: Git Pre-Commit Zero-Leak & Token Guard (`tzero_guard.py`)

**Files:**
- Create: `tzero_guard.py`
- Modify: `tzero_v3.py:7720-7760` (add `--init-hooks` argument handling)
- Test: `tests/test_guard.py`

**Interfaces:**
- Consumes: `.git/hooks`, `os`, `stat`
- Produces: `GitSecurityGuard.install_hook(repo_dir: str) -> dict`, `GitSecurityGuard.scan_staged_files(repo_dir: str) -> dict`

- [ ] **Step 1: Write failing test in `tests/test_guard.py`**
Test installing `.git/hooks/pre-commit` in a mock git directory, verifying execution permissions and verifying staged secret detection blocking commits.

- [ ] **Step 2: Run test to verify it fails**
Run: `python -m unittest tests/test_guard.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tzero_guard'`

- [ ] **Step 3: Implement `tzero_guard.py` & CLI hook installer**
Implement standalone hook template and scanner checking for API keys, secret tokens, private emails, and uncompressed AST token limits on staged git diffs. Wire `--init-hooks` into `tzero_v3.py`.

- [ ] **Step 4: Run test to verify it passes**
Run: `python -m unittest tests/test_guard.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add tzero_guard.py tzero_v3.py tests/test_guard.py
git commit -m "feat(guard): add git pre-commit zero-leak and token guard installer"
```

---

### Task 4: MCP Tools 40-42 Registration & v6.6.0 Release

**Files:**
- Modify: `tzero_mcp.py` (add tools 40, 41, 42; bump `SERVER_VERSION = "6.6.0"`)
- Modify: `addmcp.py` (bump version to `6.6.0`)
- Modify: `pyproject.toml` (bump version to `6.6.0`)
- Modify: `CHANGELOG.md` (add v6.6.0 release entry)
- Modify: `tests/test_mcp.py` (update expected tool count to 42)

**Interfaces:**
- Consumes: `CallGraphReachabilityEngine`, `PipeCompressor`, `GitSecurityGuard`
- Produces: Tool 40 `generate_zero_waste_prompt_context`, Tool 41 `compress_stream_tokens`, Tool 42 `install_git_security_guard`

- [ ] **Step 1: Update `tests/test_mcp.py` with 42 tools assertion**
Add the 3 new tool names to `expected_tools` list and assert length is 42.

- [ ] **Step 2: Run `test_mcp.py` to verify it fails**
Run: `python -m unittest tests/test_mcp.py -v`
Expected: FAIL (assertion error 39 != 42)

- [ ] **Step 3: Register tools in `tzero_mcp.py` and bump version to 6.6.0**
Implement handlers and tool definitions in `tzero_mcp.py`. Update `SERVER_VERSION = "6.6.0"`, `addmcp.py`, `pyproject.toml`, and `CHANGELOG.md`.

- [ ] **Step 4: Run full test suite to verify 100% pass**
Run: `python -m unittest discover tests -v`
Expected: 100% tests pass (all suites green).

- [ ] **Step 5: Commit & Push to GitHub**
```bash
git add tzero_mcp.py addmcp.py pyproject.toml CHANGELOG.md tests/test_mcp.py
git commit -m "release: v6.6.0 Master Edition with 42 MCP tools and Omni-Dev engines"
git push origin main
```
