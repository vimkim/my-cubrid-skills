from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "testkit-focused.py"


class TestkitFocusedTests(unittest.TestCase):
    def write(self, path: Path, content: str, *, executable: bool = False) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        if executable:
            path.chmod(0o755)
        return path

    def run_cli(
        self, root: Path, *arguments: str, env: dict[str, str]
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            cwd=root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def preflight_fixture(
        self, root: Path, *, installed_commit: str, with_testkit: bool = True
    ) -> tuple[dict[str, str], str]:
        self.write(root / "CMakeLists.txt", "project(CUBRID)\n")
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "add", "CMakeLists.txt"], cwd=root, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.com",
                "commit",
                "-qm",
                "fixture",
            ],
            cwd=root,
            check=True,
        )
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()

        cubrid = root / "install"
        self.write(
            cubrid / "bin" / "cubrid_rel",
            "#!/bin/sh\n"
            f"echo 'CUBRID 11.5.0 (11.5.0.2602-{installed_commit}) "
            "(64bit debug build for Linux)'\n",
            executable=True,
        )
        (cubrid / "databases").mkdir(parents=True)
        ctp_home = root / "CTP"
        (ctp_home / "conf").mkdir(parents=True)
        java_home = root / "jdk8"
        self.write(
            java_home / "bin" / "javac",
            "#!/bin/sh\necho 'javac 1.8.0-test' >&2\n",
            executable=True,
        )

        tool_bin = root / "tools"
        tool_bin.mkdir()
        if with_testkit:
            self.write(
                tool_bin / "testkit",
                "#!/bin/sh\n"
                "if [ \"$1\" = --version ]; then echo 'cubrid-testkit test'; exit 0; fi\n"
                "if [ \"$1\" = -h ] && [ \"$TESTKIT_CONTAIN\" = 1 ]; then exit 0; fi\n"
                "exit 9\n",
                executable=True,
            )

        env = os.environ.copy()
        env.update(
            {
                "PATH": f"{tool_bin}:/usr/bin:/bin",
                "CUBRID": str(cubrid),
                "CUBRID_DATABASES": str(cubrid / "databases"),
                "CTP_HOME": str(ctp_home),
                "JAVA_HOME": str(java_home),
            }
        )
        return env, head

    def test_preflight_stops_when_testkit_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env, head = self.preflight_fixture(
                root, installed_commit="0000000", with_testkit=False
            )

            result = self.run_cli(root, "preflight", "--suite", "sql", env=env)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("testkit is not on PATH", result.stderr)
            self.assertIn("go install", result.stderr)
            self.assertNotIn(head, result.stdout)

    def test_preflight_accepts_matching_source_and_install_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env, head = self.preflight_fixture(root, installed_commit="placeholder")
            cubrid_rel = Path(env["CUBRID"]) / "bin" / "cubrid_rel"
            self.write(
                cubrid_rel,
                "#!/bin/sh\n"
                f"echo 'CUBRID 11.5.0 (11.5.0.2602-{head[:7]}) "
                "(64bit debug build for Linux)'\n",
                executable=True,
            )

            result = self.run_cli(root, "preflight", "--suite", "sql", env=env)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"source_head={head}", result.stdout)
            self.assertIn(f"installed_commit={head[:7]}", result.stdout)
            self.assertIn("commit_match=yes", result.stdout)
            self.assertIn("testkit_version=cubrid-testkit test", result.stdout)
            self.assertRegex(result.stdout, r"testkit_sha256=[0-9a-f]{64}")

    def test_preflight_stops_on_confirmed_commit_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env, _ = self.preflight_fixture(root, installed_commit="deadbee")

            result = self.run_cli(root, "preflight", "--suite", "sql", env=env)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("source/install commit mismatch", result.stderr)
            self.assertIn("--allow-commit-mismatch", result.stderr)

    def test_preflight_accepts_external_worktree_database_root_for_disposable_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            root.mkdir()
            env, head = self.preflight_fixture(root, installed_commit="placeholder")
            cubrid_rel = Path(env["CUBRID"]) / "bin" / "cubrid_rel"
            self.write(
                cubrid_rel,
                "#!/bin/sh\n"
                f"echo 'CUBRID 11.5.0 (11.5.0.2602-{head[:7]}) "
                "(64bit debug build for Linux)'\n",
                executable=True,
            )
            external_databases = Path(directory) / "databases"
            external_databases.mkdir()
            env["CUBRID_DATABASES"] = str(external_databases)

            result = self.run_cli(root, "preflight", "--suite", "sql", env=env)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"cubrid_databases={external_databases}", result.stdout)
            self.assertIn("execution_database_layout=disposable-inside-cubrid", result.stdout)

    def test_preflight_explicit_override_bypasses_only_known_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env, _ = self.preflight_fixture(root, installed_commit="deadbee")

            result = self.run_cli(
                root,
                "preflight",
                "--suite",
                "sql",
                "--allow-commit-mismatch",
                env=env,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("commit_match=no", result.stdout)
            self.assertIn("commit_mismatch_allowed=yes", result.stdout)
            self.assertIn("WARNING", result.stderr)

    def test_preflight_override_does_not_bypass_missing_install_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env, _ = self.preflight_fixture(root, installed_commit="not-a-commit")

            result = self.run_cli(
                root,
                "preflight",
                "--suite",
                "sql",
                "--allow-commit-mismatch",
                env=env,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot parse an installed commit", result.stderr)

    def test_preflight_override_does_not_bypass_missing_containment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env, _ = self.preflight_fixture(root, installed_commit="deadbee")
            testkit = Path(env["PATH"].split(":", 1)[0]) / "testkit"
            self.write(
                testkit,
                "#!/bin/sh\n"
                "if [ \"$1\" = --version ]; then echo 'cubrid-testkit test'; exit 0; fi\n"
                "echo 'namespace unavailable' >&2\nexit 42\n",
                executable=True,
            )

            result = self.run_cli(
                root,
                "preflight",
                "--suite",
                "sql",
                "--allow-commit-mismatch",
                env=env,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("containment probe failed", result.stderr)

    def test_shell_preflight_does_not_require_java(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env, head = self.preflight_fixture(root, installed_commit="placeholder")
            cubrid_rel = Path(env["CUBRID"]) / "bin" / "cubrid_rel"
            self.write(
                cubrid_rel,
                "#!/bin/sh\n"
                f"echo 'CUBRID 11.5.0 (11.5.0.2602-{head[:7]}) "
                "(64bit debug build for Linux)'\n",
                executable=True,
            )
            env.pop("JAVA_HOME")

            result = self.run_cli(root, "preflight", "--suite", "shell", env=env)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("suite=shell", result.stdout)
            self.assertNotIn("java_home=", result.stdout)

    def test_sql_preflight_rejects_non_jdk8(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env, head = self.preflight_fixture(root, installed_commit="placeholder")
            cubrid_rel = Path(env["CUBRID"]) / "bin" / "cubrid_rel"
            self.write(
                cubrid_rel,
                "#!/bin/sh\n"
                f"echo 'CUBRID 11.5.0 (11.5.0.2602-{head[:7]}) "
                "(64bit debug build for Linux)'\n",
                executable=True,
            )
            self.write(
                Path(env["JAVA_HOME"]) / "bin" / "javac",
                "#!/bin/sh\necho 'javac 17.0.1' >&2\n",
                executable=True,
            )

            result = self.run_cli(root, "preflight", "--suite", "sql", env=env)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires JDK 8", result.stderr)

    def sql_result_fixture(
        self, root: Path, *, failed: bool = False
    ) -> tuple[Path, Path, Path]:
        case = self.write(root / "corpus" / "sql" / "group" / "cases" / "1001.sql", "select 1;\n")
        self.write(case.with_suffix(".result"), "1\n")
        expected = self.write(root / "expected-cases.txt", f"{case}\n")
        result_dir = root / "result"
        success = 0 if failed else 1
        failures = 1 if failed else 0
        verdict = "nok" if failed else "ok"
        self.write(
            result_dir / "summary_info",
            f"total:1\nsuccess:{success}\nfail:{failures}\ntotalTime:10ms\n"
            "SiteRunTimes:1times\nsql/:1    "
            f"{success}    {failures}\n",
        )
        self.write(
            result_dir / "main.info",
            f"category:sql\nsuccess:{success}\nfail:{failures}\ntotal:1\n"
            f"execute_case:1\nresult_path:{result_dir}\ncubrid_rel:CUBRID fixture\n",
        )
        xml_result = "failure" if failed else "success"
        self.write(
            result_dir / "summary.xml",
            "<results><scenario>"
            f"<case>sql/group/cases/1001.sql</case><result>{xml_result}</result>"
            "</scenario></results>\n",
        )
        self.write(
            result_dir / "linux_sql_64bit.xml",
            f'<testsuite tests="1" failures="{failures}"/>\n',
        )
        self.write(
            result_dir / "sql" / "group" / "summary_info",
            f"total:1\nsuccess:{success}\nfail:{failures}\n"
            f"{case}:{verdict}    10ms\n",
        )
        log = self.write(
            root / "run.log",
            f"Result Root Dir:{result_dir}\n"
            f"Fail:{failures}\nSuccess:{success}\nTotal:1\n[SQL] TEST END\n",
        )
        return result_dir, expected, log

    def test_verify_sql_accepts_complete_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result_dir, expected, log = self.sql_result_fixture(root)

            result = self.run_cli(
                root,
                "verify",
                "--suite",
                "sql",
                "--result-dir",
                str(result_dir),
                "--expected-list",
                str(expected),
                "--run-log",
                str(log),
                "--runner-exit",
                "0",
                env=os.environ.copy(),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("suite=sql", result.stdout)
            self.assertIn("total=1", result.stdout)
            self.assertIn("fail=0", result.stdout)

    def test_verify_sql_rejects_main_info_that_disagrees_with_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result_dir, expected, log = self.sql_result_fixture(root)
            (result_dir / "main.info").write_text(
                "category:sql\nsuccess:0\nfail:1\ntotal:1\nexecute_case:1\n"
                f"result_path:{result_dir}\ncubrid_rel:CUBRID fixture\n",
                encoding="utf-8",
            )

            result = self.run_cli(
                root,
                "verify",
                "--suite",
                "sql",
                "--result-dir",
                str(result_dir),
                "--expected-list",
                str(expected),
                "--run-log",
                str(log),
                "--runner-exit",
                "0",
                env=os.environ.copy(),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("main.info fail count is 1", result.stderr)

    def test_verify_rejects_zero_selected_cases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result_dir, expected, log = self.sql_result_fixture(root)
            expected.write_text("", encoding="utf-8")

            result = self.run_cli(
                root,
                "verify",
                "--suite",
                "sql",
                "--result-dir",
                str(result_dir),
                "--expected-list",
                str(expected),
                "--run-log",
                str(log),
                "--runner-exit",
                "0",
                env=os.environ.copy(),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("expected case list is empty", result.stderr)

    def test_verify_rejects_nonzero_runner_exit_even_with_passing_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result_dir, expected, log = self.sql_result_fixture(root)

            result = self.run_cli(
                root,
                "verify",
                "--suite",
                "sql",
                "--result-dir",
                str(result_dir),
                "--expected-list",
                str(expected),
                "--run-log",
                str(log),
                "--runner-exit",
                "1",
                env=os.environ.copy(),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("setup or execution did not complete", result.stderr)

    def test_verify_sql_rejects_nok_even_when_runner_exit_is_zero(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result_dir, expected, log = self.sql_result_fixture(root, failed=True)

            result = self.run_cli(
                root,
                "verify",
                "--suite",
                "sql",
                "--result-dir",
                str(result_dir),
                "--expected-list",
                str(expected),
                "--run-log",
                str(log),
                "--runner-exit",
                "0",
                env=os.environ.copy(),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("fail count is 1", result.stderr)
            self.assertIn("runner exit was 0", result.stderr)

    def test_verify_shell_accepts_complete_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = self.write(
                root / "corpus" / "shell" / "case1" / "cases" / "case1.sh",
                "#!/bin/sh\n",
            )
            expected = self.write(root / "expected-cases.txt", f"{case}\n")
            result_dir = root / "current_runtime_logs"
            status = (
                "total_case_count=1\n"
                "total_executed_case_count=1\n"
                "total_success_case_count=1\n"
                "total_fail_case_count=0\n"
                "total_skip_case_count=0\n"
            )
            self.write(result_dir / "test_status.data", status)
            self.write(result_dir / "dispatch_tc_ALL.txt", f"{case}\n")
            self.write(result_dir / "dispatch_tc_FIN_local.txt", f"{case}\n")
            self.write(
                result_dir / "feedback.log",
                f"[OK]:  {case} 10 EnvId=local[slot0]\n"
                "Total Case:1\nTotal Execution Case:1\nTotal Success Case:1\n"
                "Total Fail Case:0\nTotal Skip Case:0\n[TEST STOP]\n",
            )
            self.write(result_dir / "main_snapshot.properties", "test_category=shell\n")
            self.write(result_dir / "test_local.log", "case1-1 : OK\n")
            self.write(
                result_dir / "test-shell.xml",
                '<testsuite tests="1" failures="0" skipped="0"/>\n',
            )
            log = self.write(
                root / "run.log",
                "Total Execution Case:1\nTotal Success Case:1\n"
                "Total Fail Case:0\nTotal Skip Case:0\n[SHELL] TEST END\n",
            )

            result = self.run_cli(
                root,
                "verify",
                "--suite",
                "shell",
                "--result-dir",
                str(result_dir),
                "--expected-list",
                str(expected),
                "--run-log",
                str(log),
                "--runner-exit",
                "0",
                env=os.environ.copy(),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("suite=shell", result.stdout)
            self.assertIn("total=1", result.stdout)

    def test_verify_shell_rejects_feedback_summary_that_disagrees_with_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = self.write(
                root / "corpus" / "shell" / "case1" / "cases" / "case1.sh",
                "#!/bin/sh\n",
            )
            expected = self.write(root / "expected-cases.txt", f"{case}\n")
            result_dir = root / "current_runtime_logs"
            self.write(
                result_dir / "test_status.data",
                "total_case_count=1\ntotal_executed_case_count=1\n"
                "total_success_case_count=1\ntotal_fail_case_count=0\n"
                "total_skip_case_count=0\n",
            )
            self.write(result_dir / "dispatch_tc_ALL.txt", f"{case}\n")
            self.write(result_dir / "dispatch_tc_FIN_local.txt", f"{case}\n")
            self.write(
                result_dir / "feedback.log",
                f"[OK]:  {case} 10 EnvId=local[slot0]\n"
                "Total Case:1\nTotal Execution Case:1\nTotal Success Case:0\n"
                "Total Fail Case:1\nTotal Skip Case:0\n[TEST STOP]\n",
            )
            self.write(result_dir / "main_snapshot.properties", "test_category=shell\n")
            self.write(result_dir / "test_local.log", "case1-1 : OK\n")
            self.write(
                result_dir / "test-shell.xml",
                '<testsuite tests="1" failures="0" skipped="0"/>\n',
            )
            log = self.write(
                root / "run.log",
                "Total Execution Case:1\nTotal Success Case:1\n"
                "Total Fail Case:0\nTotal Skip Case:0\n[SHELL] TEST END\n",
            )

            result = self.run_cli(
                root,
                "verify",
                "--suite",
                "shell",
                "--result-dir",
                str(result_dir),
                "--expected-list",
                str(expected),
                "--run-log",
                str(log),
                "--runner-exit",
                "0",
                env=os.environ.copy(),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("feedback fail count is 1", result.stderr)

    def test_verify_shell_rejects_skipped_junit_case(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = self.write(
                root / "corpus" / "shell" / "case1" / "cases" / "case1.sh",
                "#!/bin/sh\n",
            )
            expected = self.write(root / "expected-cases.txt", f"{case}\n")
            result_dir = root / "current_runtime_logs"
            self.write(
                result_dir / "test_status.data",
                "total_case_count=1\ntotal_executed_case_count=1\n"
                "total_success_case_count=1\ntotal_fail_case_count=0\n"
                "total_skip_case_count=0\n",
            )
            self.write(result_dir / "dispatch_tc_ALL.txt", f"{case}\n")
            self.write(result_dir / "dispatch_tc_FIN_local.txt", f"{case}\n")
            self.write(
                result_dir / "feedback.log",
                f"[OK]:  {case} 10 EnvId=local[slot0]\n"
                "Total Case:1\nTotal Execution Case:1\nTotal Success Case:1\n"
                "Total Fail Case:0\nTotal Skip Case:0\n[TEST STOP]\n",
            )
            self.write(result_dir / "main_snapshot.properties", "test_category=shell\n")
            self.write(result_dir / "test_local.log", "case1-1 : OK\n")
            self.write(
                result_dir / "test-shell.xml",
                '<testsuite tests="1" failures="0" errors="0" skipped="1"/>\n',
            )
            log = self.write(
                root / "run.log",
                "Total Execution Case:1\nTotal Success Case:1\n"
                "Total Fail Case:0\nTotal Skip Case:0\n[SHELL] TEST END\n",
            )

            result = self.run_cli(
                root,
                "verify",
                "--suite",
                "shell",
                "--result-dir",
                str(result_dir),
                "--expected-list",
                str(expected),
                "--run-log",
                str(log),
                "--runner-exit",
                "0",
                env=os.environ.copy(),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("skipped=1", result.stderr)

    def test_prepare_config_writes_serial_sql_and_medium_settings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scenario = root / "corpus" / "medium" / "_01_fixed"
            (scenario / "cases").mkdir(parents=True)
            case = self.write(scenario / "cases" / "1001.sql", "select 1;\n")
            expected = self.write(root / "expected.txt", f"{case}\n")
            data_file = self.write(root / "corpus" / "medium" / "files" / "mdb.tar.gz", "data")
            base = self.write(
                root / "medium_dev.conf",
                "[sql]\nparallel_slots=8\nscenario=/old\n"
                "test_category=medium\ntestcase_exclude_from_file=/old/exclusions\n"
                "data_file=/old/mdb.tar.gz\n\n"
                "[sql/cubrid.conf]\ncreate_table_reuseoid=yes\n",
            )
            output = root / "attempt" / "medium.conf"

            result = self.run_cli(
                root,
                "prepare-config",
                "--suite",
                "medium",
                "--base-conf",
                str(base),
                "--output-conf",
                str(output),
                "--scenario",
                str(scenario),
                "--expected-list",
                str(expected),
                "--data-file",
                str(data_file),
                env=os.environ.copy(),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            config = output.read_text(encoding="utf-8")
            self.assertIn("parallel_slots=1", config)
            self.assertIn(f"scenario={scenario.resolve()}", config)
            self.assertIn("testcase_exclude_from_file=", config)
            self.assertNotIn("testcase_exclude_from_file=/old", config)
            self.assertIn(f"data_file={data_file.resolve()}", config)
            self.assertIn("create_table_reuseoid=no", config)

            repeated = self.run_cli(
                root,
                "prepare-config",
                "--suite",
                "medium",
                "--base-conf",
                str(base),
                "--output-conf",
                str(output),
                "--scenario",
                str(scenario),
                "--expected-list",
                str(expected),
                "--data-file",
                str(data_file),
                env=os.environ.copy(),
            )
            self.assertNotEqual(repeated.returncode, 0)
            self.assertIn("refusing to overwrite", repeated.stderr)

    def test_prepare_config_writes_contained_shell_overlay_and_case_list(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scenario = root / "corpus" / "shell"
            case = self.write(
                scenario / "group" / "case1" / "cases" / "case1.sh",
                "#!/bin/sh\n",
            )
            expected = self.write(root / "expected.txt", f"{case}\n")
            base = self.write(
                root / "shell_ci.conf",
                "scenario=/old\nparallel_slots=9\nscenario_ram_mb=512\n"
                "testcase_update_yn=true\ntestcase_retry_num=2\nfeedback_type=database\n",
            )
            output = root / "attempt" / "shell.conf"

            result = self.run_cli(
                root,
                "prepare-config",
                "--suite",
                "shell",
                "--base-conf",
                str(base),
                "--output-conf",
                str(output),
                "--scenario",
                str(scenario),
                "--expected-list",
                str(expected),
                env=os.environ.copy(),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            config = output.read_text(encoding="utf-8")
            for setting in (
                f"scenario={scenario.resolve()}",
                "parallel_slots=1",
                "scenario_disk=on",
                "scenario_ram_mb=",
                f"testcase_from_file={expected.resolve()}",
                "testcase_update_yn=false",
                "testcase_retry_num=0",
                "feedback_type=file",
            ):
                self.assertIn(setting, config)

    def test_prepare_medium_rejects_a_partial_directory_case_list(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scenario = root / "medium" / "group"
            first = self.write(scenario / "cases" / "1001.sql", "select 1;\n")
            self.write(scenario / "cases" / "1002.sql", "select 2;\n")
            expected = self.write(root / "expected.txt", f"{first}\n")
            data_file = self.write(root / "mdb.tar.gz", "data")
            base = self.write(
                root / "medium_dev.conf",
                "[sql]\nscenario=/old\ntest_category=medium\n\n"
                "[sql/cubrid.conf]\ncreate_table_reuseoid=no\n",
            )

            result = self.run_cli(
                root,
                "prepare-config",
                "--suite",
                "medium",
                "--base-conf",
                str(base),
                "--output-conf",
                str(root / "attempt.conf"),
                "--scenario",
                str(scenario),
                "--expected-list",
                str(expected),
                "--data-file",
                str(data_file),
                env=os.environ.copy(),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not match scenario discovery", result.stderr)

    def test_prepare_medium_rejects_a_single_file_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scenario = self.write(root / "medium" / "group" / "cases" / "1001.sql", "select 1;\n")
            expected = self.write(root / "expected.txt", f"{scenario}\n")
            data_file = self.write(root / "mdb.tar.gz", "data")
            base = self.write(
                root / "medium_dev.conf",
                "[sql]\nscenario=/old\ntest_category=medium\n\n"
                "[sql/cubrid.conf]\ncreate_table_reuseoid=no\n",
            )

            result = self.run_cli(
                root,
                "prepare-config",
                "--suite",
                "medium",
                "--base-conf",
                str(base),
                "--output-conf",
                str(root / "attempt.conf"),
                "--scenario",
                str(scenario),
                "--expected-list",
                str(expected),
                "--data-file",
                str(data_file),
                env=os.environ.copy(),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("medium scenario must be a directory", result.stderr)


if __name__ == "__main__":
    unittest.main()
