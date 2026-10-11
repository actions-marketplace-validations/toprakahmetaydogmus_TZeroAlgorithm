# Changelog

## [3.0.16] - 2026-10-11

### Fixed & Enhanced

- **Interactive T-Zero Security & AST Architecture Audit Dialog:** Fixed GUI security audit feedback where clean scans previously only showed a brief toast; now always opens an interactive, filterable audit report modal with metric badges (T-001 Zero-Leak, T-002 Layer Boundaries, T-003 AST Contracts, T-004 Code Quality) and one-click Markdown export / save options.
- **Canonical T-Zero 4-Tier Context Architecture & Rules (T-001 to T-004):** Context trees generated offline and through MCP now explicitly organize into Tier T-1 (Physical Topology), Tier T-2 (Dependencies), Tier T-3 (AST Interface Contracts), and Tier T-4 (Rules T-001 Zero-Leak Isolation, T-002 Boundary Enforcement, T-003 AST Contract Fidelity, and T-004 Maintainability Guard).
- **Fixed MCP Code Smell Description Key:** Resolved bug in `audit_codebase_quality` where `sm.get('message')` returned `None` due to key name discrepancy; now supports both `msg` and `message` aliases with rule IDs.
- **Unified Security & Code Smell Actions:** Hooked all security audit triggers (Overview card "RAPORU İNCELE", top header button, and Code Explorer toolbar "🛡 Audit") into the unified luxury audit dialog.

## [3.0.15] - 2026-10-11

### Fixed & Enhanced

- **Seamless Local AST Context Engine Fallback:** If an external API call fails due to permission/quota/authorization errors (such as HTTP 403 on personal NVIDIA accounts missing Public API Endpoints scope), T-Zero automatically generates the complete, high-fidelity context tree offline without failing or halting.
- **Deep Health Check for API Ping:** Upgraded `ping_endpoint` to perform both endpoint reachability and a lightweight chat completion probe, eliminating false-positive green lights and providing precise diagnostic advice for HTTP 403 scope issues.
- **Full CLI & TUI Resilience:** Added offline AST auto-rescue to `run_tui_wizard` ensuring context READMEs are generated 100% reliably in all environments.

## [3.0.14] - 2026-10-11

### Fixed & Enhanced

- Updated NVIDIA NIM AI models list to active, verified models with `deepseek-ai/deepseek-v4.1-flash` as primary default.
- Removed deprecated/sunsetted models that caused HTTP 410 Gone (`meta/llama-3.3-70b-instruct`, `mistralai/mistral-large-3-675b-instruct-2512`).
- Added transparent auto-fallback to `deepseek-ai/deepseek-v4.1-flash` in `ContextGenerator` if a model endpoint returns HTTP 410.
- Implemented automatic profile migration in `ConfigManager.load()` to seamlessly upgrade legacy profiles to active models.
- Enhanced GUI error diagnostics with direct resolution tips for HTTP 403 API authorization and model end-of-life.

## [3.0.13] - 2026-10-11

### Fixed

- Fixed undefined variable `provider_name` during GUI payload generation in `async_generate_payload`.
- Added automated GUI test coverage validating provider resolution and payload preparation.

## [3.0.12] - 2026-10-11

### Added

- Live animated SVG terminal demonstration with smooth 94.9% sliding progress bar and pulsing metrics.
- Added `skip-existing: true` to PyPI deployment workflow to prevent duplicate upload errors.
- 1-Line quickstart installation and pre-configured MCP JSON configuration.

- Visual terminal benchmark SVG demonstration (`assets/benchmark-demo.svg`) embedded in README.
- Reproducible VHS tape configuration (`demo.tape`) for automated zero-cost demo generation.
- Zero-cost community adoption kit (`ZERO_COST_ADOPTION_KIT.md`) with Hacker News Show HN technical draft and curated MCP registry references.
- 1-Line Quickstart section in README with direct MCP stdio configuration.

### Improved

- Verified 103 / 103 tests passing with 100% Zero-Leak security across all workspaces.
- Synchronized repository badges to reflect 103 passing tests and 16 native MCP tools.
- Updated action references and version strings across CLI, GUI, and MCP server.

## [3.0.10] - 2026-10-08

### Fixed

- Resolve the source project root when the desktop app is launched from its `dist` or `build` folder.
- Ignore numbered virtual environments such as `.venv-1` during workspace scans.
- Show helpful instructions when the file explorer has not been scanned, has no supported source files, or has no search matches.

### Improved

- Clarify that compiled `.exe` files are not source files and direct users to scan the project source folder.

## [3.0.9] - 2026-10-08

### Fixed

- Preserve complete multiline Python function, async function, class, and import headers in Ultra reduction.
- Keep a line-based fallback when Python source cannot be parsed.
- Make the desktop header search open the code explorer and filter indexed files; `Ctrl+K` focuses search.

### Improved

- Refresh the default dashboard with a warm ivory, midnight, and champagne palette and more readable typography.
- Update package, CLI, MCP, installer, and GitHub Action references to version 3.0.9.
