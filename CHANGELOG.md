# Changelog

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
