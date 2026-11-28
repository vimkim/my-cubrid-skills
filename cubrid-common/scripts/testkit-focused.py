#!/usr/bin/env python3
"""Guard and verify focused native cubrid-testkit runs."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
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

# Helpers defined in CTP/shell/init_path/init.sh (excluding bare `init`, which is ambiguous with OS init).
KNOWN_SHELL_INIT_HELPERS: frozenset[str] = frozenset(
    {
        "wait_until",
        "diff_ignore_lineno",
        "write_ok",
        "write_nok",
        "finish",
        "xkill",
        "xkill_pid",
        "xkill_java_windows",
        "change_parameter",
        "change_db_parameter",
        "change_db_section_parameter",
        "change_config_section_parameter",
        "change_broker_parameter",
        "change_ha_parameter",
        "change_broker_section_parameter",
        "change_gateway_section_parameter",
        "change_ha_section_parameter",
        "restore_broker_conf",
        "restore_gateway_conf",
        "restore_ha_conf",
        "restore_db_conf",
        "restore_all_conf",
        "delete_ini",
        "exec_sql",
        "test_exec_sql",
        "test_exec_command",
        "db_status",
        "compare_result_between_files",
        "make_answer_or_compare_result",
        "get_broker_port_from_shell_config",
        "get_cubrid_port_id",
        "generate_port",
        "get_curr_second",
        "get_curr_seconds",
        "get_curr_min",
        "get_curr_hour",
        "release_broker_sharedmemory",
        "count_time",
        "get_codeset",
        "get_language",
        "get_comment",
        "is32bit",
        "format_csql_output",
        "format_query_plan",
        "format_path_output",
        "remove_space_character",
        "format_number_output",
        "format_instance_oid_output",
        "format_tran_index_lockdb_output",
        "set_CUBRID_CHARSET",
        "setENVParam",
        "recoverENVParam",
        "unsetENVParam",
        "do_make_locale",
        "delete_make_locale",
        "backup_tz",
        "do_make_tz",
        "revert_tz",
        "get_bit_ver",
        "xgcc",
        "cas_info_replace",
        "get_csql_execution_time",
        "parse_build_version",
        "format_cubrid_version",
        "cubrid_createdb",
        "search_in_upper_path",
        "create_ccidb",
        "WINDOWS_NOT_SUPPORTED",
        "LINUX_NOT_SUPPORTED",
        "AIX_NOT_SUPPORTED",
        "get_os",
        "pick_test_compat_version",
        "version_convert_to_number",
        "get_best_compat_file",
        "get_win_service_pid",
    }
)

HEREDOC_START_RE = re.compile(
    r"<<(-?)\s*(?:'([^']+)'|\"([^\"]+)\"|\\?([A-Za-z_][A-Za-z0-9_]*))"
)
SHELL_FUNC_RE = re.compile(
    r"^\s*(?:function\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s*\(\s*\))?"
    r"|([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\))(?:\s*\{|\s*$)",
    re.MULTILINE,
)
SHELL_CMD_CALL_RE = re.compile(
    r"(?:^|[;&|({`)])"
    r"(?:\s*(?:!|if|elif|then|else|do|while|until|time)\b|\s*[A-Za-z_][A-Za-z0-9_]*=\S*)*"
    r"\s*([A-Za-z_][A-Za-z0-9_]*)(?=$|[\s;&|)`}])",
    re.MULTILINE,
)


def strip_shell_heredocs_and_comments(text: str) -> str:
    """Drop heredoc bodies, comments, and string interiors while preserving command structure."""
    logical_lines: list[str] = []
    current_parts: list[str] = []
    heredocs: list[tuple[str, bool]] = []
    in_single = False
    in_double = False

    for raw_line in text.splitlines():
        if heredocs:
            delim, strip_tabs = heredocs[0]
            candidate = raw_line.lstrip("\t") if strip_tabs else raw_line
            if candidate == delim:
                heredocs.pop(0)
            continue

        out: list[str] = []
        line_continued = False
        i = 0
        n = len(raw_line)
        while i < n:
            ch = raw_line[i]
            if in_single:
                if ch == "'":
                    in_single = False
                    out.append("'")
                i += 1
                continue
            if in_double:
                if ch == "\\":
                    i += 2
                    continue
                if ch == '"':
                    in_double = False
                    out.append('"')
                i += 1
                continue
            if ch == "\\":
                if i + 1 == n:
                    line_continued = True
                    break
                out.append(ch)
                out.append(raw_line[i + 1])
                i += 2
                continue
            if ch == "'":
                in_single = True
                out.append("'")
                i += 1
                continue
            if ch == '"':
                in_double = True
                out.append('"')
                i += 1
                continue
            if ch == "#" and (i == 0 or raw_line[i - 1] in " \t;&|({`"):
                break
            if ch == "<" and i + 1 < n and raw_line[i + 1] == "<":
                if i + 2 < n and raw_line[i + 2] == "<":
                    out.append("<<<")
                    i += 3
                    continue
                match = HEREDOC_START_RE.match(raw_line, i)
                if match:
                    strip_tabs = bool(match.group(1))
                    delim = match.group(2) or match.group(3) or match.group(4) or ""
                    heredocs.append((delim, strip_tabs))
                    out.append(" ")
                    i = match.end()
                    continue
            out.append(ch)
            i += 1

        current_parts.append("".join(out))
        if line_continued:
            current_parts.append(" ")
        else:
            logical_lines.append("".join(current_parts))
            current_parts.clear()

    if current_parts:
        logical_lines.append("".join(current_parts))
    return "\n".join(logical_lines)


def parse_shell_functions(text: str) -> set[str]:
    """Return function names declared in a shell script outside comments and heredocs."""
    stripped = strip_shell_heredocs_and_comments(text)
    names: set[str] = set()
    for match in SHELL_FUNC_RE.finditer(stripped):
        name = match.group(1) or match.group(2)
        if name:
            names.add(name)
    return names


def find_command_calls(stripped_text: str) -> set[str]:
    """Return command-position identifiers from already-stripped shell code."""
    return {match.group(1) for match in SHELL_CMD_CALL_RE.finditer(stripped_text)}


def inspect_ctp_git(ctp_home: Path, *, exclude_root: Path | None = None) -> dict[str, object]:
    """Inspect a git-backed CTP_HOME offline without triggering network fetches."""
    probe = subprocess.run(
        ["git", "-C", str(ctp_home), "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        check=False,
    )
    if probe.returncode != 0:
        return {}
    git_root = Path(probe.stdout.strip()).resolve()
    if exclude_root is not None and git_root == exclude_root.resolve():
        return {}

    head = command_output(["git", "-C", str(git_root), "rev-parse", "HEAD"])
    status_output = command_output(["git", "-C", str(git_root), "status", "--porcelain"])
    dirty_lines = [line for line in status_output.splitlines() if line.strip()]
    info: dict[str, object] = {
        "git_root": git_root,
        "head": head,
        "dirty": bool(dirty_lines),
        "dirty_count": len(dirty_lines),
    }

    origin_probe = subprocess.run(
        ["git", "-C", str(git_root), "rev-parse", "--verify", "--quiet", "refs/remotes/origin/develop"],
        text=True,
        capture_output=True,
        check=False,
    )
    if origin_probe.returncode == 0:
        origin_develop = origin_probe.stdout.strip()
        behind_count = int(
            command_output(
                ["git", "-C", str(git_root), "rev-list", "--count", "HEAD..refs/remotes/origin/develop"]
            )
        )
        info["origin_develop"] = origin_develop
        info["behind_origin_develop"] = behind_count
        init_show = subprocess.run(
            ["git", "-C", str(git_root), "show", "refs/remotes/origin/develop:CTP/shell/init_path/init.sh"],
            text=True,
            capture_output=True,
            check=False,
        )
        if init_show.returncode == 0:
            info["origin_init_helpers"] = parse_shell_functions(init_show.stdout)
    return info


def discover_shell_cases(selection: Path) -> tuple[Path, ...]:
    """Resolve a shell case file or directory subtree to concrete <name>/cases/<name>.sh files."""
    if not selection.exists():
        fail(f"shell selection does not exist: {selection}")
    resolved = selection.resolve()
    if resolved.is_file():
        if resolved.suffix != ".sh":
            fail(f"shell selection must be a .sh case or directory: {selection}")
        return (resolved,)
    if not resolved.is_dir():
        fail(f"shell selection must be a .sh case or directory: {selection}")

    cases: list[Path] = []
    for candidate in resolved.rglob("*.sh"):
        if (
            candidate.is_file()
            and candidate.parent.name == "cases"
            and candidate.name == candidate.parent.parent.name + ".sh"
        ):
            cases.append(candidate.resolve())
    cases.sort(key=str)
    if not cases:
        fail(f"shell selection contains no cases: {selection}")
    return tuple(cases)


def verify_shell_init_helpers(
    ctp_home: Path,
    cases: Sequence[Path],
    *,
    extra_known: set[str] | None = None,
) -> None:
    """Fail if selected shell cases invoke CTP init.sh helpers missing from this CTP_HOME."""
    init_sh = ctp_home / "shell" / "init_path" / "init.sh"
    defined = (
        parse_shell_functions(init_sh.read_text(encoding="utf-8", errors="replace"))
        if init_sh.is_file()
        else set()
    )
    catalog = KNOWN_SHELL_INIT_HELPERS | (extra_known or set())
    missing_by_helper: dict[str, list[Path]] = {}

    for case in cases:
        case_text = case.read_text(encoding="utf-8", errors="replace")
        local_funcs = parse_shell_functions(case_text)
        if case.parent.is_dir():
            for sibling in case.parent.iterdir():
                if sibling != case and sibling.is_file() and sibling.suffix == ".sh":
                    local_funcs |= parse_shell_functions(
                        sibling.read_text(encoding="utf-8", errors="replace")
                    )
        called = find_command_calls(strip_shell_heredocs_and_comments(case_text))
        needed = (called & catalog) - local_funcs
        for helper in sorted(needed):
            if helper not in defined:
                missing_by_helper.setdefault(helper, []).append(case)

    if not missing_by_helper:
        return

    details = "; ".join(
        f"{helper} (called by {', '.join(str(p) for p in paths)})"
        for helper, paths in sorted(missing_by_helper.items())
    )
    if not init_sh.is_file():
        fail(
            f"CTP_HOME lacks shell/init_path/init.sh needed by selected shell case(s): {details}. "
            f"Point CTP_HOME to a current clean cubrid-testtools/CTP checkout and rerun."
        )
    fail(
        f"CTP init.sh ({init_sh}) lacks shell helper(s) called by selected case(s): {details}. "
        f"Update or repoint CTP_HOME to a current clean cubrid-testtools/CTP checkout and rerun."
    )


CRASH_QUARANTINE_DIR = "crash-quarantine"


def find_crash_artifacts(cubrid: Path) -> list[Path]:
    """Return install-relative crash artifacts that testkit would report as the case's crash.

    testkit reads every file in $CUBRID/log/coredump as a server crash report and every
    core / core.* file under $CUBRID (except the engine's core.log) as a core dump.
    """
    found: list[Path] = []
    for directory, subdirectories, files in os.walk(cubrid):
        subdirectories.sort()
        relative_directory = Path(directory).relative_to(cubrid)
        in_coredump = relative_directory.parts[:2] == ("log", "coredump")
        for name in sorted(files):
            path = Path(directory) / name
            if path.is_symlink() or not path.is_file():
                continue
            lowered = name.lower()
            is_core = lowered == "core" or (lowered.startswith("core.") and lowered != "core.log")
            if in_coredump or is_core:
                found.append(relative_directory / name)
    return found


def quarantine_crash_artifacts(attempt_dir: Path) -> None:
    """Move crash artifacts out of the attempt's disposable install copy; never delete them."""
    attempt_dir = artifact_path(attempt_dir)
    attempt_cubrid = attempt_dir / "cubrid"
    if not attempt_cubrid.is_dir() or attempt_cubrid.is_symlink():
        fail(f"attempt has no copied CUBRID install at {attempt_cubrid}; copy $CUBRID there first")
    source_cubrid = os.environ.get("CUBRID", "")
    if source_cubrid and Path(source_cubrid).resolve() == attempt_cubrid.resolve():
        fail(f"refusing to quarantine inside $CUBRID itself ({attempt_cubrid}); pass the attempt copy")
    quarantine = attempt_dir / CRASH_QUARANTINE_DIR
    artifacts = find_crash_artifacts(attempt_cubrid)
    for relative in artifacts:
        if os.path.lexists(quarantine / relative):
            fail(f"refusing to overwrite quarantined crash artifact: {quarantine / relative}")
    for relative in artifacts:
        target = quarantine / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        os.rename(attempt_cubrid / relative, target)
    print(f"attempt_cubrid={attempt_cubrid}")
    print(f"crash_artifacts_quarantined={len(artifacts)}")
    if artifacts:
        print(f"crash_quarantine_dir={quarantine}")
        print(f"crash_artifacts={' '.join(str(path) for path in artifacts)}")


def preflight(suite: str, allow_commit_mismatch: bool, selection: Path | None = None) -> None:
    if selection is not None and suite != "shell":
        fail("--selection applies only to shell preflight")
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
    # Every suite needs JDK 8: shell cases start the PL server too, and the run shell exports
    # JAVA_HOME from the java_home= line printed here.
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
    java_version = ((javac_result.stdout.strip() or javac_result.stderr.strip()).splitlines() or [""])[0]
    if javac_result.returncode != 0 or not re.search(
        r"\bjavac\s+(?:1\.8(?:\.|\b)|8(?:\.|\b))", java_version
    ):
        fail(f"native {suite} requires JDK 8; selected javac reports {java_version!r}")

    # The run keeps CUBRID_JAVA_HOME, and the PL server starts from it. A JDK newer than 8
    # fails at server start ("PL server can not be started"), so stop here instead.
    cubrid_java_home = os.environ.get("CUBRID_JAVA_HOME", "")
    cubrid_java_version = ""
    if cubrid_java_home:
        java = Path(cubrid_java_home) / "bin" / "java"
        if not java.is_file() or not os.access(java, os.X_OK):
            fail(f"CUBRID_JAVA_HOME does not provide executable bin/java: {cubrid_java_home}")
        java_result = subprocess.run([str(java), "-version"], text=True, capture_output=True, check=False)
        cubrid_java_version = ((java_result.stderr.strip() or java_result.stdout.strip()).splitlines() or [""])[0]
        if java_result.returncode != 0 or not re.search(r'version\s+"1\.8[."]', cubrid_java_version):
            fail(
                f"CUBRID_JAVA_HOME must be Java 8 for the PL server; it reports {cubrid_java_version!r} "
                f"({cubrid_java_home}). Point CUBRID_JAVA_HOME at a Java 8 install and rerun."
            )

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

    source_crash_artifacts = find_crash_artifacts(cubrid)
    if source_crash_artifacts:
        print(
            f"WARNING: source CUBRID install holds {len(source_crash_artifacts)} crash artifact(s) "
            "that a copied install would attribute to the testcase; run quarantine-crash-artifacts "
            f"on the attempt copy ({', '.join(str(path) for path in source_crash_artifacts)}): {cubrid}",
            file=sys.stderr,
        )

    ctp_git = inspect_ctp_git(ctp_home, exclude_root=source_root)
    if ctp_git.get("dirty"):
        print(
            f"WARNING: CTP_HOME checkout is dirty ({ctp_git['dirty_count']} path(s)): {ctp_git['git_root']}",
            file=sys.stderr,
        )
    behind_origin = ctp_git.get("behind_origin_develop")
    if isinstance(behind_origin, int) and behind_origin > 0:
        head_short = str(ctp_git["head"])[:7]
        origin_short = str(ctp_git["origin_develop"])[:7]
        print(
            f"WARNING: CTP_HOME is {behind_origin} commit(s) behind origin/develop "
            f"({head_short} vs {origin_short}): {ctp_git['git_root']}",
            file=sys.stderr,
        )

    origin_init_helpers: set[str] = set()
    raw_origin_helpers = ctp_git.get("origin_init_helpers")
    if isinstance(raw_origin_helpers, set):
        origin_init_helpers = raw_origin_helpers

    ctp_init_has_wait_until: str | None = None
    ctp_init_missing_helpers: list[str] = []
    ctp_shell_helpers_checked = False
    if suite == "shell":
        init_sh = ctp_home / "shell" / "init_path" / "init.sh"
        if init_sh.is_file():
            defined_helpers = parse_shell_functions(init_sh.read_text(encoding="utf-8", errors="replace"))
            ctp_init_has_wait_until = "yes" if "wait_until" in defined_helpers else "no"
            ctp_init_missing_helpers = sorted(({"wait_until"} | origin_init_helpers) - defined_helpers)
            if ctp_init_missing_helpers:
                print(
                    "WARNING: CTP_HOME init.sh lacks helper(s) present in newer CTP "
                    f"({', '.join(ctp_init_missing_helpers)}): {init_sh}",
                    file=sys.stderr,
                )
        if selection is not None:
            cases = discover_shell_cases(selection)
            verify_shell_init_helpers(ctp_home, cases, extra_known=origin_init_helpers)
            ctp_shell_helpers_checked = True

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
        "source_crash_artifacts": str(len(source_crash_artifacts)),
        # CUBRID_CONF_FILE, CUBRID_BROKER_CONF_FILE and CUBRID_<PARAM> point the binaries away from the attempt's conf.
        "env_unset": " ".join(sorted(name for name in os.environ if name.startswith("CUBRID_") and name not in KEPT_CUBRID_ENV)),
    }
    if ctp_git:
        facts["ctp_git_root"] = str(ctp_git["git_root"])
        facts["ctp_head"] = str(ctp_git["head"])
        facts["ctp_dirty"] = "yes" if ctp_git["dirty"] else "no"
        if isinstance(behind_origin, int):
            facts["ctp_behind_origin_develop"] = str(behind_origin)
    if ctp_init_has_wait_until is not None:
        facts["ctp_init_has_wait_until"] = ctp_init_has_wait_until
    if ctp_init_missing_helpers:
        facts["ctp_init_missing_helpers"] = " ".join(ctp_init_missing_helpers)
    if ctp_shell_helpers_checked:
        facts["ctp_shell_helpers_checked"] = "yes"
    facts["java_home"] = str(java_home)
    facts["java_version"] = java_version
    if cubrid_java_home:
        facts["cubrid_java_home"] = cubrid_java_home
        facts["cubrid_java_version"] = cubrid_java_version
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
    attempt_root = output_conf.resolve().parent.parent
    attempt_tmp = attempt_root / "cubrid" / "tmp"
    if len(str(attempt_tmp)) > CUBRID_TMP_MAX_LENGTH:
        fail(
            f"attempt CUBRID_TMP would be {len(str(attempt_tmp))} characters ({attempt_tmp}); "
            f"CUBRID accepts at most {CUBRID_TMP_MAX_LENGTH}. Use a shorter attempt root."
        )
    attempt_cubrid = attempt_root / "cubrid"
    if attempt_cubrid.is_dir():
        leftover = find_crash_artifacts(attempt_cubrid)
        if leftover:
            fail(
                f"attempt CUBRID copy holds crash artifact(s) from earlier runs "
                f"({', '.join(str(path) for path in leftover)}): {attempt_cubrid}. "
                "testkit would attribute them to this testcase; run quarantine-crash-artifacts first."
            )
    if suite == "shell":
        # Shell testkit appends to fixed files in <CTP_HOME>/result/shell/current_runtime_logs,
        # so old runs carried by a copied CTP tree would mix into this attempt's logs.
        attempt_ctp = attempt_root / "CTP"
        if not attempt_ctp.is_dir():
            fail(f"attempt has no CTP copy at {attempt_ctp}; copy $CTP_HOME there first")
        ctp_results = attempt_ctp / "result"
        if ctp_results.is_dir() and any(ctp_results.iterdir()):
            fail(
                f"attempt CTP result tree is not empty: {ctp_results}. "
                "Earlier runs there would mix into this attempt's shell logs; remove it from the attempt first."
            )
        extra_known: set[str] = set()
        env_ctp = os.environ.get("CTP_HOME", "")
        if env_ctp and Path(env_ctp).is_dir():
            ctp_git = inspect_ctp_git(Path(env_ctp).resolve())
            raw_origin_helpers = ctp_git.get("origin_init_helpers")
            if isinstance(raw_origin_helpers, set):
                extra_known = raw_origin_helpers
        verify_shell_init_helpers(attempt_ctp, selected.cases, extra_known=extra_known)
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


