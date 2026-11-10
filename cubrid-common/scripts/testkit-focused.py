#!/usr/bin/env python3
"""Guard and verify focused native cubrid-testkit runs."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


class CheckError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise CheckError(message)


def command_output(arguments: list[str], *, cwd: Path | None = None) -> str:
    completed = subprocess.run(
        arguments,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        fail(f"command failed ({' '.join(arguments)}): {detail}")
    return completed.stdout.strip()


def required_directory(variable: str) -> Path:
    value = os.environ.get(variable, "")
    if not value:
        fail(f"{variable} is not set by the selected CUBRID worktree environment")
    path = Path(value).resolve()
    if not path.is_dir():
        fail(f"{variable} is not a directory: {path}")
    return path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_testkit() -> Path:
    testkit_name = shutil.which("testkit")
    if testkit_name is None:
        fail(
            "testkit is not on PATH. Install the intended cubrid-testkit revision "
            "manually with go install, then rerun this preflight."
        )
    target = Path(testkit_name).resolve()
    if target.name != "mise":
        return target
    # A mise shim is a symlink to mise itself. Report the binary the shim runs
    # here, not mise; an inactive tool fails instead of falling through PATH.
    real = Path(command_output([str(target), "which", "testkit"])).resolve()
    if not real.is_file():
        fail(f"mise reports a testkit binary that does not exist: {real}")
    return real


KEPT_CUBRID_ENV = {"CUBRID_DATABASES", "CUBRID_TMP", "CUBRID_JAVA_HOME"}
# CUBRID exits when $CUBRID_TMP is longer: socket paths go there (environment_variable.c: 108-byte sun_path minus 12).
CUBRID_TMP_MAX_LENGTH = 108 - 12


def preflight(suite: str, allow_commit_mismatch: bool) -> None:
    testkit = resolve_testkit()
    version = command_output([str(testkit), "--version"])

    try:
        source_root = Path(command_output(["git", "rev-parse", "--show-toplevel"])).resolve()
        source_head = command_output(["git", "-C", str(source_root), "rev-parse", "HEAD"])
    except CheckError as error:
        fail(f"run from inside the intended CUBRID Git worktree: {error}")

    cmake = source_root / "CMakeLists.txt"
    if not cmake.is_file() or not re.search(
        r"(?m)^\s*project\s*\(\s*CUBRID(?:\s|\)|$)",
        cmake.read_text(encoding="utf-8", errors="replace"),
    ):
        fail(f"the current Git worktree is not a CUBRID source tree: {source_root}")

    cubrid = required_directory("CUBRID")
    databases = required_directory("CUBRID_DATABASES")
    ctp_home = required_directory("CTP_HOME")
    if not (ctp_home / "conf").is_dir():
        fail(f"CTP_HOME has no conf directory: {ctp_home}")
    java_home: Path | None = None
    java_version = ""
    if suite in {"sql", "medium"}:
        java_home = required_directory("JAVA_HOME")
        javac = java_home / "bin" / "javac"
        if not javac.is_file() or not os.access(javac, os.X_OK):
            fail(f"JAVA_HOME does not provide executable bin/javac: {java_home}")
        javac_result = subprocess.run(
            [str(javac), "-version"],
            text=True,
            capture_output=True,
            check=False,
        )
        java_version = (javac_result.stdout.strip() or javac_result.stderr.strip()).splitlines()[0]
        if javac_result.returncode != 0 or not re.search(
            r"\bjavac\s+(?:1\.8(?:\.|\b)|8(?:\.|\b))", java_version
        ):
            fail(f"native {suite} requires JDK 8; selected javac reports {java_version!r}")

    if suite in {"sql", "medium"} and not (cubrid / "jdbc" / "cubrid_jdbc.jar").is_file():
        fail(f"native {suite} needs the JDBC driver, but the install has no jdbc/cubrid_jdbc.jar: {cubrid}")

    cubrid_rel = cubrid / "bin" / "cubrid_rel"
    if not cubrid_rel.is_file() or not os.access(cubrid_rel, os.X_OK):
        fail(f"selected CUBRID install has no executable bin/cubrid_rel: {cubrid}")
    relation = command_output([str(cubrid_rel)])
    commit_matches = re.findall(r"-([0-9a-f]{7,40})(?=[)\s])", relation, re.IGNORECASE)
    if not commit_matches:
        fail(f"cannot parse an installed commit from {cubrid_rel}: {relation!r}")
    installed_commit = commit_matches[-1].lower()
    commit_match = source_head.lower().startswith(installed_commit) or installed_commit.startswith(
        source_head.lower()
    )
    if not commit_match and not allow_commit_mismatch:
        fail(
            "source/install commit mismatch: "
            f"source HEAD is {source_head}, installed commit is {installed_commit}. "
            "Stop or rerun only with the user's explicit --allow-commit-mismatch authorization."
        )

    containment_env = os.environ.copy()
    containment_env["TESTKIT_CONTAIN"] = "1"
    contained_help = subprocess.run(
        [str(testkit), "-h"],
        env=containment_env,
        text=True,
        capture_output=True,
        check=False,
    )
    if contained_help.returncode != 0:
        detail = contained_help.stderr.strip() or contained_help.stdout.strip()
        fail(f"testkit containment probe failed: {detail}")

    dirty = bool(command_output(["git", "-C", str(source_root), "status", "--porcelain"]))
    if dirty:
        print(
            f"WARNING: selected CUBRID worktree is dirty: {source_root}",
            file=sys.stderr,
        )
    if not commit_match:
        print(
            "WARNING: proceeding with the explicitly allowed source/install commit mismatch",
            file=sys.stderr,
        )

    facts = {
        "suite": suite,
        "source_root": str(source_root),
        "source_head": source_head,
        "source_dirty": "yes" if dirty else "no",
        "cubrid": str(cubrid),
        "cubrid_databases": str(databases),
        "execution_database_layout": "disposable-inside-cubrid",
        "installed_commit": installed_commit,
        "commit_match": "yes" if commit_match else "no",
        "commit_mismatch_allowed": "yes" if allow_commit_mismatch else "no",
        "ctp_home": str(ctp_home),
        "testkit": str(testkit),
        "testkit_version": version,
        "testkit_sha256": sha256(testkit),
        "containment": "available",
        # CUBRID_CONF_FILE, CUBRID_BROKER_CONF_FILE and CUBRID_<PARAM> point the binaries away from the attempt's conf.
        "env_unset": " ".join(sorted(name for name in os.environ if name.startswith("CUBRID_") and name not in KEPT_CUBRID_ENV)),
    }
    if java_home is not None:
        facts["java_home"] = str(java_home)
        facts["java_version"] = java_version
    for key, value in facts.items():
        print(f"{key}={value}")


def read_required(path: Path, label: str) -> str:
    if not path.is_file():
        fail(f"missing {label}: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


def expected_cases(path: Path) -> list[str]:
    lines = [line.strip() for line in read_required(path, "expected case list").splitlines()]
    cases = [line for line in lines if line and not line.startswith("#")]
    if not cases:
        fail(f"expected case list is empty: {path}")
    if len(cases) != len(set(cases)):
        fail(f"expected case list contains duplicates: {path}")
    if any(not Path(case).is_absolute() for case in cases):
        fail(f"expected case paths must be absolute: {path}")
    return cases


def replace_ini_values(text: str, updates: dict[str, dict[str, str]]) -> str:
    lines = text.splitlines()
    counts: dict[tuple[str, str], int] = {}
    current = ""
    for line in lines:
        section = re.match(r"^\s*\[([^]]+)]\s*$", line)
        if section:
            current = section.group(1).strip()
            continue
        assignment = re.match(r"^\s*([^#;][^=]*?)\s*=", line)
        if assignment and current in updates:
            key = assignment.group(1).strip()
            if key in updates[current]:
                counts[(current, key)] = counts.get((current, key), 0) + 1
    duplicates = [f"[{section}] {key}" for (section, key), count in counts.items() if count > 1]
    if duplicates:
        fail(f"configuration has duplicate focused-run keys: {', '.join(duplicates)}")

    output: list[str] = []
    current = ""
    emitted: set[tuple[str, str]] = set()

    def finish_section(section: str) -> None:
        if section not in updates:
            return
        for key, value in updates[section].items():
            identity = (section, key)
            if identity not in emitted:
                output.append(f"{key}={value}")
                emitted.add(identity)

    for line in lines:
        section = re.match(r"^\s*\[([^]]+)]\s*$", line)
        if section:
            finish_section(current)
            current = section.group(1).strip()
            output.append(line)
            continue
        assignment = re.match(r"^\s*([^#;][^=]*?)\s*=", line)
        if assignment and current in updates:
            key = assignment.group(1).strip()
            if key in updates[current]:
                output.append(f"{key}={updates[current][key]}")
                emitted.add((current, key))
                continue
        output.append(line)
    finish_section(current)

    for section, values in updates.items():
        missing = [(key, value) for key, value in values.items() if (section, key) not in emitted]
        if not missing:
            continue
        if output and output[-1] != "":
            output.append("")
        output.append(f"[{section}]")
        output.extend(f"{key}={value}" for key, value in missing)
    return "\n".join(output) + "\n"


def replace_property_values(text: str, updates: dict[str, str]) -> str:
    lines = text.splitlines()
    counts: dict[str, int] = {}
    for line in lines:
        assignment = re.match(r"^\s*([^#!][^:=]*?)\s*[:=]", line)
        if assignment:
            key = assignment.group(1).strip()
            if key in updates:
                counts[key] = counts.get(key, 0) + 1
    duplicates = [key for key, count in counts.items() if count > 1]
    if duplicates:
        fail(f"configuration has duplicate focused-run keys: {', '.join(duplicates)}")

    output: list[str] = []
    emitted: set[str] = set()
    for line in lines:
        assignment = re.match(r"^\s*([^#!][^:=]*?)\s*[:=]", line)
        if assignment:
            key = assignment.group(1).strip()
            if key in updates:
                output.append(f"{key}={updates[key]}")
                emitted.add(key)
                continue
        output.append(line)
    output.extend(f"{key}={value}" for key, value in updates.items() if key not in emitted)
    return "\n".join(output) + "\n"


@dataclass(frozen=True)
class Selection:
    scenario: Path
    cases: tuple[Path, ...]


def artifact_path(path: Path) -> Path:
    path = Path(os.path.abspath(path))
    value = str(path)
    if any(c in value for c in "\r\n\x00") or value != value.strip() or "\\" in value:
        fail(f"path cannot be represented in an artifact: {path!r}")
    return path


def select_cases(suite: str, scenario: Path, selected: Path) -> Selection:
    scenario = artifact_path(scenario)
    selected = artifact_path(selected)
    if not scenario.is_dir():
        fail(f"scenario must be a directory: {scenario}")
    scenario_real = scenario.resolve(strict=True)
    try:
        selected_real = selected.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        fail(f"selection cannot be resolved: {selected}: {error}")
    if not selected_real.is_relative_to(scenario_real):
        fail(f"selection is outside scenario: {selected}")
    if suite == "shell":
        if scenario.is_symlink():
            fail(f"shell scenario must not be a symlink: {scenario}")
        if not selected.is_relative_to(scenario):
            fail(f"shell selection must be under the lexical scenario: {selected}")
        path = scenario
        for part in selected.relative_to(scenario).parts:
            path = path / part
            if path.is_symlink():
                fail(f"shell selection contains a symlink: {path}")
    relative_parts = selected_real.relative_to(scenario_real).parts
    lexical_parts = selected.relative_to(scenario).parts if selected.is_relative_to(scenario) else ()
    if suite in {"sql", "medium"} and any(
        part in {"common", "answers"} for part in (*relative_parts, *lexical_parts)
    ):
        fail(f"selection is in an excluded directory: {selected}")
    if suite == "medium":
        if not selected.is_dir() or "cases" in relative_parts:
            fail(f"medium selection must be a whole group directory: {selected}")
        if not (selected / "cases").is_dir() or not (selected / "answers").is_dir():
            fail(f"medium group must contain cases and answers: {selected}")

    found: list[Path] = []

    def walk(path: Path, ancestors: frozenset[Path]) -> None:
        artifact_path(path)
        if suite == "shell" and path.is_symlink():
            return
        try:
            real = path.resolve(strict=True)
            if not real.is_relative_to(scenario_real) or not real.is_relative_to(selected_real):
                fail(f"discovered path escapes selected scope: {path}")
            if path.is_dir():
                if real in ancestors:
                    fail(f"directory cycle: {path}")
                entries = list(path.iterdir())
                if suite == "shell":
                    entries.sort(key=lambda entry: entry.name)
                else:
                    entries.sort(key=lambda entry: entry.name.encode("utf-16-be"))
                for child in entries:
                    if (
                        suite != "shell"
                        and child.name in {"common", "answers"}
                        and child.is_dir()
                    ):
                        continue
                    walk(child, ancestors | {real})
            elif path.is_file():
                if suite == "shell":
                    if (
                        path.parent.name == "cases"
                        and path.suffix == ".sh"
                        and path.name == path.parent.parent.name + ".sh"
                    ):
                        found.append(path)
                elif path.name.endswith(".sql"):
                    directory = str(path.parent)
                    index = directory.rfind("cases")
                    if index >= 0:
                        directory = directory[:index] + "answers"
                    answer = Path(directory) / (path.name.split(".")[0] + ".answer")
                    artifact_path(answer)
                    answer_real = answer.resolve(strict=True)
                    if not answer_real.is_relative_to(scenario_real) or not answer.is_file():
                        fail(f"missing or outside base answer for {path}: {answer}")
                    found.append(path)
        except (OSError, RuntimeError, UnicodeError) as error:
            fail(f"cannot inspect {path}: {error}")

    walk(selected, frozenset())
    if not found:
        fail(f"selection contains no cases: {selected}")
    if suite == "shell":
        found.sort(key=str)
    return Selection(scenario if suite == "shell" else selected, tuple(found))


def prepare_config(
    suite: str,
    base_conf: Path,
    output_conf: Path,
    scenario: Path,
    selection: Path,
    output_expected_list: Path,
    data_file: Path | None,
) -> None:
    base_conf = artifact_path(base_conf)
    output_conf = artifact_path(output_conf)
    output_expected_list = artifact_path(output_expected_list)
    scenario = artifact_path(scenario)
    selection = artifact_path(selection)
    if data_file is not None:
        data_file = artifact_path(data_file)
    base_text = read_required(base_conf, "base configuration")
    selected = select_cases(suite, scenario, selection)
    inputs = [base_conf, scenario, selection, *selected.cases]
    if data_file is not None:
        inputs.append(data_file)
    outputs = [output_expected_list, output_conf]
    if output_conf.resolve() == output_expected_list.resolve():
        fail("output paths must differ")
    attempt_tmp = output_conf.resolve().parent.parent / "cubrid" / "tmp"
    if len(str(attempt_tmp)) > CUBRID_TMP_MAX_LENGTH:
        fail(
            f"attempt CUBRID_TMP would be {len(str(attempt_tmp))} characters ({attempt_tmp}); "
            f"CUBRID accepts at most {CUBRID_TMP_MAX_LENGTH}. Use a shorter attempt root."
        )
    for output in outputs:
        if output.resolve().is_relative_to(scenario.resolve()):
            fail(f"output is inside scenario: {output}")
        if os.path.lexists(output):
            fail(f"refusing to overwrite retained attempt output: {output}")
        if any(output.resolve() == item.resolve() for item in inputs):
            fail(f"output collides with input: {output}")
    if suite in {"sql", "medium"}:
        sql_updates = {
            "parallel_slots": "1",
            "scenario": str(selected.scenario),
            "enable_memory_leak": "no",
            "testcase_exclude_from_file": "",
            "test_category": suite,
        }
        updates = {"sql": sql_updates}
        if suite == "medium":
            if data_file is None or not data_file.is_file():
                fail("medium requires an existing --data-file")
            sql_updates["data_file"] = str(data_file)
            updates["sql/cubrid.conf"] = {"create_table_reuseoid": "no"}
        elif data_file is not None:
            fail("--data-file applies only to medium")
        rendered = replace_ini_values(base_text, updates)
    else:
        if data_file is not None:
            fail("--data-file applies only to medium")
        rendered = replace_property_values(
            base_text,
            {
                "scenario": str(selected.scenario),
                "parallel_slots": "1",
                "scenario_disk": "on",
                "scenario_ram_mb": "",
                "testcase_workspace_dir": "",
                "testcase_from_file": str(output_expected_list),
                "testcase_exclude_from_file": "",
                "testcase_update_yn": "false",
                "testcase_retry_num": "0",
                "test_continue_yn": "false",
                "test_category": "shell",
                "feedback_type": "file",
            },
        )
    expected_text = "".join(f"{case}\n" for case in selected.cases)
    expected_text.encode("utf-8")
    rendered.encode("utf-8")
    for output, content in ((output_expected_list, expected_text), (output_conf, rendered)):
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as stream:
            stream.write(content)
    print(f"suite={suite}")
    print(f"config={output_conf}")
    print(f"config_sha256={sha256(output_conf)}")
    print(f"expected_list={output_expected_list}")
    print(f"expected_list_sha256={sha256(output_expected_list)}")
    print(f"case_count={len(selected.cases)}")
    if data_file is not None:
        print(f"data_file={data_file}")
        print(f"data_file_sha256={sha256(data_file)}")


def count_value(text: str, key: str, separator: str) -> int:
    pattern = rf"(?m)^{re.escape(key)}{re.escape(separator)}([0-9]+)\s*$"
    match = re.search(pattern, text)
    if match is None:
        fail(f"summary is incomplete; missing {key}{separator}<count>")
    return int(match.group(1))


def verify_xml(path: Path, expected: int, *, require_skipped: bool = False) -> None:
    read_required(path, "XML result")
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as error:
        fail(f"invalid XML result {path}: {error}")
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    if not suites:
        fail(f"XML result has no testsuite: {path}")
    tests = sum(int(suite.attrib.get("tests", "0")) for suite in suites)
    failures = sum(int(suite.attrib.get("failures", "0")) for suite in suites)
    errors = sum(int(suite.attrib.get("errors", "0")) for suite in suites)
    if require_skipped and any("skipped" not in suite.attrib for suite in suites):
        fail(f"XML result is incomplete; missing skipped count: {path}")
    skipped = sum(int(suite.attrib.get("skipped", "0")) for suite in suites)
    if tests != expected or failures != 0 or errors != 0 or skipped != 0:
        fail(
            f"XML result is not a complete pass: tests={tests}, failures={failures}, "
            f"errors={errors}, skipped={skipped}, expected={expected} ({path})"
        )


def verify_sql_summary_xml(path: Path, expected: int) -> None:
    read_required(path, "summary.xml")
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as error:
        fail(f"invalid summary.xml {path}: {error}")
    scenarios = list(root.findall("scenario"))
    verdicts = [(scenario.findtext("result") or "").strip() for scenario in scenarios]
    if len(scenarios) != expected or any(verdict != "success" for verdict in verdicts):
        fail(
            f"summary.xml is not a complete pass: scenarios={len(scenarios)}, "
            f"verdicts={verdicts!r}, expected={expected} ({path})"
        )


def verify_sql_like(
    suite: str, result_dir: Path, cases: list[str], run_log: str, runner_exit: int
) -> None:
    summary = read_required(result_dir / "summary_info", "root summary_info")
    main_info = read_required(result_dir / "main.info", "main.info")
    junit = sorted(result_dir.glob(f"linux_{suite}_*.xml"))
    if len(junit) != 1:
        fail(f"expected exactly one linux_{suite}_*.xml result in {result_dir}")

    total = count_value(summary, "total", ":")
    success = count_value(summary, "success", ":")
    failures = count_value(summary, "fail", ":")
    if "test_error=Y" in summary:
        fail("summary_info reports test_error=Y")
    if total != len(cases):
        fail(f"total count is {total}, expected {len(cases)}")
    if failures != 0:
        fail(f"fail count is {failures} even though runner exit was {runner_exit}")
    if success != total:
        fail(f"success count is {success}, total is {total}")

    main_total = count_value(main_info, "total", ":")
    main_executed = count_value(main_info, "execute_case", ":")
    main_success = count_value(main_info, "success", ":")
    main_failures = count_value(main_info, "fail", ":")
    if main_failures != 0:
        fail(f"main.info fail count is {main_failures}")
    if (main_total, main_executed, main_success) != (total, total, success):
        fail(
            "main.info counts disagree with summary_info: "
            f"total={main_total}, executed={main_executed}, success={main_success}"
        )
    category = re.search(r"(?m)^category:(.*)$", main_info)
    if category is None or category.group(1).strip() != suite:
        fail(f"main.info category is not {suite}")
    result_path = re.search(r"(?m)^result_path:(.*)$", main_info)
    if result_path is None or Path(result_path.group(1).strip()).resolve() != result_dir.resolve():
        fail("main.info result_path does not identify this result directory")

    log_total = count_value(run_log, "Total", ":")
    log_success = count_value(run_log, "Success", ":")
    log_failures = count_value(run_log, "Fail", ":")
    if (log_total, log_success, log_failures) != (total, success, 0):
        fail(
            "run log counts disagree with summary_info: "
            f"total={log_total}, success={log_success}, fail={log_failures}"
        )

    verify_sql_summary_xml(result_dir / "summary.xml", len(cases))
    verify_xml(junit[0], len(cases))

    actual: list[str] = []
    verdicts: list[str] = []
    for summary_path in sorted(result_dir.rglob("summary_info")):
        for line in read_required(summary_path, "summary_info").splitlines():
            match = re.match(r"^(.+\.sql):(ok|nok)(?:\s|$)", line, re.IGNORECASE)
            if match:
                actual.append(match.group(1))
                verdicts.append(match.group(2).lower())
    if actual != cases:
        fail(f"executed case identities differ from expected: actual={actual!r}, expected={cases!r}")
    if any(verdict != "ok" for verdict in verdicts):
        fail(f"case verdicts are not all OK: {verdicts!r}")
    for case in cases:
        result = Path(case).with_suffix(".result")
        if not result.is_file():
            fail(f"missing generated testcase result: {result}")

    marker = f"[{suite.upper()}] TEST END"
    if marker not in run_log or "Result Root Dir:" not in run_log:
        fail(f"run log lacks the completed {suite} markers")


def parse_shell_status(text: str) -> dict[str, int]:
    names = (
        "total_case_count",
        "total_executed_case_count",
        "total_success_case_count",
        "total_fail_case_count",
        "total_skip_case_count",
    )
    return {name: count_value(text, name, "=") for name in names}


def verify_shell(
    result_dir: Path, cases: list[str], run_log: str, runner_exit: int
) -> None:
    status = parse_shell_status(
        read_required(result_dir / "test_status.data", "test_status.data")
    )
    expected = len(cases)
    if status["total_case_count"] != expected:
        fail(f"total case count is {status['total_case_count']}, expected {expected}")
    if status["total_executed_case_count"] != expected:
        fail(
            f"executed case count is {status['total_executed_case_count']}, expected {expected}"
        )
    if status["total_fail_case_count"] != 0:
        fail(
            f"fail count is {status['total_fail_case_count']} even though runner exit was {runner_exit}"
        )
    if status["total_skip_case_count"] != 0:
        fail(f"skip count is {status['total_skip_case_count']}")
    if status["total_success_case_count"] != expected:
        fail(f"success count is {status['total_success_case_count']}, expected {expected}")

    dispatched = [
        line.strip()
        for line in read_required(result_dir / "dispatch_tc_ALL.txt", "dispatch list").splitlines()
        if line.strip()
    ]
    if dispatched != cases:
        fail(f"dispatched case identities differ from expected: {dispatched!r}")
    finished: list[str] = []
    for path in sorted(result_dir.glob("dispatch_tc_FIN_*.txt")):
        finished.extend(line.strip() for line in read_required(path, "finished list").splitlines() if line.strip())
    if sorted(finished) != sorted(cases):
        fail(f"finished case identities differ from expected: {finished!r}")

    feedback = read_required(result_dir / "feedback.log", "feedback.log")
    read_required(result_dir / "main_snapshot.properties", "main_snapshot.properties")
    logs = sorted(result_dir.glob("test_*.log"))
    if not logs:
        fail(f"missing per-environment test log in {result_dir}")
    if "[TEST STOP]" not in feedback:
        fail("feedback.log has no complete final summary")
    feedback_counts = {
        "total": count_value(feedback, "Total Case", ":"),
        "executed": count_value(feedback, "Total Execution Case", ":"),
        "success": count_value(feedback, "Total Success Case", ":"),
        "fail": count_value(feedback, "Total Fail Case", ":"),
        "skip": count_value(feedback, "Total Skip Case", ":"),
    }
    if feedback_counts["fail"] != 0:
        fail(f"feedback fail count is {feedback_counts['fail']}")
    if feedback_counts != {
        "total": expected,
        "executed": expected,
        "success": expected,
        "fail": 0,
        "skip": 0,
    }:
        fail(f"feedback summary counts disagree with test_status.data: {feedback_counts!r}")
    for log in logs:
        if re.search(r"\bNOK\b", read_required(log, "per-environment test log")):
            fail(f"per-environment test log contains NOK: {log}")
    for case in cases:
        if not re.search(rf"(?m)^\[OK\]:\s+{re.escape(case)}(?:\s|$)", feedback):
            fail(f"feedback.log has no OK verdict for {case}")
    verify_xml(result_dir / "test-shell.xml", expected, require_skipped=True)
    if "[SHELL] TEST END" not in run_log:
        fail("run log lacks the completed shell marker")
    run_counts = {
        "executed": count_value(run_log, "Total Execution Case", ":"),
        "success": count_value(run_log, "Total Success Case", ":"),
        "fail": count_value(run_log, "Total Fail Case", ":"),
        "skip": count_value(run_log, "Total Skip Case", ":"),
    }
    if run_counts != {"executed": expected, "success": expected, "fail": 0, "skip": 0}:
        fail(f"run log summary counts disagree with test_status.data: {run_counts!r}")


def verify(
    suite: str,
    result_dir: Path,
    expected_list: Path,
    run_log_path: Path,
    runner_exit: int,
) -> None:
    cases = expected_cases(expected_list)
    if runner_exit != 0:
        fail(f"testkit runner exit was {runner_exit}; setup or execution did not complete")
    if not result_dir.is_dir():
        fail(f"result directory does not exist: {result_dir}")
    run_log = read_required(run_log_path, "run log")
    if suite in {"sql", "medium"}:
        verify_sql_like(suite, result_dir, cases, run_log, runner_exit)
    elif suite == "shell":
        verify_shell(result_dir, cases, run_log, runner_exit)
    else:
        fail(f"unsupported suite: {suite}")
    print(f"suite={suite}")
    print(f"total={len(cases)}")
    print(f"success={len(cases)}")
    print("fail=0")
    print(f"result_dir={result_dir.resolve()}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    preflight_parser = subparsers.add_parser("preflight")
    preflight_parser.add_argument("--suite", required=True, choices=("sql", "medium", "shell"))
    preflight_parser.add_argument("--allow-commit-mismatch", action="store_true")
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--suite", required=True, choices=("sql", "medium", "shell"))
    verify_parser.add_argument("--result-dir", required=True, type=Path)
    verify_parser.add_argument("--expected-list", required=True, type=Path)
    verify_parser.add_argument("--run-log", required=True, type=Path)
    verify_parser.add_argument("--runner-exit", required=True, type=int)
    config_parser = subparsers.add_parser("prepare-config")
    config_parser.add_argument("--suite", required=True, choices=("sql", "medium", "shell"))
    config_parser.add_argument("--base-conf", required=True, type=Path)
    config_parser.add_argument("--output-conf", required=True, type=Path)
    config_parser.add_argument("--scenario", required=True, type=Path)
    config_parser.add_argument("--selection", required=True, type=Path)
    config_parser.add_argument("--output-expected-list", required=True, type=Path)
    config_parser.add_argument("--data-file", type=Path)
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        if arguments.command == "preflight":
            preflight(arguments.suite, arguments.allow_commit_mismatch)
        elif arguments.command == "verify":
            verify(
                arguments.suite,
                arguments.result_dir,
                arguments.expected_list,
                arguments.run_log,
                arguments.runner_exit,
            )
        elif arguments.command == "prepare-config":
            prepare_config(
                arguments.suite,
                arguments.base_conf,
                arguments.output_conf,
                arguments.scenario,
                arguments.selection,
                arguments.output_expected_list,
                arguments.data_file,
            )
        else:
            fail(f"unsupported command: {arguments.command}")
    except (CheckError, OSError, UnicodeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
