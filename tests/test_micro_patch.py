# -*- coding: utf-8 -*-
"""Unit tests for AST Smart Micro-Patch Compressor."""

import unittest
from tzero_patch import SmartMicroPatcher


class TestSmartMicroPatcher(unittest.TestCase):
    def test_compress_unified_diff(self):
        raw_diff = """
diff --git a/services/payment.py b/services/payment.py
index 4b825dc..91a72fb 100644
--- a/services/payment.py
+++ b/services/payment.py
@@ -20,7 +20,7 @@ class PaymentProcessor:
     def __init__(self, gateway_url: str):
         self.gateway_url = gateway_url
         self.timeout = 30
-        self.sandbox = True
+        self.sandbox = False
         self.retry_limit = 3
 
     def charge(self, amount: int) -> bool:
"""
        compact, savings = SmartMicroPatcher.compress_diff(raw_diff)
        self.assertGreater(savings, 30.0)
        self.assertIn("[services/payment.py]", compact)
        self.assertIn("class PaymentProcessor:", compact)
        self.assertIn("-        self.sandbox = True", compact)
        self.assertIn("+        self.sandbox = False", compact)
        self.assertNotIn("index 4b825dc", compact)

    def test_format_micro_patch_report(self):
        raw_diff = """
diff --git a/main.go b/main.go
--- a/main.go
+++ b/main.go
@@ -5,3 +5,3 @@ func Start() {
-	port := ":8080"
+	port := ":9000"
 }
"""
        report = SmartMicroPatcher.format_micro_patch_report(raw_diff)
        self.assertIn("# 🧩 T-Zero AST Smart Micro-Patch", report)
        self.assertIn("```patch", report)
        self.assertIn("port := \":9000\"", report)


if __name__ == "__main__":
    unittest.main()