def verify_xml(path: Path, expected: int) -> None:
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
    skipped = sum(int(suite.attrib.get("skipped", "0")) for suite in suites)
    if tests != expected or failures != 0 or errors != 0 or skipped != 0:
        fail(
            f"XML result is not a complete pass: tests={tests}, failures={failures}, "
            f"errors={errors}, skipped={skipped}, expected={expected} ({path})"
        )


MACRO_SKIP_MESSAGE = "Skipped by macro"


def verify_shell_xml(path: Path, cases: list[str], run_log: str) -> int:
    """Check the shell XML and return the count of macro skips outside the selection."""
    read_required(path, "XML result")
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as error:
        fail(f"invalid XML result {path}: {error}")
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    if not suites:
        fail(f"XML result has no testsuite: {path}")
    if any("skipped" not in suite.attrib for suite in suites):
        fail(f"XML result is incomplete; missing skipped count: {path}")
    tests = sum(int(suite.attrib.get("tests", "0")) for suite in suites)
    failures = sum(int(suite.attrib.get("failures", "0")) for suite in suites)
    errors = sum(int(suite.attrib.get("errors", "0")) for suite in suites)
    skipped = sum(int(suite.attrib.get("skipped", "0")) for suite in suites)
    if tests != len(cases) or failures != 0 or errors != 0:
        fail(
            f"XML result is not a complete pass: tests={tests}, failures={failures}, "
            f"errors={errors}, skipped={skipped}, expected={len(cases)} ({path})"
        )
    if any(element.tag in {"failure", "error"} for element in root.iter()):
        fail(f"XML result contains a failure or error entry: {path}")
    expected = set(cases)
    skips: list[str] = []
    for case in root.iter("testcase"):
        entry = case.find("skipped")
        if entry is None:
            continue
        name = case.attrib.get("file", case.attrib.get("name", ""))
        if name in expected:
            fail(f"expected case was skipped: {name}")
        if entry.attrib.get("message") != MACRO_SKIP_MESSAGE:
            fail(f"skip outside the selection is not a macro skip: {name}")
        skips.append(name)
    if skipped != len(skips):
        fail(f"XML skipped={skipped} does not match {len(skips)} skipped entries ({path})")
    logged = re.findall(r"(?m)^Skipped File\(macro\): (.+?)\s*$", run_log)
    if sorted(logged) != sorted(skips):
        fail(
            f"run log macro skips ({len(logged)}) differ from XML skipped entries ({len(skips)})"
        )
    return len(skips)


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
    skips = verify_shell_xml(result_dir / "test-shell.xml", cases, run_log)
    if status["total_case_count"] != expected + skips:
        fail(
            f"total case count is {status['total_case_count']}, "
            f"expected {expected} (+{skips} macro skips outside the selection)"
        )
    if status["total_executed_case_count"] != expected:
        fail(
            f"executed case count is {status['total_executed_case_count']}, expected {expected}"
        )
    if status["total_fail_case_count"] != 0:
        fail(
            f"fail count is {status['total_fail_case_count']} even though runner exit was {runner_exit}"
        )
    if status["total_skip_case_count"] != skips:
        fail(f"skip count is {status['total_skip_case_count']}, expected {skips} macro skips")
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
        "total": expected + skips,
        "executed": expected,
        "success": expected,
        "fail": 0,
        "skip": skips,
    }:
        fail(f"feedback summary counts disagree with test_status.data: {feedback_counts!r}")
    for log in logs:
        if re.search(r"\bNOK\b", read_required(log, "per-environment test log")):
            fail(f"per-environment test log contains NOK: {log}")
    for case in cases:
        if not re.search(rf"(?m)^\[OK\]:\s+{re.escape(case)}(?:\s|$)", feedback):
            fail(f"feedback.log has no OK verdict for {case}")
    if "[SHELL] TEST END" not in run_log:
        fail("run log lacks the completed shell marker")
    run_counts = {
        "executed": count_value(run_log, "Total Execution Case", ":"),
        "success": count_value(run_log, "Total Success Case", ":"),
        "fail": count_value(run_log, "Total Fail Case", ":"),
        "skip": count_value(run_log, "Total Skip Case", ":"),
    }
    if run_counts != {"executed": expected, "success": expected, "fail": 0, "skip": skips}:
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
    preflight_parser.add_argument("--selection", type=Path)
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--suite", required=True, choices=("sql", "medium", "shell"))
    verify_parser.add_argument("--result-dir", required=True, type=Path)
    verify_parser.add_argument("--expected-list", required=True, type=Path)
    verify_parser.add_argument("--run-log", required=True, type=Path)
    verify_parser.add_argument("--runner-exit", required=True, type=int)
    quarantine_parser = subparsers.add_parser("quarantine-crash-artifacts")
    quarantine_parser.add_argument("--attempt-dir", required=True, type=Path)
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
            preflight(arguments.suite, arguments.allow_commit_mismatch, arguments.selection)
        elif arguments.command == "verify":
            verify(
                arguments.suite,
                arguments.result_dir,
                arguments.expected_list,
                arguments.run_log,
                arguments.runner_exit,
            )
        elif arguments.command == "quarantine-crash-artifacts":
            quarantine_crash_artifacts(arguments.attempt_dir)
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
