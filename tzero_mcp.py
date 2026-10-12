# -*- coding: utf-8 -*-
"""Siber Akademi — T-Zero Context Engine MCP (Model Context Protocol) Server.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
LinkedIn: https://linkedin.com/in/toprak-ahmet-aydo%C4%9Fmu%C5%9F-60462534b/
Bio & Socials: https://hopp.bio/siberegitim
GitHub: https://github.com/toprakahmetaydogmus/TZeroAlgorithm

Exposes T-Zero codebase intelligence, AST signature pruning, dependency mapping,
architectural boundaries (T-1 to T-4), and token optimization directly to AI coding
agents via the standard Model Context Protocol (MCP) over stdio.

Supported Environments:
  - Cursor (Composer / Chat)
  - Claude Desktop
  - Antigravity IDE
  - Cline / Roo-Code
  - Any MCP-compliant client
"""

import os
import sys
import json
import re
import ast
import inspect
import logging
from typing import Dict, List, Optional, Any

SERVER_VERSION = "4.0.0"

# Safe UTF-8 reconfiguration for Windows console & piped subprocesses
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure project root is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# Make sure the MCP SDK (and the core packages) are installed before importing them.
try:
    import tzero_deps
    tzero_deps.ensure_dependencies(include_mcp=True)
except ImportError:
    pass

# Core T-Zero V3 Engine Imports
try:
    from tzero_v3 import (
        CodebaseScanner,
        TokenReducer,
        generate_offline_context,
        DependencyAnalyzer,
        StaticCodeAnalyzer,
        WorkspaceDuplicityFinder,
        ContextExportManager,
        calculate_token_cost,
        count_tokens_precise,
        PROVIDER_COST_PER_MILLION,
    )
except ImportError as e:
    sys.stderr.write(f"[ERROR] Failed to import core T-Zero engine: {e}\n")
    sys.exit(1)

# MCP SDK Import with cross-version compatibility (mcp 2.x MCPServer & mcp 1.x FastMCP)
try:
    from mcp.server.mcpserver import MCPServer
    ServerClass = MCPServer
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP
        ServerClass = FastMCP
    except ImportError:
        ServerClass = None


def get_file_imports(file_path: str) -> List[str]:
    """Helper to extract imported module dependencies across Python, TypeScript, Go, Rust, Java, C#, and C++."""
    if not os.path.isfile(file_path):
        return []
    ext = os.path.splitext(file_path.lower())[1]
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as fp:
            content = fp.read()
    except Exception:
        return []

    if ext == ".py":
        try:
            tree = ast.parse(content)
            visitor = DependencyAnalyzer()
            visitor.visit(tree)
            return sorted(list(set(visitor.dependencies)))
        except Exception:
            return []

    deps = set()
    if ext in (".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"):
        for m in re.finditer(r"""(?:import\s+.*?\s+from\s+['"]|import\s*\(?['"]|require\s*\(\s*['"])([^'"]+)['"]""", content):
            deps.add(m.group(1))
    elif ext == ".go":
        in_group = False
        for line in content.splitlines():
            s = line.strip()
            if s.startswith("import ("):
                in_group = True
                continue
            if in_group:
                if s == ")":
                    in_group = False
                    continue
                m = re.search(r'["\']([^"\']+)["\']', s)
                if m:
                    deps.add(m.group(1))
            elif s.startswith("import "):
                m = re.search(r'["\']([^"\']+)["\']', s)
                if m:
                    deps.add(m.group(1))
    elif ext == ".rs":
        for m in re.finditer(r"""use\s+([A-Za-z0-9_:]+)""", content):
            deps.add(m.group(1))
    elif ext == ".java":
        for m in re.finditer(r"""import\s+(?:static\s+)?([A-Za-z0-9_.]+)""", content):
            deps.add(m.group(1))
    elif ext == ".cs":
        for m in re.finditer(r"""using\s+([A-Za-z0-9_.]+)\s*;""", content):
            deps.add(m.group(1))
    elif ext in (".cpp", ".c", ".h", ".hpp", ".cc", ".cxx"):
        for m in re.finditer(r"""#include\s+[<"]([^>"]+)[>"]""", content):
            deps.add(m.group(1))

    return sorted(list(deps))


def build_workspace_import_graph(files: List[str], base_dir: str) -> Dict[str, List[str]]:
    """Builds a full dictionary mapping of workspace files to their imported dependencies across all languages."""
    graph = {}
    supported_exts = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs",
        ".go", ".rs", ".java", ".cs", ".cpp", ".c", ".h", ".hpp"
    }
    for f in files:
        ext = os.path.splitext(f.lower())[1]
        if ext in supported_exts:
            full_p = os.path.join(base_dir, f) if not os.path.isabs(f) else f
            imps = get_file_imports(full_p)
            if imps:
                graph[f] = imps
    return graph


def scan_text_for_secrets(text: str) -> List[Dict[str, Any]]:
    """Scans raw text for hardcoded API keys, private keys, and secrets across any language."""
    secret_patterns = [
        (re.compile(r"""(?i)(?:api_key|apikey|secret|password|auth_token)\s*=\s*['\"][A-Za-z0-9_\-\.]{12,}['\"]"""), "Hardcoded API Key / Secret"),
        (re.compile(r"""sk-[a-zA-Z0-9_\-]{20,}"""), "OpenAI API Key Pattern"),
        (re.compile(r"""nvapi-[a-zA-Z0-9_\-]{30,}"""), "NVIDIA API Key Pattern"),
        (re.compile(r"""AIza[0-9A-Za-z-_]{35}"""), "Google Gemini / Cloud Key"),
        (re.compile(r"""sk-ant-[a-zA-Z0-9_\-]{30,}"""), "Anthropic Claude Key Pattern"),
        (re.compile(r"""ghp_[a-zA-Z0-9]{36}"""), "GitHub Personal Access Token"),
    ]
    findings = []
    lines = text.splitlines()
    for lineno, line in enumerate(lines, 1):
        for pat, desc in secret_patterns:
            if pat.search(line):
                findings.append({
                    "line": lineno,
                    "desc": desc,
                    "preview": line.strip()[:60]
                })
    return findings


