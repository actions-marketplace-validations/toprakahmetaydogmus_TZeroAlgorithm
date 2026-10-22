# -*- coding: utf-8 -*-
"""Unit tests for T-Zero Model Context Protocol (MCP) server tools and prompts."""

import os
import unittest
import tempfile
import asyncio
import tzero_mcp


def tool_result_text(result):
    if isinstance(result, tuple):
        result = result[0]
    content = getattr(result, "content", result)
    return content[0].text


class TestMCPServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = tzero_mcp.create_mcp_server()

    def run_async(self, coro):
        return asyncio.run(coro)

    def test_mcp_tools_and_prompts_registration(self):
        """Verifies that all 25 MCP tools and grounding prompt are properly registered."""
        tools = self.run_async(self.server.list_tools())
        tool_names = [t.name for t in tools]
        self.assertEqual(len(tool_names), 39)
        expected_tools = [
            "get_project_context_tree",
            "query_module_dependencies",
            "query_architecture_boundaries",
            "generate_architecture_blueprint",
            "generate_repo_map",
            "audit_codebase_quality",
            "find_code_duplicity",
            "estimate_token_cost",
            "analyze_change_impact",
            "enforce_architecture_boundaries",
            "search_codebase_semantic",
            "export_agent_rules",
            "get_token_savings_metrics",
            "get_incremental_diff_context",
            "prune_code_snippet",
            "verify_zero_leak_security",
            "verify_hallucination_guard",
            "get_smart_skeleton_context",
            "rank_repository_pagerank",
            "trace_symbol_call_chain",
            "find_dead_code",
            "jarvis_compress_semantic_memory",
            "jarvis_decompress_semantic_memory",
            "jarvis_orchestrate_goal",
            "jarvis_zero_key_query",
            "jarvis_query_knowledge_graph",
            "jarvis_compress_document",
            "jarvis_export_memory_store",
            "jarvis_causal_chain_query",
            "jarvis_self_healing_execute",
            "jarvis_consolidate_memory",
            "jarvis_hybrid_search",
            "jarvis_swarm_orchestrate",
            "jarvis_export_graph_visualization",
            "jarvis_minhash_similarity",
            "jarvis_bft_swarm_consensus",
            "jarvis_latent_press_compress",
            "prune_schema_definition",
            "generate_smart_micro_patch",
        ]
        for exp in expected_tools:
            self.assertIn(exp, tool_names)

        prompts = self.run_async(self.server.list_prompts())
        prompt_names = [p.name for p in prompts]
        self.assertIn("tzero_grounding", prompt_names)

    def test_tool_get_project_context_tree(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_a = os.path.join(temp_dir, "app.py")
            with open(file_a, "w", encoding="utf-8") as f:
                f.write("import os\n\ndef run():\n    '''Run app'''\n    pass\n")

            res = self.run_async(self.server.call_tool(
                "get_project_context_tree",
                {"project_root": temp_dir, "reduction_mode": "ultra", "include_file_contents": True}
            ))
            output = tool_result_text(res)
            self.assertIn("T-Zero Context Tree", output)
            self.assertIn("app.py", output)
            self.assertIn("Architecture Overview", output)

    def test_tool_query_module_dependencies(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_a = os.path.join(temp_dir, "a.py")
            file_b = os.path.join(temp_dir, "b.py")
            with open(file_a, "w", encoding="utf-8") as f:
                f.write("import json\nimport sys\n")
            with open(file_b, "w", encoding="utf-8") as f:
                f.write("import a\n")

            # Workspace query
            res_ws = self.run_async(self.server.call_tool(
                "query_module_dependencies",
                {"project_root": temp_dir}
            ))
            out_ws = tool_result_text(res_ws)
            self.assertIn("Workspace Dependency Topology", out_ws)
            self.assertIn("json", out_ws)

            # Single file query
            res_file = self.run_async(self.server.call_tool(
                "query_module_dependencies",
                {"project_root": temp_dir, "file_path": "a.py"}
            ))
            out_file = tool_result_text(res_file)
            self.assertIn("Dependency Analysis for `a.py`", out_file)
            self.assertIn("json", out_file)
            self.assertIn("b.py", out_file)

    def test_tool_query_architecture_boundaries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fpath = os.path.join(temp_dir, "server.py")
            with open(fpath, "w", encoding="utf-8") as f:
                f.write("class Server:\n    pass\n")

            res = self.run_async(self.server.call_tool(
                "query_architecture_boundaries",
                {"project_root": temp_dir, "extra_guidance": "Follow strict clean code."}
            ))
            out = tool_result_text(res)
            self.assertIn("AGENTS & AI ASSISTANT BLUEPRINT", out)
            self.assertIn("Follow strict clean code.", out)
            self.assertIn("Zero-Leak", out)

    def test_tool_generate_architecture_blueprint(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fpath = os.path.join(temp_dir, "core.py")
            with open(fpath, "w", encoding="utf-8") as f:
                f.write("import os\n")

            res = self.run_async(self.server.call_tool(
                "generate_architecture_blueprint",
                {"project_root": temp_dir}
            ))
            out = tool_result_text(res)
            self.assertIn("Architecture & System Blueprint", out)
            self.assertIn("```mermaid", out)

    def test_tool_generate_repo_map(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fpath = os.path.join(temp_dir, "math_utils.py")
            with open(fpath, "w", encoding="utf-8") as f:
                f.write("def add(x, y):\n    return x + y\n")

            res = self.run_async(self.server.call_tool(
                "generate_repo_map",
                {"project_root": temp_dir, "max_tokens": 1000}
            ))
            out = tool_result_text(res)
            self.assertIn("REPO MAP", out)
            self.assertIn("math_utils.py", out)

    def test_tool_audit_codebase_quality(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            clean_file = os.path.join(temp_dir, "clean.py")
            with open(clean_file, "w", encoding="utf-8") as f:
                f.write("'''Clean docstring module.'''\n\ndef good_function():\n    '''Good docstring.'''\n    return 42\n")

            res = self.run_async(self.server.call_tool(
                "audit_codebase_quality",
                {"project_root": temp_dir}
            ))
            out = tool_result_text(res)
            self.assertIn("Code Quality & Security Audit", out)
            self.assertIn("Zero-Leak Verified", out)

    def test_tool_find_code_duplicity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            dup_block = "a = 1\nb = 2\nc = 3\nd = 4\ne = 5\nf = 6\ng = 7\n"
            f1 = os.path.join(temp_dir, "mod1.py")
            f2 = os.path.join(temp_dir, "mod2.py")
            with open(f1, "w", encoding="utf-8") as f:
                f.write(dup_block)
            with open(f2, "w", encoding="utf-8") as f:
                f.write(dup_block)

            res = self.run_async(self.server.call_tool(
                "find_code_duplicity",
                {"project_root": temp_dir, "min_lines": 6}
            ))
            out = tool_result_text(res)
            self.assertIn("Code Duplicity Report", out)
            self.assertIn("mod1.py", out)
            self.assertIn("mod2.py", out)

    def test_tool_estimate_token_cost(self):
        res = self.run_async(self.server.call_tool(
            "estimate_token_cost",
            {"text": "Sample text for token and pricing estimation."}
        ))
        out = tool_result_text(res)
        self.assertIn("Token & API Cost Estimation", out)
        self.assertIn("OpenAI (GPT-4o)", out)
        self.assertIn("Anthropic (Claude 3.7 Sonnet)", out)
        self.assertIn("Ollama (Local Private)", out)
        self.assertIn("FREE ($0.00)", out)

    def test_prompt_tzero_grounding(self):
        res = self.run_async(self.server.get_prompt(
            "tzero_grounding",
            {"project_root": "C:/my_project"}
        ))
        text = res.messages[0].content.text
        self.assertIn("C:/my_project", text)
        self.assertIn("MANDATORY OPERATIONAL DIRECTIVES", text)
        self.assertIn("Zero-Leak", text)

    def test_tool_analyze_change_impact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            f1 = os.path.join(temp_dir, "lib.py")
            f2 = os.path.join(temp_dir, "caller.py")
            with open(f1, "w", encoding="utf-8") as fp:
                fp.write("def target_func(): pass\n")
            with open(f2, "w", encoding="utf-8") as fp:
                fp.write("import lib\nlib.target_func()\n")

            res = self.run_async(self.server.call_tool(
                "analyze_change_impact",
                {"target_symbol": "target_func", "project_root": temp_dir}
            ))
            out = tool_result_text(res)
            self.assertIn("Change Impact & Blast Radius", out)
            self.assertIn("caller.py", out)

    def test_tool_enforce_architecture_boundaries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            rules_p = os.path.join(temp_dir, "tzero.rules.json")
            with open(rules_p, "w", encoding="utf-8") as fp:
                fp.write('{"layers":{"core":["core/*"]},"forbidden_imports":[{"from_layer":"core","cannot_import":["ui"],"reason":"test"}]}')
            os.makedirs(os.path.join(temp_dir, "core"), exist_ok=True)
            with open(os.path.join(temp_dir, "core", "test.py"), "w", encoding="utf-8") as fp:
                fp.write("import ui\n")

            res = self.run_async(self.server.call_tool(
                "enforce_architecture_boundaries",
                {"project_root": temp_dir, "rules_file": "tzero.rules.json"}
            ))
            out = tool_result_text(res)
            self.assertIn("ARCH VIOLATION", out)

    def test_tool_search_codebase_semantic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            f = os.path.join(temp_dir, "auth_service.py")
            with open(f, "w", encoding="utf-8") as fp:
                fp.write("def authenticate_user(token):\n    '''Validates jwt security token.'''\n    return True\n")

            res = self.run_async(self.server.call_tool(
                "search_codebase_semantic",
                {"query": "jwt token authenticate", "project_root": temp_dir, "top_k": 3}
            ))
            out = tool_result_text(res)
            self.assertIn("Semantic Code Search", out)
            self.assertIn("auth_service.py", out)

    def test_tool_export_agent_rules(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            res = self.run_async(self.server.call_tool(
                "export_agent_rules",
                {"project_root": temp_dir, "target": "all"}
            ))
            out = tool_result_text(res)
            self.assertIn("Generated AI Agent rule files", out)
            self.assertTrue(os.path.exists(os.path.join(temp_dir, ".cursorrules")))
            self.assertTrue(os.path.exists(os.path.join(temp_dir, ".clinerules")))

    def test_tool_get_token_savings_metrics(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            f = os.path.join(temp_dir, "sample.py")
            with open(f, "w", encoding="utf-8") as fp:
                fp.write("def foo():\n    pass\n")

            res = self.run_async(self.server.call_tool(
                "get_token_savings_metrics",
                {"project_root": temp_dir, "team_size": 3}
            ))
            out = tool_result_text(res)
            self.assertIn("T-Zero Token Reduction & Economic ROI Report", out)
            self.assertIn("Monthly Team Cost", out)

    def test_tool_get_incremental_diff_context(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            res = self.run_async(self.server.call_tool(
                "get_incremental_diff_context",
                {"project_root": temp_dir, "base_ref": "HEAD~1"}
            ))
            out = tool_result_text(res)
            self.assertIn("No Git Changes Detected", out)

    def test_tool_prune_code_snippet(self):
        sample_code = """
import os
import sys

class Worker:
    def execute(self):
        # Long body
""" + "\n".join([f"        x_{i} = {i} * 2" for i in range(100)]) + """
        return True
"""
        res = self.run_async(self.server.call_tool(
            "prune_code_snippet",
            {"code": sample_code, "file_path_or_ext": "worker.py", "reduction_mode": "ultra"}
        ))
        out = tool_result_text(res)
        self.assertIn("T-Zero Code Pruning Result", out)
        self.assertIn("class Worker", out)
        self.assertIn("reduction", out)
        self.assertNotIn("x_50", out)

    def test_tool_verify_zero_leak_security(self):
        # 1. Clean snippet
        res_clean = self.run_async(self.server.call_tool(
            "verify_zero_leak_security",
            {"code_snippet": "def hello():\n    return 'clean'\n"}
        ))
        self.assertIn("ZERO-LEAK PASS", tool_result_text(res_clean))

        # 2. Leaking snippet
        fake_test_key = "sk-" + "dummytestkey1234567890abcdef1234567890abcdef"
        res_leak = self.run_async(self.server.call_tool(
            "verify_zero_leak_security",
            {"code_snippet": f'OPENAI_API_KEY = "{fake_test_key}"'}
        ))
        self.assertIn("Zero-Leak Security Alert", tool_result_text(res_leak))

    def test_tool_query_module_dependencies_polyglot(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ts_file = os.path.join(temp_dir, "service.ts")
            with open(ts_file, "w", encoding="utf-8") as f:
                f.write("import { Injectable } from '@nestjs/common';\nimport * as fs from 'fs';\n")

            res = self.run_async(self.server.call_tool(
                "query_module_dependencies",
                {"project_root": temp_dir, "file_path": "service.ts"}
            ))
            out = tool_result_text(res)
            self.assertIn("Dependency Analysis for `service.ts`", out)
            self.assertIn("@nestjs/common", out)
            self.assertIn("fs", out)

    def test_mcp_resources_registration(self):
        resources = self.run_async(self.server.list_resources())
        uris = [str(r.uri) for r in resources]
        self.assertIn("tzero://architecture", uris)
        self.assertIn("tzero://boundaries", uris)
        self.assertIn("tzero://token-roi", uris)


    def test_tool_jarvis_semantic_memory_tools(self):
        sample_text = "Toprak dün akşam laboratuvarda ESP32 kartı üzerinde nRF24L01 modülünü SPI portuna bağlayarak test etti."
        res_compress = self.run_async(self.server.call_tool(
            "jarvis_compress_semantic_memory",
            {"text": sample_text}
        ))
        out_comp = tool_result_text(res_compress)
        self.assertIn("T-Zero Jarvis 3-Layer Semantic Memory Compression", out_comp)
        self.assertIn("reduction", out_comp)
        self.assertIn("<|tzero:mem:", out_comp)

        # Decompress tool test
        res_decomp = self.run_async(self.server.call_tool(
            "jarvis_decompress_semantic_memory",
            {"token_or_code": "8421"}
        ))
        out_decomp = tool_result_text(res_decomp)
        self.assertIn("T-Zero Jarvis Semantic Memory Resolution", out_decomp)
        self.assertIn("Toprak", out_decomp)
        self.assertIn("ESP32", out_decomp)

    def test_tool_jarvis_orchestration_tools(self):
        # 1. Orchestrate goal
        res_orch = self.run_async(self.server.call_tool(
            "jarvis_orchestrate_goal",
            {"goal": "ESP32 SPI haberleşmesini test et ve güvenliği doğrula.", "project_root": "."}
        ))
        out_orch = tool_result_text(res_orch)
        self.assertIn("T-Zero Jarvis Autonomous Goal Orchestration", out_orch)
        self.assertIn("COMPLETED", out_orch)
        self.assertIn("0.00$", out_orch)

        # 2. Zero-key query
        res_query = self.run_async(self.server.call_tool(
            "jarvis_zero_key_query",
            {"prompt": "T-Zero ve Jarvis mimarisini özetle."}
        ))
        out_query = tool_result_text(res_query)
        self.assertIn("T-Zero Jarvis Zero-Cost Intelligence", out_query)
        self.assertIn("0.00$", out_query)

    def test_tool_jarvis_universal_tools(self):
        # 1. Query Knowledge Graph
        res_graph = self.run_async(self.server.call_tool(
            "jarvis_query_knowledge_graph",
            {"query": "ESP32"}
        ))
        out_graph = tool_result_text(res_graph)
        self.assertIn("T-Zero Knowledge Graph Search Results", out_graph)
        self.assertIn("8421", out_graph)

        # 2. Compress Document
        doc = (
            "Toprak dün akşam laboratuvarda ESP32 kartı üzerinde nRF24L01 modülünü SPI portuna bağlayarak test etti.\n\n"
            "Geliştirici ekibi Kubernetes kümesinde PostgreSQL veritabanını devreye aldı."
        )
        res_doc = self.run_async(self.server.call_tool(
            "jarvis_compress_document",
            {"document_text": doc}
        ))
        out_doc = tool_result_text(res_doc)
        self.assertIn("T-Zero Universal Document Memory Compression", out_doc)
        self.assertIn("Net Token Savings", out_doc)

        # 3. Export Memory Store
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_store = tmp.name

        try:
            res_store = self.run_async(self.server.call_tool(
                "jarvis_export_memory_store",
                {"action": "save", "file_path": tmp_store}
            ))
            out_store = tool_result_text(res_store)
            self.assertIn("T-Zero Memory Store Exported", out_store)
            self.assertTrue(os.path.exists(tmp_store))
        finally:
            if os.path.exists(tmp_store):
                os.remove(tmp_store)

    def test_tool_jarvis_master_upgrades(self):
        # 1. Causal Chain Query
        res_causal = self.run_async(self.server.call_tool(
            "jarvis_causal_chain_query",
            {"target_node_id": "test_err_node", "query_type": "timeline"}
        ))
        out_causal = tool_result_text(res_causal)
        self.assertIn("T-Zero Chronological Timeline", out_causal)

        # 2. Self-Healing Execute
        res_heal = self.run_async(self.server.call_tool(
            "jarvis_self_healing_execute",
            {"command": "python -c \"print('MCP Self-Healing Test OK')\""}
        ))
        out_heal = tool_result_text(res_heal)
        self.assertIn("Self-Healing Execution Result", out_heal)
        self.assertIn("MCP Self-Healing Test OK", out_heal)

        # 3. Consolidate Memory
        res_cons = self.run_async(self.server.call_tool(
            "jarvis_consolidate_memory",
            {"action": "summary"}
        ))
        out_cons = tool_result_text(res_cons)
        self.assertIn("T-Zero Memory Consolidation State", out_cons)

        # 4. Hybrid Search
        res_search = self.run_async(self.server.call_tool(
            "jarvis_hybrid_search",
            {"query": "ESP32", "top_k": 5}
        ))
        out_search = tool_result_text(res_search)
        self.assertIn("Zero-Vector-DB Hybrid Search Results", out_search)

        # 5. Swarm Orchestrate
        res_swarm = self.run_async(self.server.call_tool(
            "jarvis_swarm_orchestrate",
            {"mission_goal": "ESP32 SPI güvenli bağlantı testi", "context": "Lab"}
        ))
        out_swarm = tool_result_text(res_swarm)
        self.assertIn("Autonomous Swarm Mission Consensus", out_swarm)
        self.assertIn("JARVIS Prime", out_swarm)

        # 6. Export Graph Visualization
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
            tmp_html = tmp.name

        try:
            res_viz = self.run_async(self.server.call_tool(
                "jarvis_export_graph_visualization",
                {"output_path": tmp_html}
            ))
            out_viz = tool_result_text(res_viz)
            self.assertIn("Cyberpunk Knowledge & Causal Graph Exported", out_viz)
            self.assertTrue(os.path.exists(tmp_html))
        finally:
            if os.path.exists(tmp_html):
                os.remove(tmp_html)

    def test_jarvis_research_breakthrough_tools(self):
        """Verifies Tools 35, 36, and 37 (MinHash, PBFT Swarm, LatentPress)."""
        # 1. MinHash Similarity Tool
        res_minhash = self.run_async(self.server.call_tool(
            "jarvis_minhash_similarity",
            {
                "text_a": "Toprak ESP32 mikrodenetleyicisine nRF24L01 modülünü SPI veriyolu üzerinden bağladı",
                "text_b": "Toprak ESP32 kartına nRF24L01 telsiz modülünü SPI hattı ile entegre etti"
            }
        ))
        out_minhash = tool_result_text(res_minhash)
        self.assertIn("MinHash LSH Analysis", out_minhash)
        self.assertIn("Estimated Jaccard Similarity", out_minhash)

        # 2. PBFT Swarm Consensus Tool
        res_pbft = self.run_async(self.server.call_tool(
            "jarvis_bft_swarm_consensus",
            {
                "mission_goal": "ESP32 SPI haberleşme protokolünü doğrula",
                "context": "Donanım laboratuvarı"
            }
        ))
        out_pbft = tool_result_text(res_pbft)
        self.assertIn("Byzantine Fault-Tolerant (PBFT) Swarm Certificate", out_pbft)
        self.assertIn("Consensus Verdict", out_pbft)

        # 3. LatentPress Compression Tool
        long_context = "Toprak ESP32 mikrodenetleyicisine nRF24L01 bağladı.\n" * 5
        res_lp = self.run_async(self.server.call_tool(
            "jarvis_latent_press_compress",
            {
                "context_text": long_context,
                "near_dup_threshold": 0.65
            }
        ))
        out_lp = tool_result_text(res_lp)
        self.assertIn("LatentPress (LCLM) Context Compression", out_lp)
        self.assertIn("Compression Ratio", out_lp)

    def test_tool_prune_schema_definition(self):
        res = self.run_async(self.server.call_tool(
            "prune_schema_definition",
            {
                "content": "CREATE TABLE ledger (id INT PRIMARY KEY, amount NUMERIC);\nINSERT INTO ledger VALUES (1, 500);",
                "schema_type_or_filename": "schema.sql"
            }
        ))
        out = tool_result_text(res)
        self.assertIn("Infrastructure Schema Reduction", out)
        self.assertIn("CREATE TABLE ledger", out)

    def test_tool_generate_smart_micro_patch(self):
        diff_text = """
diff --git a/core.py b/core.py
--- a/core.py
+++ b/core.py
@@ -10,3 +10,3 @@ def run():
-    val = 10
+    val = 20
"""
        res = self.run_async(self.server.call_tool(
            "generate_smart_micro_patch",
            {"diff_content": diff_text}
        ))
        out = tool_result_text(res)
        self.assertIn("T-Zero AST Smart Micro-Patch", out)
        self.assertIn("[core.py]", out)


if __name__ == "__main__":
    unittest.main()

