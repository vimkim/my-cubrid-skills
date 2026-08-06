#!/usr/bin/env python3
"""Disposable integration tests for reportctl.py."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone


SCRIPT = Path(__file__).resolve().with_name("reportctl.py")


def invoke(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class ReportctlTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.original_path = os.environ.get("PATH", "")
        self.original_cubrid = os.environ.get("CUBRID")
        self.original_databases = os.environ.get("CUBRID_DATABASES")
        self.original_build_dir = os.environ.get("CUBRID_BUILD_DIR")
        self.fake_bin = self.root / "bin"
        self.fake_bin.mkdir()
        runtime_tool = """#!/usr/bin/env python3
import pathlib
import sys
name = pathlib.Path(sys.argv[0]).name
if '--version' in sys.argv:
    print(f'{name} test-runtime 1')
    raise SystemExit(0)
for flag in ('--input-file', '-i'):
    if flag in sys.argv:
        path = pathlib.Path(sys.argv[sys.argv.index(flag) + 1])
        print(f'{name} executed ' + path.read_text(encoding='utf-8').strip())
        raise SystemExit(0)
print(f'{name} executed')
"""
        for name in ("csql", "cubrid", "cub_server", "cubrid_rel"):
            path = self.fake_bin / name
            path.write_text(runtime_tool, encoding="utf-8")
            path.chmod(0o755)
        os.environ["PATH"] = f"{self.fake_bin}{os.pathsep}{self.original_path}"
        os.environ["CUBRID"] = str(self.root)
        os.environ["CUBRID_DATABASES"] = str(self.root / "databases")
        os.environ["CUBRID_BUILD_DIR"] = str(self.root / "build")
        self.cubrid = self.make_repo(
            "cubrid",
            {
                "CMakeLists.txt": "cmake_minimum_required(VERSION 3.16)\nproject(CUBRID)\n",
                "source.txt": "cubrid evidence\n",
                "justfile": (
                    "build:\n"
                    f"    @mkdir -p {self.root / 'build'}\n"
                    f"    @printf 'CMAKE_HOME_DIRECTORY:INTERNAL={self.root / 'cubrid'}\\nCMAKE_INSTALL_PREFIX:PATH={self.root}\\n' > {self.root / 'build' / 'CMakeCache.txt'}\n"
                    f"    @sha256sum source.txt > {self.fake_bin / 'cub_server'}\n"
                    f"    @chmod +x {self.fake_bin / 'cub_server'}\n"
                ),
            },
        )
        self.postgres = self.make_repo(
            "postgres",
            {
                "configure.ac": "AC_INIT([PostgreSQL], [test])\n",
                "meson.build": "project('postgresql')\n",
                "src/include/postgres.h": "/* postgres */\n",
            },
        )
        self.mysql = self.make_repo(
            "mysql",
            {
                "CMakeLists.txt": "project(MySQL)\n",
                "MYSQL_VERSION": "MYSQL_VERSION_MAJOR=9\n",
                "sql/mysqld.cc": "// mysql\n",
            },
        )
        self.output = self.root / "report"

    def tearDown(self) -> None:
        os.environ["PATH"] = self.original_path
        if self.original_cubrid is None:
            os.environ.pop("CUBRID", None)
        else:
            os.environ["CUBRID"] = self.original_cubrid
        if self.original_databases is None:
            os.environ.pop("CUBRID_DATABASES", None)
        else:
            os.environ["CUBRID_DATABASES"] = self.original_databases
        if self.original_build_dir is None:
            os.environ.pop("CUBRID_BUILD_DIR", None)
        else:
            os.environ["CUBRID_BUILD_DIR"] = self.original_build_dir
        self.temporary.cleanup()

    def make_repo(self, name: str, files: dict[str, str]) -> Path:
        root = self.root / name
        root.mkdir()
        for relative, content in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.com"], check=True)
        remote = {
            "cubrid": "https://github.com/CUBRID/cubrid",
            "postgres": "https://github.com/postgres/postgres",
            "mysql": "https://github.com/mysql/mysql-server",
        }[name]
        subprocess.run(["git", "-C", str(root), "remote", "add", "origin", remote], check=True)
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
        return root

    def initialize(self) -> dict[str, object]:
        result = invoke(
            "init",
            "--topic",
            "page buffer",
            "--cubrid-root",
            str(self.cubrid),
            "--postgres-root",
            str(self.postgres),
            "--mysql-root",
            str(self.mysql),
            "--agent",
            "codex",
            "--output",
            str(self.output),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def record(
        self,
        run_id: str,
        cwd: Path | None = None,
        command: list[str] | None = None,
        runtime_snapshot: str | None = None,
        bind_files: list[str] | None = None,
    ) -> None:
        cwd = cwd or self.output
        command = command or [sys.executable, "-c", "print('observed')"]
        arguments = [
            "record",
            "--report-dir",
            str(self.output),
            "--id",
            run_id,
            "--cwd",
            str(cwd),
            "--expect-exit",
            "0",
        ]
        if runtime_snapshot:
            arguments.extend(["--runtime-tools-snapshot", runtime_snapshot])
        for bound_file in bind_files or []:
            arguments.extend(["--bind-file", bound_file])
        result = invoke(*arguments, "--", *command)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def build(self, run_id: str) -> None:
        result = invoke(
            "build",
            "--report-dir",
            str(self.output),
            "--id",
            run_id,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_init_resume_collision_and_record_immutability(self) -> None:
        self.assertFalse(self.initialize()["resumed"])
        self.assertTrue(self.initialize()["resumed"])
        self.record("experiment-1-run")
        duplicate = invoke(
            "record",
            "--report-dir",
            str(self.output),
            "--id",
            "experiment-1-run",
            "--cwd",
            str(self.output),
            "--",
            sys.executable,
            "-c",
            "pass",
        )
        self.assertEqual(duplicate.returncode, 21)
        literal_argv = [
            sys.executable,
            "-c",
            "import sys; print(repr(sys.argv[1:]))",
            "space value",
            "$(touch should-not-exist)",
            "*.c",
            ";",
            "",
        ]
        self.record("literal-argv", self.output, literal_argv)
        meta = json.loads(
            (self.output / "evidence" / "runs" / "literal-argv" / "meta.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(meta["argv"], literal_argv)
        self.assertFalse((self.output / "should-not-exist").exists())
        (self.cubrid / "source.txt").write_text("changed\n", encoding="utf-8")
        self.assertEqual(self.initialize_failure(), 4)

    def initialize_failure(self) -> int:
        return invoke(
            "init",
            "--topic",
            "page buffer",
            "--cubrid-root",
            str(self.cubrid),
            "--postgres-root",
            str(self.postgres),
            "--mysql-root",
            str(self.mysql),
            "--agent",
            "codex",
            "--output",
            str(self.output),
        ).returncode

    def test_report_and_complete_verification(self) -> None:
        self.initialize()
        self.write_report_artifacts()
        report = invoke("verify", "--report-dir", str(self.output), "--phase", "report")
        self.assertEqual(report.returncode, 0, report.stdout + report.stderr)
        self.write_grill_artifacts()
        complete = invoke("verify", "--report-dir", str(self.output), "--phase", "complete")
        self.assertEqual(complete.returncode, 0, complete.stdout + complete.stderr)

    def test_tampered_evidence_and_remote_resource_are_rejected(self) -> None:
        self.initialize()
        self.write_report_artifacts()
        run_dir = self.output / "evidence" / "runs" / "experiment-1-run"
        (run_dir / "meta.json").write_text('{"matched_expectation": true}\n', encoding="utf-8")
        (run_dir / "stdout.txt").unlink()
        index_path = self.output / "index.html"
        index_path.write_text(
            index_path.read_text(encoding="utf-8").replace(
                "</main>", '<img src="//remote.invalid/image.png" alt="원격 이미지"></main>'
            ),
            encoding="utf-8",
        )
        result = invoke("verify", "--report-dir", str(self.output), "--phase", "report")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Recorded run metadata ID mismatch", result.stdout)
        self.assertIn("Recorded run output is unreadable", result.stdout)
        self.assertIn("Protocol-relative loaded resource", result.stdout)

    def test_claim_matrix_and_duplicate_coverage_anchor_are_rejected(self) -> None:
        self.initialize()
        self.write_report_artifacts()
        claims_path = self.output / "evidence" / "claims.jsonl"
        claims = [json.loads(line) for line in claims_path.read_text(encoding="utf-8").splitlines()]
        comparison = next(claim for claim in claims if claim["database"] == "comparison")
        comparison["source_refs"] = comparison["source_refs"][:1]
        claims_path.write_text(
            "".join(json.dumps(claim, ensure_ascii=False) + "\n" for claim in claims),
            encoding="utf-8",
        )
        report_path = self.output / "report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["coverage"][1]["anchor"] = report["coverage"][0]["anchor"]
        report_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
        result = invoke("verify", "--report-dir", str(self.output), "--phase", "report")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must cite all three databases", result.stdout)
        self.assertIn("Coverage obligations share one chapter anchor", result.stdout)

    def test_malformed_grill_event_returns_structured_failure(self) -> None:
        self.initialize()
        self.write_report_artifacts()
        self.write_grill_artifacts()
        (self.output / "grill" / "session.jsonl").write_text("[]\n", encoding="utf-8")
        result = invoke("verify", "--report-dir", str(self.output), "--phase", "complete")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("Grill event 1 is not an object", result.stdout)

    def test_inert_runner_unrelated_claim_and_forged_runtime_are_rejected(self) -> None:
        self.initialize()
        self.write_report_artifacts()
        experiment = self.output / "experiments" / "experiment-1"
        manifest_path = experiment / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        inert_argv = [sys.executable, "-c", "pass", "experiment.sql"]
        manifest["runner_argv"] = inert_argv
        manifest["claim_ids"] = ["PG-C001"]
        manifest["runner_sha256"] = "f" * 64
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        meta_path = self.output / "evidence" / "runs" / "experiment-1-run" / "meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["argv"] = inert_argv
        meta_path.write_text(json.dumps(meta), encoding="utf-8")
        runtime_path = self.output / "evidence" / "runtime-tools-baseline.json"
        runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
        runtime["tools"]["csql"]["sha256"] = "0" * 64
        runtime_path.write_text(json.dumps(runtime), encoding="utf-8")
        self.write_audit("report")
        result = invoke("verify", "--report-dir", str(self.output), "--phase", "report")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must directly execute captured csql or cubrid", result.stdout)
        self.assertIn("runs must be consumed by a linked CUBRID runtime Claim", result.stdout)
        self.assertIn("Active runtime tool identity drift: csql", result.stdout)
        self.assertIn("runner hash mismatch", result.stdout)

    def test_recursive_offline_html_and_navigation_are_rejected(self) -> None:
        self.initialize()
        self.write_report_artifacts()
        index_path = self.output / "index.html"
        index_path.write_text(
            index_path.read_text(encoding="utf-8").replace(
                "</main>",
                '<svg role="img" aria-label="외부 그림"><image href="https://remote.invalid/x.png"></image></svg>'
                '<img srcset="data:image/png;base64,AAAA 1x, https://remote.invalid/y.png 2x" alt="외부 후보">'
                '<script>new Image().src="https://remote.invalid/z.png"</script>'
                '<a href="chapters/02.html">둘째 장</a></main>',
            ),
            encoding="utf-8",
        )
        extra = self.output / "chapters"
        (extra / "02.html").write_text(
            '<!doctype html><html lang="ko"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width"><title>숨은 장</title></head>'
            '<body><main><h1>숨은 장</h1><p>두 번째 설명이다.</p>'
            '<a href="../index.html">목차</a></main></body></html>',
            encoding="utf-8",
        )
        self.write_audit("report")
        result = invoke("verify", "--report-dir", str(self.output), "--phase", "report")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("External loaded resource", result.stdout)
        self.assertIn("script elements are forbidden", result.stdout)
        self.assertIn("lacks rel=", result.stdout)

    def test_scope_status_audit_and_grill_sequence_gates(self) -> None:
        self.initialize()
        self.write_report_artifacts()
        report_path = self.output / "report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["status"] = "DRAFT"
        report["scope"]["sha256"] = "f" * 64
        report_path.write_text(json.dumps(report), encoding="utf-8")
        result = invoke("verify", "--report-dir", str(self.output), "--phase", "report")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("status must be REPORT_READY", result.stdout)
        self.assertIn("Declared Scope digest", result.stdout)
        self.assertIn("audit seal does not match", result.stdout)

        report["status"] = "REPORT_READY"
        scope = self.output / "research" / "scope.md"
        report["scope"]["sha256"] = hashlib.sha256(scope.read_bytes()).hexdigest()
        report_path.write_text(json.dumps(report), encoding="utf-8")
        self.write_audit("report")
        self.write_grill_artifacts()
        session_path = self.output / "grill" / "session.jsonl"
        events = [json.loads(line) for line in session_path.read_text(encoding="utf-8").splitlines()]
        events[0]["evaluation"] = "PARTIAL"
        events[0]["state_after"] = "ASK_NARROWER"
        events[0]["references"] = ["chapters/01.html#does-not-exist"]
        session_path.write_text(
            "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events),
            encoding="utf-8",
        )
        self.write_audit("complete")
        complete = invoke("verify", "--report-dir", str(self.output), "--phase", "complete")
        self.assertNotEqual(complete.returncode, 0)
        self.assertIn("must continue narrower questioning", complete.stdout)
        self.assertIn("invalid Book reference", complete.stdout)

    def test_malformed_existing_provenance_is_a_conflict(self) -> None:
        self.output.mkdir()
        (self.output / "provenance.json").write_text("[]\n", encoding="utf-8")
        result = invoke(
            "init",
            "--topic",
            "page buffer",
            "--cubrid-root",
            str(self.cubrid),
            "--postgres-root",
            str(self.postgres),
            "--mysql-root",
            str(self.mysql),
            "--agent",
            "codex",
            "--output",
            str(self.output),
        )
        self.assertEqual(result.returncode, 4, result.stdout + result.stderr)
        self.assertNotIn("Internal validation error", result.stdout)

    def test_baseline_snapshot_substitution_is_rejected(self) -> None:
        self.initialize()
        self.write_report_artifacts()
        provenance_path = self.output / "provenance.json"
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        snapshot = provenance["repositories"]["postgresql"]["baseline_files"][
            "worktree.diff"
        ]
        snapshot_path = self.output / snapshot["path"]
        substituted = b"forged baseline\n"
        snapshot_path.write_bytes(substituted)
        snapshot["sha256"] = hashlib.sha256(substituted).hexdigest()
        provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
        self.write_audit("report")
        result = invoke("verify", "--report-dir", str(self.output), "--phase", "report")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not bound to repository fingerprint", result.stdout)

    def test_used_restored_instrumentation_positive_and_tamper_gates(self) -> None:
        self.initialize()
        self.write_report_artifacts(instrumented=True)
        positive = invoke("verify", "--report-dir", str(self.output), "--phase", "report")
        self.assertEqual(positive.returncode, 0, positive.stdout + positive.stderr)

        transaction_path = self.output / "evidence" / "instrumentation.json"
        transaction = json.loads(transaction_path.read_text(encoding="utf-8"))
        patch_path = self.output / "evidence" / "instrumentation.patch"
        patch_path.write_bytes(b"")
        transaction["patch"]["sha256"] = hashlib.sha256(b"").hexdigest()
        transaction["build_run_ids"]["instrumented"] = "runtime-baseline-build"
        transaction["markers"] = ["BAD_MARKER"]
        transaction["applied_at_utc"] = "2026-08-06T00:00:10+00:00"
        transaction["reversed_at_utc"] = "2026-08-06T00:00:09+00:00"
        transaction["cleanup_verification"]["runner_argv"] = [sys.executable, "-c", "pass"]
        provenance_path = self.output / "provenance.json"
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        status_info = provenance["repositories"]["cubrid"]["baseline_files"][
            "status.porcelain-v1.z"
        ]
        status_path = self.output / status_info["path"]
        dirty_status = b" M source.txt\0"
        status_path.write_bytes(dirty_status)
        dirty_digest = hashlib.sha256(dirty_status).hexdigest()
        status_info["sha256"] = dirty_digest
        provenance["repositories"]["cubrid"]["status_sha256"] = dirty_digest
        transaction["baseline"]["status_sha256"] = dirty_digest
        provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
        transaction_path.write_text(json.dumps(transaction), encoding="utf-8")
        report_path = self.output / "report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["instrumentation"]["markers"] = ["BAD_MARKER"]
        report_path.write_text(json.dumps(report), encoding="utf-8")
        self.write_audit("report")
        negative = invoke("verify", "--report-dir", str(self.output), "--phase", "report")
        self.assertNotEqual(negative.returncode, 0)
        self.assertIn("requires three distinct build run IDs", negative.stdout)
        self.assertIn("patch must not be empty", negative.stdout)
        self.assertIn("needs unique markers", negative.stdout)
        self.assertIn("reversal must occur after application", negative.stdout)
        self.assertIn("did not execute the cleanup verifier", negative.stdout)
        self.assertIn("target appears in baseline Git status", negative.stdout)

    def write_report_artifacts(self, *, instrumented: bool = False) -> None:
        report_state = json.loads((self.output / "report.json").read_text(encoding="utf-8"))
        sections = "".join(
            f'<section id="cov-{item["id"]}" data-claim-id="CUBRID-C001 PG-C001 MYSQL-C001 CMP-C001"><h2>{item["id"]}</h2><p>이 의무의 동작과 근거를 설명한다.</p></section>'
            for item in report_state["coverage"]
        )
        index = """<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>페이지 버퍼 분석</title><link rel="stylesheet" href="assets/report.css"></head><body><main><h1>페이지 버퍼 분석</h1><p>이 보고서는 동작을 설명한다.</p><a href="chapters/01.html">분석 장</a></main></body></html>"""
        chapter = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>전체 분석</title><link rel="stylesheet" href="../assets/report.css"></head><body><main><h1>전체 분석</h1>{sections}<a href="../index.html">목차</a></main></body></html>"""
        (self.output / "index.html").write_text(index, encoding="utf-8")
        (self.output / "chapters" / "01.html").write_text(chapter, encoding="utf-8")

        self.build("runtime-baseline-build")
        snapshot = invoke(
            "runtime-snapshot",
            "--report-dir",
            str(self.output),
            "--id",
            "baseline",
            "--build-run-id",
            "runtime-baseline-build",
        )
        self.assertEqual(snapshot.returncode, 0, snapshot.stdout + snapshot.stderr)

        experiment_runtime_snapshot = "evidence/runtime-tools-baseline.json"
        quiz_runtime_snapshot = experiment_runtime_snapshot
        instrumentation_transaction: dict[str, object] | None = None
        if instrumented:
            marker = "CUBRID_CODE_ANALYSIS_TEST_MARKER"
            target = self.cubrid / "source.txt"
            original = target.read_bytes()
            target.write_bytes(original + f"/* {marker} */\n".encode())
            applied_at = datetime.now(timezone.utc).isoformat()
            patch_data = subprocess.run(
                ["git", "-C", str(self.cubrid), "diff", "--binary", "--no-ext-diff", "--", "source.txt"],
                check=True,
                stdout=subprocess.PIPE,
            ).stdout
            patch_path = self.output / "evidence" / "instrumentation.patch"
            patch_path.write_bytes(patch_data)
            self.build("instrumented-build")
            instrumented_snapshot = invoke(
                "runtime-snapshot",
                "--report-dir",
                str(self.output),
                "--id",
                "instrumented",
                "--build-run-id",
                "instrumented-build",
            )
            self.assertEqual(
                instrumented_snapshot.returncode,
                0,
                instrumented_snapshot.stdout + instrumented_snapshot.stderr,
            )
            experiment_runtime_snapshot = "evidence/runtime-tools-instrumented.json"

        experiment = self.output / "experiments" / "experiment-1"
        experiment.mkdir()
        (experiment / "experiment.md").write_text("# 실험\n\n동작을 관찰한다.\n", encoding="utf-8")
        (experiment / "experiment.sql").write_text("select 'experiment';\n", encoding="utf-8")
        (experiment / "expected-oracle.md").write_text("# Oracle\n\n상태 전이를 관찰한다.\n", encoding="utf-8")
        quiz = self.output / "quiz" / "quiz-1"
        quiz.mkdir()
        (quiz / "quiz.md").write_text("# 문제\n\n결과를 예측하고 이유를 설명하라.\n", encoding="utf-8")
        (quiz / "answer.md").write_text("# 정답\n\n상태 전이 때문에 이 결과가 나온다.\n", encoding="utf-8")
        (quiz / "quiz.sql").write_text("select 'quiz';\n", encoding="utf-8")
        csql = str((self.fake_bin / "csql").resolve())
        experiment_argv = [csql, "--input-file", "experiment.sql"]
        quiz_argv = [csql, "--input-file", "quiz.sql"]
        self.record(
            "experiment-1-run",
            experiment,
            experiment_argv,
            experiment_runtime_snapshot,
        )
        if instrumented:
            target = self.cubrid / "source.txt"
            target.write_text("cubrid evidence\n", encoding="utf-8")
            reversed_at = datetime.now(timezone.utc).isoformat()
            self.build("post-clean-build")
            post_clean_snapshot = invoke(
                "runtime-snapshot",
                "--report-dir",
                str(self.output),
                "--id",
                "post-clean",
                "--build-run-id",
                "post-clean-build",
            )
            self.assertEqual(
                post_clean_snapshot.returncode,
                0,
                post_clean_snapshot.stdout + post_clean_snapshot.stderr,
            )
            quiz_runtime_snapshot = "evidence/runtime-tools-post-clean.json"
            cleanup_runner = self.output / "evidence" / "instrumentation-cleanup.sh"
            cleanup_runner.write_text(
                "#!/usr/bin/env bash\nset -eu\n"
                "if rg --fixed-strings 'CUBRID_CODE_ANALYSIS_TEST_MARKER' \"$1/source.txt\"; then exit 1; fi\n",
                encoding="utf-8",
            )
            cleanup_runner.chmod(0o755)
            cleanup_argv = [
                "bash",
                "evidence/instrumentation-cleanup.sh",
                str(self.cubrid),
            ]
            self.record("instrumentation-cleanup", self.output, cleanup_argv)
            provenance = json.loads(
                (self.output / "provenance.json").read_text(encoding="utf-8")
            )
            instrumentation_transaction = {
                "schema_version": 1,
                "baseline": {
                    field: provenance["repositories"]["cubrid"][field]
                    for field in ("status_sha256", "diff_sha256", "cached_diff_sha256")
                },
                "markers": ["CUBRID_CODE_ANALYSIS_TEST_MARKER"],
                "target_files": [
                    {
                        "path": "source.txt",
                        "original_sha256": hashlib.sha256(b"cubrid evidence\n").hexdigest(),
                        "restored_sha256": hashlib.sha256(b"cubrid evidence\n").hexdigest(),
                    }
                ],
                "patch": {
                    "path": "evidence/instrumentation.patch",
                    "sha256": hashlib.sha256(
                        (self.output / "evidence" / "instrumentation.patch").read_bytes()
                    ).hexdigest(),
                },
                "applied_at_utc": applied_at,
                "reversed_at_utc": reversed_at,
                "instrumented_experiment_run_ids": ["experiment-1-run"],
                "build_run_ids": {
                    "baseline": "runtime-baseline-build",
                    "instrumented": "instrumented-build",
                    "post_clean": "post-clean-build",
                },
                "runtime_snapshots": {
                    "baseline": "evidence/runtime-tools-baseline.json",
                    "instrumented": "evidence/runtime-tools-instrumented.json",
                    "post_clean": "evidence/runtime-tools-post-clean.json",
                },
                "cleanup_verification": {
                    "runner": "evidence/instrumentation-cleanup.sh",
                    "runner_sha256": hashlib.sha256(cleanup_runner.read_bytes()).hexdigest(),
                    "runner_argv": cleanup_argv,
                    "run_ids": ["instrumentation-cleanup"],
                    "oracle_ko": "instrumentation marker와 owned process가 남지 않아야 한다.",
                },
            }
        self.record("quiz-1-run-1", quiz, quiz_argv, quiz_runtime_snapshot)
        self.record("quiz-1-run-2", quiz, quiz_argv, quiz_runtime_snapshot)
        self.write_claims_and_report()
        if instrumentation_transaction is not None:
            report_path = self.output / "report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["runtime"]["active_tools_snapshot"] = quiz_runtime_snapshot
            report["instrumentation"] = {
                "status": "used-restored",
                "post_clean_build_run_id": "post-clean-build",
                "markers": ["CUBRID_CODE_ANALYSIS_TEST_MARKER"],
                "target_files": ["source.txt"],
            }
            report_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
            (self.output / "evidence" / "instrumentation.json").write_text(
                json.dumps(instrumentation_transaction, ensure_ascii=False),
                encoding="utf-8",
            )
        behavior_id = "page-fix-flow"
        (experiment / "manifest.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "id": "experiment-1",
                    "behavior_ids": [behavior_id],
                    "claim_ids": ["CUBRID-C001"],
                    "runner": "experiment.sql",
                    "runner_sha256": hashlib.sha256((experiment / "experiment.sql").read_bytes()).hexdigest(),
                    "runner_argv": experiment_argv,
                    "run_ids": ["experiment-1-run"],
                    "oracle_ko": "정상 상태 전이가 관찰되어야 한다.",
                    "controls_ko": "동일한 입력을 사용한다.",
                    "alternative_explanations_ko": "환경 차이가 결과를 바꿀 수 있다.",
                    "repetitions": 1,
                    "cubrid_runtime_only": True,
                    "runtime_tools_snapshot": experiment_runtime_snapshot,
                    "cleanup_verified": True,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (quiz / "quiz.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "id": "quiz-1",
                    "behavior_ids": [behavior_id],
                    "claim_ids": ["CUBRID-C001"],
                    "runner": "quiz.sql",
                    "runner_sha256": hashlib.sha256((quiz / "quiz.sql").read_bytes()).hexdigest(),
                    "runner_argv": quiz_argv,
                    "run_ids": ["quiz-1-run-1", "quiz-1-run-2"],
                    "oracle_ko": "두 실행에서 같은 invariant를 설명해야 한다.",
                    "cubrid_runtime_only": True,
                    "runtime_tools_snapshot": quiz_runtime_snapshot,
                    "cleanup_verified": True,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        self.write_audit("report")

    def write_claims_and_report(self) -> None:
        provenance = json.loads((self.output / "provenance.json").read_text(encoding="utf-8"))
        report = json.loads((self.output / "report.json").read_text(encoding="utf-8"))
        report_locations = [
            f'chapters/01.html#cov-{item["id"]}' for item in report["coverage"]
        ]
        specs = {
            "cubrid": ("CUBRID-C001", "source.txt", "cubrid"),
            "postgresql": ("PG-C001", "configure.ac", "AC_INIT"),
            "mysql": ("MYSQL-C001", "MYSQL_VERSION", "MYSQL_VERSION_MAJOR"),
        }
        claims = []
        comparison_refs = []
        for database, (claim_id, relative, symbol) in specs.items():
            source = Path(provenance["repositories"][database]["root"]) / relative
            source_ref = {
                "path": relative,
                "symbol": symbol,
                "line_start": 1,
                "line_end": 1,
                "file_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "evidence_state": "COMMIT",
            }
            comparison_refs.append({"database": database, **source_ref})
            claims.append(
                {
                    "id": claim_id,
                    "claim_ko": f"{database}의 핵심 동작을 설명한다.",
                    "database": database,
                    "revision": provenance["repositories"][database]["head"],
                    "kind": "source+runtime" if database == "cubrid" else "source",
                    "confidence": "SOURCE+RUNTIME-CONFIRMED" if database == "cubrid" else "SOURCE-CONFIRMED",
                    "source_refs": [source_ref],
                    "runtime_run_ids": ["experiment-1-run"] if database == "cubrid" else [],
                    "limitations_ko": "이 검증 범위로 제한된다.",
                    "report_locations": report_locations,
                }
            )
        claims.append(
            {
                "id": "CMP-C001",
                "claim_ko": "세 데이터베이스의 책임 차이를 비교한다.",
                "database": "comparison",
                "revision": "three pinned revisions",
                "kind": "analogy",
                "confidence": "SOURCE-CONFIRMED",
                "analogy_class": "partial analogy",
                "source_refs": comparison_refs,
                "runtime_run_ids": [],
                "limitations_ko": "공유 scenario 범위의 비교다.",
                "report_locations": report_locations,
            }
        )
        (self.output / "evidence" / "claims.jsonl").write_text(
            "".join(json.dumps(claim, ensure_ascii=False) + "\n" for claim in claims), encoding="utf-8"
        )
        for item in report["coverage"]:
            item.update(
                status="covered",
                chapter="chapters/01.html",
                anchor=f'cov-{item["id"]}',
                claim_ids=["CUBRID-C001", "PG-C001", "MYSQL-C001", "CMP-C001"],
                rationale_ko="전체 분석 장에서 다룬다.",
            )
        report.update(readiness="READY WITHIN DECLARED SCOPE", runtime_run_ids=["experiment-1-run"])
        report["runtime"] = {
            "runtime_build_run_id": "runtime-baseline-build",
            "baseline_tools_snapshot": "evidence/runtime-tools-baseline.json",
            "active_tools_snapshot": "evidence/runtime-tools-baseline.json",
        }
        scope = self.output / "research" / "scope.md"
        scope.write_text("# 범위\n\n페이지 fix 흐름과 비교 메커니즘을 분석한다.\n", encoding="utf-8")
        report["scope"] = {
            "path": "research/scope.md",
            "sha256": hashlib.sha256(scope.read_bytes()).hexdigest(),
            "frozen": True,
        }
        report["status"] = "REPORT_READY"
        report["central_behaviors"] = [
            {
                "id": "page-fix-flow",
                "name_ko": "페이지 fix 상태 전이",
                "claim_ids": ["CUBRID-C001", "PG-C001", "MYSQL-C001", "CMP-C001"],
                "coverage_ids": [item["id"] for item in report["coverage"]],
                "experiment_ids": ["experiment-1"],
                "quiz_ids": ["quiz-1"],
                "chapter": "chapters/01.html",
                "anchor": "cov-core-workflows",
                "grill_concepts": [
                    "scope-interface-seams",
                    "data-ownership-lifetime",
                    "lifecycle-state-machines",
                    "concurrency",
                    "durability-recovery-failures",
                    "policy-performance",
                    "experiment-interpretation",
                    "cross-database-non-equivalence",
                ],
            }
        ]
        (self.output / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    def write_grill_artifacts(self) -> None:
        summary = """<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>학습 결과</title><link rel="stylesheet" href="../assets/report.css"></head><body><main><h1>학습 결과</h1><p>모든 핵심 개념을 설명했다.</p><a href="../index.html">목차</a></main></body></html>"""
        (self.output / "grill" / "mastery-summary.html").write_text(summary, encoding="utf-8")
        index_path = self.output / "index.html"
        index_path.write_text(
            index_path.read_text(encoding="utf-8").replace(
                "</main>", '<a href="grill/mastery-summary.html">학습 결과</a></main>'
            ),
            encoding="utf-8",
        )
        concepts = {
            name: "MASTERED"
            for name in (
                "scope-interface-seams",
                "data-ownership-lifetime",
                "lifecycle-state-machines",
                "concurrency",
                "durability-recovery-failures",
                "policy-performance",
                "experiment-interpretation",
                "cross-database-non-equivalence",
            )
        }
        (self.output / "grill" / "mastery.json").write_text(
            json.dumps({"state": "COMPLETE", "concepts": concepts, "capstone": "MASTERED"}),
            encoding="utf-8",
        )
        events = []
        for number, concept in enumerate(concepts, 1):
            events.append(
                {
                    "timestamp_utc": f"2026-08-06T00:00:{number:02d}+00:00",
                    "concept": concept,
                    "exchange_id": f"exchange-{number}",
                    "host_turn_id": f"host-{number}",
                    "user_turn_id": f"user-{number}",
                    "attempt": 1,
                    "state_before": "WAIT_FOR_USER",
                    "state_after": "CAPSTONE_TEACHBACK" if number == len(concepts) else "SELECT_NEXT",
                    "question_ko": f"{concept}의 동작을 설명해 주세요.",
                    "answer_ko": "원인과 상태 전이를 근거와 함께 설명한다.",
                    "evaluation": "MASTERED",
                    "references": ["chapters/01.html#cov-core-workflows"],
                }
            )
        events.append(
            {
                "timestamp_utc": "2026-08-06T00:00:09+00:00",
                "concept": "capstone",
                "exchange_id": "exchange-capstone",
                "host_turn_id": "host-capstone",
                "user_turn_id": "user-capstone",
                "attempt": 1,
                "state_before": "WAIT_FOR_USER",
                "state_after": "COMPLETE",
                "question_ko": "전체 동작을 처음부터 끝까지 설명해 주세요.",
                "answer_ko": "Interface부터 상태 전이와 복구까지 설명한다.",
                "evaluation": "MASTERED",
                "references": ["chapters/01.html#cov-core-workflows"],
            }
        )
        (self.output / "grill" / "session.jsonl").write_text(
            "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events),
            encoding="utf-8",
        )
        report = json.loads((self.output / "report.json").read_text(encoding="utf-8"))
        report["status"] = "COMPLETE"
        (self.output / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        self.write_audit("complete")

    def write_audit(self, phase: str) -> None:
        materials = invoke(
            "materials", "--report-dir", str(self.output), "--phase", phase
        )
        self.assertEqual(materials.returncode, 0, materials.stdout + materials.stderr)
        reviewed_files = json.loads(materials.stdout)["reviewed_files"]
        report = json.loads((self.output / "report.json").read_text(encoding="utf-8"))
        prefix = "report-audit" if phase == "report" else "complete-audit"
        manifest = {
            "schema_version": 1,
            "phase": phase,
            "reviewer_id": "isolated-test-reviewer",
            "isolated_reviewer": True,
            "round": 1,
            "timestamp_utc": "2026-08-06T00:00:00+00:00",
            "verdict": "APPROVED",
            "findings": [],
            "coverage_obligations": [item["id"] for item in report["coverage"]],
            "reviewed_files": reviewed_files,
        }
        (self.output / "evidence" / f"{prefix}.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (self.output / "evidence" / f"{prefix}.md").write_text(
            "# 독립 감사\n\n모든 의무를 검토했다.\n\nVERDICT: APPROVED\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
