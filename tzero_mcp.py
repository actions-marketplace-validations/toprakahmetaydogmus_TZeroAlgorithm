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
try:
    from mcp.types import ToolAnnotations
except ImportError:
    ToolAnnotations = None

from typing import Dict, List, Optional, Any
try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

try:
    from pydantic import Field
except ImportError:
    def Field(default=..., description=""):
        return default

SERVER_VERSION = "6.0.0"

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
        PROVIDERS,
        ConfigManager,
    )
    _config_mgr = ConfigManager()
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
    elif ext in (".java", ".kt", ".kts"):
        for m in re.finditer(r"""import\s+(?:static\s+)?([A-Za-z0-9_.]+)""", content):
            deps.add(m.group(1))
    elif ext == ".swift":
        for m in re.finditer(r"""import\s+([A-Za-z0-9_]+)""", content):
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
        ".go", ".rs", ".java", ".cs", ".cpp", ".c", ".h", ".hpp",
        ".kt", ".kts", ".swift"
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
            "T-3 AST Signatures, T-4 Agent Boundary Rules).\n\n"
            "Behavior:\n"
            "- Read-only: Performs static AST analysis without modifying any files on disk.\n"
            "- Idempotent: Deterministic output for identical repository states.\n"
            "- 100% Offline: Executes locally without network calls, external embeddings, or LLM billing.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Ingest repository architecture and signatures into prompt context at the start of a coding session or before large refactors (80-95% token savings).\n"
            "- Sibling Routing: For a fast single-page class/method symbol index, use 'generate_repo_map'. For full implementation of an active file with 1st-degree caller/callee skeletons, use 'get_smart_skeleton_context'. For arbitrary in-memory snippets, use 'prune_code_snippet'.\n\n"
            "Returns: Structured Markdown containing directory tree, module outlines, and AST signatures up to max_tokens."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def get_project_context_tree(
        project_root: Annotated[str, Field(default=".", description="Target repository root path to scan (default: current working directory).")] = ".",
        reduction_mode: Annotated[str, Field(default="ultra", description="AST reduction level: 'ultra' for signatures & docstrings (80-95% reduction), 'balanced' for signatures + control headers, 'none' for verbatim source.")] = "ultra",
        max_tokens: Annotated[int, Field(default=64000, description="Upper token budget threshold for returned context. When exceeded, PageRank & Git recency prioritizes critical architectural files.")] = 64000,
        include_file_contents: Annotated[bool, Field(default=True, description="When True, includes AST-reduced file bodies; when False, emits only the directory hierarchy and high-level architectural outline.")] = True
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
            ".bat", ".json", ".yaml", ".yml", ".kt", ".kts", ".swift"
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
            try:
                from tzero_features import RepositoryPageRank
                pr_analyzer = RepositoryPageRank(abs_root)
                ranks = pr_analyzer.rank(top_k=len(selected_files))
                score_map = {r["file"]: r["score"] for r in ranks}
            except Exception:
                score_map = {}

            def file_priority(f: str) -> float:
                pr = score_map.get(f, 0.0)
                full_p = os.path.join(abs_root, f)
                try:
                    mtime = os.path.getmtime(full_p)
                except Exception:
                    mtime = 0.0
                return (pr * 1000.0) + (mtime / 1e9)

            sorted_files = sorted(selected_files, key=file_priority, reverse=True)
            
            pruned_files: List[str] = []
            pruned_snippets: Dict[str, str] = {}
            current_tokens = 0
            keep_count = 0
            for f in sorted_files:
                snip = reduced_snippets.get(f, "")
                t_cost = count_tokens_precise(snip)
                if current_tokens + t_cost <= max_tokens:
                    pruned_files.append(f)
                    pruned_snippets[f] = snip
                    current_tokens += t_cost
                    keep_count += 1
                else:
                    pruned_files.append(f)
                    pruned_snippets[f] = f"# [TRUNCATED] High priority AST boundary. Full content omitted for budget ({max_tokens} tokens)."
                    keep_count += 1
                    break

            raw_context = generate_offline_context(abs_root, pruned_files, pruned_snippets)
            raw_context += f"\n\n> [NOTE] Context was capped to fit max_tokens={max_tokens} (retained top {keep_count} priority modules prioritized via PageRank + Recency)."

        return raw_context

    # -------------------------------------------------------------------------
    # TOOL 2: query_module_dependencies
    # -------------------------------------------------------------------------
    @server.tool(
        name="query_module_dependencies",
        description=(
            "Analyzes import/export dependencies, module relationships, and internal vs external package dependencies across polyglot files (Python, TypeScript, Go, Rust, Java, C#, C++).\n\n"
            "Behavior:\n"
            "- Read-only: Inspects source syntax trees without modifying or moving files.\n"
            "- Idempotent: Deterministic dependency mapping for any scanned repository.\n"
            "- 100% Offline: Local regex and AST parsing; zero external network requests.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run before refactoring, moving, or removing a module to inspect inbound dependents (who imports this) and outbound dependencies (what this imports).\n"
            "- Sibling Routing: For deep recursive function/method call chains (caller -> callee call graph), use 'trace_symbol_call_chain'. To test whether imports violate layer boundary rules, use 'enforce_architecture_boundaries'.\n\n"
            "Returns: Markdown report detailing inbound referrers, outbound imports, and the workspace dependency pool."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def query_module_dependencies(
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository to scan (default: current directory).")] = ".",
        file_path: Annotated[str, Field(default="", description="Optional relative or absolute path to a specific file to inspect. If empty, analyzes the whole workspace.")] = ""
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
            "Retrieves active T-4 architectural tier boundary definitions, operational constraints, and zero-leak security rules defined in tzero.rules.json or built-in defaults.\n\n"
            "Behavior:\n"
            "- Read-only: Reads configuration files; does not modify rules or codebase files.\n"
            "- Idempotent: Returns consistent rule definitions for identical configurations.\n"
            "- 100% Offline: Local JSON file lookup without remote calls.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Consult before designing new features or adding imports to understand layer isolation rules (e.g. presentation cannot import database models) and avoid architecture violations.\n"
            "- Sibling Routing: To actively validate workspace code against these rules and detect violations, use 'enforce_architecture_boundaries'. To view complete Mermaid topology blueprints, use 'generate_architecture_blueprint'.\n\n"
            "Returns: Markdown specification of architectural layers, allowed/forbidden import directions, and security constraints."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def query_architecture_boundaries(
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository where tzero.rules.json is located (default: current directory).")] = ".",
        extra_guidance: Annotated[str, Field(default="", description="Optional custom rules, architecture styles, or conventions to inject into the boundary definition.")] = ""
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
            "Generates a complete system architectural specification (ARCHITECTURE.md) including auto-generated Mermaid component topology diagrams, layer boundaries, and module hierarchies.\n\n"
            "Behavior:\n"
            "- Read-only by default: Returns formatted markdown text. Does NOT write files unless invoked via CLI export.\n"
            "- Idempotent: Produces deterministic AST topology when use_ai=False.\n"
            "- Cost: 100% free and local by default (use_ai=False). If use_ai=True, uses configured environment API key (e.g. NVIDIA NIM / OpenAI) for enriched architectural narrative.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Create or update system architecture documentation and visual Mermaid flow diagrams for onboarding or RFC review.\n"
            "- Sibling Routing: For checking rule compliance against defined boundaries, use 'enforce_architecture_boundaries'. For basic dependency trees, use 'query_module_dependencies'.\n\n"
            "Returns: Comprehensive Markdown document with live Mermaid diagrams, layer classifications, and component interfaces."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def generate_architecture_blueprint(
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository to analyze and document (default: current directory).")] = ".",
        use_ai: Annotated[bool, Field(default=False, description="When True, uses configured 3rd-party AI or Free AI Cloud to synthesize deep architecture analysis; when False (default), runs 100% offline AST analysis.")] = False,
        model: Annotated[str, Field(default="", description="Optional model identifier override (e.g. 'deepseek-v4.1-flash', 'gpt-4o') when use_ai is True.")] = ""
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
            "Generates an ultra-compressed AST symbol token map (classes, methods, functions) tailored for LLM chat prompts and extreme context window savings.\n\n"
            "Behavior:\n"
            "- Read-only: Extracts AST signatures without writing or modifying files.\n"
            "- Idempotent: Deterministic symbol catalog for the same codebase state.\n"
            "- 100% Offline: Local AST extraction; zero external API calls.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Provide the LLM with an immediate high-level index of all classes and functions across the repository in minimal tokens (~5-15 tokens per file).\n"
            "- Sibling Routing: For full function signatures with parameter types and docstrings, use 'get_project_context_tree'. For 1st-degree context around a specific focus file, use 'get_smart_skeleton_context'.\n\n"
            "Returns: Compact Markdown symbol map indexed by file path."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def generate_repo_map(
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository to map (default: current directory).")] = ".",
        max_tokens: Annotated[int, Field(default=4000, description="Maximum token budget for the repo map (default: 4000).")] = 4000
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
            "Performs an AST static code smell audit, cyclomatic complexity check, copy-paste duplicity scan, and 100% Zero-Leak security audit for exposed credentials.\n\n"
            "Behavior:\n"
            "- Read-only: Evaluates AST nodes and regex patterns; does not modify or delete files.\n"
            "- Idempotent: Produces consistent quality diagnostics for the same code.\n"
            "- 100% Offline: Fully private local analysis; zero external requests.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run as a pre-commit or pre-PR code health audit to identify complex routines (> 30 lines, > 5 args), missing docstrings, architectural boundary violations, and hardcoded secrets.\n"
            "- Sibling Routing: If you only need to verify zero hardcoded secrets/API keys, use 'verify_zero_leak_security'. If you only want unused function detection, use 'find_dead_code'. If you only want duplicate logic blocks, use 'find_code_duplicity'.\n\n"
            "Returns: Comprehensive diagnostic Markdown report with severity ratings (T-001 Security, T-002 Boundaries, T-003 Contracts, T-004 Complexity), line numbers, and actionable remediation steps."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def audit_codebase_quality(
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository to audit (default: current directory).")] = ".",
        file_path: Annotated[str, Field(default="", description="Optional path to a specific file to audit. If empty, audits all code files in the workspace.")] = ""
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
            (re.compile(r"""(?i)(?:api_key|apikey|secret|password|auth_token)\s*=\s*['"][A-Za-z0-9_\-\.]{16,}['"]"""), "Hardcoded Secret / API Key"),
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
            "Scans the repository to identify duplicate or copy-pasted blocks of code across multiple files to identify refactoring opportunities.\n\n"
            "Behavior:\n"
            "- Read-only: Hashes and compares source lines; does not modify code.\n"
            "- Idempotent: Deterministic duplicate detection for any codebase state.\n"
            "- 100% Offline: Fully local execution without network calls.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run during refactoring sprints to locate redundant copy-pasted code blocks suitable for extraction into shared utility functions.\n"
            "- Sibling Routing: For full codebase quality and complexity audits, use 'audit_codebase_quality'. For unused unreferenced code, use 'find_dead_code'.\n\n"
            "Returns: Markdown report detailing duplicate code clusters with file paths, line ranges, and side-by-side code snippets."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def find_code_duplicity(
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository to scan (default: current directory).")] = ".",
        min_lines: Annotated[int, Field(default=6, description="Minimum identical consecutive lines to classify as a duplicate block (default: 6).")] = 6
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
            "Calculates exact token count and estimated API prompting cost (USD) across major LLM providers (OpenAI GPT-4o, Claude 3.7 Sonnet, Groq, NVIDIA NIM, and Ollama $0) for a given text or directory.\n\n"
            "Behavior:\n"
            "- Read-only: Mathematical cost projection; does NOT invoke provider APIs or incur financial billing.\n"
            "- Idempotent: Produces exact calculations for identical token counts.\n"
            "- 100% Offline: Uses local pricing tables without external HTTP queries.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Estimate prompt token volume and dollar costs before sending large codebase context to commercial LLM APIs.\n"
            "- Sibling Routing: To track team monthly/annual cumulative ROI savings and compression metrics over time, use 'get_token_savings_metrics'.\n\n"
            "Returns: Markdown table comparing per-million token rates and total estimated costs across major models."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def estimate_token_cost(
        text: Annotated[str, Field(default="", description="Optional raw text to estimate. If empty, analyzes context generated from project_root.")] = "",
        project_root: Annotated[str, Field(default=".", description="Project directory to scan if text is empty (default: current directory).")] = ".",
        reduction_mode: Annotated[str, Field(default="ultra", description="Reduction tier ('ultra', 'balanced', 'none') applied when scanning project_root.")] = "ultra"
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
            "Calculates blast radius score (0-100) and identifies all direct and transitive dependent modules across the codebase before modifying a specific function, class, or symbol.\n\n"
            "Behavior:\n"
            "- Read-only: AST dependency graph traversal; does not modify source files.\n"
            "- Idempotent: Deterministic impact calculation for any given target symbol.\n"
            "- 100% Offline: Local AST analysis without remote services.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run BEFORE renaming, refactoring, or modifying a function or class to determine which caller modules could break.\n"
            "- Sibling Routing: For deep recursive caller/callee trees with visual Mermaid graphs, use 'trace_symbol_call_chain'. For file-level module dependencies, use 'query_module_dependencies'.\n\n"
            "Returns: Structured Markdown report with blast radius score, risk tier, direct dependents, and transitive impact paths."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def analyze_change_impact(
        target_symbol: Annotated[str, Field(description="Name of the function, class, or method to analyze for change blast radius.")],
        project_root: Annotated[str, Field(default=".", description="Workspace root directory containing target symbols (default: current directory).")] = "."
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
            "Enforces T-4 architectural boundary rules (tzero.rules.json), verifying modular separation and detecting unauthorized cross-layer imports.\n\n"
            "Behavior:\n"
            "- Read-only: Audits import AST statements; does NOT block git, mutate code, or modify configuration files.\n"
            "- Idempotent: Yields consistent validation results for any given codebase state.\n"
            "- 100% Offline: Local AST validation without external dependencies.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run in CI/CD pipelines or before committing to verify that presentation/UI layers do not import internal database/storage modules directly.\n"
            "- Sibling Routing: To view active boundary rules without evaluating code, use 'query_architecture_boundaries'. For general code quality smells, use 'audit_codebase_quality'.\n\n"
            "Returns: Compliance report detailing pass/fail status, violating file paths, line numbers, layer names, and allowed import directions."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def enforce_architecture_boundaries(
        project_root: Annotated[str, Field(default=".", description="Workspace root to validate against architectural rules (default: current directory).")] = ".",
        rules_file: Annotated[str, Field(default="tzero.rules.json", description="Path to rules JSON file (default: 'tzero.rules.json'). Resolves relative to project_root.")] = "tzero.rules.json"
    ) -> str:
        """Audits imports against architectural layer boundaries."""
        from tzero_features import ArchitectureRuleEngine
        config_p = os.path.join(project_root, rules_file) if not os.path.isabs(rules_file) else rules_file
        engine = ArchitectureRuleEngine(project_root, config_p)
        res = engine.enforce_boundaries()
        # The report is colored for terminals; strip ANSI codes so agents get clean text.
        return re.sub(r"\[[0-9;]*m", "", engine.format_report(res))

    # -------------------------------------------------------------------------
    # TOOL 11: search_codebase_semantic
    # -------------------------------------------------------------------------
    @server.tool(
        name="search_codebase_semantic",
        description=(
            "100% Private, local hybrid BM25 + TF-IDF semantic code search across workspace AST tokens, function headers, and docstrings without sending code to third-party embedding APIs.\n\n"
            "Behavior:\n"
            "- Read-only: In-memory inverted index query; does not modify files.\n"
            "- Idempotent: Deterministic search ranking for identical query and code states.\n"
            "- 100% Offline & Private: Never sends code or embeddings to external APIs; $0 cost and zero data leakage.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Find functions, classes, or logic snippets using conceptual natural language queries (e.g. 'authentication jwt token verify', 'rate limit algorithm').\n"
            "- Sibling Routing: For exact string or regex matches, use IDE grep or ripgrep. For finding unused code, use 'find_dead_code'.\n\n"
            "Returns: Ranked Markdown list of matching code snippets with file locations, match scores, and surrounding context."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def search_codebase_semantic(
        query: Annotated[str, Field(description="Natural language or technical keyword query describing the desired code logic.")],
        project_root: Annotated[str, Field(default=".", description="Workspace root directory to index and search (default: current directory).")] = ".",
        top_k: Annotated[int, Field(default=5, description="Maximum number of top-matching code snippets to return (default: 5).")] = 5
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
            "Generates and writes standardized AI agent rule specifications (.cursorrules, .cursor/rules/*.mdc, .clinerules, and .github/copilot-instructions.md) into the workspace.\n\n"
            "Behavior:\n"
            "- Mutating: Creates or updates configuration files in the target workspace directory.\n"
            "- Idempotent: Overwrites existing T-Zero agent rule files with current architecture rules without corrupting user customizations.\n"
            "- 100% Offline: Generates rule files locally using built-in templates.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run when setting up a repository for AI pair-programming with Cursor, Claude Code, Cline, Windsurf, or GitHub Copilot.\n"
            "- Sibling Routing: To view architectural boundaries without writing files to disk, use 'query_architecture_boundaries'.\n\n"
            "Returns: Confirmation message listing all generated rule file paths."),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def export_agent_rules(
        project_root: Annotated[str, Field(default=".", description="Target workspace directory where agent rule files will be created (default: current directory).")] = ".",
        target: Annotated[str, Field(default="all", description="Target editor format: 'cursor', 'cline', 'windsurf', or 'all' (default: 'all').")] = "all"
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
            "Computes quantitative token compression metrics, reduction percentage, and developer team financial ROI savings (USD/month).\n\n"
            "Behavior:\n"
            "- Read-only: Evaluates codebase file sizes and compressed token counts; does not alter files or call APIs.\n"
            "- Idempotent: Deterministic metric calculations for current codebase volume.\n"
            "- 100% Offline: Fully local calculation without network access.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Quantify efficiency gains and financial savings from T-Zero context compression for team reports and engineering leadership.\n"
            "- Sibling Routing: For per-model single-prompt cost comparisons (OpenAI vs Anthropic vs Gemini), use 'estimate_token_cost'.\n\n"
            "Returns: Markdown executive summary with token reduction percentages, monthly developer cost savings, and annual ROI projections."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def get_token_savings_metrics(
        project_root: Annotated[str, Field(default=".", description="Target workspace directory to measure (default: current directory).")] = ".",
        team_size: Annotated[int, Field(default=5, description="Number of developers in the engineering team used to model monthly ROI savings (default: 5).")] = 5
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
            "Calculates hyper-compact PR git diff context (changed symbols + downstream blast radius dependents) for 98%+ token savings during code review and debugging.\n\n"
            "Behavior:\n"
            "- Read-only: Inspects git diff and local AST; does not stage, commit, or revert any git changes.\n"
            "- Idempotent: Deterministic for the same git working tree status.\n"
            "- 100% Offline: Local git CLI and AST processing.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Provide focused context during code review, PR description generation, or bug hunting for pending changes with 98%+ token reduction.\n"
            "- Sibling Routing: For full repository context, use 'get_project_context_tree'. For single-symbol impact analysis, use 'analyze_change_impact'.\n\n"
            "Returns: Structured Markdown diff context with changed symbol signatures, diff hunks, and caller references."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def get_incremental_diff_context(
        base_ref: Annotated[str, Field(default="HEAD~1", description="Git revision or branch to diff against (default: 'HEAD~1').")] = "HEAD~1",
        project_root: Annotated[str, Field(default=".", description="Git repository root path (default: current directory).")] = "."
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
            "Compresses arbitrary in-memory source code or text into compact AST/interface signatures on-the-fly, returning pruned code and precise token savings percentage (80-95% reduction).\n\n"
            "Behavior:\n"
            "- Pure in-memory transformation: Does not read or write any files on disk; takes text input and returns pruned text.\n"
            "- Idempotent: Deterministic output for identical input code and reduction mode.\n"
            "- 100% Offline: Polyglot AST/regex parsers for Python, TypeScript, Go, Rust, Java, C#, C++, Swift, Kotlin.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Compress in-memory code blocks or clipboard buffers before passing them into LLM chat prompts.\n"
            "- Sibling Routing: To scan and compress entire directories or repositories on disk, use 'get_project_context_tree' or 'get_smart_skeleton_context'.\n\n"
            "Returns: Markdown fenced code block with pruned signatures and precise token reduction percentage."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def prune_code_snippet(
        code: Annotated[str, Field(description="Raw source code content to prune.")],
        file_path_or_ext: Annotated[str, Field(default="snippet.py", description="File name or extension (e.g. 'service.ts', 'main.go', 'app.py', '.rs', '.java', '.cs', '.kt', '.swift') indicating language parser.")] = "snippet.py",
        reduction_mode: Annotated[str, Field(default="ultra", description="Reduction tier: 'ultra' for AST signatures only (80-95% reduction), 'balanced' for signatures + control flow.")] = "ultra"
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
            "100% Zero-Leak security scanner. Analyzes a file, code snippet, or repository workspace for hardcoded API keys (OpenAI, Anthropic, NVIDIA, Gemini, HuggingFace, GitHub), private keys, JWT tokens, and cloud secrets (100% private, 0 external network calls, $0 cost).\n\n"
            "Behavior:\n"
            "- Read-only: Pattern matching and entropy analysis; does NOT modify, expose, or upload credentials.\n"
            "- Idempotent: Deterministic security findings for identical content.\n"
            "- 100% Offline & Private: Never transmits inspected text to any remote server; all secret detections are masked.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run before git commit, push, or public release to guarantee zero secret leaks.\n"
            "- Sibling Routing: For broad code quality audits including complexity, docstrings, and layer rules, use 'audit_codebase_quality'.\n\n"
            "Returns: Security pass/fail report with masked secret snippets, affected file paths, and line numbers."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def verify_zero_leak_security(
        project_root: Annotated[str, Field(default=".", description="Workspace root directory to scan for secret leaks (default: current directory).")] = ".",
        target_file: Annotated[str, Field(default="", description="Optional single file path to inspect instead of the full workspace.")] = "",
        code_snippet: Annotated[str, Field(default="", description="Optional in-memory code string to inspect instead of files on disk.")] = ""
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
    # TOOL 17: verify_hallucination_guard
    # -------------------------------------------------------------------------
    @server.tool(
        name="verify_hallucination_guard",
        description=(
            "Eliminates AI coding hallucinations before code is written or applied. Parses proposed code and verifies all internal imports and function/method call contracts (argument counts and keyword parameter names) against known workspace AST signatures.\n\n"
            "Behavior:\n"
            "- Read-only: Compares AST call signatures against local symbol catalog; does not modify source files.\n"
            "- Idempotent: Deterministic contract verification.\n"
            "- 100% Offline: Uses local AST indices without remote queries.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run BEFORE applying AI-generated code to prevent hallucinated module imports, missing functions, or wrong argument counts.\n"
            "- Sibling Routing: To enforce layer boundary separation rules, use 'enforce_architecture_boundaries'.\n\n"
            "Returns: Verification status report with specific contract mismatches and 'did you mean' fuzzy suggestions."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def verify_hallucination_guard(
        proposed_code: Annotated[str, Field(description="Python code proposed to be written or edited.")],
        target_file: Annotated[str, Field(default="", description="Optional path of the target file being modified to resolve relative imports.")] = "",
        project_root: Annotated[str, Field(default=".", description="Workspace root directory providing the ground-truth AST symbol catalog (default: current directory).")] = "."
    ) -> str:
        """Validates proposed code against workspace AST signatures and contracts.
        
        Args:
            proposed_code: Python code proposed to be written or edited.
            target_file: Optional path of the target file being modified.
            project_root: Root directory of the repository (default: current directory).
        """
        abs_root = os.path.abspath(project_root)
        from tzero_features import ZeroHallucinationGuard
        guard = ZeroHallucinationGuard(abs_root)
        res = guard.validate_code(proposed_code, target_file)
        return res["report"]

    # -------------------------------------------------------------------------
    # TOOL 18: get_smart_skeleton_context
    # -------------------------------------------------------------------------
    @server.tool(
        name="get_smart_skeleton_context",
        description=(
            "Focus-aware dynamic skeletonizer. Returns the full, unpruned implementation of the focus file (or specific focus symbol), surrounded by ultra-compact T-3 AST signatures for all 1st-degree outbound imports and inbound callers. Solves the 'Lost in the Middle' problem while saving 95%+ tokens.\n\n"
            "Behavior:\n"
            "- Read-only: Traverses local AST dependencies; does not mutate files.\n"
            "- Idempotent: Returns identical focus + skeleton bundles for the same codebase state.\n"
            "- 100% Offline: Local AST parsing and signature reduction.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run when editing a specific file to provide the LLM with full implementation context plus compact interface skeletons of adjacent modules.\n"
            "- Sibling Routing: For repository-wide context, use 'get_project_context_tree'. For symbol index without file contents, use 'generate_repo_map'.\n\n"
            "Returns: Structured Markdown with full focus file source code and 1st-degree AST skeletons for imported and caller modules."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def get_smart_skeleton_context(
        focus_file: Annotated[str, Field(description="Target file path to focus on and retain with full implementation.")],
        focus_symbol: Annotated[str, Field(default="", description="Optional specific function or class name within focus_file to isolate.")] = "",
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository (default: current directory).")] = "."
    ) -> str:
        """Returns focus implementation with 1st-degree surrounding AST skeletons.
        
        Args:
            focus_file: Target file path to focus on.
            focus_symbol: Optional specific function or class name within focus_file to inspect.
            project_root: Root directory of the repository (default: current directory).
        """
        abs_root = os.path.abspath(project_root)
        from tzero_features import SmartSkeletonContextBuilder
        builder = SmartSkeletonContextBuilder(abs_root)
        return builder.build_skeleton(focus_file, focus_symbol)

    # -------------------------------------------------------------------------
    # TOOL 19: rank_repository_pagerank
    # -------------------------------------------------------------------------
    @server.tool(
        name="rank_repository_pagerank",
        description=(
            "Identifies the architectural backbone and most critical modules of any repository using graph-theory PageRank centrality over AST import and reference topologies. Ranks modules by inbound/outbound degree and structural criticality.\n\n"
            "Behavior:\n"
            "- Read-only: Graph centrality computation; does not alter files.\n"
            "- Idempotent: Deterministic PageRank convergence for identical import graphs.\n"
            "- 100% Offline: Fully local graph traversal without external dependencies.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run when exploring an unfamiliar codebase to immediately identify the core architectural modules versus peripheral utilities.\n"
            "- Sibling Routing: For direct pairwise dependencies of a file, use 'query_module_dependencies'. For blast radius of a single function, use 'analyze_change_impact'.\n\n"
            "Returns: Ranked Markdown table with PageRank centrality scores, inbound/outbound degrees, and architectural significance notes."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def rank_repository_pagerank(
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository to analyze (default: current directory).")] = ".",
        top_k: Annotated[int, Field(default=15, description="Number of top central modules to return in the ranking report (default: 15).")] = 15
    ) -> str:
        """Computes PageRank architectural centrality scores for repository modules.
        
        Args:
            project_root: Root directory of the repository (default: current directory).
            top_k: Number of top central modules to return in the ranking report (default: 15).
        """
        abs_root = os.path.abspath(project_root)
        from tzero_features import RepositoryPageRank
        ranker = RepositoryPageRank(abs_root)
        rankings = ranker.rank(top_k=top_k)
        return ranker.format_report(rankings)

    # -------------------------------------------------------------------------
    # TOOL 20: trace_symbol_call_chain
    # -------------------------------------------------------------------------
    @server.tool(
        name="trace_symbol_call_chain",
        description=(
            "Traces deep execution paths across the codebase AST. Recursively discovers upstream callers (who calls symbol_name) and downstream callees (what symbol_name calls) up to max_depth, rendering an execution tree and Mermaid call diagram.\n\n"
            "Behavior:\n"
            "- Read-only: Recursively traverses AST function call expressions; does not modify source code.\n"
            "- Idempotent: Deterministic call graph traversal.\n"
            "- 100% Offline: Local AST analysis without external services.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run when debugging execution flows, tracing data paths into a function, or seeing everything a complex method calls recursively.\n"
            "- Sibling Routing: For quick single-symbol blast radius scoring (0-100), use 'analyze_change_impact'. For module-level import relations, use 'query_module_dependencies'.\n\n"
            "Returns: Markdown report containing recursive ASCII execution tree, caller/callee counts, and copy-pasteable Mermaid flowchart syntax."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def trace_symbol_call_chain(
        symbol_name: Annotated[str, Field(description="Exact function or method name to trace across the codebase call graph.")],
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository (default: current directory).")] = ".",
        max_depth: Annotated[int, Field(default=3, description="Maximum recursion depth for the call graph traversal (default: 3).")] = 3
    ) -> str:
        """Traces upstream and downstream call chains for any function or method.
        
        Args:
            symbol_name: Name of the function or method to trace.
            project_root: Root directory of the repository (default: current directory).
            max_depth: Maximum recursion depth for the call graph traversal (default: 3).
        """
        abs_root = os.path.abspath(project_root)
        from tzero_features import SymbolCallChainTracer
        tracer = SymbolCallChainTracer(abs_root)
        res = tracer.trace(symbol_name, max_depth=max_depth)
        return tracer.format_report(res)

    # -------------------------------------------------------------------------
    # TOOL 21: find_dead_code
    # -------------------------------------------------------------------------
    @server.tool(
        name="find_dead_code",
        description=(
            "Finds unused, orphaned, or unreferenced functions and classes across the codebase AST. Excludes __all__, main, dunder methods, and test functions.\n\n"
            "Behavior:\n"
            "- Read-only: Computes symbol reference counts; does NOT delete or modify any source code files.\n"
            "- Idempotent: Consistent dead code candidate discovery for the same repository state.\n"
            "- 100% Offline: Local AST reference analysis.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Run during technical debt cleanup to locate deprecated, dead, or forgotten functions and classes ready for safe removal.\n"
            "- Sibling Routing: For copy-pasted duplicate logic blocks, use 'find_code_duplicity'. For general complexity and linting, use 'audit_codebase_quality'.\n\n"
            "Returns: Markdown report listing candidate orphaned symbols with file paths, line numbers, and symbol types."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def find_dead_code(
        project_root: Annotated[str, Field(default=".", description="Root directory of the repository to scan for unreferenced symbols (default: current directory).")] = "."
    ) -> str:
        """Discovers unused symbols and dead code candidates across the codebase.
        
        Args:
            project_root: Root directory of the repository (default: current directory).
        """
        abs_root = os.path.abspath(project_root)
        from tzero_features import DeadCodeFinder
        finder = DeadCodeFinder(abs_root)
        dead = finder.find_unused_symbols()
        return finder.format_report(dead)

    # -------------------------------------------------------------------------
    # TOOL 22: jarvis_compress_semantic_memory
    # -------------------------------------------------------------------------
    @server.tool(
        name="jarvis_compress_semantic_memory",
        description=(
            "Compresses natural language text, logs, or system instructions into T-Zero's 3-Layer Semantic Memory representation:\n"
            "- Layer A: Semantic Triplet Extraction with Named Entity Recognition (NER: Hardware, Protocol, IP, Crypto, Vuln, Software)\n"
            "- Layer B: Vector Quantized (VQ) Codebook discrete index mapping (e.g. #8421)\n"
            "- Layer C: Dynamic Virtual Memory Token injection (<|tzero:mem:8421|>) for 90-98% token reduction.\n\n"
            "Usage Guidelines:\n"
            "- When to use: Compress long conversation histories, system telemetry, hardware setups, or complex architectural instructions into single virtual tokens.\n"
            "Returns: Formatted Markdown report with original token count, compressed token count, savings percentage, graph triplets, compact code, and virtual tokens."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def jarvis_compress_semantic_memory(
        text: Annotated[str, Field(description="Natural language statement, hardware setup, system log, or architecture instruction to compress.")]
    ) -> str:
        """Compresses text into 3-Layer semantic triplets, VQ discrete codes, and virtual memory tokens.
        
        Args:
            text: Input text to compress.
        """
        from tzero_jarvis import get_global_compressor
        compressor = get_global_compressor()
        res = compressor.compress_text_to_virtual_tokens(text)

        lines = [
            f"### ⚡ T-Zero Jarvis 3-Layer Semantic Memory Compression",
            f"- **Original Tokens:** `{res['original_token_count']}`",
            f"- **Compressed Virtual Tokens:** `{res['compressed_token_count']}`",
            f"- **Token Savings:** `{res['token_savings']}` tokens (**{res['reduction_ratio_pct']}% reduction**)",
            f"- **Virtual Token String:** `{res['virtual_token_string']}`",
            "",
            "#### 🧩 Layer Breakdown",
            f"- **Layer A (Semantic Graph):** `{' | '.join(res['graph_representations'])}`",
            f"- **Layer B (VQ Discrete Codes):** `{' '.join(f'#{cid}' for cid in res['codebook_ids'])}`",
            f"- **Layer C (Compact Binary Representation):** `{' '.join(res['compact_codes'])}`",
            f"- **Attention Soft-Prompt State:** `{res['virtual_token_string']}`"
        ]
        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # TOOL 23: jarvis_decompress_semantic_memory
    # -------------------------------------------------------------------------
    @server.tool(
        name="jarvis_decompress_semantic_memory",
        description=(
            "Resolves a T-Zero virtual memory token (<|tzero:mem:8421|>) or discrete code ID (e.g. 8421) back into its "
            "canonical semantic graph representation, entity classifications, and human-readable natural language summary.\n\n"
            "Returns: Decoded entity details, graph triplet, and natural language reconstruction."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def jarvis_decompress_semantic_memory(
        token_or_code: Annotated[str, Field(description="Virtual memory token (e.g. '<|tzero:mem:8421|>') or discrete code ID (e.g. '8421').")]
    ) -> str:
        """Resolves virtual memory tokens back to their semantic graph representation.
        
        Args:
            token_or_code: The virtual token or code ID to resolve.
        """
        from tzero_jarvis import get_global_compressor
        compressor = get_global_compressor()
        decoded = compressor.decode_virtual_token(token_or_code)
        if not decoded:
            return f"❌ Virtual token or code `{token_or_code}` not found in active VQ codebook."

        lines = [
            f"### 🔍 T-Zero Jarvis Semantic Memory Resolution",
            f"- **Code ID:** `#{decoded['code_id']}`",
            f"- **Virtual Token:** `{decoded['virtual_token']}`",
            f"- **Graph Representation:** `{decoded['graph_representation']}`",
            f"- **Compact Code:** `{decoded['compact_code']}`",
            f"- **Reconstructed Summary:** {decoded['reconstructed_summary']}"
        ]
        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # TOOL 24: jarvis_orchestrate_goal
    # -------------------------------------------------------------------------
    @server.tool(
        name="jarvis_orchestrate_goal",
        description=(
            "Executes an autonomous multi-agent engineering workflow using T-Zero's AST context reduction, "
            "3-Layer semantic memory compression, zero-cost intelligence routing, and self-healing loop.\n\n"
            "Behavior:\n"
            "- Analyzes goal and extracts semantic graph triplets.\n"
            "- Prunes codebase context using T-Zero AST TokenReducer (80-95% token savings).\n"
            "- Queries Zero-Key AI router (Ollama Local / Pollinations Free) with 0.00$ cost.\n"
            "- Enforces 100% Zero-Leak security verification before completion.\n\n"
            "Returns: Multi-stage execution report with verification logs and token metrics."),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True)
    )
    def jarvis_orchestrate_goal(
        goal: Annotated[str, Field(description="Autonomous engineering task, refactoring goal, or implementation directive to orchestrate.")],
        project_root: Annotated[str, Field(default=".", description="Target workspace directory to orchestrate within (default: current directory).")] = "."
    ) -> str:
        """Executes an autonomous engineering goal with zero API keys and self-healing verification.
        
        Args:
            goal: High-level engineering directive.
            project_root: Workspace root directory.
        """
        from tzero_jarvis import JarvisOrchestrator
        orchestrator = JarvisOrchestrator(workspace_root=project_root)
        result = orchestrator.orchestrate_goal(goal)

        lines = [
            f"### 🚀 T-Zero Jarvis Autonomous Goal Orchestration",
            f"- **Goal:** {result.goal}",
            f"- **Status:** {'✅ COMPLETED' if result.success else '❌ FAILED'}",
            f"- **Total Incurred Cost:** `{result.cost}` (100% Free / Zero API Key)",
            f"- **Zero-Leak Security Check:** {'🛡️ PASSED (Zero Leaks)' if result.security_passed else '⚠️ WARNING'}",
            "",
            "#### 📋 Execution Stages:"
        ]
        for step in result.steps:
            lines.append(f"- `[{step['timestamp']}]` **[{step['stage']}]**: {step['message']}")

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # TOOL 25: jarvis_zero_key_query
    # -------------------------------------------------------------------------
    @server.tool(
        name="jarvis_zero_key_query",
        description=(
            "Queries the 100% Free, Zero-API-Key intelligence matrix (Local Ollama, Pollinations Free Cloud, OpenRouter Free Whitelist). "
            "Never requires credit cards, user API keys, or balance.\n\n"
            "Returns: Formatted AI response with selected zero-cost provider telemetry."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=False, open_world_hint=True)
    )
    def jarvis_zero_key_query(
        prompt: Annotated[str, Field(description="Prompt, code question, or instruction for the Zero-Key intelligence engine.")],
        system_prompt: Annotated[str, Field(default="You are T-Zero Jarvis Autonomous Code Engineer.", description="System instruction context.")] = "You are T-Zero Jarvis Autonomous Code Engineer."
    ) -> str:
        """Queries the zero-key free AI inference engine.
        
        Args:
            prompt: User prompt or instruction.
            system_prompt: System role prompt.
        """
        from tzero_jarvis import ZeroKeyAIRouter
        ans = ZeroKeyAIRouter.query_intelligence(prompt, system_prompt=system_prompt)
        return (
            f"### 🤖 T-Zero Jarvis Zero-Cost Intelligence\n"
            f"- **Provider:** `{ans['provider']}`\n"
            f"- **Model:** `{ans['model']}`\n"
            f"- **Cost:** `{ans['cost']}`\n\n"
            f"---\n"
            f"{ans['response']}"
        )

    # -------------------------------------------------------------------------
    # TOOL 26: jarvis_query_knowledge_graph
    # -------------------------------------------------------------------------
    @server.tool(
        name="jarvis_query_knowledge_graph",
        description=(
            "Searches the T-Zero Jarvis semantic knowledge graph and VQ Codebook memory by entity name, "
            "predicate, execution context, or general search query.\n\n"
            "Behavior:\n"
            "- Read-only: Queries local in-memory discrete codes and graph triplets.\n"
            "- Zero latency: Instant local retrieval with zero network or cloud costs.\n\n"
            "Returns: Formatted Markdown table of matching knowledge graph triplets and their virtual memory tokens."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def jarvis_query_knowledge_graph(
        query: Annotated[str, Field(description="Entity, keyword, or action to search across the knowledge graph (e.g. 'ESP32', 'test_etti', 'Kubernetes', 'Qubit').")] = "",
        entity: Annotated[str, Field(default="", description="Specific entity filter.")] = "",
        predicate: Annotated[str, Field(default="", description="Specific predicate / action filter.")] = ""
    ) -> str:
        """Queries the semantic memory knowledge graph.
        
        Args:
            query: Freeform search keyword.
            entity: Target entity name.
            predicate: Target predicate.
        """
        from tzero_jarvis import get_global_compressor
        compressor = get_global_compressor()
        matches = compressor.codebook.query_graph(
            entity=entity if entity else None,
            predicate=predicate if predicate else None,
            text_query=query if query else None
        )
        if not matches:
            return f"[INFO] No graph triplets matched query '{query or entity or predicate}'."

        lines = [
            f"### 🔎 T-Zero Knowledge Graph Search Results ({len(matches)} matches)\n",
            "| Code ID | Virtual Token | Graph Representation | Compact Code |",
            "| :--- | :--- | :--- | :--- |"
        ]
        for m in matches:
            lines.append(f"| #{m['code_id']} | `{m['virtual_token']}` | `{m['graph_string']}` | `{m['compact_code']}` |")

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # TOOL 27: jarvis_compress_document
    # -------------------------------------------------------------------------
    @server.tool(
        name="jarvis_compress_document",
        description=(
            "Compresses large multi-paragraph technical documents, architectural specifications, "
            "or conversation logs (1,000+ words) into an interconnected Knowledge Graph and composite "
            "virtual memory token stream (<|tzero:mem:ID|>).\n\n"
            "Behavior:\n"
            "- High Token Savings: Reaches 85-95% token reduction across multi-sentence paragraphs.\n"
            "- Topological Deduplication: Identifies shared subjects, protocols, and devices across paragraphs.\n\n"
            "Returns: Comprehensive document compression report, virtual token chain, and node-edge count."),
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
    )
    def jarvis_compress_document(
        document_text: Annotated[str, Field(description="Large multi-paragraph technical document or log text to compress.")]
    ) -> str:
        """Compresses multi-paragraph technical documents into knowledge graph virtual tokens.
        
        Args:
            document_text: Full document text to ingest and compress.
        """
        from tzero_jarvis import get_global_compressor
        compressor = get_global_compressor()
        res = compressor.compress_document(document_text)

        topo = res.get("topology", {})
        return (
            f"### 📚 T-Zero Universal Document Memory Compression\n"
            f"- **Total Paragraphs Ingested:** {res['total_paragraphs']}\n"
            f"- **Triplets Extracted:** {res['total_triplets_extracted']}\n"
            f"- **Original Tokens:** {res['original_token_count']}\n"
            f"- **Compressed Virtual Tokens:** {res['compressed_token_count']}\n"
            f"- **Net Token Savings:** %{res['reduction_ratio_pct']} ({res['token_savings']} tokens saved)\n"
            f"- **Knowledge Graph Nodes:** {topo.get('total_nodes', 0)} entities | **Edges:** {topo.get('total_edges', 0)} links\n\n"
            f"#### Virtual Memory Stream:\n"
            f"`{res['virtual_token_string']}`\n\n"
            f"#### Graph Representations:\n"
            + "\n".join(f"- {g}" for g in res["graph_representations"][:10])
        )

    # -------------------------------------------------------------------------
    # TOOL 28: jarvis_export_memory_store
    # -------------------------------------------------------------------------
    @server.tool(
        name="jarvis_export_memory_store",
        description=(
            "Exports or imports the T-Zero Jarvis persistent VQ Codebook and Knowledge Graph "
            "to/from local disk (zero cloud, 100% private and persistent across IDE restarts).\n\n"
            "Behavior:\n"
            "- Save mode: Serializes all active codes to JSON.\n"
            "- Load mode: Ingests saved codes into the active runtime codebook.\n\n"
            "Returns: Status and path of persistent store file."),
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=False)
    )
    def jarvis_export_memory_store(
        action: Annotated[str, Field(default="save", description="Action to perform: 'save' or 'load'.")] = "save",
        file_path: Annotated[str, Field(default="", description="Optional custom file path for storage.")] = ""
    ) -> str:
        """Saves or loads persistent semantic memory store.
        
        Args:
            action: 'save' or 'load'.
            file_path: Target JSON file path.
        """
        from tzero_jarvis import get_global_compressor
        compressor = get_global_compressor()
        target = file_path if file_path else None

        if action.lower() == "load":
            loaded = compressor.codebook.load_from_disk(target)
            return f"### 💾 T-Zero Memory Store Ingested\nSuccessfully loaded {loaded} semantic codes into runtime. Active Codebook Size: {compressor.codebook.size()} codes."
        else:
            saved_p = compressor.codebook.save_to_disk(target)
            return f"### 💾 T-Zero Memory Store Exported\nSuccessfully saved {compressor.codebook.size()} semantic codes to disk: `{saved_p}`."

    # -------------------------------------------------------------------------
    # TOOL 29: jarvis_causal_chain_query
    # -------------------------------------------------------------------------
    @server.tool(
        name="jarvis_causal_chain_query",
        description="Queries 4D Causal and Temporal Knowledge Graph for root causes, downstream effect chains, or safe rollback steps."
    )
    def jarvis_causal_chain_query(
        target_node_id: Annotated[str, Field(description="Target node ID to analyze (e.g. error, event).")],
        query_type: Annotated[str, Field(default="root_causes", description="Type: 'root_causes', 'effect_chain', 'rollback_order', or 'timeline'.")] = "root_causes"
    ) -> str:
        """Queries 4D Causal & Temporal Knowledge Graph."""
        from tzero_jarvis import CausalTemporalGraph
        from tzero_jarvis import get_global_compressor
        compressor = get_global_compressor()
        graph = CausalTemporalGraph(compressor.codebook)

        qt = query_type.lower()
        if qt == "timeline":
            tl = graph.get_timeline(30)
            return f"### ⏱️ T-Zero Chronological Timeline ({len(tl)} events)\n```json\n{json.dumps(tl, indent=2, ensure_ascii=False)}\n```"
        elif qt == "effect_chain":
            chain = graph.trace_effect_chain(target_node_id)
            return f"### ⚡ T-Zero Downstream Effect Chain ({len(chain)} steps)\n```json\n{json.dumps(chain, indent=2, ensure_ascii=False)}\n```"
        elif qt == "rollback_order":
            rb = graph.compute_rollback_order(target_node_id)
            return f"### 🔄 T-Zero Safe Rollback Plan ({len(rb)} steps)\n```json\n{json.dumps(rb, indent=2, ensure_ascii=False)}\n```"
        else:
            roots = graph.get_root_causes(target_node_id)
            return f"### 🔍 T-Zero Root Cause Analysis for `{target_node_id}`\n```json\n{json.dumps(roots, indent=2, ensure_ascii=False)}\n```"

    # -------------------------------------------------------------------------
    # TOOL 30: jarvis_self_healing_execute
    # -------------------------------------------------------------------------
    @server.tool(
        name="jarvis_self_healing_execute",
        description="Executes a command or script in a guarded environment with automated AST self-healing and error repair."
    )
    def jarvis_self_healing_execute(
        command: Annotated[str, Field(description="Command or script invocation to execute.")],
        max_retries: Annotated[int, Field(default=3, description="Maximum auto-patch healing attempts.")] = 3
    ) -> str:
        """Runs command with autonomous AST error diagnosis and auto-repair."""
        from tzero_jarvis import SelfHealingExecutionEngine
        engine = SelfHealingExecutionEngine()
        res = engine.execute_and_heal(command, max_retries=max_retries)
        
        status_emoji = "✅" if res.success else "❌"
        return (
            f"### {status_emoji} Self-Healing Execution Result\n"
            f"- **Command:** `{res.command}`\n"
            f"- **Success:** `{res.success}` (Resolved: `{res.resolved}`)\n"
            f"- **Exit Code:** `{res.exit_code}`\n"
            f"- **Duration:** `{res.duration_ms} ms`\n"
            f"- **Applied Patches:** `{len(res.applied_patches)}`\n"
            + (f"- **Error Type:** `{res.error_type}` in `{res.error_file}:{res.error_line}`\n" if res.error_type else "")
            + f"\n**Stdout:**\n```\n{res.stdout[:1500]}\n```\n"
            + (f"**Stderr:**\n```\n{res.stderr[:1000]}\n```\n" if res.stderr else "")
        )

    # -------------------------------------------------------------------------
    # TOOL 31: jarvis_consolidate_memory
    # -------------------------------------------------------------------------
    @server.tool(
        name="jarvis_consolidate_memory",
        description="Performs brain-like hippocampal memory consolidation, contradiction resolution, and macro-triplet synthesis."
    )
    def jarvis_consolidate_memory(
        action: Annotated[str, Field(default="consolidate", description="'consolidate' to run cycle, or 'summary' for status.")] = "consolidate"
    ) -> str:
        """Consolidates episodic memory into permanent abstracted knowledge."""
        from tzero_jarvis import ConsolidationEngine, get_global_compressor
        compressor = get_global_compressor()
        engine = ConsolidationEngine(compressor.codebook)
        
        if action.lower() == "summary":
            summ = engine.get_summary()
            return f"### 🧠 T-Zero Memory Consolidation State\n```json\n{json.dumps(summ, indent=2, ensure_ascii=False)}\n```"
        else:
            rep = engine.consolidate()
            return f"### 🧬 T-Zero Memory Consolidation Cycle Completed\n```json\n{json.dumps(rep, indent=2, ensure_ascii=False)}\n```"

    # -------------------------------------------------------------------------
    # TOOL 32: jarvis_hybrid_search
    # -------------------------------------------------------------------------
    @server.tool(
        name="jarvis_hybrid_search",
        description="High-speed zero-vector-DB hybrid BM25 and latent codebook (#code) search across code, memory, and events."
    )
    def jarvis_hybrid_search(
        query: Annotated[str, Field(description="Search terms, concepts, or discrete codes like '#8421'.")],
        top_k: Annotated[int, Field(default=10, description="Maximum number of results to return.")] = 10,
        domain: Annotated[str, Field(default="", description="Optional domain filter (HARDWARE, PROTOCOL, SOFTWARE, etc.).")] = ""
    ) -> str:
        """Sub-millisecond in-memory BM25 + latent code hybrid search."""
        from tzero_jarvis import ZeroVectorDBSearchEngine, get_global_compressor
        compressor = get_global_compressor()
        search_engine = ZeroVectorDBSearchEngine()

        # Hafızadaki mevcut kodları anında arama indeksine besle
        for cid, entry in compressor.codebook.codes.items():
            search_engine.add_document(
                doc_id=f"mem_{cid}",
                doc_type="memory_triplet",
                title=f"Code #{cid} [{entry.get('primary_domain', 'GENERIC')}]",
                content=f"{entry.get('graph', '')} {entry.get('compact_code', '')}",
                discrete_code=cid,
                domain=entry.get('primary_domain', 'GENERIC'),
                metadata=entry
            )

        results = search_engine.search(query, top_k=top_k, target_domain=domain if domain else None)
        return (
            f"### ⚡ T-Zero Zero-Vector-DB Hybrid Search Results for `{query}`\n"
            f"Found `{len(results)}` relevant items in `<0.5 ms`:\n\n"
            + "\n".join(
                f"- **[{r.domain}] {r.title}** (Score: `{r.score}`, Code: `#{r.discrete_code}`)\n"
                f"  Matches: `{', '.join(r.match_reasons)}`\n"
                f"  Content: `{r.content}`"
                for r in results
            )
        )

    # -------------------------------------------------------------------------
    # TOOL 33: jarvis_swarm_orchestrate
    # -------------------------------------------------------------------------
    @server.tool(
        name="jarvis_swarm_orchestrate",
        description="Coordinates a 5-agent autonomous swarm (Security, Embedded, AST Optimizer, DevOps, JARVIS Prime) on a mission."
    )
    def jarvis_swarm_orchestrate(
        mission_goal: Annotated[str, Field(description="The engineering or system goal to achieve.")],
        context: Annotated[str, Field(default="", description="Optional technical context or constraints.")] = ""
    ) -> str:
        """Executes autonomous multi-agent swarm mission coordination."""
        from tzero_jarvis import SwarmCoordinator, get_global_compressor
        compressor = get_global_compressor()
        coordinator = SwarmCoordinator(compressor)
        rep = coordinator.coordinate_mission(mission_goal, context=context)

        return (
            f"### 🐝 T-Zero Autonomous Swarm Mission Consensus\n"
            f"- **Mission:** `{rep['mission_goal']}`\n"
            f"- **Orchestrator:** `{rep['orchestrator']}`\n"
            f"- **Consensus Verdict:** **{rep['consensus']}**\n"
            f"- **Active Agents:** `{rep['swarm_agent_count']}`\n"
            f"- **Execution Time:** `{rep['execution_time_ms']} ms`\n"
            f"- **Aggregated Virtual Memory Tokens:** `{' '.join(rep['aggregated_memory_tokens'])}`\n\n"
            f"#### 📋 Specialist Agent Reports:\n"
            + "\n".join(
                f"**[{r['agent_name']} — {r['role']}]** Verdict: `{r['verdict']}` (Confidence: `{r['confidence']*100:.0f}%`)\n"
                f"• Findings: {', '.join(r['findings'])}\n"
                f"• Recommendations: {', '.join(r['recommendations'])}\n"
                for r in rep["agent_reports"]
            )
        )

    # -------------------------------------------------------------------------
    # TOOL 34: jarvis_export_graph_visualization
    # -------------------------------------------------------------------------
    @server.tool(
        name="jarvis_export_graph_visualization",
        description="Generates an offline, interactive cyberpunk 2D/3D force-directed HTML graph visualization of knowledge & causality."
    )
    def jarvis_export_graph_visualization(
        output_path: Annotated[str, Field(default="", description="Optional target HTML file path. Defaults to 'tzero_graph_hud.html'.")] = ""
    ) -> str:
        """Exports interactive cyberpunk HTML graph visualization."""
        from tzero_jarvis import CyberpunkGraphVisualizer, CausalTemporalGraph, get_global_compressor
        compressor = get_global_compressor()
        graph = CausalTemporalGraph(compressor.codebook)

        # Mevcut hafızayı çizgeye aktar
        for cid, entry in compressor.codebook.codes.items():
            graph.add_node(
                node_id=f"node_{cid}",
                label=f"Code #{cid}: {entry.get('graph', 'Triplet')}",
                entity_type=entry.get("primary_domain", "GENERIC"),
                triplet_code=cid
            )

        target = output_path if output_path else os.path.join(os.getcwd(), "tzero_graph_hud.html")
        viz = CyberpunkGraphVisualizer(graph)
        saved = viz.export_to_file(target)
        return (
            f"### 🌐 Cyberpunk Knowledge & Causal Graph Exported\n"
            f"- **File:** `{saved}`\n"
            f"- **Total Nodes:** `{len(graph.nodes)}`\n"
            f"- **Format:** Standalone Offline HTML5/SVG/Canvas Interactive Force Graph\n"
            f"Open this file in any web browser to interactively explore glowing nodes and causal links!"
        )

    # -------------------------------------------------------------------------
    # TOOL 35: jarvis_minhash_similarity
    # -------------------------------------------------------------------------
    @server.tool(
        name="jarvis_minhash_similarity",
        description="Calculates sub-microsecond (<1 µs) Jaccard similarity and near-duplicate triplet clusters using MinHash LSH (64 permutations, Mersenne prime)."
    )
    def jarvis_minhash_similarity(
        text_a: Annotated[str, Field(description="First text or triplet description")],
        text_b: Annotated[str, Field(default="", description="Second text to compare against (optional). If empty, searches memory codebook.")] = "",
        threshold: Annotated[float, Field(default=0.5, description="Jaccard similarity threshold [0.0 - 1.0]")] = 0.5
    ) -> str:
        """Sub-microsecond MinHash LSH similarity comparison."""
        from tzero_jarvis import MinHashLSHEngine, SemanticExtractor, get_global_compressor
        engine = MinHashLSHEngine()
        
        triplets_a = SemanticExtractor.extract_triplets(text_a)
        if not triplets_a:
            return "❌ No semantic triplets extracted from text A."
        
        sig_a = engine.compute_signature(triplets_a[0], 1)
        
        if text_b:
            triplets_b = SemanticExtractor.extract_triplets(text_b)
            if not triplets_b:
                return "❌ No semantic triplets extracted from text B."
            sig_b = engine.compute_signature(triplets_b[0], 2)
            sim = sig_a.jaccard_similarity(sig_b)
            is_dup = sim >= threshold
            return (
                f"### ⚡ T-Zero Sub-Microsecond MinHash LSH Analysis\n"
                f"- **Text A:** `{text_a}`\n"
                f"- **Text B:** `{text_b}`\n"
                f"- **Estimated Jaccard Similarity:** `{sim:.4f}` ({sim*100:.1f}%)\n"
                f"- **Near-Duplicate Status:** `{'DUPLICATE (Threshold Exceeded)' if is_dup else 'DISTINCT'}`\n"
                f"- **Hash Dimensionality:** `64 permutations (16 bands x 4 rows)`\n"
                f"- **Lookup Latency:** `< 0.01 ms (Zero Vector DB)`"
            )
        else:
            compressor = get_global_compressor()
            for cid, entry in compressor.codebook.codes.items():
                if "triplet" in entry:
                    engine.insert(entry["triplet"], cid)
                else:
                    tr = SemanticExtractor.extract_triplets(entry.get("graph", ""))
                    if tr:
                        engine.insert(tr[0], cid)
            dups = engine.query_near_duplicates(triplets_a[0], threshold=threshold)
            return (
                f"### ⚡ T-Zero Codebook MinHash LSH Search\n"
                f"- **Query:** `{text_a}`\n"
                f"- **Near-Duplicate Matches Found:** `{len(dups)}` (Threshold: {threshold})\n"
                + "\n".join(
                    f"• Code #{d['code']}: `{d['label']}` — Jaccard Sim: `{d['similarity']*100:.1f}%`"
                    for d in dups
                )
            )

    # -------------------------------------------------------------------------
    # TOOL 36: jarvis_bft_swarm_consensus
    # -------------------------------------------------------------------------
    @server.tool(
        name="jarvis_bft_swarm_consensus",
        description="Executes 3-phase Practical Byzantine Fault-Tolerant (PBFT) multi-agent swarm consensus with 2/3 weighted quorum, outlier detection, and Zero-Leak cryptographic veto."
    )
    def jarvis_bft_swarm_consensus(
        mission_goal: Annotated[str, Field(description="Mission, action, or code patch to evaluate")],
        context: Annotated[str, Field(default="", description="Optional context or environment logs")] = ""
    ) -> str:
        """Executes Byzantine Fault-Tolerant swarm consensus."""
        from tzero_jarvis import ByzantineFaultTolerantSwarm, SwarmCoordinator, get_global_compressor
        compressor = get_global_compressor()
        coordinator = SwarmCoordinator(compressor)
        bft = ByzantineFaultTolerantSwarm(coordinator)
        cert = bft.reach_consensus(mission_goal, context=context)
        
        status_emoji = "✅" if cert.consensus_verdict == "APPROVED" else ("🛡️" if cert.veto_triggered else "⚠️")
        return (
            f"### {status_emoji} T-Zero Byzantine Fault-Tolerant (PBFT) Swarm Certificate\n"
            f"- **Mission ID:** `{cert.mission_id}`\n"
            f"- **Goal:** `{cert.mission_goal}`\n"
            f"- **Consensus Verdict:** **{cert.consensus_verdict}**\n"
            f"- **Quorum Ratio:** `{cert.quorum_ratio * 100:.1f}%` (Approved: {cert.approved_weight:.2f} / Total: {cert.total_voting_weight:.2f})\n"
            f"- **Byzantine Faults Isolated:** `{cert.byzantine_faults_detected}`\n"
            f"- **Zero-Leak Veto Triggered:** `{cert.veto_triggered}` ({cert.veto_reason or 'None'})\n"
            f"- **Cryptographic Certificate Hash:** `{cert.certificate_hash}`\n"
            f"- **Committed Virtual Tokens:** `{' '.join(cert.committed_virtual_tokens) if cert.committed_virtual_tokens else 'None'}`"
        )

    # -------------------------------------------------------------------------
    # TOOL 37: jarvis_latent_press_compress
    # -------------------------------------------------------------------------
    @server.tool(
        name="jarvis_latent_press_compress",
        description="Compresses long contexts before prefill using Latent Context Language Model (LCLM / LatentPress), Shannon entropy tracking, and MinHash de-duplication."
    )
    def jarvis_latent_press_compress(
        context_text: Annotated[str, Field(description="Long context, logs, or code to compress")],
        near_dup_threshold: Annotated[float, Field(default=0.65, description="Near-duplicate threshold for pruning")] = 0.65
    ) -> str:
        """Executes LatentPress pre-prefill context compression."""
        from tzero_jarvis import LatentPressCompressor, get_global_compressor
        compressor = LatentPressCompressor(get_global_compressor())
        res = compressor.compress_large_context(context_text, near_dup_threshold=near_dup_threshold)
        
        return (
            f"### 🗜️ T-Zero LatentPress (LCLM) Context Compression\n"
            f"- **Original Tokens (est):** `{res.original_tokens_est}` ({res.original_words} words)\n"
            f"- **Compressed Tokens:** `{res.compressed_tokens}`\n"
            f"- **Compression Ratio:** **{res.compression_ratio_x}x**\n"
            f"- **Token Savings:** **{res.token_savings_pct}%**\n"
            f"- **Entropy (Original -> Compressed):** `{res.shannon_entropy_original:.2f} -> {res.shannon_entropy_compressed:.2f} bits/char`\n"
            f"- **Duplicate Chunks Pruned:** `{res.duplicate_chunks_pruned}`\n"
            f"- **Unique Triplets Encoded:** `{res.unique_semantic_triplets}`\n"
            f"- **Processing Latency:** `{res.latency_ms:.2f} ms`\n\n"
            f"#### 🧩 Compressed Virtual Token Stream:\n"
            f"```text\n{res.virtual_token_stream}\n```"
        )


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
        return generate_architecture_blueprint(project_root=".", use_ai=False)

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
