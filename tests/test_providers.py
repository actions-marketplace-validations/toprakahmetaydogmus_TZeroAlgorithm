# -*- coding: utf-8 -*-
"""Unit tests for multi-provider AI adapters."""

import unittest
from tzero_v3 import (
    PROVIDERS,
    NvidiaProvider,
    OpenAIProvider,
    GeminiProvider,
    OpenRouterProvider,
    AnthropicProvider,
    LocalOllamaProvider,
)


class TestProviders(unittest.TestCase):
    def test_registered_providers_count(self):
        self.assertGreaterEqual(len(PROVIDERS), 6)
        expected = ["NVIDIA NIM", "OpenAI", "Google Gemini", "OpenRouter", "Anthropic", "Local Ollama"]
        for exp in expected:
            self.assertIn(exp, PROVIDERS)

    def test_nvidia_provider(self):
        p = PROVIDERS["NVIDIA NIM"]
        self.assertEqual(p.name, "NVIDIA NIM")
        headers = p.get_headers("dummy-nv-key")
        self.assertEqual(headers["X-Nvidia-Api-Key"], "dummy-nv-key")
        self.assertEqual(p.get_models()[0], "deepseek-ai/deepseek-v4.1-flash")
        expected_models = [
            "deepseek-ai/deepseek-v4.1-flash",
            "deepseek-ai/deepseek-coder-6.7b-instruct",
            "nvidia/llama-3.1-nemotron-70b-instruct",
            "mistralai/mistral-large-2-instruct",
            "meta/llama-3.2-90b-vision-instruct"
        ]
        self.assertEqual(p.get_models(), expected_models)
        # Test alias resolution
        payload = p.format_payload("deepseek-v4.1-flash", [{"role": "user", "content": "hi"}])
        self.assertEqual(payload["model"], "deepseek-ai/deepseek-v4.1-flash")
        payload2 = p.format_payload("nemotron-70b", [{"role": "user", "content": "hi"}])
        self.assertEqual(payload2["model"], "nvidia/llama-3.1-nemotron-70b-instruct")

    def test_openai_provider(self):
        p = PROVIDERS["OpenAI"]
        self.assertEqual(p.name, "OpenAI")
        headers = p.get_headers("dummy-openai-key")
        self.assertEqual(headers["Authorization"], "Bearer dummy-openai-key")
        self.assertEqual(p.get_models(), ["gpt-4o", "gpt-4o-mini", "o3-mini", "o1"])

    def test_gemini_provider(self):
        p = PROVIDERS["Google Gemini"]
        self.assertEqual(p.name, "Google Gemini")
        self.assertEqual(p.get_models(), ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"])

    def test_openrouter_provider(self):
        p = PROVIDERS["OpenRouter"]
        self.assertEqual(p.name, "OpenRouter")
        self.assertEqual(p.get_models(), [
            "anthropic/claude-3.7-sonnet",
            "openai/gpt-4o",
            "deepseek/deepseek-r1"
        ])
        # Test alias resolution
        payload = p.format_payload("claude-3.7-sonnet", [{"role": "user", "content": "hi"}])
        self.assertEqual(payload["model"], "anthropic/claude-3.7-sonnet")

    def test_anthropic_provider(self):
        p = PROVIDERS["Anthropic"]
        self.assertEqual(p.name, "Anthropic")
        headers = p.get_headers("dummy-anthropic-key")
        self.assertEqual(headers["x-api-key"], "dummy-anthropic-key")
        self.assertEqual(headers["anthropic-version"], "2023-06-01")
        self.assertEqual(p.get_models(), ["claude-3-7-sonnet-20250219", "claude-3-5-sonnet", "claude-3-5-haiku"])

        # Test endpoint
        endpoint = p.get_endpoint_url("https://api.anthropic.com/v1")
        self.assertTrue(endpoint.endswith("/messages"))

        # Test payload format with system prompt extraction and alias resolution
        messages = [
            {"role": "system", "content": "You are an architect."},
            {"role": "user", "content": "Build context."}
        ]
        payload = p.format_payload("claude-3-5-sonnet", messages)
        self.assertEqual(payload["model"], "claude-3-5-sonnet-20241022")
        self.assertEqual(payload["system"], "You are an architect.")
        self.assertEqual(len(payload["messages"]), 1)
        self.assertEqual(payload["messages"][0]["role"], "user")

        # Test response parsing
        sample_resp = {
            "content": [
                {"type": "text", "text": "# Anthropic Output Markdown"}
            ]
        }
        parsed = p.parse_response(sample_resp)
        self.assertEqual(parsed, "# Anthropic Output Markdown")

    def test_local_ollama_provider(self):
        p = PROVIDERS["Local Ollama"]
        self.assertEqual(p.name, "Local Ollama")
        self.assertIn("11434", p.get_base_url())
        self.assertEqual(p.get_models(), ["llama3:latest", "mistral:latest", "phi3:latest", "qwen2.5:latest"])
        headers = p.get_headers("")
        self.assertEqual(headers["Content-Type"], "application/json")


if __name__ == "__main__":
    unittest.main()