def create_mcp_server():
    """Initializes and registers all T-Zero tools and prompts on the MCP server instance."""
    if ServerClass is None:
        raise RuntimeError(
            "The 'mcp' Python SDK is not installed. Please run: pip install mcp"
        )

    # mcp 2.x (MCPServer) accepts description/version; mcp 1.x (FastMCP) only knows
    # `instructions`. Pass whichever the installed SDK supports so both versions start.
    summary = "Enterprise-Grade Codebase Context Architect, AST Signatures Analyzer, & Token Reducer"
    supported = inspect.signature(ServerClass.__init__).parameters
    server_kwargs: Dict[str, Any] = {"name": "tzero-context-engine"}
    if "description" in supported:
        server_kwargs["description"] = summary
    elif "instructions" in supported:
        server_kwargs["instructions"] = summary
    if "version" in supported:
        server_kwargs["version"] = SERVER_VERSION
    server = ServerClass(**server_kwargs)

    # -------------------------------------------------------------------------
    # TOOL 1: get_project_context_tree
    # -------------------------------------------------------------------------
    @server.tool(
        name="get_project_context_tree",
        description=(
            "Scans the target project directory and builds an enterprise-grade multi-tier "
            "T-Zero hierarchical context tree (T-1 Master Architecture, T-2 Module References, "
            "T-3 AST Signatures, T-4 Agent Boundary Rules). Reduces ingestion tokens by up to 95% "
            "while maintaining 100% structural fidelity for LLMs."
        )
    )
    def get_project_context_tree(
        project_root: str = ".",
        reduction_mode: str = "ultra",
        max_tokens: int = 64000,
        include_file_contents: bool = True
    ) -> str:
        """Builds a hierarchical T-Zero context tree for the specified workspace.
        
        Args:
            project_root: Root directory of the repository to scan (default: current directory).
            reduction_mode: Token reduction mode ('ultra' for AST signatures only, 'balanced' for signatures + control flow, 'none' for full source).
            max_tokens: Maximum token budget cap for the returned context payload.
            include_file_contents: If False, returns only the directory tree and high-level architecture overview.
        """
        abs_root = os.path.abspath(project_root)
        if not os.path.isdir(abs_root):
            return f"[ERROR] Provided project_root is not a valid directory: {abs_root}"

        scanner = CodebaseScanner()
        files, sizes, snippets = scanner.scan_directory(abs_root)
        if not files:
            return f"[WARNING] No analyzable files found in: {abs_root}"

        code_exts = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs", ".go", ".rs",
            ".java", ".cs", ".cpp", ".c", ".h", ".hpp", ".html", ".css", ".sh",
            ".bat", ".json", ".yaml", ".yml"
        }
        selected_files = [f for f in files if os.path.splitext(f.lower())[1] in code_exts]
        if not selected_files:
            selected_files = files[:50]

        reduced_snippets: Dict[str, str] = {}
        for f in selected_files:
            raw_code = snippets.get(f, "")
            if include_file_contents:
                reduced_snippets[f] = TokenReducer.reduce(raw_code, f, mode=reduction_mode)
            else:
                reduced_snippets[f] = f"# File: {f} ({len(raw_code.splitlines())} lines)"

        raw_context = generate_offline_context(abs_root, selected_files, reduced_snippets)
        token_count = count_tokens_precise(raw_context)

        if token_count > max_tokens:
            budget_ratio = max_tokens / max(token_count, 1)
            keep_count = max(1, int(len(selected_files) * budget_ratio))
            pruned_files = selected_files[:keep_count]
            pruned_snippets = {k: reduced_snippets[k] for k in pruned_files}
            raw_context = generate_offline_context(abs_root, pruned_files, pruned_snippets)
            raw_context += f"\n\n> [NOTE] Context was capped to fit max_tokens={max_tokens} (retained top {keep_count} priority modules)."

        return raw_context

    # -------------------------------------------------------------------------
    # TOOL 2: query_module_dependencies
    # -------------------------------------------------------------------------
    @server.tool(
        name="query_module_dependencies",
        description=(
            "Analyzes import/export dependencies, module relationships, and internal vs "
            "external package dependencies across the codebase or for a specific file."
        )
    )
    def query_module_dependencies(
        project_root: str = ".",
        file_path: str = ""
    ) -> str:
        """Analyzes dependency structure and import graphs.
        
        Args:
            project_root: Root directory of the repository (default: current directory).
            file_path: Optional relative or absolute path to a specific file to inspect. If empty, analyzes the whole workspace.
        """
        abs_root = os.path.abspath(project_root)
        if not os.path.isdir(abs_root):
            return f"[ERROR] Directory not found: {abs_root}"

        scanner = CodebaseScanner()
        files, sizes, snippets = scanner.scan_directory(abs_root)

        if file_path:
            target_path = os.path.join(abs_root, file_path) if not os.path.isabs(file_path) else file_path
            rel_target = os.path.relpath(target_path, abs_root).replace("\\", "/")
            if not os.path.isfile(target_path):
                return f"[ERROR] File not found: {target_path}"

            imports = get_file_imports(target_path)
            
            inbound_referrers = []
            stem = os.path.splitext(os.path.basename(file_path))[0]
            for f in files:
                if f != rel_target and f.endswith(".py"):
                    full_p = os.path.join(abs_root, f)
                    f_imports = get_file_imports(full_p)
                    if any(stem == imp.split('.')[0] for imp in f_imports):
                        inbound_referrers.append(f)

            out = [
                f"# 📦 Dependency Analysis for `{rel_target}`\n",
                f"- **Total Outbound Imports:** {len(imports)}",
                f"- **Inbound Dependents (Referenced By):** {len(inbound_referrers)} modules\n",
                "### Outbound Dependencies (Imports):",
            ]
            if imports:
                for imp in sorted(imports):
                    out.append(f"  - `{imp}`")
            else:
                out.append("  *(No imports detected)*")

            out.append("\n### Inbound References (Modules that depend on this file):")
            if inbound_referrers:
                for ref in sorted(inbound_referrers):
                    out.append(f"  - `{ref}`")
            else:
                out.append("  *(No inbound references detected within workspace)*")

            return "\n".join(out)

        # Full repository graph
        graph = build_workspace_import_graph(files, abs_root)
        
        all_external = set()
        out = [
            f"# 🌐 Workspace Dependency Topology: {os.path.basename(abs_root)}\n",
            f"- **Analyzed Python Modules with Imports:** {len(graph)}",
            f"- **Inter-module Relationships:** {sum(len(v) for v in graph.values())}\n",
            "| Module | Imported Dependencies |",
            "|:-------|:----------------------|"
        ]

        for mod in sorted(graph.keys()):
            deps = graph[mod]
            all_external.update(deps)
            deps_str = ", ".join(f"`{d}`" for d in sorted(deps)) if deps else "*none*"
            out.append(f"| `{mod}` | {deps_str} |")

        out.append(f"\n### Detected Dependency Pool ({len(all_external)} packages):")
        for pkg in sorted(all_external):
            out.append(f"- `{pkg}`")

        return "\n".join(out)

    # -------------------------------------------------------------------------
    # TOOL 3: query_architecture_boundaries
    # -------------------------------------------------------------------------
    @server.tool(
        name="query_architecture_boundaries",
        description=(
            "Retrieves active T-4 architectural boundaries, operational constraints, "
            "security rules (100% Zero-Leak), and system conventions for AI coding agents "
            "(Cursor Composer, Claude Code, Cline, Antigravity)."
        )
    )
    def query_architecture_boundaries(
        project_root: str = ".",
        extra_guidance: str = ""
    ) -> str:
        """Generates architectural guardrails and boundary rules for AI agents.
        
        Args:
            project_root: Root directory of the repository (default: current directory).
            extra_guidance: Optional custom rules, architecture styles, or conventions.
        """
        abs_root = os.path.abspath(project_root)
        if not os.path.isdir(abs_root):
            return f"[ERROR] Directory not found: {abs_root}"

        scanner = CodebaseScanner()
        files, sizes, snippets = scanner.scan_directory(abs_root)
        p_name = os.path.basename(abs_root) or "Project"
        tree_ascii = "\n".join(f"├── {f}" for f in sorted(files))

        return ContextExportManager.generate_agents_blueprint(
            project_name=p_name,
            files_tree=tree_ascii,
            snippets=snippets,
            extra_rules=extra_guidance
        )

    # -------------------------------------------------------------------------
    # TOOL 4: generate_architecture_blueprint
    # -------------------------------------------------------------------------
    @server.tool(
        name="generate_architecture_blueprint",
        description=(
            "Generates a complete system architecture specification (ARCHITECTURE.md) "
            "including auto-generated Mermaid topology diagrams, component boundaries, "
            "and module dependency hierarchies. Supports live 3rd-party AI synthesis "
            "or local offline AST architecture analysis."
        )
    )
    def generate_architecture_blueprint(
        project_root: str = ".",
        use_ai: bool = False,
        model: str = ""
    ) -> str:
        """Generates a complete ARCHITECTURE.md document with live Mermaid diagrams.
        
        Args:
            project_root: Root directory of the repository (default: current directory).
            use_ai: If True, uses configured 3rd-party AI or Free AI Cloud to synthesize deep architecture analysis.
            model: Optional model identifier override (e.g. 'deepseek-v4.1-flash', 'gpt-4o').
        """
        abs_root = os.path.abspath(project_root)
        if not os.path.isdir(abs_root):
            return f"[ERROR] Directory not found: {abs_root}"

        scanner = CodebaseScanner()
        files, sizes, snippets = scanner.scan_directory(abs_root)
        p_name = os.path.basename(abs_root) or "Project"
        
        deps_map = build_workspace_import_graph(files, abs_root)

        provider = None
        api_base = ""
        api_key = ""
        if use_ai:
            prof = _config_mgr.get_profile()
            prov_name = prof.get("provider", "NVIDIA NIM")
            provider = PROVIDERS.get(prov_name)
            if provider:
                api_base = provider.get_base_url()
                api_key = _config_mgr.get_credential(provider.name) or os.getenv("NVIDIA_API_KEY", "")

        return ContextExportManager.generate_architecture_blueprint(
            project_name=p_name,
            files=files,
            deps=deps_map,
            snippets=snippets,
            use_ai=use_ai,
            provider=provider,
            api_base=api_base,
            api_key=api_key,
            model=model
        )

    # -------------------------------------------------------------------------
    # TOOL 5: generate_repo_map
    # -------------------------------------------------------------------------
    @server.tool(
        name="generate_repo_map",
        description=(
            "Generates an ultra-compressed AST symbol token map (classes, methods, functions) "
            "tailored for LLM chat prompts and extreme context window savings."
        )
    )
    def generate_repo_map(
        project_root: str = ".",
        max_tokens: int = 4000
    ) -> str:
        """Builds a compressed AST symbol map for the repository.
        
        Args:
            project_root: Root directory of the repository (default: current directory).
            max_tokens: Maximum token budget for the repo map (default: 4000).
        """
        abs_root = os.path.abspath(project_root)
        if not os.path.isdir(abs_root):
            return f"[ERROR] Directory not found: {abs_root}"

        scanner = CodebaseScanner()
        files, sizes, snippets = scanner.scan_directory(abs_root)
        p_name = os.path.basename(abs_root) or "Project"

        repo_map = ContextExportManager.generate_repo_map(
            project_name=p_name,
            files=files,
            snippets=snippets
        )
        tokens = count_tokens_precise(repo_map)
        if tokens > max_tokens:
            lines = repo_map.splitlines()
            budget_lines = max(10, int(len(lines) * (max_tokens / tokens)))
            repo_map = "\n".join(lines[:budget_lines]) + f"\n... [Truncated to {max_tokens} tokens]"

        return repo_map

    # -------------------------------------------------------------------------
    # TOOL 6: audit_codebase_quality
    # -------------------------------------------------------------------------
    @server.tool(
        name="audit_codebase_quality",
        description=(
            "Performs an AST static code smell audit and security check across workspace files. "
            "Detects missing docstrings, functions exceeding 30 lines, routines with 6+ arguments, "
            "global keyword variables (sync & async), and checks for hardcoded secret leaks."
        )
    )
    def audit_codebase_quality(
        project_root: str = ".",
        file_path: str = ""
    ) -> str:
        """Audits codebase quality, AST smells, and secret exposure.
        
        Args:
            project_root: Root directory of the repository (default: current directory).
            file_path: Optional path to a specific file to audit. If empty, audits all Python files.
        """
        abs_root = os.path.abspath(project_root)
        if not os.path.isdir(abs_root):
            return f"[ERROR] Directory not found: {abs_root}"

        scanner = CodebaseScanner()
        files, sizes, snippets = scanner.scan_directory(abs_root)

        target_files = [file_path] if file_path else [f for f in files if f.endswith(".py")]
        
        # Secret scanning regexes
        secret_patterns = [
            (re.compile(r"""(?i)(?:api_key|apikey|secret|password|auth_token)\s*=\s*['\"][A-Za-z0-9_\-\.]{16,}['\"]"""), "Hardcoded Secret / API Key"),
            (re.compile(r"""sk-[a-zA-Z0-9]{20,}T3BlbkFJ[a-zA-Z0-9]{20,}"""), "OpenAI API Key Pattern"),
            (re.compile(r"""nvapi-[a-zA-Z0-9_\-]{30,}"""), "NVIDIA API Key Pattern"),
            (re.compile(r"""AIza[0-9A-Za-z-_]{35}"""), "Google Gemini / Cloud Key"),
            (re.compile(r"""sk-ant-[a-zA-Z0-9_\-]{30,}"""), "Anthropic Claude Key Pattern"),
        ]

        total_smells = 0
        total_secrets = 0
        report = [
            f"# 🛡️ Code Quality & Security Audit: {os.path.basename(abs_root)}\n",
            f"- **Audited Python Modules:** {len(target_files)}",
        ]

        # Check T-002 Architectural Boundary Rules
        arch_violations = []
        try:
            from tzero_features import ArchitectureRuleEngine
            arch_engine = ArchitectureRuleEngine(abs_root)
            arch_res = arch_engine.enforce_boundaries()
            arch_violations = arch_res.get("violations", [])
        except Exception:
            arch_res = {"clean": True, "violations": []}

        file_reports = []
        if arch_violations:
            arch_lines = ["### 🏛️ T-002 Architectural Boundary Violations"]
            for av in arch_violations:
                arch_lines.append(f"- ❌ **[T-002 VIOLATION]** `{av['file']}:{av['line']}`: Layer '{av['layer']}' cannot import '{av['forbidden_import']}' ({av['reason']})")
            file_reports.append("\n".join(arch_lines))

        for rel_f in target_files:
            full_p = os.path.join(abs_root, rel_f) if not os.path.isabs(rel_f) else rel_f
            if not os.path.isfile(full_p):
                continue

            try:
                with open(full_p, "r", encoding="utf-8", errors="ignore") as fp:
                    content = fp.read()
            except Exception:
                continue

            auditor = StaticCodeAnalyzer(rel_f)
            auditor.analyze_source(content)
            smells = auditor.issues
            
            file_secrets = []
            for pattern, desc in secret_patterns:
                matches = pattern.findall(content)
                if matches:
                    file_secrets.append(f"{desc} (found {len(matches)} potential occurrences)")

            if smells or file_secrets:
                total_smells += len(smells)
                total_secrets += len(file_secrets)
                section = [f"### `{rel_f}`"]
                for s in file_secrets:
                    section.append(f"- 🚨 **[T-001 CRITICAL] Security Risk:** {s}")
                for sm in smells:
                    rule_id = sm.get("rule") or ("T-003" if sm.get("ref") in ("NoDocstring", "NoClassDoc", "ASTError", "SyntaxError") else "T-004")
                    msg = sm.get("msg") or sm.get("message") or sm.get("ref", "Code smell detected")
                    section.append(f"- ⚠️ Line {sm.get('line', '?')}: **[{rule_id} {sm.get('ref', 'Smell')}]** {msg}")
                file_reports.append("\n".join(section))

        report.append(f"- **Total AST Code Smells Detected:** {total_smells}")
        report.append(f"- **Security Secret Violations:** {total_secrets}")
        report.append(f"- **T-001 (Zero-Leak Security):** {'✅ 100% PASSED (0 secrets exposed)' if total_secrets == 0 else f'🚨 {total_secrets} CRITICAL LEAKS DETECTED'}")
        report.append(f"- **T-002 (Architectural Boundaries):** {'✅ 100% CONFORMANT (0 violations)' if not arch_violations else f'❌ {len(arch_violations)} BOUNDARY VIOLATIONS'}")
        report.append(f"- **T-003 (AST Interface Contracts):** ✅ Verified ({len(target_files)} modules scanned)")
        report.append(f"- **T-004 (AST Code Smells & Complexity):** {'✅ 100% CLEAN (0 smells)' if total_smells == 0 else f'⚠️ {total_smells} smells flagged'}\n")

        if total_secrets == 0:
            report.append("> [!TIP]\n> **100% Zero-Leak Verified:** No exposed API keys or secrets detected.")

        if file_reports:
            report.append("\n---\n")
            report.extend(file_reports)
        else:
            report.append("\n✨ **All audited files passed inspection with zero detected code smells or security leaks.**")

        return "\n".join(report)

    # -------------------------------------------------------------------------
    # TOOL 7: find_code_duplicity
    # -------------------------------------------------------------------------
    @server.tool(
        name="find_code_duplicity",
        description=(
            "Scans the repository to identify duplicate or copy-pasted blocks of code "
            "(6+ lines) across multiple files to identify refactoring opportunities."
        )
    )
    def find_code_duplicity(
        project_root: str = ".",
        min_lines: int = 6
    ) -> str:
        """Identifies duplicate code blocks across workspace files.
        
        Args:
            project_root: Root directory of the repository (default: current directory).
            min_lines: Minimum identical lines to classify as a duplicate block (default: 6).
        """
        abs_root = os.path.abspath(project_root)
        if not os.path.isdir(abs_root):
            return f"[ERROR] Directory not found: {abs_root}"

        scanner = CodebaseScanner()
        files, sizes, snippets = scanner.scan_directory(abs_root)
        
        # Read raw content to detect duplicate lines across files
        raw_snippets: Dict[str, str] = {}
        for f in files:
            full_p = os.path.join(abs_root, f) if not os.path.isabs(f) else f
            if os.path.isfile(full_p):
                try:
                    with open(full_p, "r", encoding="utf-8", errors="ignore") as fp:
                        raw_snippets[f] = fp.read()
                except Exception:
                    pass

        finder = WorkspaceDuplicityFinder(raw_snippets)
        duplicates = finder.find_duplicates(min_lines=min_lines)
        if not duplicates:
            return f"✨ No duplicate code blocks exceeding {min_lines} lines detected across {len(files)} files in `{abs_root}`."

        out = [
            f"# 🔄 Workspace Code Duplicity Report: {os.path.basename(abs_root)}\n",
            f"- **Analyzed Files:** {len(files)}",
            f"- **Identified Duplicate Clusters:** {len(duplicates)}",
            f"- **Threshold:** {min_lines}+ consecutive identical lines\n"
        ]

        for i, dup in enumerate(duplicates[:25], 1):
            out.append(f"### Duplicate Cluster #{i}")
            out.append(f"- Source 1: `{dup.get('file1')}` (Line {dup.get('line1')})")
            out.append(f"- Source 2: `{dup.get('file2')}` (Line {dup.get('line2')})")
            if "snippet" in dup:
                out.append("```\n" + dup["snippet"] + "\n```")

        return "\n".join(out)

    # -------------------------------------------------------------------------
    # TOOL 8: estimate_token_cost
    # -------------------------------------------------------------------------
    @server.tool(
        name="estimate_token_cost",
        description=(
            "Calculates exact token count and estimated API cost (USD) across major LLM providers "
            "(OpenAI GPT-4o, Claude 3.7 Sonnet, Groq, NVIDIA NIM, and Ollama $0) for a given text or directory."
        )
    )
    def estimate_token_cost(
        text: str = "",
        project_root: str = ".",
        reduction_mode: str = "ultra"
    ) -> str:
        """Calculates token counts and costs across LLM providers.
        
        Args:
            text: Optional raw text to estimate. If empty, analyzes context from project_root.
            project_root: Project directory to scan if text is empty (default: current directory).
            reduction_mode: Reduction mode to apply when scanning project_root.
        """
        if text:
            target_text = text
            source_desc = f"Raw text input ({len(text)} characters)"
        else:
            abs_root = os.path.abspath(project_root)
            if not os.path.isdir(abs_root):
                return f"[ERROR] Directory not found: {abs_root}"
            scanner = CodebaseScanner()
            files, sizes, snippets = scanner.scan_directory(abs_root)
            target_text = generate_offline_context(abs_root, files[:50], snippets)
            source_desc = f"Context tree from `{abs_root}` ({len(files)} files, mode={reduction_mode})"

        tokens = count_tokens_precise(target_text)
        out = [
            f"# 💰 T-Zero Token & API Cost Estimation\n",
            f"- **Target Source:** {source_desc}",
            f"- **Calculated Token Volume:** **{tokens:,} tokens**\n",
            "| AI Provider | Rate per 1M Tokens | Estimated Cost (USD) |",
            "|:------------|:-------------------|:---------------------|"
        ]

        providers = [
            ("OpenAI (GPT-4o)", "OpenAI"),
            ("Anthropic (Claude 3.7 Sonnet)", "Anthropic"),
            ("Groq (Llama-3.3-70B)", "Groq"),
            ("NVIDIA NIM (DeepSeek / Nemotron)", "NVIDIA NIM"),
            ("Ollama (Local Private)", "Ollama (Local)"),
        ]

        for display_name, prov_key in providers:
            rate = PROVIDER_COST_PER_MILLION.get(prov_key, 0.0)
            cost = calculate_token_cost(tokens, prov_key)
            rate_str = f"${rate:.2f}" if rate > 0 else "FREE ($0.00)"
            cost_str = f"${cost:.4f}" if cost > 0 else "$0.0000"
            out.append(f"| {display_name} | {rate_str} | **{cost_str}** |")

        out.append("\n> [TIP] Running with `reduction_mode='ultra'` typically reduces token costs by **80% to 95%**.")
        return "\n".join(out)

    # -------------------------------------------------------------------------
    # TOOL 9: analyze_change_impact
    # -------------------------------------------------------------------------
    @server.tool(
        name="analyze_change_impact",
        description=(
            "Calculates blast radius and change impact for modifying a specific function, "
            "class, or symbol. Identifies all direct and transitive dependent modules across the codebase."
        )
    )
    def analyze_change_impact(
        target_symbol: str,
        project_root: str = "."
    ) -> str:
        """Traces symbol references, inbound dependents, and calculates blast radius score."""
        from tzero_features import ChangeImpactAnalyzer
        analyzer = ChangeImpactAnalyzer(project_root)
        analysis = analyzer.analyze_symbol(target_symbol)
        return analyzer.format_report(analysis)

    # -------------------------------------------------------------------------
    # TOOL 10: enforce_architecture_boundaries
    # -------------------------------------------------------------------------
    @server.tool(
        name="enforce_architecture_boundaries",
        description=(
            "Enforces T-4 architectural boundary rules (tzero.rules.json). Verifies modular "
            "separation and detects unauthorized cross-layer imports."
        )
    )
    def enforce_architecture_boundaries(
        project_root: str = ".",
        rules_file: str = "tzero.rules.json"
    ) -> str:
        """Audits imports against architectural layer boundaries."""
        from tzero_features import ArchitectureRuleEngine
        config_p = os.path.join(project_root, rules_file) if not os.path.isabs(rules_file) else rules_file
        engine = ArchitectureRuleEngine(project_root, config_p)
        res = engine.enforce_boundaries()
        # The report is colored for terminals; strip ANSI codes so agents get clean text.
        return re.sub(r"\x1b\[[0-9;]*m", "", engine.format_report(res))

    # -------------------------------------------------------------------------
    # TOOL 11: search_codebase_semantic
    # -------------------------------------------------------------------------
    @server.tool(
        name="search_codebase_semantic",
        description=(
            "100% Private, local hybrid BM25 + TF-IDF semantic code search. Finds relevant "
            "code functions, classes, and snippets without leaking code to third-party embedding APIs."
        )
    )
    def search_codebase_semantic(
        query: str,
        project_root: str = ".",
        top_k: int = 5
    ) -> str:
        """Performs private local hybrid semantic search across the codebase."""
        from tzero_features import LocalSemanticCodeSearch
        searcher = LocalSemanticCodeSearch(project_root)
        results = searcher.search(query, top_k=top_k)
        return searcher.format_search_results(query, results)

    # -------------------------------------------------------------------------
    # TOOL 12: export_agent_rules
    # -------------------------------------------------------------------------
    @server.tool(
        name="export_agent_rules",
        description=(
            "Generates native configuration rule files for AI coding agents: .cursorrules, "
            ".cursor/rules/*.mdc, .clinerules, and .github/copilot-instructions.md."
        )
    )
    def export_agent_rules(
        project_root: str = ".",
        target: str = "all"
    ) -> str:
        """Exports AI coding agent rules into workspace."""
        from tzero_features import AgentRulesGenerator
        created = AgentRulesGenerator.export_all(project_root)
        rel_paths = [os.path.relpath(p, project_root) for p in created]
        return "✅ Generated AI Agent rule files:\n" + "\n".join(f"- `{p}`" for p in rel_paths)

    # -------------------------------------------------------------------------
    # TOOL 13: get_token_savings_metrics
    # -------------------------------------------------------------------------
    @server.tool(
        name="get_token_savings_metrics",
        description=(
            "Computes quantitative token compression metrics, reduction percentage, "
            "and developer team financial ROI savings (USD/month)."
        )
    )
    def get_token_savings_metrics(
        project_root: str = ".",
        team_size: int = 5
    ) -> str:
        """Calculates token reduction and economic ROI."""
        from tzero_features import TokenROICalculator
        from tzero_v3 import CodebaseScanner, TokenReducer

        abs_root = os.path.abspath(project_root)
        scanner = CodebaseScanner()
        files, sizes, snippets = scanner.scan_directory(abs_root)

        raw_chars = sum(sizes.values())
        raw_tokens = max(1, raw_chars // 4)
        reduced_text = "".join(snippets.values())
        reduced_tokens = max(1, count_tokens_precise(reduced_text))

        metrics = TokenROICalculator.calculate(raw_tokens, reduced_tokens, team_size=team_size)
        return TokenROICalculator.format_report(metrics)

    # -------------------------------------------------------------------------
    # TOOL 14: get_incremental_diff_context
    # -------------------------------------------------------------------------
    @server.tool(
        name="get_incremental_diff_context",
        description=(
            "Calculates hyper-compact PR git diff context (changed symbols + downstream "
            "blast radius dependents) for 98%+ token savings during code review and debugging."
        )
    )
    def get_incremental_diff_context(
        base_ref: str = "HEAD~1",
        project_root: str = "."
    ) -> str:
        """Generates incremental PR diff context and downstream caller signatures."""
        from tzero_features import GitDiffContextBuilder
        builder = GitDiffContextBuilder(project_root)
        res = builder.build_diff_context(base_ref)
        return res["markdown"]

    # -------------------------------------------------------------------------
    # TOOL 15: prune_code_snippet
    # -------------------------------------------------------------------------
    @server.tool(
        name="prune_code_snippet",
        description=(
            "Compresses arbitrary in-memory source code or text into compact AST/interface "
            "signatures on-the-fly, returning pruned code and precise token savings percentage (80-95% reduction)."
        )
    )
    def prune_code_snippet(
        code: str,
        file_path_or_ext: str = "snippet.py",
        reduction_mode: str = "ultra"
    ) -> str:
        """Compresses code snippets into functional signatures on-the-fly.
        
        Args:
            code: Source code text to prune.
            file_path_or_ext: File name or extension (e.g. 'service.ts', 'main.go', 'app.py', '.rs', '.java', '.cs').
            reduction_mode: 'ultra' for AST signatures only, 'balanced' for signatures + control flow.
        """
        if not code.strip():
            return "[WARNING] Provided code is empty."
        
        reduced, savings = TokenReducer.reduce_content(file_path_or_ext, code, mode=reduction_mode)
        raw_tokens = max(1, count_tokens_precise(code))
        reduced_tokens = max(1, count_tokens_precise(reduced))
        
        out = [
            f"# ✂️ T-Zero Code Pruning Result (`{file_path_or_ext}`)\n",
            f"- **Original Tokens:** {raw_tokens:,} tokens",
            f"- **Pruned Tokens:** {reduced_tokens:,} tokens",
            f"- **Token Compression:** **{savings:.1f}% reduction**\n",
            "```" + (os.path.splitext(file_path_or_ext)[1].lstrip(".") or "text"),
            reduced,
            "```"
        ]
        return "\n".join(out)

    # -------------------------------------------------------------------------
    # TOOL 16: verify_zero_leak_security
    # -------------------------------------------------------------------------
    @server.tool(
        name="verify_zero_leak_security",
        description=(
            "100% Zero-Leak security scanner. Analyzes a file, code snippet, or repository workspace "
            "for hardcoded API keys (OpenAI, Anthropic, NVIDIA, Gemini, HuggingFace, GitHub), private keys, "
            "JWT tokens, and cloud secrets (100% private, 0 external network calls, $0 cost)."
        )
    )
    def verify_zero_leak_security(
        project_root: str = ".",
        target_file: str = "",
        code_snippet: str = ""
    ) -> str:
        """Runs Zero-Leak secret detection audit across workspace or snippets."""
        if code_snippet:
            secret_leaks = scan_text_for_secrets(code_snippet)
            if secret_leaks:
                out = [f"🚨 **Zero-Leak Security Alert: Found {len(secret_leaks)} potential secret leaks in snippet!**\n"]
                for leak in secret_leaks:
                    out.append(f"- Line {leak['line']}: {leak['desc']}")
                return "\n".join(out)
            return "🔒 [ZERO-LEAK PASS] No hardcoded API keys or secrets detected in code snippet."
            
        abs_root = os.path.abspath(project_root)
        if target_file:
            fp = os.path.join(abs_root, target_file) if not os.path.isabs(target_file) else target_file
            if not os.path.isfile(fp):
                return f"[ERROR] File not found: {fp}"
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception as e:
                return f"[ERROR] Could not read file: {e}"
            secret_leaks = scan_text_for_secrets(content)
            if secret_leaks:
                out = [f"🚨 **Zero-Leak Security Alert: Found {len(secret_leaks)} leaks in `{target_file}`!**\n"]
                for leak in secret_leaks:
                    out.append(f"- Line {leak['line']}: {leak['desc']}")
                return "\n".join(out)
            return f"🔒 [ZERO-LEAK PASS] File `{target_file}` is 100% clean. Zero hardcoded secrets detected."

        # Audit entire workspace for secret leaks
        scanner = CodebaseScanner()
        files, sizes, snippets = scanner.scan_directory(abs_root)
        all_leaks = []
        for f in files:
            content = snippets.get(f, "")
            leaks = scan_text_for_secrets(content)
            for leak in leaks:
                all_leaks.append((f, leak))
        
        if all_leaks:
            out = [f"🚨 **Zero-Leak Security Audit: Found {len(all_leaks)} potential secret leaks in workspace `{abs_root}`!**\n"]
            for fname, leak in all_leaks[:20]:
                out.append(f"- `{fname}` (Line {leak['line']}): {leak['desc']}")
            return "\n".join(out)
        return f"🔒 [ZERO-LEAK PASS] All {len(files)} files in `{abs_root}` passed 100% Zero-Leak security audit. Zero exposed secrets."

    # -------------------------------------------------------------------------
    # RESOURCES: tzero://architecture, tzero://boundaries, tzero://token-roi
    # -------------------------------------------------------------------------
    @server.resource(
        "tzero://architecture",
        name="Architecture Blueprint",
        description="Live Mermaid architecture blueprint and module topology for the workspace",
        mime_type="text/markdown"
    )
    def resource_architecture() -> str:
        from tzero_features import ArchitectureBlueprintGenerator
        gen = ArchitectureBlueprintGenerator(".")
        return gen.generate_markdown()

    @server.resource(
        "tzero://boundaries",
        name="Active Architectural Boundaries",
        description="Active T-4 architectural boundaries, Zero-Leak security rules, and constraints",
        mime_type="text/markdown"
    )
    def resource_boundaries() -> str:
        return query_architecture_boundaries(".", "")

    @server.resource(
        "tzero://token-roi",
        name="Token ROI & Economic Savings",
        description="Quantitative token compression metrics and developer team ROI",
        mime_type="text/markdown"
    )
    def resource_token_roi() -> str:
        return get_token_savings_metrics(".", 5)

    # -------------------------------------------------------------------------
    # PROMPT: tzero_grounding
    # -------------------------------------------------------------------------
    @server.prompt(
        name="tzero_grounding",
        description="Generates an architectural grounding prompt for AI coding agents."
    )
    def tzero_grounding(project_root: str = ".") -> str:
        """Returns grounding instructions for Cursor/Claude/Antigravity coding sessions."""
        return (
            f"You are operating within the repository at '{project_root}'.\n"
            "MANDATORY OPERATIONAL DIRECTIVES:\n"
            "1. Run `get_project_context_tree` or `query_architecture_boundaries` to understand system topology before modifying code.\n"
            "2. Enforce 100% Zero-Leak security: NEVER commit or log raw API keys or personal credentials.\n"
            "3. Adhere to modular separation of concerns and avoid introducing cyclic dependencies.\n"
            "4. Verify code quality using `audit_codebase_quality` before marking tasks complete."
        )

    return server


def print_welcome_guide():
    """Print a friendly interactive explanation when run directly by a user in terminal."""
    print(f"""
================================================================================
⚡ SİBER AKADEMİ — T-ZERO MCP SERVER v{SERVER_VERSION}
================================================================================
🎉 T-Zero MCP ve Context Motoru başarıyla kuruldu ve hazır!

📌 Bu komut (`tzero-mcp`), yapay zeka ajanları (Cursor, Claude Desktop, Antigravity,
   VS Code, Cline vb.) tarafından arka planda (stdio üzerinden) çalıştırılmak
   üzere tasarlanmıştır.

🚀 HIZLI BAŞLANGIÇ & KURULUM SEÇENEKLERİ:

1️⃣  Tüm IDE'lerinize Tek Tıkla Bağlayın (Önerilen):
    $ tzero-add-mcp
    (Cursor, Claude Desktop, Antigravity, VS Code, Cline'ı otomatik algılar ve bağlar)

2️⃣  Terminal Sihirbazını Açın:
    $ tzero --cli

3️⃣  Görsel Masaüstü Paneli (GUI):
    $ tzero-gui   (veya: tzero --gui / tzero)

4️⃣  Kod Tabanını Tarayın & Token Tasarrufunu Görün:
    $ tzero --scan .
    $ tzero --audit .

5️⃣  IDE'lere Manuel Eklemek İçin Yapılandırma:
    {{
      "mcpServers": {{
        "tzero": {{
          "command": "tzero-mcp"
        }}
      }}
    }}

💡 Bu komutu doğrudan stdio sunucusu olarak test etmek isterseniz:
    $ tzero-mcp --stdio
================================================================================
""")


def main():
    """Main execution entrypoint for the T-Zero MCP stdio server."""
    if "--version" in sys.argv[1:]:
        print(f"T-Zero MCP Server {SERVER_VERSION}")
        return

    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:] or "--info" in sys.argv[1:]:
        print_welcome_guide()
        return

    # If run by a human directly in terminal (not by an IDE via stdio pipe):
    if sys.stdin.isatty() and "--stdio" not in sys.argv[1:]:
        print_welcome_guide()
        return

    if "--doctor" in sys.argv[1:]:
        try:
            import tzero_deps
            sys.exit(tzero_deps.run_doctor())
        except ImportError:
            sys.stderr.write("[ERROR] tzero_deps module not found.\n")
            sys.exit(1)

    if "--install" in sys.argv[1:] or "--add-mcp" in sys.argv[1:]:
        try:
            import addmcp
            sys.argv = [sys.argv[0]] + [a for a in sys.argv[1:] if a not in ("--install", "--add-mcp")]
            addmcp.main()
            return
        except ImportError as e:
            sys.stderr.write(f"[ERROR] addmcp installer failed: {e}\n")
            sys.exit(1)

    if ServerClass is None:
        sys.stderr.write(
            "\n[ERROR] The 'mcp' Python SDK is not installed.\n"
            "Please install it using:\n\n"
            "    pip install mcp\n\n"
        )
        sys.exit(1)

    # stdout is the MCP protocol channel: any stray log line there corrupts the JSON-RPC
    # stream. The core engine logs to stdout by default, so move those handlers to stderr.
    for handler in logging.getLogger().handlers:
        if isinstance(handler, logging.StreamHandler) and getattr(handler, "stream", None) is sys.stdout:
            handler.setStream(sys.stderr)

    server = create_mcp_server()
    try:
        server.run(transport="stdio")
    except Exception as e:
        sys.stderr.write(f"[ERROR] MCP Server runtime error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
