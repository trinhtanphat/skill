"""Regression tests for local assessment dispatch and CI exit status."""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import assess
import full_assess


class AssessmentCliTests(unittest.TestCase):
    def test_dot_selects_local_artifact(self):
        self.assertEqual("artifact", assess.classify(".")[0])

    def test_explicit_windows_log_target_still_works(self):
        self.assertEqual("winlog", assess.classify("winlogs")[0])

    def run_mock_assessment(self, exit_code):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "sample.bin"
            target.write_bytes(b"fixture")
            out = root / "output"
            step = full_assess.Step("Artifact audit", "orchestrate.py", [], exit_code, None)
            argv = ["full_assess.py", str(target), "--out", str(out)]
            with mock.patch.object(full_assess, "delegate_orchestrate", return_value=step):
                with mock.patch.object(sys, "argv", argv):
                    with contextlib.redirect_stdout(io.StringIO()):
                        result = full_assess.main()
            report = (out / "assessment" / "REPORT.md")
            self.assertTrue(report.exists())
            return result, report.read_text(encoding="utf-8")

    def test_failed_step_fails_ci_and_still_writes_report(self):
        status, report = self.run_mock_assessment(2)
        self.assertEqual(1, status)
        self.assertIn("FAIL (2)", report)

    def test_successful_step_exits_zero(self):
        status, report = self.run_mock_assessment(0)
        self.assertEqual(0, status)
        self.assertIn("OK", report)


if __name__ == "__main__":
    unittest.main()
