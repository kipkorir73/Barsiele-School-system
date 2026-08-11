import os
import sys
import unittest
from unittest.mock import patch

from app.core.file_open import open_local_path
from app.core.payment_receipt_flow import handle_post_payment_receipt


class TestFileOpen(unittest.TestCase):
    def test_open_local_path_requires_path(self):
        with self.assertRaises(ValueError):
            open_local_path("")

    def test_open_local_path_uses_xdg_open_on_linux(self):
        if hasattr(os, "startfile"):
            self.skipTest("Windows startfile present")
        if sys.platform == "darwin":
            self.skipTest("macOS open path")

        with patch("app.core.file_open.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stderr = b""
            run.return_value.stdout = b""
            open_local_path("/tmp/receipt.pdf")
            run.assert_called_once()
            args = run.call_args[0][0]
            self.assertEqual(args[:2], ["xdg-open", "/tmp/receipt.pdf"])

    def test_open_local_path_raises_when_handler_fails(self):
        if hasattr(os, "startfile"):
            self.skipTest("Windows startfile present")
        if sys.platform == "darwin":
            self.skipTest("macOS open path")

        with patch("app.core.file_open.subprocess.run") as run:
            run.return_value.returncode = 1
            run.return_value.stderr = b"failed to open"
            run.return_value.stdout = b""
            with self.assertRaises(OSError):
                open_local_path("/tmp/missing.pdf")


class TestPostPaymentReceiptFlow(unittest.TestCase):
    def test_open_failure_is_receipt_stage_not_payment(self):
        def generate(_pid, _receipt):
            return "/tmp/receipt.pdf"

        def open_boom(_path):
            raise OSError("module 'os' has no attribute 'startfile'")

        path, err, stage = handle_post_payment_receipt(
            1, "abc12345", generate, open_boom, should_open=True
        )
        self.assertEqual(path, "/tmp/receipt.pdf")
        self.assertEqual(stage, "open")
        self.assertIsInstance(err, OSError)

    def test_generate_failure_is_receipt_stage(self):
        def generate(_pid, _receipt):
            raise RuntimeError("pdf backend crashed")

        path, err, stage = handle_post_payment_receipt(
            1, "abc12345", generate, lambda p: None, should_open=True
        )
        self.assertIsNone(path)
        self.assertEqual(stage, "generate")
        self.assertIsInstance(err, RuntimeError)

    def test_success_path(self):
        opened = []
        path, err, stage = handle_post_payment_receipt(
            1,
            "abc12345",
            lambda *_: "/tmp/receipt.pdf",
            opened.append,
            should_open=True,
        )
        self.assertEqual(path, "/tmp/receipt.pdf")
        self.assertIsNone(err)
        self.assertEqual(stage, "ok")
        self.assertEqual(opened, ["/tmp/receipt.pdf"])


if __name__ == "__main__":
    unittest.main()
