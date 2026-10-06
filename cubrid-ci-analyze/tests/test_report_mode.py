import json
import subprocess
import sys
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "report_mode.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


class ReportModeFixtures(unittest.TestCase):
    def test_fixture_bundles_select_the_safe_report_mode(self) -> None:
        for fixture in sorted(FIXTURES.iterdir()):
            with self.subTest(fixture=fixture.name):
                assessment = fixture / "assessment.json"
                expected_path = fixture / "expected.json"
                if not assessment.is_file() or not expected_path.is_file():
                    continue
                expected = json.loads(expected_path.read_text())
                completed = subprocess.run(
                    [sys.executable, str(SCRIPT), str(assessment)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(json.loads(completed.stdout), expected)

    def test_baseline_scope_does_not_downgrade_head_or_upgrade_incomplete_head(self) -> None:
        spec = importlib.util.spec_from_file_location("report_mode", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        full = dict(identity="established", observation="complete", manifest="validated",
                    requested_summaries="validated", result_matches_observation=True,
                    requested_suites_reconciled=True)
        for baseline in ("not_assessed", "unavailable", "invalid", "partial_exact", "validated_exact"):
            with self.subTest(baseline=baseline):
                result = module.decide(dict(full, baseline=baseline))
                self.assertEqual(result["mode"], "full")
                self.assertEqual(result["regression_conclusions_allowed"], baseline in {"partial_exact", "validated_exact"})
                result = module.decide(dict(full, baseline=baseline, observation="incomplete"))
                self.assertEqual(result["mode"], "warning")
                self.assertEqual(result["comparison_scope"], "none")

    def test_invalid_assessments_are_rejected(self) -> None:
        invalid = FIXTURES / "invalid"
        for assessment in sorted(invalid.glob("*.json")):
            with self.subTest(fixture=assessment.name):
                completed = subprocess.run(
                    [sys.executable, str(SCRIPT), str(assessment)],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(completed.stdout, "")
                self.assertTrue(completed.stderr.startswith("report_mode:"))


if __name__ == "__main__":
    unittest.main()
