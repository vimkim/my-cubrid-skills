import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


COLLECTION = Path(__file__).resolve().parents[2]
CHECKER = COLLECTION / "cubrid-common" / "scripts" / "check-shared-links.py"
PR_CHECKER = COLLECTION / "cubrid-pr-create" / "scripts" / "check-pr-material.sh"
PRIVATE_URL = "https://dev2.baboon-rudd.ts.net:8443/reports/evidence.md"
PUBLIC_URL = "https://github.com/CUBRID/cubrid/pull/1234"


class SharedLinksTests(unittest.TestCase):
    def run_checker(self, *files: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CHECKER), *map(str, files)],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_rejects_private_links_in_shared_formats_without_changing_files(self):
        examples = [
            PRIVATE_URL,
            f"[Evidence]({PRIVATE_URL})",
            f"[Evidence](<{PRIVATE_URL}>)",
            f"See [evidence].\n[evidence]: {PRIVATE_URL}",
            f"![Results]({PRIVATE_URL})",
            f"<{PRIVATE_URL}>",
            f'<a href="{PRIVATE_URL}">Evidence</a>',
            f"<img src='{PRIVATE_URL}'>",
            f"```text\n{PRIVATE_URL}\n```",
            f"[Evidence]({PRIVATE_URL})[PR]({PUBLIC_URL})",
            "https://dev2.baboon-rudd.ts.net",
            "http://DEV2.BABOON-RUDD.TS.NET:80/other?x=1#results",
            "https://dev2.baboon-rudd.ts.net.:9443/other",
            "//dev2.baboon-rudd.ts.net:8443/other",
            "ftp://dev2.baboon-rudd.ts.net:21/other",
            "https://reader@dev2.baboon-rudd.ts.net/other",
            "See https://dev2.baboon-rudd.ts.net.",
        ]
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "CBRD-12345-issue.md"
            for example in examples:
                with self.subTest(example=example):
                    content = f"# Shared report\n\n{example}\n"
                    report.write_text(content, encoding="utf-8")
                    result = self.run_checker(report)
                    self.assertEqual(result.returncode, 1, result)
                    self.assertIn(f"{report}:", result.stderr)
                    self.assertIn("personal viewing URL", result.stderr)
                    self.assertEqual(report.read_text(encoding="utf-8"), content)

    def test_allows_shared_links_and_hostname_mentions_that_are_not_private_urls(self):
        content = "\n".join(
            [
                PUBLIC_URL,
                "https://jira.cubrid.org/browse/CBRD-12345",
                "https://github.com/CUBRID/cubrid/actions/runs/1234",
                "[Implementation](../src/file.cpp)",
                "[Results](#results)",
                "한국어 본문과 링크 없는 검증 결과.",
                "The personal hostname is dev2.baboon-rudd.ts.net.",
                "https://github.com/example/repo/blob/main/dev2.baboon-rudd.ts.net.md",
                "https://dev2.baboon-rudd.ts.net.example.org/report",
                "https://dev2.baboon-rudd.ts.net@github.com/example/repo",
                "https://[2001:db8::1]/report",
            ]
        )
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report.md"
            report.write_text(content, encoding="utf-8")
            result = self.run_checker(report)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Shared link check passed", result.stdout)
            self.assertEqual(report.read_text(encoding="utf-8"), content)

    def test_checks_all_supplied_files_and_reports_actual_line(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = [root / name for name in ("body.md", "detail one.md", "detail2.md")]
            paths[0].write_text(PUBLIC_URL, encoding="utf-8")
            paths[1].write_text(f"# Details\n\nEvidence\n{PRIVATE_URL}", encoding="utf-8")
            paths[2].write_text(PRIVATE_URL, encoding="utf-8")
            result = self.run_checker(*paths)
            self.assertEqual(result.returncode, 1, result)
            self.assertIn(f"{paths[1]}:4:", result.stderr)
            self.assertIn(f"{paths[2]}:1:", result.stderr)
            self.assertNotIn("check passed", result.stdout)

    def test_missing_directory_and_non_utf8_inputs_fail_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invalid = root / "invalid.md"
            invalid.write_bytes(b"\xff")
            for path in (root / "missing.md", root, invalid):
                with self.subTest(path=path):
                    result = self.run_checker(path)
                    self.assertEqual(result.returncode, 1, result)
                    self.assertIn("cannot read UTF-8 material", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)

    def test_requires_at_least_one_file(self):
        result = self.run_checker()
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)


class PrMaterialIntegrationTests(unittest.TestCase):
    def run_checker(self, root: Path, body: Path, *files: Path):
        return subprocess.run(
            ["bash", str(PR_CHECKER), "--body", str(body), *map(str, files)],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )

    def body(self, evidence: str) -> str:
        return f"## Purpose\nChange behavior.\n## Implementation\nFix it.\n## Remarks\n{evidence}\n"

    def test_rejects_private_body_and_explanation_from_another_working_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            body, detail = root / "body.md", root / "explanation.md"
            for private_body in (True, False):
                with self.subTest(private_body=private_body):
                    body.write_text(self.body(PRIVATE_URL if private_body else PUBLIC_URL))
                    detail.write_text(PUBLIC_URL if private_body else PRIVATE_URL)
                    before = {path: path.read_bytes() for path in (body, detail)}
                    result = self.run_checker(root, body, detail)
                    self.assertEqual(result.returncode, 1, result)
                    self.assertIn("personal viewing URL", result.stderr)
                    self.assertNotIn("PR material check passed", result.stdout)
                    self.assertEqual({p: p.read_bytes() for p in before}, before)

    def test_accepts_shared_body_and_explanation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            body, detail = root / "body.md", root / "explanation.md"
            body.write_text(self.body(PUBLIC_URL))
            detail.write_text(f"# Explanation\n[PR]({PUBLIC_URL})\n")
            result = self.run_checker(root, body, detail)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PR material check passed", result.stdout)

    def test_preserves_existing_pr_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            body = root / "body.md"
            for content, expected in (
                ("## Purpose\nMissing sections.\n", "top-level sections"),
                (self.body("/home/author/report.md"), "local path or file URL"),
                (self.body("`just build`"), "just task-runner command"),
            ):
                with self.subTest(expected=expected):
                    body.write_text(content)
                    result = self.run_checker(root, body)
                    self.assertEqual(result.returncode, 1, result)
                    self.assertIn(expected, result.stderr)


if __name__ == "__main__":
    unittest.main()
