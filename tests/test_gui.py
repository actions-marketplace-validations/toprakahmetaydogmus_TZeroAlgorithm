"""
Test GUI Instantiation and Tab Switching
Safely skipped if running in a headless CI container without DISPLAY.
"""
import unittest
import os

class TestGUIInstantiation(unittest.TestCase):
    def test_gui_initialization_and_tabs(self):
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
        except Exception as e:
            raise unittest.SkipTest(f"Tkinter display not available: {e}")
        
        try:
            from tzero_v3 import AutoReadmeGUI
            app = AutoReadmeGUI(root)
            self.assertIsNotNone(app)
            self.assertIsNotNone(app.console_text)
            self.assertIn("Choose a workspace folder", app.tree_empty_lbl.cget("text"))
            self.assertEqual(app.header_search_entry.get(), "Search files...")
            self.assertTrue(root.bind("<Control-k>"))

            app.scanned_files = ["src/app.py", "README.md"]
            app.file_sizes = {"src/app.py": 128, "README.md": 64}
            app.file_snippets = {"src/app.py": "def app(): pass", "README.md": "# App"}
            app.file_checked = {"src/app.py": True, "README.md": False}
            app.has_scanned = True
            app.header_search_entry.delete(0, "end")
            app.header_search_entry.insert(0, "app.py")
            app._submit_header_search()

            self.assertEqual(app.active_tab_index, 1)
            self.assertTrue(app.tree.exists("src/app.py"))
            self.assertFalse(app.tree.exists("README.md"))

            original_target = app.dir_entry.get()
            app._rebuild_layout_for_theme("Glass Dark")
            self.assertEqual(app.dir_entry.get(), original_target)
            self.assertEqual(app.search_entry.get(), "app.py")
            self.assertTrue(app.tree.exists("src/app.py"))
            self.assertFalse(app.tree.exists("README.md"))
            self.assertIn("1 / 2 selected", app.selector_stats_lbl.cget("text"))
            
            # Verify cycling through all tabs
            for i in range(len(app.tab_frames)):
                app.switch_tab(i)
                root.update()
                
            self.assertEqual(len(app.tab_frames), 7)
            app.scanned_files = []
            app.file_checked = {}
            # Verify async_generate_payload resolves provider_name without NameError
            app.file_checked = {"src/app.py": True}
            app.file_snippets = {"src/app.py": "def test(): pass"}
            # Mock generator to avoid real network call during test
            from unittest.mock import patch, MagicMock
            with patch("tzero_v3.ContextGenerator.generate_readme", return_value="# Mock Result"):
                app.async_generate_payload("https://api.openai.com/v1", "test-key", ["src/app.py"])
                self.assertFalse(app.cancel_event.is_set())

            # Verify that an API 403 error triggers seamless offline AST fallback
            with patch("tzero_v3.ContextGenerator.generate_readme", side_effect=IOError("API Error code HTTP 403: Authorization failed")):
                app.async_generate_payload("https://integrate.api.nvidia.com/v1", "test-key", ["src/app.py"])
                root.update()
                preview = app.preview_text.get("1.0", "end").strip()
                self.assertIn("T-Zero Context Tree", preview)
                self.assertIn("src/app.py", preview)

                # Verify security audit executes and logs audit results
                app.run_quick_security_audit()
                root.update()
                self.assertIn("Security Audit", app.console_text.get("1.0", "end"))
        finally:
            try:
                root.destroy()
            except Exception:
                pass

if __name__ == "__main__":
    unittest.main()
