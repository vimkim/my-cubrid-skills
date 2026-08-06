#!/usr/bin/env python3
"""Initialize, record evidence for, and verify a CUBRID analysis report."""

from __future__ import annotations

import argparse
import base64
import hashlib
from html.parser import HTMLParser
import json
import os
import platform
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
import unicodedata
from urllib.parse import unquote, urlparse


EXIT_USAGE = 2
EXIT_PREFLIGHT = 3
EXIT_CONFLICT = 4
EXIT_FILESYSTEM = 5
EXIT_COMMAND_MISMATCH = 20
EXIT_COMMAND_ID = 21
EXIT_COMMAND_CAPTURE = 22
EXIT_REPORT = 30
EXIT_PROVENANCE = 31
EXIT_TEACHING = 32
EXIT_MULTIPLE = 33

ROOT = Path(__file__).resolve().parents[1]
COMMON = ROOT.parent / "cubrid-common" / "scripts" / "cubrid-common.sh"
CSS_SOURCE = ROOT / "assets" / "report.css"

COVERAGE_IDS = (
    "orientation",
    "mental-model",
    "scope-interface-seams",
    "data-ownership-lifetime",
    "lifecycle-state-machines",
    "core-workflows",
    "concurrency",
    "storage-durability-recovery",
    "policies-algorithms",
    "errors-resource-pressure",
    "performance-observability",
    "experimental-validation",
    "postgresql-analysis",
    "mysql-analysis",
    "cross-database-comparison",
    "reimplementation-blueprint",
    "glossary-evidence-unknowns",
    "teaching-map",
)

MASTERY_IDS = (
    "scope-interface-seams",
    "data-ownership-lifetime",
    "lifecycle-state-machines",
    "concurrency",
    "durability-recovery-failures",
    "policy-performance",
    "experiment-interpretation",
    "cross-database-non-equivalence",
)

ALLOWED_DATABASES = {"cubrid", "postgresql", "mysql", "comparison"}
ALLOWED_KINDS = {
    "source",
    "runtime",
    "source+runtime",
    "documented-intent",
    "inference",
    "unknown",
    "analogy",
}
ALLOWED_CONFIDENCE = {
    "SOURCE-CONFIRMED",
    "RUNTIME-OBSERVED",
    "SOURCE+RUNTIME-CONFIRMED",
    "DOCUMENTED",
    "INFERRED",
    "UNKNOWN",
}
READY = "READY WITHIN DECLARED SCOPE"
KOREAN_RE = re.compile(r"[가-힣]")
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|PLACEHOLDER|LOREM IPSUM)\b|\{\{[^}]+\}\}", re.I)
SAFE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
AGENT_RE = re.compile(r"^[a-z][a-z0-9-]{0,31}$")
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
INSTRUMENT_MARKER_RE = re.compile(r"^CUBRID_CODE_ANALYSIS_[A-Z0-9_.-]+$")


class ToolError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_utc(value: object, label: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str):
        errors.append(f"{label} must be an ISO-8601 UTC string")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{label} has an invalid timestamp")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        errors.append(f"{label} must be timezone-aware UTC")
        return None
    return parsed


def string_list(value: object, label: str, errors: list[str], *, nonempty: bool = True) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        errors.append(f"{label} must be a string list")
        return []
    if nonempty and not value:
        errors.append(f"{label} must not be empty")
    return value


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def run(
    args: list[str],
    cwd: Path | None = None,
    *,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    try:
        result = subprocess.run(
            args, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except OSError as exc:
        raise ToolError(EXIT_PREFLIGHT, f"Could not execute {args[0]}: {exc}") from exc
    if check and result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise ToolError(EXIT_PREFLIGHT, f"Command failed ({' '.join(args)}): {detail}")
    return result


def git(root: Path, *args: str, check: bool = True) -> bytes:
    return run(["git", "-C", str(root), *args], check=check).stdout


def git_root(path: Path) -> Path:
    value = git(path, "rev-parse", "--show-toplevel").decode().strip()
    return Path(value).resolve()


def validate_cubrid(root: Path) -> None:
    if not COMMON.is_file():
        raise ToolError(EXIT_PREFLIGHT, f"Shared CUBRID helper is missing: {COMMON}")
    result = run(
        [
            "bash",
            "-c",
            'source "$1" && cubrid_require_source_tree "$2"',
            "reportctl",
            str(COMMON),
            str(root),
        ],
        check=False,
    )
    if result.returncode:
        raise ToolError(
            EXIT_PREFLIGHT,
            result.stderr.decode("utf-8", "replace").strip() or "CUBRID source validation failed",
        )


def require_markers(root: Path, label: str, markers: tuple[str, ...]) -> None:
    missing = [marker for marker in markers if not (root / marker).exists()]
    if missing:
        raise ToolError(
            EXIT_PREFLIGHT,
            f"{label} source validation failed at {root}; missing: {', '.join(missing)}",
        )


def require_remote(identity: dict[str, object], label: str, pattern: str) -> None:
    remotes = identity.get("remotes")
    if not isinstance(remotes, list) or not any(re.search(pattern, str(value), re.I) for value in remotes):
        raise ToolError(EXIT_PREFLIGHT, f"{label} repository has no expected project remote")


def tool_identity(name: str, env: dict[str, str] | None = None) -> dict[str, object]:
    resolved = shutil.which(name, path=env.get("PATH") if env else None)
    if not resolved:
        raise ToolError(EXIT_PREFLIGHT, f"Required command not found: {name}")
    path = Path(resolved).resolve()
    digest = sha256(path.read_bytes()) if path.is_file() else ""
    version = run([str(path), "--version"], check=False, env=env)
    combined = (version.stdout + version.stderr).decode("utf-8", "replace").strip()
    return {
        "path": str(path),
        "sha256": digest,
        "version_exit": version.returncode,
        "version_output": combined[:2000],
    }


def binary_identity(name: str, env: dict[str, str]) -> dict[str, object]:
    resolved = shutil.which(name, path=env.get("PATH"))
    if not resolved:
        raise ToolError(EXIT_PREFLIGHT, f"Required built binary not found: {name}")
    path = Path(resolved).resolve()
    return {"path": str(path), "sha256": sha256(path.read_bytes())}


def installed_runtime_identity(environment: dict[str, str]) -> dict[str, object]:
    cubrid_value = environment.get("CUBRID", "")
    if not Path(cubrid_value).is_absolute():
        raise ToolError(
            EXIT_COMMAND_CAPTURE,
            "Pinned worktree environment must define an absolute CUBRID install root",
        )
    cubrid_install = Path(cubrid_value).resolve()
    tools = {
        name: binary_identity(name, environment)
        for name in ("csql", "cubrid", "cub_server")
    }
    release_tool = binary_identity("cubrid_rel", environment)
    release_result = run([str(release_tool["path"])], check=False, env=environment)
    release_output = (release_result.stdout + release_result.stderr).decode(
        "utf-8", "replace"
    ).strip()[:2000]
    if release_result.returncode != 0 or not release_output:
        raise ToolError(EXIT_COMMAND_CAPTURE, "cubrid_rel did not produce a release identity")
    release_identity = {
        **release_tool,
        "exit": release_result.returncode,
        "output": release_output,
    }
    for name, identity in {**tools, "cubrid_rel": release_identity}.items():
        try:
            Path(str(identity.get("path", ""))).resolve().relative_to(cubrid_install)
        except ValueError as exc:
            raise ToolError(
                EXIT_COMMAND_CAPTURE,
                f"Pinned {name} is outside the worktree CUBRID install root: {cubrid_install}",
            ) from exc
    return {"tools": tools, "release_identity": release_identity}


def worktree_environment(root: Path) -> dict[str, str]:
    result = run(["direnv", "exec", str(root), "env"])
    environment: dict[str, str] = {}
    for line in result.stdout.splitlines():
        key, separator, value = line.partition(b"=")
        if not separator:
            continue
        try:
            decoded_key = key.decode("utf-8")
            decoded_value = value.decode("utf-8")
        except UnicodeDecodeError:
            continue
        environment[decoded_key] = decoded_value
    if not environment.get("PATH"):
        raise ToolError(EXIT_PREFLIGHT, f"Pinned worktree environment has no PATH: {root}")
    return environment


def environment_digest(environment: dict[str, str]) -> str:
    ignored = {"_", "SHLVL", "PWD", "OLDPWD"}
    stable = {
        key: value
        for key, value in environment.items()
        if key not in ignored and not key.startswith("DIRENV_")
    }
    return sha256(json.dumps(stable, sort_keys=True, separators=(",", ":")).encode())


def runtime_environment_from_worktree(environment: dict[str, str]) -> dict[str, str]:
    allowed = {
        "CUBRID",
        "CUBRID_DATABASES",
        "LD_LIBRARY_PATH",
        "DYLD_LIBRARY_PATH",
        "PATH",
        "HOME",
        "USER",
        "LOGNAME",
        "SHELL",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "TZ",
        "TMPDIR",
        "ASAN_OPTIONS",
        "LSAN_OPTIONS",
        "UBSAN_OPTIONS",
    }
    return {key: value for key, value in environment.items() if key in allowed}


def repo_identity(path: Path, label: str) -> dict[str, object]:
    root = git_root(path)
    head = git(root, "rev-parse", "HEAD").decode().strip()
    if not HEX40_RE.fullmatch(head):
        raise ToolError(EXIT_PREFLIGHT, f"{label} HEAD is not a 40-hex commit: {head}")
    branch_result = run(
        ["git", "-C", str(root), "symbolic-ref", "--short", "-q", "HEAD"], check=False
    )
    branch = branch_result.stdout.decode().strip() or "DETACHED"
    status = git(root, "status", "--porcelain=v1", "-z")
    diff = git(root, "diff", "--binary", "--no-ext-diff")
    cached_diff = git(root, "diff", "--cached", "--binary", "--no-ext-diff")
    remotes = git(root, "remote", "-v").decode("utf-8", "replace").splitlines()
    return {
        "label": label,
        "root": str(root),
        "head": head,
        "branch": branch,
        "dirty": bool(status),
        "status_sha256": sha256(status),
        "status_porcelain_v1_z_base64": base64.b64encode(status).decode("ascii"),
        "diff_sha256": sha256(diff),
        "cached_diff_sha256": sha256(cached_diff),
        "remotes": remotes,
    }


def topic_slug(topic: str) -> str:
    normalized = unicodedata.normalize("NFKD", topic).encode("ascii", "ignore").decode().lower()
    normalized = re.sub(r"^\s*cubrid\b", "", normalized).strip()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    if not slug:
        slug = f"topic-{sha256(topic.encode('utf-8'))[:10]}"
    return slug[:64].rstrip("-")


def same_identity(current: dict[str, object], expected: dict[str, object]) -> bool:
    keys = (
        "root", "head", "branch", "status_sha256", "diff_sha256",
        "cached_diff_sha256", "remotes",
    )
    return all(current.get(key) == expected.get(key) for key in keys)


def initial_report_state() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "DRAFT",
        "readiness": "NOT READY",
        "scope": {
            "path": "research/scope.md",
            "sha256": "",
            "frozen": False,
        },
        "central_behaviors": [],
        "coverage": [
            {
                "id": item,
                "status": "pending",
                "chapter": "",
                "anchor": "",
                "claim_ids": [],
                "rationale_ko": "",
            }
            for item in COVERAGE_IDS
        ],
        "runtime_run_ids": [],
        "runtime": {
            "runtime_build_run_id": None,
            "baseline_tools_snapshot": None,
            "active_tools_snapshot": None,
        },
        "instrumentation": {
            "status": "not-used",
            "post_clean_build_run_id": None,
            "markers": [],
            "target_files": [],
        },
    }


def init_report(args: argparse.Namespace) -> int:
    topic = args.topic.strip()
    if not topic:
        raise ToolError(EXIT_USAGE, "Topic must not be empty")
    if not AGENT_RE.fullmatch(args.agent):
        raise ToolError(EXIT_USAGE, "Agent must match ^[a-z][a-z0-9-]{0,31}$")

    cubrid = repo_identity(Path(args.cubrid_root).resolve(), "cubrid")
    postgres = repo_identity(Path(args.postgres_root).resolve(), "postgresql")
    mysql = repo_identity(Path(args.mysql_root).resolve(), "mysql")
    validate_cubrid(Path(str(cubrid["root"])))
    require_markers(
        Path(str(postgres["root"])),
        "PostgreSQL",
        ("configure.ac", "meson.build", "src/include/postgres.h"),
    )
    require_markers(
        Path(str(mysql["root"])),
        "MySQL",
        ("CMakeLists.txt", "MYSQL_VERSION", "sql/mysqld.cc"),
    )
    require_remote(cubrid, "CUBRID", r"github\.com[:/]+cubrid/cubrid(?:\.git)?(?:\s|$)")
    require_remote(postgres, "PostgreSQL", r"github\.com[:/]+postgres/postgres(?:\.git)?(?:\s|$)")
    require_remote(mysql, "MySQL", r"github\.com[:/]+mysql/mysql-server(?:\.git)?(?:\s|$)")
    tools = {name: tool_identity(name) for name in ("git", "rg", "just", "direnv")}

    slug = topic_slug(topic)
    if args.output:
        report_dir = Path(args.output)
        if not report_dir.is_absolute():
            raise ToolError(EXIT_USAGE, "--output must be an absolute report directory")
        if report_dir.suffix.lower() in {".html", ".htm"}:
            raise ToolError(EXIT_USAGE, "--output must be a directory, not an HTML file")
        report_dir = report_dir.resolve()
    else:
        docs_root = Path(args.docs_root).resolve()
        if not docs_root.is_dir():
            raise ToolError(EXIT_PREFLIGHT, f"CUBRID docs root is unavailable: {docs_root}")
        report_dir = docs_root / "code-analysis" / slug / f"{str(cubrid['head'])[:7]}_{args.agent}"

    provenance = {
        "schema_version": 1,
        "topic": topic,
        "topic_slug": slug,
        "agent": args.agent,
        "created_at_utc": now_utc(),
        "report_dir": str(report_dir),
        "output_mode": "explicit" if args.output else "default",
        "environment": {
            "platform": platform.platform(),
            "python": sys.version,
            "CUBRID": os.environ.get("CUBRID", ""),
            "CUBRID_DATABASES": os.environ.get("CUBRID_DATABASES", ""),
            "PRESET_MODE": os.environ.get("PRESET_MODE", ""),
            "tools": tools,
        },
        "repositories": {"cubrid": cubrid, "postgresql": postgres, "mysql": mysql},
    }

    provenance_path = report_dir / "provenance.json"
    if report_dir.exists():
        if not provenance_path.is_file():
            raise ToolError(EXIT_CONFLICT, f"Output exists without provenance: {report_dir}")
        try:
            existing = json.loads(provenance_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ToolError(EXIT_CONFLICT, f"Could not read existing provenance: {exc}") from exc
        if not isinstance(existing, dict):
            raise ToolError(EXIT_CONFLICT, "Existing provenance must be a JSON object")
        existing_repositories = existing.get("repositories")
        identity_matches = (
            existing.get("schema_version") == 1
            and existing.get("topic") == topic
            and existing.get("topic_slug") == slug
            and existing.get("agent") == args.agent
            and existing.get("report_dir") == str(report_dir)
            and existing.get("output_mode") == ("explicit" if args.output else "default")
            and isinstance(existing_repositories, dict)
            and all(
                isinstance(existing_repositories.get(name), dict)
                and same_identity(provenance["repositories"][name], existing_repositories[name])
                for name in ("cubrid", "postgresql", "mysql")
            )
        )
        if not identity_matches:
            raise ToolError(EXIT_CONFLICT, f"Output identity conflicts with existing provenance: {report_dir}")
        print(json.dumps({"ok": True, "resumed": True, "report_dir": str(report_dir)}))
        return 0

    if not CSS_SOURCE.is_file():
        raise ToolError(EXIT_FILESYSTEM, f"Report stylesheet is missing: {CSS_SOURCE}")
    staging_dir: Path | None = None
    try:
        report_dir.parent.mkdir(parents=True, exist_ok=True)
        staging_dir = Path(
            tempfile.mkdtemp(prefix=f".{report_dir.name}.init-", dir=report_dir.parent)
        )
        for relative in (
            "assets",
            "chapters",
            "evidence/baseline",
            "evidence/raw",
            "evidence/runs",
            "experiments",
            "research",
            "research/packets",
            "quiz",
            "grill",
        ):
            (staging_dir / relative).mkdir(parents=True, exist_ok=False)
        shutil.copy2(CSS_SOURCE, staging_dir / "assets" / "report.css")
        for name, identity in provenance["repositories"].items():
            repo_root_path = Path(str(identity["root"]))
            snapshots = {
                "status.porcelain-v1.z": git(
                    repo_root_path, "status", "--porcelain=v1", "-z"
                ),
                "worktree.diff": git(
                    repo_root_path, "diff", "--binary", "--no-ext-diff"
                ),
                "index.diff": git(
                    repo_root_path, "diff", "--cached", "--binary", "--no-ext-diff"
                ),
            }
            identity["baseline_files"] = {}
            for suffix, data in snapshots.items():
                relative = Path("evidence") / "baseline" / f"{name}.{suffix}"
                (staging_dir / relative).write_bytes(data)
                identity["baseline_files"][suffix] = {
                    "path": relative.as_posix(),
                    "sha256": sha256(data),
                }
        (staging_dir / "research" / "scope.md").write_text(
            "# Declared Scope\n\n"
            "Status: UNFROZEN\n\n"
            "## Analysis Topic\n\n"
            "분석할 CUBRID Module과 해결하는 문제를 적는다.\n\n"
            "## Included Interfaces and Dependencies\n\n"
            "caller obligations, dependency seams, 포함 코드를 적는다.\n\n"
            "## Exclusions and Compatibility Limits\n\n"
            "제외 범위와 보장하지 않는 compatibility를 적는다.\n\n"
            "## Shared Three-Database Scenario\n\n"
            "CUBRID, PostgreSQL, MySQL에 공통으로 적용할 scenario를 적는다.\n\n"
            "## Central Behaviors\n\n"
            "report.json central_behaviors와 일치하는 핵심 메커니즘을 적는다.\n\n"
            "## Coverage Questions\n\n"
            "report.json의 18개 Coverage Obligation이 답할 질문을 적는다.\n",
            encoding="utf-8",
        )
        atomic_json(staging_dir / "provenance.json", provenance)
        atomic_json(staging_dir / "report.json", initial_report_state())
        (staging_dir / "evidence" / "claims.jsonl").write_text("", encoding="utf-8")
        staging_dir.rename(report_dir)
    except ToolError:
        raise
    except OSError as exc:
        if staging_dir is not None:
            shutil.rmtree(staging_dir, ignore_errors=True)
        if report_dir.exists():
            raise ToolError(EXIT_CONFLICT, f"Output appeared during initialization: {report_dir}") from exc
        raise ToolError(EXIT_FILESYSTEM, f"Could not initialize report tree: {exc}") from exc

    print(json.dumps({"ok": True, "resumed": False, "report_dir": str(report_dir)}))
    return 0


def record_command(args: argparse.Namespace) -> int:
    report_dir = Path(args.report_dir).resolve()
    if not (report_dir / "provenance.json").is_file():
        raise ToolError(EXIT_COMMAND_ID, f"Not an initialized report directory: {report_dir}")
    if not SAFE_ID_RE.fullmatch(args.id):
        raise ToolError(EXIT_COMMAND_ID, "Run ID must match ^[a-z0-9][a-z0-9._-]{0,79}$")
    cwd = Path(args.cwd).resolve()
    if not cwd.is_dir():
        raise ToolError(EXIT_COMMAND_ID, f"Command cwd does not exist: {cwd}")
    command = list(args.command)
    if command and command[0] == "--":
        command.pop(0)
    if not command:
        raise ToolError(EXIT_COMMAND_ID, "No command supplied after --")

    execution_env: dict[str, str] | None = None
    runtime_environment_sha256 = ""
    runtime_snapshot_relative = args.runtime_tools_snapshot or ""
    if runtime_snapshot_relative:
        snapshot_path = (report_dir / runtime_snapshot_relative).resolve()
        try:
            snapshot_path.relative_to(report_dir / "evidence")
        except ValueError as exc:
            raise ToolError(
                EXIT_COMMAND_ID, "Runtime tools snapshot must stay under evidence/"
            ) from exc
        snapshot_errors: list[str] = []
        snapshot = load_json(snapshot_path, snapshot_errors)
        runtime_environment = snapshot.get("runtime_environment") if snapshot else None
        if snapshot_errors or not isinstance(runtime_environment, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in runtime_environment.items()
        ):
            raise ToolError(
                EXIT_COMMAND_ID,
                "; ".join(snapshot_errors) or "Runtime snapshot has no valid environment",
            )
        execution_env = dict(runtime_environment)
        runtime_environment_sha256 = sha256(
            json.dumps(runtime_environment, sort_keys=True, separators=(",", ":")).encode()
        )

    bound_files: list[dict[str, str]] = []
    seen_bound_paths: set[Path] = set()
    for value in args.bind_file or []:
        bound_path = Path(value)
        if not bound_path.is_absolute():
            bound_path = cwd / bound_path
        bound_path = bound_path.resolve()
        if bound_path in seen_bound_paths:
            raise ToolError(EXIT_COMMAND_ID, f"Duplicate bound file: {bound_path}")
        try:
            before_data = bound_path.read_bytes()
        except OSError as exc:
            raise ToolError(EXIT_COMMAND_ID, f"Cannot bind input file {bound_path}: {exc}") from exc
        seen_bound_paths.add(bound_path)
        bound_files.append(
            {"path": str(bound_path), "before_sha256": sha256(before_data)}
        )

    runs_dir = report_dir / "evidence" / "runs"
    final_dir = runs_dir / args.id
    if final_dir.exists():
        raise ToolError(EXIT_COMMAND_ID, f"Run ID already exists: {args.id}")
    try:
        final_dir.mkdir()
    except FileExistsError as exc:
        raise ToolError(EXIT_COMMAND_ID, f"Run ID already exists: {args.id}") from exc
    except OSError as exc:
        raise ToolError(EXIT_COMMAND_CAPTURE, f"Could not reserve run ID {args.id}: {exc}") from exc
    started = now_utc()
    try:
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                env=execution_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            execution_error = ""
        except OSError as exc:
            result = None
            execution_error = str(exc)
        finished = now_utc()
        stdout = result.stdout if result else b""
        stderr = result.stderr if result else execution_error.encode("utf-8", "replace")
        actual_exit = result.returncode if result else None
        for entry in bound_files:
            try:
                after_data = Path(entry["path"]).read_bytes()
            except OSError:
                entry["after_sha256"] = "UNREADABLE"
            else:
                entry["after_sha256"] = sha256(after_data)
        (final_dir / "stdout.txt").write_bytes(stdout)
        (final_dir / "stderr.txt").write_bytes(stderr)
        meta = {
            "schema_version": 1,
            "id": args.id,
            "argv": command,
            "cwd": str(cwd),
            "started_at_utc": started,
            "finished_at_utc": finished,
            "expected_exit": args.expect_exit,
            "actual_exit": actual_exit,
            "matched_expectation": actual_exit == args.expect_exit,
            "stdout_sha256": sha256(stdout),
            "stderr_sha256": sha256(stderr),
            "execution_error": execution_error,
            "runtime_tools_snapshot": runtime_snapshot_relative,
            "runtime_environment_sha256": runtime_environment_sha256,
            "bound_files": bound_files,
            "kind": "command",
        }
        # meta.json is the completion marker and is written last.
        atomic_json(final_dir / "meta.json", meta)
    except OSError as exc:
        raise ToolError(EXIT_COMMAND_CAPTURE, f"Could not capture command: {exc}") from exc

    print(json.dumps({"ok": meta["matched_expectation"], "run_dir": str(final_dir), **meta}))
    if result is None:
        return EXIT_COMMAND_CAPTURE
    return 0 if meta["matched_expectation"] else EXIT_COMMAND_MISMATCH


def capture_build(args: argparse.Namespace) -> int:
    report_dir = Path(args.report_dir).resolve()
    provenance_errors: list[str] = []
    provenance = load_json(report_dir / "provenance.json", provenance_errors)
    if provenance_errors:
        raise ToolError(EXIT_COMMAND_ID, "; ".join(provenance_errors))
    if not SAFE_ID_RE.fullmatch(args.id):
        raise ToolError(EXIT_COMMAND_ID, "Build run ID is unsafe")
    repositories = provenance.get("repositories")
    cubrid_repo = repositories.get("cubrid") if isinstance(repositories, dict) else None
    if not isinstance(cubrid_repo, dict):
        raise ToolError(EXIT_COMMAND_ID, "CUBRID provenance is missing")
    cubrid_root = Path(str(cubrid_repo.get("root", ""))).resolve()
    environment = worktree_environment(cubrid_root)
    build_dir_value = environment.get("CUBRID_BUILD_DIR", "")
    install_value = environment.get("CUBRID", "")
    if not Path(build_dir_value).is_absolute() or not Path(install_value).is_absolute():
        raise ToolError(
            EXIT_COMMAND_ID,
            "Pinned build environment needs absolute CUBRID_BUILD_DIR and CUBRID",
        )
    before = repo_identity(cubrid_root, "cubrid")
    if before.get("head") != cubrid_repo.get("head"):
        raise ToolError(EXIT_PROVENANCE, "CUBRID HEAD changed before build")
    raw_source = {
        "status.porcelain-v1.z": git(cubrid_root, "status", "--porcelain=v1", "-z"),
        "worktree.diff": git(cubrid_root, "diff", "--binary", "--no-ext-diff"),
        "index.diff": git(cubrid_root, "diff", "--cached", "--binary", "--no-ext-diff"),
    }
    run_dir = report_dir / "evidence" / "runs" / args.id
    try:
        run_dir.mkdir()
    except FileExistsError as exc:
        raise ToolError(EXIT_COMMAND_ID, f"Run ID already exists: {args.id}") from exc
    started = now_utc()
    execution_error = ""
    try:
        result = subprocess.run(
            ["just", "build"],
            cwd=cubrid_root,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        result = None
        execution_error = str(exc)
    finished = now_utc()
    stdout = result.stdout if result else b""
    stderr = result.stderr if result else execution_error.encode("utf-8", "replace")
    actual_exit = result.returncode if result else None
    (run_dir / "stdout.txt").write_bytes(stdout)
    (run_dir / "stderr.txt").write_bytes(stderr)
    source_receipt: dict[str, object] = {}
    for name, data in raw_source.items():
        path = run_dir / f"source-{name}"
        path.write_bytes(data)
        source_receipt[name] = {"path": path.relative_to(report_dir).as_posix(), "sha256": sha256(data)}
    after = repo_identity(cubrid_root, "cubrid")
    source_unchanged = same_identity(before, after)
    build_receipt: dict[str, object] = {
        "source_before": {
            field: before.get(field)
            for field in ("root", "head", "status_sha256", "diff_sha256", "cached_diff_sha256")
        },
        "source_after": {
            field: after.get(field)
            for field in ("root", "head", "status_sha256", "diff_sha256", "cached_diff_sha256")
        },
        "source_snapshots": source_receipt,
        "source_unchanged": source_unchanged,
        "worktree_environment_sha256": environment_digest(environment),
        "environment": {
            key: environment.get(key, "")
            for key in ("CUBRID", "CUBRID_BUILD_DIR", "CUBRID_DATABASES", "PRESET_MODE")
        },
    }
    if actual_exit == 0:
        cache_path = Path(build_dir_value).resolve() / "CMakeCache.txt"
        try:
            cache_data = cache_path.read_bytes()
        except OSError as exc:
            execution_error = f"Built without readable CMakeCache.txt: {exc}"
        else:
            cache_text = cache_data.decode("utf-8", "replace")
            home_match = re.search(r"^CMAKE_HOME_DIRECTORY:INTERNAL=(.+)$", cache_text, re.M)
            prefix_match = re.search(r"^CMAKE_INSTALL_PREFIX:PATH=(.+)$", cache_text, re.M)
            cmake_home = Path(home_match.group(1)).resolve() if home_match else None
            install_prefix = Path(prefix_match.group(1)).resolve() if prefix_match else None
            if cmake_home != cubrid_root or install_prefix != Path(install_value).resolve():
                execution_error = "CMakeCache source/install roots do not match the pinned worktree environment"
            else:
                try:
                    install_identity = installed_runtime_identity(environment)
                except ToolError as exc:
                    execution_error = str(exc)
                else:
                    captured_cache = run_dir / "CMakeCache.txt"
                    captured_cache.write_bytes(cache_data)
                    build_receipt.update(
                        {
                            "cmake_cache": {
                                "path": captured_cache.relative_to(report_dir).as_posix(),
                                "sha256": sha256(cache_data),
                                "source_root": str(cmake_home),
                                "install_prefix": str(install_prefix),
                            },
                            "install_identity": install_identity,
                        }
                    )
    matched = actual_exit == 0 and source_unchanged and not execution_error
    meta = {
        "schema_version": 1,
        "kind": "build",
        "id": args.id,
        "argv": ["just", "build"],
        "cwd": str(cubrid_root),
        "started_at_utc": started,
        "finished_at_utc": finished,
        "expected_exit": 0,
        "actual_exit": actual_exit,
        "matched_expectation": matched,
        "stdout_sha256": sha256(stdout),
        "stderr_sha256": sha256(stderr),
        "execution_error": execution_error,
        "runtime_tools_snapshot": "",
        "runtime_environment_sha256": environment_digest(environment),
        "bound_files": [],
        "build_receipt": build_receipt,
    }
    atomic_json(run_dir / "meta.json", meta)
    print(json.dumps({"ok": matched, "run_dir": str(run_dir), **meta}, ensure_ascii=False))
    if result is None:
        return EXIT_COMMAND_CAPTURE
    return 0 if matched else EXIT_COMMAND_MISMATCH


def snapshot_runtime(args: argparse.Namespace) -> int:
    report_dir = Path(args.report_dir).resolve()
    if not SAFE_ID_RE.fullmatch(args.id):
        raise ToolError(EXIT_COMMAND_ID, "Runtime snapshot ID is unsafe")
    provenance_errors: list[str] = []
    provenance = load_json(report_dir / "provenance.json", provenance_errors)
    if provenance_errors:
        raise ToolError(EXIT_COMMAND_ID, "; ".join(provenance_errors))
    repositories = provenance.get("repositories")
    cubrid_repo = repositories.get("cubrid") if isinstance(repositories, dict) else None
    if not isinstance(cubrid_repo, dict):
        raise ToolError(EXIT_COMMAND_ID, "CUBRID provenance is missing")
    cubrid_root = Path(str(cubrid_repo.get("root", ""))).resolve()
    current = repo_identity(cubrid_root, "cubrid")
    if current.get("head") != cubrid_repo.get("head"):
        raise ToolError(EXIT_PROVENANCE, "CUBRID HEAD changed before runtime snapshot")
    if args.id in {"baseline", "post-clean"} and not same_identity(current, cubrid_repo):
        raise ToolError(
            EXIT_PROVENANCE,
            f"CUBRID worktree must match frozen provenance for {args.id} runtime snapshot",
        )
    run_errors: list[str] = []
    build_meta = verify_run(report_dir, args.build_run_id, run_errors)
    if run_errors or not build_meta:
        raise ToolError(EXIT_COMMAND_ID, "; ".join(run_errors) or "Build run is missing")
    if build_meta.get("kind") != "build" or build_meta.get("argv") != ["just", "build"] or Path(
        str(build_meta.get("cwd", ""))
    ).resolve() != cubrid_root:
        raise ToolError(
            EXIT_COMMAND_ID,
            "Runtime snapshot requires a successful captured `just build` in the pinned CUBRID root",
        )
    build_receipt = build_meta.get("build_receipt")
    if not isinstance(build_receipt, dict):
        raise ToolError(EXIT_COMMAND_ID, "Build run has no build receipt")
    worktree_env = worktree_environment(cubrid_root)
    worktree_env_hash = environment_digest(worktree_env)
    if (
        build_receipt.get("worktree_environment_sha256") != worktree_env_hash
        or build_meta.get("runtime_environment_sha256") != worktree_env_hash
    ):
        raise ToolError(
            EXIT_COMMAND_ID,
            "Runtime snapshot worktree environment differs from the captured build environment",
        )
    source_after = build_receipt.get("source_after")
    if not isinstance(source_after, dict) or any(
        current.get(field) != source_after.get(field)
        for field in ("root", "head", "status_sha256", "diff_sha256", "cached_diff_sha256")
    ):
        raise ToolError(EXIT_PROVENANCE, "Runtime snapshot source differs from its build receipt")
    install_identity = installed_runtime_identity(worktree_env)
    if install_identity != build_receipt.get("install_identity"):
        raise ToolError(EXIT_COMMAND_CAPTURE, "Installed runtime differs from build outputs")
    runtime_environment = runtime_environment_from_worktree(worktree_env)
    captured = datetime.now(timezone.utc)
    build_finished_errors: list[str] = []
    build_finished = parse_utc(
        build_meta.get("finished_at_utc"),
        f"Build run {args.build_run_id} finish",
        build_finished_errors,
    )
    if build_finished_errors or build_finished is None or captured < build_finished:
        raise ToolError(
            EXIT_COMMAND_ID,
            "; ".join(build_finished_errors) or "Runtime snapshot precedes its build",
        )
    snapshot = {
        "schema_version": 1,
        "id": args.id,
        "source_root": str(cubrid_root),
        "source_head": cubrid_repo.get("head"),
        "build_run_id": args.build_run_id,
        "build_meta_sha256": sha256(
            (report_dir / "evidence" / "runs" / args.build_run_id / "meta.json").read_bytes()
        ),
        "captured_at_utc": captured.isoformat(),
        "worktree_environment_sha256": worktree_env_hash,
        "runtime_environment": runtime_environment,
        **install_identity,
    }
    destination = report_dir / "evidence" / f"runtime-tools-{args.id}.json"
    if destination.exists():
        raise ToolError(EXIT_COMMAND_ID, f"Runtime snapshot already exists: {args.id}")
    atomic_json(destination, snapshot)
    print(
        json.dumps(
            {"ok": True, "path": destination.relative_to(report_dir).as_posix(), **snapshot},
            ensure_ascii=False,
        )
    )
    return 0


class BookParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang = ""
        self.charset = ""
        self.viewport = False
        self.title_depth = 0
        self.title_text: list[str] = []
        self.h1_count = 0
        self.main_count = 0
        self.ids: list[str] = []
        self.links: list[tuple[str, str, str]] = []
        self.claim_ids: set[str] = set()
        self.claims_by_anchor: dict[str, set[str]] = {}
        self.visible: list[str] = []
        self.hidden_depth = 0
        self.head_depth = 0
        self.doctype = False
        self.stack: list[str] = []
        self.structure_errors: list[str] = []
        self.table_stack: list[dict[str, object]] = []
        self.rel_links: dict[str, set[str]] = {}

    def handle_decl(self, decl: str) -> None:
        if decl.strip().lower() == "doctype html":
            self.doctype = True

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key.lower(): value or "" for key, value in attrs}
        if tag == "html":
            self.lang = data.get("lang", "")
        if tag == "meta" and data.get("charset"):
            self.charset = data["charset"].lower()
        if tag == "meta" and data.get("name", "").lower() == "viewport" and data.get("content"):
            self.viewport = True
        if tag == "meta" and data.get("http-equiv", "").lower() == "refresh":
            self.links.append(("meta-refresh", "content", data.get("content", "")))
        if tag == "script":
            self.structure_errors.append("script elements are forbidden in the offline Book")
        if tag == "style" or data.get("style"):
            self.structure_errors.append("inline CSS is forbidden; use assets/report.css")
        if data.get("srcdoc"):
            self.structure_errors.append("iframe srcdoc is forbidden in the offline Book")
        if tag == "title":
            self.title_depth += 1
        if tag == "head":
            self.head_depth += 1
        if tag == "h1":
            self.h1_count += 1
        if tag == "main":
            self.main_count += 1
        if tag == "table":
            self.table_stack.append({"caption": False, "headers": 0})
        if tag == "caption" and self.table_stack:
            self.table_stack[-1]["caption"] = True
        if tag == "th" and self.table_stack:
            self.table_stack[-1]["headers"] = int(self.table_stack[-1]["headers"]) + 1
        if tag == "svg" and (
            data.get("role") != "img" or not KOREAN_RE.search(data.get("aria-label", ""))
        ):
            self.structure_errors.append("svg needs role=img and Korean aria-label")
        if tag in {"script", "style"}:
            self.hidden_depth += 1
        if data.get("id"):
            self.ids.append(data["id"])
        if data.get("data-claim-id"):
            element_claims = set(filter(None, re.split(r"[\s,]+", data["data-claim-id"])))
            self.claim_ids.update(element_claims)
            if data.get("id"):
                self.claims_by_anchor.setdefault(data["id"], set()).update(element_claims)
        for attr in ("href", "xlink:href", "src", "srcset", "poster", "data", "formaction"):
            if data.get(attr):
                if attr == "srcset":
                    for candidate in data[attr].split(","):
                        target = candidate.strip().split()[0] if candidate.strip() else ""
                        if target:
                            self.links.append((tag, attr, target))
                else:
                    self.links.append((tag, attr, data[attr]))
        if tag == "a" and data.get("href") and data.get("rel"):
            for relation in data["rel"].split():
                self.rel_links.setdefault(relation.lower(), set()).add(data["href"])
        if tag not in {
            "area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr",
        }:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self.title_depth:
            self.title_depth -= 1
        if tag in {"script", "style"} and self.hidden_depth:
            self.hidden_depth -= 1
        if tag == "head" and self.head_depth:
            self.head_depth -= 1
        if tag == "table" and self.table_stack:
            table = self.table_stack.pop()
            if not table["caption"] or int(table["headers"]) < 1:
                self.structure_errors.append("table needs a caption and at least one th")
        if not self.stack:
            self.structure_errors.append(f"unexpected closing tag </{tag}>")
        elif self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            self.structure_errors.append(
                f"misnested closing tag </{tag}> after <{self.stack[-1]}>"
            )
            while self.stack and self.stack[-1] != tag:
                self.stack.pop()
            if self.stack:
                self.stack.pop()
        else:
            self.structure_errors.append(f"closing tag without opener </{tag}>")

    def handle_data(self, data: str) -> None:
        if self.title_depth:
            self.title_text.append(data)
        if not self.hidden_depth and not self.head_depth and data.strip():
            self.visible.append(data)


def load_json(path: Path, errors: list[str]) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"Missing file: {path}")
        return {}
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Invalid JSON {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"Expected JSON object: {path}")
        return {}
    return value


def verify_provenance(report_dir: Path, provenance: dict[str, object], errors: list[str]) -> None:
    if provenance.get("schema_version") != 1:
        errors.append("Unsupported provenance schema")
    if provenance.get("report_dir") != str(report_dir):
        errors.append("Report directory differs from immutable provenance")
    repositories = provenance.get("repositories")
    if not isinstance(repositories, dict):
        errors.append("provenance.json has no repositories object")
        return
    for name in ("cubrid", "postgresql", "mysql"):
        expected = repositories.get(name)
        if not isinstance(expected, dict):
            errors.append(f"Missing provenance repository: {name}")
            continue
        root = Path(str(expected.get("root", "")))
        try:
            current = repo_identity(root, name)
        except ToolError as exc:
            errors.append(str(exc))
            continue
        if not same_identity(current, expected):
            errors.append(f"Repository identity drift: {name}")
        baseline_files = expected.get("baseline_files")
        if not isinstance(baseline_files, dict):
            errors.append(f"Missing baseline source snapshots: {name}")
            continue
        for snapshot_name in ("status.porcelain-v1.z", "worktree.diff", "index.diff"):
            snapshot = baseline_files.get(snapshot_name)
            if not isinstance(snapshot, dict):
                errors.append(f"Missing {name} baseline snapshot: {snapshot_name}")
                continue
            snapshot_path = (report_dir / str(snapshot.get("path", ""))).resolve()
            try:
                snapshot_path.relative_to(report_dir)
                data = snapshot_path.read_bytes()
            except (ValueError, OSError) as exc:
                errors.append(f"Invalid {name} baseline snapshot {snapshot_name}: {exc}")
                continue
            if snapshot.get("sha256") != sha256(data):
                errors.append(f"Baseline snapshot hash mismatch: {name}/{snapshot_name}")
            fingerprint_field = {
                "status.porcelain-v1.z": "status_sha256",
                "worktree.diff": "diff_sha256",
                "index.diff": "cached_diff_sha256",
            }[snapshot_name]
            if snapshot.get("sha256") != expected.get(fingerprint_field):
                errors.append(
                    f"Baseline snapshot is not bound to repository fingerprint: "
                    f"{name}/{snapshot_name}"
                )
    cubrid = repositories.get("cubrid", {})
    if not isinstance(cubrid, dict):
        errors.append("CUBRID provenance entry is not an object")
        cubrid = {}
    expected_dir = f"{str(cubrid.get('head', ''))[:7]}_{provenance.get('agent', '')}"
    if provenance.get("output_mode") == "default" and report_dir.name != expected_dir:
        errors.append(f"Default report directory identity mismatch: expected {expected_dir}")
    environment = provenance.get("environment")
    if not isinstance(environment, dict) or not environment.get("platform") or not environment.get("python"):
        errors.append("Provenance lacks OS/Python environment")
        return
    tools = environment.get("tools")
    if not isinstance(tools, dict):
        errors.append("Provenance lacks runtime tool identities")
        return
    for name in ("git", "rg", "just", "direnv"):
        tool = tools.get(name)
        if not isinstance(tool, dict):
            errors.append(f"Provenance lacks tool identity: {name}")
            continue
        if not Path(str(tool.get("path", ""))).is_absolute() or not HEX64_RE.fullmatch(
            str(tool.get("sha256", ""))
        ):
            errors.append(f"Provenance has invalid tool path/hash: {name}")


def parse_book(report_dir: Path, errors: list[str]) -> tuple[dict[Path, BookParser], set[str]]:
    html_files = [
        path
        for path in sorted(report_dir.rglob("*.html"))
        if path.is_file()
        and path.relative_to(report_dir).parts[0]
        not in {"evidence", "research", "experiments"}
        and not (
            path.relative_to(report_dir).parts[0] == "quiz"
            and {"raw-output", "observed", "expected"}
            & set(path.relative_to(report_dir).parts[1:])
        )
    ]
    if report_dir / "index.html" not in html_files:
        errors.append("Missing index.html")
    if not html_files:
        return {}, set()
    parsed: dict[Path, BookParser] = {}
    all_claim_ids: set[str] = set()
    titles: dict[str, Path] = {}
    for path in html_files:
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"Cannot read UTF-8 HTML {path}: {exc}")
            continue
        if PLACEHOLDER_RE.search(raw):
            errors.append(f"Placeholder text remains in {path}")
        if re.search(r"(?:https?:|ftp:|file:|//)", raw, re.I) and re.search(
            r"(?:url\s*\(|@import|fetch\s*\(|XMLHttpRequest|WebSocket|EventSource|"
            r"new\s+Image|import\s*\()",
            raw,
            re.I,
        ):
            errors.append(f"Network-dependent inline resource in {path}")
        parser = BookParser()
        try:
            parser.feed(raw)
            parser.close()
        except Exception as exc:  # HTMLParser errors are rare but must not abort all checks.
            errors.append(f"Cannot parse HTML {path}: {exc}")
            continue
        parsed[path] = parser
        all_claim_ids.update(parser.claim_ids)
        if not parser.doctype:
            errors.append(f"HTML must declare <!doctype html>: {path}")
        if parser.stack:
            parser.structure_errors.append(f"unclosed tags: {', '.join(parser.stack)}")
        for structure_error in parser.structure_errors:
            errors.append(f"Malformed HTML in {path}: {structure_error}")
        if parser.lang.lower() != "ko":
            errors.append(f"HTML lang must be ko: {path}")
        if parser.charset not in {"utf-8", "utf8"}:
            errors.append(f"HTML must declare UTF-8: {path}")
        if not parser.viewport:
            errors.append(f"HTML must declare a viewport: {path}")
        title = "".join(parser.title_text).strip()
        if not title:
            errors.append(f"HTML has no title: {path}")
        elif title in titles:
            errors.append(f"Duplicate HTML title '{title}': {titles[title]} and {path}")
        else:
            titles[title] = path
        if parser.h1_count != 1:
            errors.append(f"HTML must have exactly one h1 ({parser.h1_count}): {path}")
        if parser.main_count != 1:
            errors.append(f"HTML must have exactly one main ({parser.main_count}): {path}")
        if len(parser.ids) != len(set(parser.ids)):
            errors.append(f"Duplicate HTML id in {path}")
        if not KOREAN_RE.search(" ".join(parser.visible)):
            errors.append(f"HTML has no Korean visible prose: {path}")

    graph: dict[Path, set[Path]] = {path: set() for path in parsed}
    loaded_tags = {
        "base", "link", "script", "img", "iframe", "source", "track", "video", "audio",
        "object", "embed", "input", "meta-refresh", "image", "use", "feimage",
    }
    for source, parser in parsed.items():
        for tag, attribute, target in parser.links:
            if tag in {"object", "embed", "iframe"}:
                errors.append(f"Active embedded document is forbidden in {source}: {target}")
                continue
            if tag == "base":
                errors.append(f"HTML base URL is forbidden in {source}: {target}")
                continue
            if tag == "meta-refresh":
                errors.append(f"HTML refresh is forbidden in {source}: {target}")
                continue
            parsed_url = urlparse(target)
            if parsed_url.scheme.lower() in {"javascript", "vbscript"}:
                errors.append(f"Active URL scheme is forbidden in {source}: {target}")
                continue
            if target.startswith("//"):
                if tag in loaded_tags:
                    errors.append(f"Protocol-relative loaded resource in {source}: {target}")
                continue
            if parsed_url.scheme:
                if tag in loaded_tags:
                    errors.append(f"External loaded resource in {source}: {target}")
                continue
            path_part = unquote(parsed_url.path)
            if not path_part:
                destination = source
            elif path_part.startswith("/"):
                if tag in loaded_tags:
                    errors.append(f"Absolute loaded resource in {source}: {target}")
                continue
            else:
                destination = (source.parent / path_part).resolve()
                try:
                    destination.relative_to(report_dir)
                except ValueError:
                    errors.append(f"Link escapes report directory in {source}: {target}")
                    continue
                if not destination.exists():
                    errors.append(f"Broken local link in {source}: {target}")
                    continue
            if tag == "link" and destination.suffix.lower() == ".css" and destination != report_dir / "assets" / "report.css":
                errors.append(f"Only assets/report.css may be loaded: {source}: {target}")
            if tag in loaded_tags and destination.suffix.lower() == ".svg":
                errors.append(f"External SVG documents are forbidden; use inline SVG: {source}: {target}")
            if destination.suffix.lower() in {".html", ".htm"} and destination in parsed:
                graph[source].add(destination)
                if parsed_url.fragment and parsed_url.fragment not in set(parsed[destination].ids):
                    errors.append(f"Broken fragment in {source}: {target}")
            elif parsed_url.fragment and destination == source and parsed_url.fragment not in set(parser.ids):
                errors.append(f"Broken fragment in {source}: {target}")

    index = report_dir / "index.html"
    reachable: set[Path] = set()
    stack = [index] if index in graph else []
    while stack:
        node = stack.pop()
        if node in reachable:
            continue
        reachable.add(node)
        stack.extend(graph[node] - reachable)
    missing = set(parsed) - reachable
    for path in sorted(missing):
        errors.append(f"HTML is not reachable from index.html: {path.relative_to(report_dir)}")

    chapters = sorted(
        path for path in parsed if (report_dir / "chapters") in path.parents
    )
    if index in graph:
        for chapter in chapters:
            if chapter not in graph[index]:
                errors.append(
                    f"index.html must link each chapter directly: {chapter.relative_to(report_dir)}"
                )
    for chapter in chapters:
        linked = graph.get(chapter, set())
        if index not in linked:
            errors.append(f"Chapter has no link back to index.html: {chapter.relative_to(report_dir)}")
        if len(chapters) > 1 and not (linked & set(chapters)):
            errors.append(f"Chapter has no previous/next chapter link: {chapter.relative_to(report_dir)}")
        position = chapters.index(chapter)
        if position > 0 and "prev" not in parsed[chapter].rel_links:
            errors.append(f"Chapter lacks rel=prev navigation: {chapter.relative_to(report_dir)}")
        if position + 1 < len(chapters) and "next" not in parsed[chapter].rel_links:
            errors.append(f"Chapter lacks rel=next navigation: {chapter.relative_to(report_dir)}")

    css = report_dir / "assets" / "report.css"
    if not css.is_file():
        errors.append("Missing assets/report.css")
    else:
        css_text = css.read_text(encoding="utf-8", errors="replace")
        css_targets = [
            match.group(1).strip().strip("\"'")
            for match in re.finditer(r"url\s*\(([^)]+)\)", css_text, re.I)
        ]
        css_targets.extend(
            match.group(1)
            for match in re.finditer(r"@import\s+[\"']([^\"']+)[\"']", css_text, re.I)
        )
        if re.search(r"@import\b", css_text, re.I):
            errors.append("CSS @import is forbidden in assets/report.css")
        for target in css_targets:
            parsed_url = urlparse(target)
            if target.startswith("//") or parsed_url.scheme or parsed_url.path.startswith("/"):
                errors.append(f"External/absolute URL found in assets/report.css: {target}")
                continue
            destination = (css.parent / unquote(parsed_url.path)).resolve()
            try:
                destination.relative_to(report_dir)
            except ValueError:
                errors.append(f"CSS URL escapes report directory: {target}")
            else:
                if not destination.is_file():
                    errors.append(f"Broken CSS URL in assets/report.css: {target}")
                elif destination.suffix.lower() in {".css", ".svg", ".html", ".htm"}:
                    errors.append(f"Active/nested CSS resource is forbidden: {target}")
    return parsed, all_claim_ids


def verify_coverage(
    report: dict[str, object],
    parsed: dict[Path, BookParser],
    report_dir: Path,
    errors: list[str],
) -> dict[str, set[str]]:
    coverage = report.get("coverage")
    if not isinstance(coverage, list):
        errors.append("report.json coverage must be a list")
        return {}
    found: set[str] = set()
    locations: set[str] = set()
    claim_locations: dict[str, set[str]] = {}
    for item in coverage:
        if not isinstance(item, dict):
            errors.append("Coverage entry must be an object")
            continue
        item_id = str(item.get("id", ""))
        if item_id in found:
            errors.append(f"Duplicate coverage id: {item_id}")
        found.add(item_id)
        status = item.get("status")
        if status not in {"covered", "not-applicable"}:
            errors.append(f"Coverage {item_id} is not resolved: {status}")
        chapter = str(item.get("chapter", ""))
        anchor = str(item.get("anchor", ""))
        location = f"{chapter}#{anchor}"
        if location in locations:
            errors.append(f"Coverage obligations share one chapter anchor: {location}")
        locations.add(location)
        chapter_path = (report_dir / chapter).resolve() if chapter else None
        if not chapter_path or chapter_path not in parsed:
            errors.append(f"Coverage {item_id} has invalid chapter: {chapter}")
        elif not anchor or anchor not in set(parsed[chapter_path].ids):
            errors.append(f"Coverage {item_id} has invalid anchor: {anchor}")
        claim_ids = item.get("claim_ids")
        if not isinstance(claim_ids, list) or not claim_ids:
            errors.append(f"Coverage {item_id} has no claim IDs")
        else:
            for value in claim_ids:
                claim_locations.setdefault(str(value), set()).add(location)
        if status == "not-applicable" and not KOREAN_RE.search(str(item.get("rationale_ko", ""))):
            errors.append(f"Coverage {item_id} needs Korean not-applicable rationale")
    missing = set(COVERAGE_IDS) - found
    extra = found - set(COVERAGE_IDS)
    if missing:
        errors.append(f"Missing coverage IDs: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"Unknown coverage IDs: {', '.join(sorted(extra))}")
    if report.get("readiness") != READY:
        errors.append(f"Report readiness must be '{READY}'")
    return claim_locations


def verify_scope_and_status(
    report_dir: Path,
    report: dict[str, object],
    phase: str,
    errors: list[str],
) -> None:
    expected_status = "REPORT_READY" if phase == "report" else "COMPLETE"
    if report.get("status") != expected_status:
        errors.append(f"report.json status must be {expected_status} for {phase} phase")
    scope = report.get("scope")
    if not isinstance(scope, dict):
        errors.append("report.json scope must be an object")
        return
    if scope.get("frozen") is not True:
        errors.append("Declared Scope is not frozen")
    relative = str(scope.get("path", ""))
    scope_path = (report_dir / relative).resolve()
    try:
        scope_path.relative_to(report_dir)
    except ValueError:
        errors.append("Declared Scope path escapes the report directory")
        return
    try:
        content = scope_path.read_bytes()
    except OSError as exc:
        errors.append(f"Declared Scope is unreadable: {exc}")
        return
    digest = str(scope.get("sha256", ""))
    if not HEX64_RE.fullmatch(digest) or digest != sha256(content):
        errors.append("Declared Scope digest does not match research/scope.md")


def verify_run(report_dir: Path, run_id: str, errors: list[str]) -> dict[str, object]:
    if not SAFE_ID_RE.fullmatch(run_id):
        errors.append(f"Recorded run has unsafe ID: {run_id}")
        return {}
    run_dir = report_dir / "evidence" / "runs" / run_id
    meta = load_json(run_dir / "meta.json", errors)
    if not meta:
        return {}
    if meta.get("schema_version") != 1:
        errors.append(f"Recorded run has unsupported schema: {run_id}")
    if meta.get("id") != run_id:
        errors.append(f"Recorded run metadata ID mismatch: {run_id}")
    argv = meta.get("argv")
    if not isinstance(argv, list) or not argv or not all(isinstance(value, str) for value in argv):
        errors.append(f"Recorded run argv must be a nonempty string list: {run_id}")
    cwd = meta.get("cwd")
    if not isinstance(cwd, str) or not Path(cwd).is_absolute():
        errors.append(f"Recorded run cwd must be absolute: {run_id}")
    expected = meta.get("expected_exit")
    actual = meta.get("actual_exit")
    if type(expected) is not int or type(actual) is not int:
        errors.append(f"Recorded run exit codes must be integers: {run_id}")
    matched = type(expected) is int and type(actual) is int and expected == actual
    if meta.get("matched_expectation") is not matched or not matched:
        errors.append(f"Recorded run did not match expected exit: {run_id}")
    if meta.get("execution_error") != "":
        errors.append(f"Recorded run has an execution error: {run_id}")
    started = parse_utc(
        meta.get("started_at_utc"), f"Recorded run {run_id} start", errors
    )
    finished = parse_utc(
        meta.get("finished_at_utc"), f"Recorded run {run_id} finish", errors
    )
    if started is not None and finished is not None and started > finished:
        errors.append(f"Recorded run timestamps are reversed: {run_id}")
    for filename, field in (("stdout.txt", "stdout_sha256"), ("stderr.txt", "stderr_sha256")):
        output_path = run_dir / filename
        try:
            data = output_path.read_bytes()
        except OSError as exc:
            errors.append(f"Recorded run output is unreadable ({run_id}/{filename}): {exc}")
            continue
        digest = str(meta.get(field, ""))
        if not HEX64_RE.fullmatch(digest) or digest != sha256(data):
            errors.append(f"Recorded run output hash mismatch: {run_id}/{filename}")
    return meta


def verify_claims(
    report_dir: Path,
    provenance: dict[str, object],
    parsed: dict[Path, BookParser],
    html_claim_ids: set[str],
    coverage_claim_locations: dict[str, set[str]],
    errors: list[str],
) -> dict[str, dict[str, object]]:
    path = report_dir / "evidence" / "claims.jsonl"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        errors.append(f"Cannot read claims ledger: {exc}")
        return {}
    claims: dict[str, dict[str, object]] = {}
    databases: set[str] = set()
    repositories = provenance.get("repositories", {})
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            claim = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid claims.jsonl line {number}: {exc}")
            continue
        if not isinstance(claim, dict):
            errors.append(f"Claim line {number} is not an object")
            continue
        claim_id = str(claim.get("id", ""))
        if not claim_id or claim_id in claims:
            errors.append(f"Missing or duplicate claim ID at line {number}: {claim_id}")
            continue
        claims[claim_id] = claim
        database = str(claim.get("database", ""))
        databases.add(database)
        if database not in ALLOWED_DATABASES:
            errors.append(f"Claim {claim_id} has invalid database: {database}")
        expected_prefix = {
            "cubrid": "CUBRID-C",
            "postgresql": "PG-C",
            "mysql": "MYSQL-C",
            "comparison": "CMP-C",
        }.get(database, "")
        if expected_prefix and not re.fullmatch(re.escape(expected_prefix) + r"\d{3,}", claim_id):
            errors.append(f"Claim {claim_id} does not match the {database} ID prefix")
        if claim.get("kind") not in ALLOWED_KINDS:
            errors.append(f"Claim {claim_id} has invalid kind: {claim.get('kind')}")
        if claim.get("confidence") not in ALLOWED_CONFIDENCE:
            errors.append(f"Claim {claim_id} has invalid confidence: {claim.get('confidence')}")
        if not KOREAN_RE.search(str(claim.get("claim_ko", ""))):
            errors.append(f"Claim {claim_id} needs Korean claim text")
        if "limitations_ko" not in claim or not isinstance(claim.get("limitations_ko"), str):
            errors.append(f"Claim {claim_id} needs a limitations_ko string")
        if database in {"cubrid", "postgresql", "mysql"}:
            expected = repositories.get(database, {}) if isinstance(repositories, dict) else {}
            if not isinstance(expected, dict):
                errors.append(f"Claim {claim_id} cannot resolve {database} provenance")
                expected = {}
            if claim.get("revision") != expected.get("head"):
                errors.append(f"Claim {claim_id} revision does not match {database} provenance")
        source_refs = claim.get("source_refs")
        if not isinstance(source_refs, list):
            errors.append(f"Claim {claim_id} source_refs must be a list")
            source_refs = []
        comparison_databases: set[str] = set()
        for ref in source_refs:
            if not isinstance(ref, dict):
                errors.append(f"Claim {claim_id} has invalid source ref")
                continue
            ref_database = database if database != "comparison" else str(ref.get("database", ""))
            if ref_database not in {"cubrid", "postgresql", "mysql"}:
                errors.append(f"Claim {claim_id} source ref has invalid database: {ref_database}")
                continue
            comparison_databases.add(ref_database)
            repo = repositories.get(ref_database, {}) if isinstance(repositories, dict) else {}
            if not isinstance(repo, dict):
                errors.append(f"Claim {claim_id} cannot resolve {ref_database} provenance")
                continue
            root = Path(str(repo.get("root", "")))
            source_path = (root / str(ref.get("path", ""))).resolve()
            try:
                source_path.relative_to(root.resolve())
            except ValueError:
                errors.append(f"Claim {claim_id} source path escapes repository")
                continue
            if not source_path.is_file():
                errors.append(f"Claim {claim_id} source file is missing: {source_path}")
                continue
            try:
                source_data = source_path.read_bytes()
                source_lines = source_data.decode("utf-8", "replace").splitlines()
            except OSError as exc:
                errors.append(f"Claim {claim_id} source file is unreadable: {exc}")
                continue
            digest = sha256(source_data)
            if not HEX64_RE.fullmatch(str(ref.get("file_sha256", ""))):
                errors.append(f"Claim {claim_id} source hash is not 64-hex")
            elif ref.get("file_sha256") != digest:
                errors.append(f"Claim {claim_id} source hash drift: {source_path}")
            if not str(ref.get("symbol", "")).strip():
                errors.append(f"Claim {claim_id} source ref has no symbol")
            start, end = ref.get("line_start"), ref.get("line_end")
            if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start:
                errors.append(f"Claim {claim_id} has invalid line range")
            elif end > len(source_lines):
                errors.append(f"Claim {claim_id} line range exceeds file: {source_path}")
            else:
                cited_lines = source_lines[start - 1 : end]
                if str(ref.get("symbol", "")) not in "\n".join(cited_lines):
                    errors.append(f"Claim {claim_id} symbol is outside its cited range")
            committed = run(
                ["git", "-C", str(root), "show", f"{repo.get('head')}:{ref.get('path')}"] ,
                check=False,
            )
            expected_state = (
                "COMMIT"
                if committed.returncode == 0 and sha256(committed.stdout) == digest
                else "WORKTREE"
            )
            if ref.get("evidence_state") != expected_state:
                errors.append(
                    f"Claim {claim_id} evidence_state must be {expected_state}: {source_path}"
                )
        runtime_ids = claim.get("runtime_run_ids")
        if not isinstance(runtime_ids, list):
            errors.append(f"Claim {claim_id} runtime_run_ids must be a list")
            runtime_ids = []
        for run_id in runtime_ids:
            verify_run(report_dir, str(run_id), errors)
        kind = claim.get("kind")
        confidence = claim.get("confidence")
        evidence_matrix = {
            "source": (True, False, {"SOURCE-CONFIRMED"}),
            "runtime": (False, True, {"RUNTIME-OBSERVED"}),
            "source+runtime": (True, True, {"SOURCE+RUNTIME-CONFIRMED"}),
            "documented-intent": (True, False, {"DOCUMENTED"}),
            "inference": (False, False, {"INFERRED"}),
            "unknown": (False, False, {"UNKNOWN"}),
            "analogy": (True, False, {"SOURCE-CONFIRMED", "INFERRED"}),
        }
        if kind in evidence_matrix:
            require_source, require_runtime, allowed_confidence = evidence_matrix[kind]
            if require_source and not source_refs:
                errors.append(f"Claim {claim_id} kind {kind} requires source_refs")
            if require_runtime and not runtime_ids:
                errors.append(f"Claim {claim_id} kind {kind} requires runtime_run_ids")
            if kind in {"source", "documented-intent", "analogy"} and runtime_ids:
                errors.append(f"Claim {claim_id} kind {kind} may not carry runtime evidence")
            if kind == "runtime" and source_refs:
                errors.append(f"Claim {claim_id} runtime kind may not carry source evidence")
            if confidence not in allowed_confidence:
                errors.append(f"Claim {claim_id} kind/confidence mismatch")
        if kind in {"inference", "unknown"} and not KOREAN_RE.search(
            str(claim.get("limitations_ko", ""))
        ):
            errors.append(f"Claim {claim_id} {kind} needs Korean limitations/falsifier")
        if database == "comparison":
            if kind != "analogy":
                errors.append(f"Comparison claim {claim_id} must use analogy kind")
            if comparison_databases != {"cubrid", "postgresql", "mysql"}:
                errors.append(f"Comparison claim {claim_id} must cite all three databases")
            if claim.get("analogy_class") not in {
                "equivalent", "partial analogy", "no equivalent"
            }:
                errors.append(f"Comparison claim {claim_id} has invalid analogy_class")
        locations = claim.get("report_locations")
        if not isinstance(locations, list) or not locations:
            errors.append(f"Claim {claim_id} has no report locations")
            continue
        for location in locations:
            text = str(location)
            file_part, separator, fragment = text.partition("#")
            report_path = (report_dir / file_part).resolve()
            if report_path not in parsed or not separator or fragment not in set(parsed[report_path].ids):
                errors.append(f"Claim {claim_id} has invalid report location: {text}")
            elif claim_id not in parsed[report_path].claims_by_anchor.get(fragment, set()):
                errors.append(f"Claim {claim_id} is not declared at report location: {text}")
        missing_coverage_locations = coverage_claim_locations.get(claim_id, set()) - {
            str(value) for value in locations
        }
        for location in sorted(missing_coverage_locations):
            errors.append(f"Claim {claim_id} does not support its coverage location: {location}")

    missing_databases = ALLOWED_DATABASES - databases
    if missing_databases:
        errors.append(f"Claims ledger lacks databases: {', '.join(sorted(missing_databases))}")
    known = set(claims)
    for missing_id in sorted((html_claim_ids | set(coverage_claim_locations)) - known):
        errors.append(f"HTML/coverage references unknown claim ID: {missing_id}")
    return claims


def verify_central_behaviors(
    report_dir: Path,
    report: dict[str, object],
    claims: dict[str, dict[str, object]],
    parsed: dict[Path, BookParser],
    errors: list[str],
) -> dict[str, dict[str, object]]:
    behaviors = report.get("central_behaviors")
    if not isinstance(behaviors, list) or not behaviors:
        errors.append("report.json must declare at least one central behavior")
        return {}
    coverage_entries = {
        str(item.get("id")): item
        for item in report.get("coverage", [])
        if isinstance(item, dict)
    } if isinstance(report.get("coverage"), list) else {}
    known_coverage = set(coverage_entries)
    by_id: dict[str, dict[str, object]] = {}
    seen: set[str] = set()
    referenced_experiments: set[str] = set()
    referenced_quizzes: set[str] = set()
    for behavior in behaviors:
        if not isinstance(behavior, dict):
            errors.append("Central behavior entry must be an object")
            continue
        behavior_id = str(behavior.get("id", ""))
        if not SAFE_ID_RE.fullmatch(behavior_id) or behavior_id in seen:
            errors.append(f"Central behavior has missing/duplicate/unsafe ID: {behavior_id}")
        seen.add(behavior_id)
        by_id[behavior_id] = behavior
        if not KOREAN_RE.search(str(behavior.get("name_ko", ""))):
            errors.append(f"Central behavior {behavior_id} needs a Korean name")
        claim_ids = behavior.get("claim_ids")
        if not isinstance(claim_ids, list) or not claim_ids:
            errors.append(f"Central behavior {behavior_id} has no claims")
            claim_ids = []
        for claim_id in claim_ids:
            claim = claims.get(str(claim_id))
            if claim is None:
                errors.append(f"Central behavior {behavior_id} references unknown claim: {claim_id}")
            elif claim.get("kind") in {"inference", "unknown"}:
                errors.append(f"Central behavior {behavior_id} depends on weak claim: {claim_id}")
        behavior_databases = {
            str(claims[str(claim_id)].get("database"))
            for claim_id in claim_ids
            if str(claim_id) in claims
            and claims[str(claim_id)].get("kind") not in {"inference", "unknown"}
        }
        if "cubrid" not in behavior_databases:
            errors.append(f"Central behavior {behavior_id} lacks a direct CUBRID claim")
        missing_comparison = {"postgresql", "mysql", "comparison"} - behavior_databases
        if missing_comparison:
            errors.append(
                f"Central behavior {behavior_id} lacks comparison claims for: "
                f"{', '.join(sorted(missing_comparison))}"
            )
        coverage_ids = behavior.get("coverage_ids")
        if not isinstance(coverage_ids, list) or not coverage_ids:
            errors.append(f"Central behavior {behavior_id} has no coverage obligations")
        else:
            for coverage_id in coverage_ids:
                if str(coverage_id) not in known_coverage:
                    errors.append(
                        f"Central behavior {behavior_id} references unknown coverage: {coverage_id}"
                    )
        experiment_ids = behavior.get("experiment_ids")
        if not isinstance(experiment_ids, list) or not experiment_ids:
            errors.append(f"Central behavior {behavior_id} has no experiments")
        else:
            for experiment_id in experiment_ids:
                value = str(experiment_id)
                referenced_experiments.add(value)
                if not re.fullmatch(r"experiment-[1-9][0-9]*", value):
                    errors.append(f"Central behavior {behavior_id} has invalid experiment ID: {value}")
        quiz_ids = behavior.get("quiz_ids")
        if not isinstance(quiz_ids, list) or not quiz_ids:
            errors.append(f"Central behavior {behavior_id} has no quizzes")
        else:
            for quiz_id in quiz_ids:
                value = str(quiz_id)
                referenced_quizzes.add(value)
                if not re.fullmatch(r"quiz-[1-9][0-9]*", value):
                    errors.append(f"Central behavior {behavior_id} has invalid quiz ID: {value}")
        concepts = behavior.get("grill_concepts")
        if not isinstance(concepts, list) or not concepts:
            errors.append(f"Central behavior {behavior_id} has no grill concepts")
        elif any(str(value) not in MASTERY_IDS for value in concepts):
            errors.append(f"Central behavior {behavior_id} has unknown grill concepts")
        chapter = str(behavior.get("chapter", ""))
        anchor = str(behavior.get("anchor", ""))
        chapter_path = (report_dir / chapter).resolve() if chapter else None
        if not chapter_path or chapter_path not in parsed or anchor not in set(parsed[chapter_path].ids):
            errors.append(f"Central behavior {behavior_id} has invalid chapter anchor")
        elif not (set(str(value) for value in claim_ids) & parsed[chapter_path].claims_by_anchor.get(anchor, set())):
            errors.append(f"Central behavior {behavior_id} anchor exposes none of its claims")
        coverage_locations = {
            (str(coverage_entries[value].get("chapter", "")), str(coverage_entries[value].get("anchor", "")))
            for value in (str(item) for item in coverage_ids)
            if value in coverage_entries
        } if isinstance(coverage_ids, list) else set()
        if (chapter, anchor) not in coverage_locations:
            errors.append(
                f"Central behavior {behavior_id} anchor is not one of its coverage locations"
            )

    experiment_dirs = {path.name for path in (report_dir / "experiments").glob("experiment-*") if path.is_dir()}
    quiz_dirs = {path.name for path in (report_dir / "quiz").glob("quiz-*") if path.is_dir()}
    for value in sorted(experiment_dirs - referenced_experiments):
        errors.append(f"Experiment is not linked to a central behavior: {value}")
    for value in sorted(referenced_experiments - experiment_dirs):
        errors.append(f"Central behavior references missing experiment: {value}")
    for value in sorted(quiz_dirs - referenced_quizzes):
        errors.append(f"Quiz is not linked to a central behavior: {value}")
    for value in sorted(referenced_quizzes - quiz_dirs):
        errors.append(f"Central behavior references missing quiz: {value}")
    declared_concepts = {
        str(concept)
        for behavior in behaviors
        if isinstance(behavior, dict) and isinstance(behavior.get("grill_concepts"), list)
        for concept in behavior["grill_concepts"]
    }
    if declared_concepts != set(MASTERY_IDS):
        errors.append("Central behaviors must map every and only the eight Live Grill concepts")
    return by_id


def verify_runtime_snapshot(
    report_dir: Path,
    relative: object,
    provenance: dict[str, object],
    errors: list[str],
    *,
    require_current: bool,
) -> tuple[dict[str, object], datetime | None]:
    if not isinstance(relative, str) or not relative:
        errors.append("Runtime tools snapshot path must be a nonempty string")
        return {}, None
    path = (report_dir / relative).resolve()
    try:
        path.relative_to(report_dir / "evidence")
    except ValueError:
        errors.append(f"Runtime tools snapshot must stay under evidence/: {relative}")
        return {}, None
    snapshot = load_json(path, errors)
    if not snapshot:
        return {}, None
    repositories = provenance.get("repositories")
    cubrid_repo = repositories.get("cubrid") if isinstance(repositories, dict) else None
    if not isinstance(cubrid_repo, dict):
        errors.append("Runtime snapshot cannot resolve CUBRID provenance")
        return snapshot, None
    cubrid_root = Path(str(cubrid_repo.get("root", ""))).resolve()
    if (
        snapshot.get("schema_version") != 1
        or snapshot.get("source_root") != str(cubrid_root)
        or snapshot.get("source_head") != cubrid_repo.get("head")
    ):
        errors.append(f"Runtime snapshot source identity is invalid: {relative}")
    build_run_id = snapshot.get("build_run_id")
    if not isinstance(build_run_id, str):
        errors.append(f"Runtime snapshot has no build run ID: {relative}")
        build_meta = {}
    else:
        build_meta = verify_run(report_dir, build_run_id, errors)
    if build_meta:
        if build_meta.get("expected_exit") != 0 or build_meta.get("actual_exit") != 0:
            errors.append(f"Runtime snapshot build did not exit zero: {relative}")
        if build_meta.get("argv") != ["just", "build"] or Path(
            str(build_meta.get("cwd", ""))
        ).resolve() != cubrid_root:
            errors.append(
                f"Runtime snapshot build must be `just build` in pinned CUBRID root: {relative}"
            )
        if build_meta.get("kind") != "build":
            errors.append(f"Runtime snapshot requires a dedicated build receipt: {relative}")
        meta_path = report_dir / "evidence" / "runs" / str(build_run_id) / "meta.json"
        try:
            meta_digest = sha256(meta_path.read_bytes())
        except OSError as exc:
            errors.append(f"Runtime snapshot build metadata is unreadable: {exc}")
        else:
            if snapshot.get("build_meta_sha256") != meta_digest:
                errors.append(f"Runtime snapshot build metadata hash mismatch: {relative}")
    captured = parse_utc(snapshot.get("captured_at_utc"), f"Runtime snapshot {relative}", errors)
    if build_meta and captured is not None:
        finished = parse_utc(
            build_meta.get("finished_at_utc"),
            f"Runtime snapshot build {build_run_id} finish",
            errors,
        )
        if finished is not None and captured < finished:
            errors.append(f"Runtime snapshot predates its build: {relative}")
    tools = snapshot.get("tools")
    snapshot_environment = snapshot.get("runtime_environment")
    if not isinstance(snapshot_environment, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in snapshot_environment.items()
    ):
        errors.append(f"Runtime snapshot lacks a valid runtime_environment: {relative}")
        snapshot_environment = {}
    captured_cubrid = str(snapshot_environment.get("CUBRID", ""))
    captured_install = Path(captured_cubrid).resolve() if Path(captured_cubrid).is_absolute() else None
    if captured_install is None:
        errors.append(f"Runtime snapshot has no absolute CUBRID install root: {relative}")
    if build_meta:
        receipt = build_meta.get("build_receipt")
        if not isinstance(receipt, dict):
            errors.append(f"Runtime snapshot build receipt is missing: {relative}")
        else:
            if (
                snapshot.get("worktree_environment_sha256")
                != receipt.get("worktree_environment_sha256")
                or build_meta.get("runtime_environment_sha256")
                != receipt.get("worktree_environment_sha256")
            ):
                errors.append(f"Runtime/build worktree environment mismatch: {relative}")
            build_environment = receipt.get("environment")
            if not isinstance(build_environment, dict) or build_environment.get("CUBRID") != captured_cubrid:
                errors.append(f"Runtime/build CUBRID install root mismatch: {relative}")
            cmake = receipt.get("cmake_cache")
            if not isinstance(cmake, dict):
                errors.append(f"Runtime build lacks CMake receipt: {relative}")
            else:
                cache_path = (report_dir / str(cmake.get("path", ""))).resolve()
                try:
                    cache_path.relative_to(report_dir / "evidence" / "runs")
                    cache_data = cache_path.read_bytes()
                except (ValueError, OSError) as exc:
                    errors.append(f"Runtime build CMake receipt is invalid: {exc}")
                else:
                    if cmake.get("sha256") != sha256(cache_data):
                        errors.append(f"Runtime build CMake receipt hash mismatch: {relative}")
                if cmake.get("source_root") != str(cubrid_root) or cmake.get(
                    "install_prefix"
                ) != captured_cubrid:
                    errors.append(f"Runtime build CMake roots are not pinned: {relative}")
            snapshots = receipt.get("source_snapshots")
            source_before = receipt.get("source_before")
            source_after = receipt.get("source_after")
            if (
                receipt.get("source_unchanged") is not True
                or not isinstance(snapshots, dict)
                or not isinstance(source_before, dict)
                or source_before != source_after
            ):
                errors.append(f"Runtime build source receipt is incomplete: {relative}")
            else:
                expected_fields = {
                    "status.porcelain-v1.z": "status_sha256",
                    "worktree.diff": "diff_sha256",
                    "index.diff": "cached_diff_sha256",
                }
                for name, field in expected_fields.items():
                    item = snapshots.get(name)
                    if not isinstance(item, dict):
                        errors.append(f"Runtime build source snapshot is missing: {name}")
                        continue
                    source_path = (report_dir / str(item.get("path", ""))).resolve()
                    try:
                        source_path.relative_to(report_dir / "evidence" / "runs")
                        source_data = source_path.read_bytes()
                    except (ValueError, OSError) as exc:
                        errors.append(f"Runtime build source snapshot is invalid: {exc}")
                    else:
                        digest = sha256(source_data)
                        if item.get("sha256") != digest or source_before.get(field) != digest:
                            errors.append(f"Runtime build source snapshot hash mismatch: {name}")
            receipt_identity = receipt.get("install_identity")
            snapshot_identity = {
                "tools": snapshot.get("tools"),
                "release_identity": snapshot.get("release_identity"),
            }
            if receipt_identity != snapshot_identity:
                errors.append(f"Runtime snapshot differs from captured build outputs: {relative}")
    if not isinstance(tools, dict):
        errors.append(f"Runtime snapshot lacks tools object: {relative}")
        return snapshot, captured
    for name in ("csql", "cubrid", "cub_server"):
        tool = tools.get(name)
        if not isinstance(tool, dict):
            errors.append(f"Runtime snapshot lacks {name}: {relative}")
            continue
        tool_path = Path(str(tool.get("path", "")))
        if not tool_path.is_absolute() or not HEX64_RE.fullmatch(str(tool.get("sha256", ""))):
            errors.append(f"Runtime snapshot has invalid {name} path/hash: {relative}")
        if captured_install is not None:
            try:
                tool_path.resolve().relative_to(captured_install)
            except ValueError:
                errors.append(f"Runtime snapshot {name} is outside its CUBRID install root")
        if require_current:
            try:
                current_hash = sha256(tool_path.resolve().read_bytes())
            except OSError as exc:
                errors.append(f"Active runtime tool is unreadable ({name}): {exc}")
                continue
            identity_changed = (
                tool.get("path") != str(tool_path.resolve())
                or tool.get("sha256") != current_hash
            )
            if identity_changed:
                errors.append(f"Active runtime tool identity drift: {name}")
    release = snapshot.get("release_identity")
    if not isinstance(release, dict):
        errors.append(f"Runtime snapshot lacks cubrid_rel release identity: {relative}")
    else:
        release_path = Path(str(release.get("path", "")))
        if (
            not release_path.is_absolute()
            or not HEX64_RE.fullmatch(str(release.get("sha256", "")))
            or release.get("exit") != 0
            or not str(release.get("output", "")).strip()
        ):
            errors.append(f"Runtime snapshot has invalid cubrid_rel identity: {relative}")
        if captured_install is not None:
            try:
                release_path.resolve().relative_to(captured_install)
            except ValueError:
                errors.append("Runtime snapshot cubrid_rel is outside its CUBRID install root")
        if require_current:
            current_environment = {
                str(key): str(value) for key, value in snapshot_environment.items()
            }
            try:
                release_hash = sha256(release_path.resolve().read_bytes())
            except OSError as exc:
                errors.append(f"Active cubrid_rel is unreadable: {exc}")
            else:
                release_result = run(
                    [str(release_path.resolve())], check=False, env=current_environment
                )
                release_output = (release_result.stdout + release_result.stderr).decode(
                    "utf-8", "replace"
                ).strip()[:2000]
                if (
                    release.get("path") != str(release_path.resolve())
                    or release.get("sha256") != release_hash
                    or release.get("exit") != release_result.returncode
                    or release.get("output") != release_output
                ):
                    errors.append("Active cubrid_rel release identity drift")
    return snapshot, captured


def verify_runtime_contract(
    report_dir: Path,
    report: dict[str, object],
    provenance: dict[str, object],
    errors: list[str],
) -> tuple[str, str]:
    runtime = report.get("runtime")
    if not isinstance(runtime, dict):
        errors.append("report.json runtime must be an object")
        return "", ""
    build_run_id = runtime.get("runtime_build_run_id")
    baseline_path = runtime.get("baseline_tools_snapshot")
    active_path = runtime.get("active_tools_snapshot")
    if not isinstance(build_run_id, str) or not build_run_id:
        errors.append("report.json needs runtime.runtime_build_run_id")
        build_run_id = ""
    baseline, _ = verify_runtime_snapshot(
        report_dir, baseline_path, provenance, errors, require_current=baseline_path == active_path
    )
    if baseline and baseline.get("id") != "baseline":
        errors.append("Baseline runtime snapshot must have id=baseline")
    if baseline and baseline.get("build_run_id") != build_run_id:
        errors.append("runtime_build_run_id differs from baseline runtime snapshot")
    if active_path == baseline_path:
        active = baseline
    else:
        active, _ = verify_runtime_snapshot(
            report_dir, active_path, provenance, errors, require_current=True
        )
    if not active:
        errors.append("report.json has no valid active runtime tools snapshot")
    return str(baseline_path or ""), str(active_path or "")


def verify_execution_bound_runner(
    owner_id: str,
    run_id: str,
    meta: dict[str, object],
    runner: Path,
    runner_digest: str,
    errors: list[str],
) -> None:
    bound_files = meta.get("bound_files")
    if not isinstance(bound_files, list):
        errors.append(f"{owner_id} run has no execution-time bound files: {run_id}")
        return
    matches = [
        entry
        for entry in bound_files
        if isinstance(entry, dict)
        and Path(str(entry.get("path", ""))).resolve() == runner
    ]
    if len(matches) != 1:
        errors.append(f"{owner_id} run did not bind its runner bytes: {run_id}")
        return
    entry = matches[0]
    if (
        entry.get("before_sha256") != runner_digest
        or entry.get("after_sha256") != runner_digest
    ):
        errors.append(f"{owner_id} runner bytes changed or differ from execution: {run_id}")


def verify_lifecycle_run_spec(
    report_dir: Path,
    owner_dir: Path,
    owner_id: str,
    phase: str,
    spec: object,
    runtime_snapshot: object,
    expected_environment_hash: str,
    snapshot_time: datetime | None,
    errors: list[str],
) -> tuple[str, dict[str, object]]:
    if not isinstance(spec, dict):
        errors.append(f"{owner_id} {phase} run spec must be an object")
        return "", {}
    run_id = str(spec.get("run_id", ""))
    runner_value = spec.get("runner")
    if not isinstance(runner_value, str) or not runner_value:
        errors.append(f"{owner_id} {phase} run spec has no runner")
        return run_id, verify_run(report_dir, run_id, errors) if run_id else {}
    runner = (owner_dir / runner_value).resolve()
    try:
        runner.relative_to(owner_dir.resolve())
        runner_data = runner.read_bytes()
    except (ValueError, OSError) as exc:
        errors.append(f"{owner_id} {phase} runner is invalid: {exc}")
        return run_id, verify_run(report_dir, run_id, errors) if run_id else {}
    digest = sha256(runner_data)
    if spec.get("runner_sha256") != digest:
        errors.append(f"{owner_id} {phase} runner hash mismatch: {run_id}")
    argv = string_list(spec.get("runner_argv"), f"{owner_id} {phase} runner_argv", errors)
    meta = verify_run(report_dir, run_id, errors) if run_id else {}
    if not meta:
        return run_id, meta
    if Path(str(meta.get("cwd", ""))).resolve() != owner_dir.resolve():
        errors.append(f"{owner_id} {phase} cwd must be its artifact directory: {run_id}")
    if meta.get("argv") != argv:
        errors.append(f"{owner_id} {phase} argv differs from its run spec: {run_id}")
    if meta.get("expected_exit") != 0 or meta.get("actual_exit") != 0:
        errors.append(f"{owner_id} {phase} run must exit zero: {run_id}")
    if (
        meta.get("runtime_tools_snapshot") != runtime_snapshot
        or meta.get("runtime_environment_sha256") != expected_environment_hash
    ):
        errors.append(f"{owner_id} {phase} run did not use the sealed runtime: {run_id}")
    verify_execution_bound_runner(owner_id, run_id, meta, runner, digest, errors)
    if snapshot_time is not None:
        started = parse_utc(meta.get("started_at_utc"), f"{owner_id} {phase} {run_id}", errors)
        if started is not None and started < snapshot_time:
            errors.append(f"{owner_id} {phase} run predates its runtime snapshot: {run_id}")
    if phase == "observation" and spec.get("observation_kind") not in {
        "sql-output",
        "log",
        "counter",
        "debugger",
        "utility",
        "trace",
    }:
        errors.append(f"{owner_id} observation has invalid observation_kind: {run_id}")
    return run_id, meta


def verify_manifest_lifecycle(
    report_dir: Path,
    owner_dir: Path,
    owner_id: str,
    manifest: dict[str, object],
    trigger_run_ids: list[str],
    runtime_snapshot: object,
    expected_environment_hash: str,
    snapshot_time: datetime | None,
    errors: list[str],
) -> list[str]:
    lifecycle = manifest.get("lifecycle")
    if not isinstance(lifecycle, dict):
        errors.append(f"{owner_id} manifest lacks explicit lifecycle")
        return []
    resources = lifecycle.get("owned_resources")
    if not isinstance(resources, list) or not resources:
        errors.append(f"{owner_id} lifecycle must declare owned resources")
    else:
        for resource in resources:
            if (
                not isinstance(resource, dict)
                or not str(resource.get("name", "")).startswith("cubrid_code_analysis_")
                or not str(resource.get("kind", "")).strip()
                or not KOREAN_RE.search(str(resource.get("owner_ko", "")))
            ):
                errors.append(f"{owner_id} has an invalid owned-resource declaration")
    passes = lifecycle.get("passes")
    expected_passes = (
        2
        if owner_id.startswith("quiz-")
        else int(manifest.get("repetitions", 0))
        if type(manifest.get("repetitions")) is int
        else 0
    )
    if not isinstance(passes, list) or len(passes) != expected_passes or expected_passes < 1:
        errors.append(f"{owner_id} lifecycle pass count must equal {expected_passes}")
        return []
    seen_run_ids: set[str] = set()
    lifecycle_trigger_ids: list[str] = []
    observation_ids: list[str] = []
    previous_cleanup_finish: datetime | None = None
    for position, pass_entry in enumerate(passes, 1):
        if not isinstance(pass_entry, dict) or pass_entry.get("pass") != position:
            errors.append(f"{owner_id} lifecycle passes must be contiguous from 1")
            continue
        phase_meta: dict[str, list[dict[str, object]]] = {
            "setup": [], "trigger": [], "observation": [], "cleanup": []
        }
        for phase in ("setup", "observation", "cleanup"):
            specs = pass_entry.get(phase)
            if not isinstance(specs, list) or not specs:
                errors.append(f"{owner_id} pass {position} needs {phase} runs")
                continue
            for spec in specs:
                run_id, meta = verify_lifecycle_run_spec(
                    report_dir,
                    owner_dir,
                    owner_id,
                    phase,
                    spec,
                    runtime_snapshot,
                    expected_environment_hash,
                    snapshot_time,
                    errors,
                )
                if run_id in seen_run_ids:
                    errors.append(f"{owner_id} lifecycle reuses run ID: {run_id}")
                seen_run_ids.add(run_id)
                if meta:
                    phase_meta[phase].append(meta)
                if phase == "observation":
                    observation_ids.append(run_id)
        pass_triggers = string_list(
            pass_entry.get("trigger_run_ids"),
            f"{owner_id} pass {position} trigger_run_ids",
            errors,
        )
        for run_id in pass_triggers:
            if run_id in seen_run_ids:
                errors.append(f"{owner_id} lifecycle reuses run ID: {run_id}")
            seen_run_ids.add(run_id)
            lifecycle_trigger_ids.append(run_id)
            meta = verify_run(report_dir, run_id, errors)
            if meta:
                phase_meta["trigger"].append(meta)
        def earliest(phase: str, field: str) -> datetime | None:
            values = [
                parse_utc(meta.get(field), f"{owner_id} {phase} boundary", errors)
                for meta in phase_meta[phase]
            ]
            valid = [value for value in values if value is not None]
            return min(valid) if valid else None
        def latest(phase: str, field: str) -> datetime | None:
            values = [
                parse_utc(meta.get(field), f"{owner_id} {phase} boundary", errors)
                for meta in phase_meta[phase]
            ]
            valid = [value for value in values if value is not None]
            return max(valid) if valid else None
        boundaries = (
            ("setup", "trigger"),
            ("trigger", "observation"),
            ("observation", "cleanup"),
        )
        for first, second in boundaries:
            first_finish = latest(first, "finished_at_utc")
            second_start = earliest(second, "started_at_utc")
            if first_finish and second_start and first_finish > second_start:
                errors.append(
                    f"{owner_id} pass {position} violates {first}->{second} ordering"
                )
        setup_start = earliest("setup", "started_at_utc")
        if previous_cleanup_finish and setup_start and previous_cleanup_finish > setup_start:
            errors.append(f"{owner_id} pass {position} began before prior cleanup")
        previous_cleanup_finish = latest("cleanup", "finished_at_utc")
    if lifecycle_trigger_ids != trigger_run_ids:
        errors.append(f"{owner_id} lifecycle trigger IDs differ from manifest run_ids")
    return observation_ids


def verify_runner_manifest(
    report_dir: Path,
    owner_dir: Path,
    manifest_name: str,
    owner_id: str,
    report: dict[str, object],
    claims: dict[str, dict[str, object]],
    provenance: dict[str, object],
    active_runtime_snapshot: str,
    errors: list[str],
) -> tuple[dict[str, object], list[str], list[str]]:
    manifest = load_json(owner_dir / manifest_name, errors)
    if not manifest:
        return {}, [], []
    if manifest.get("schema_version") != 1 or manifest.get("id") != owner_id:
        errors.append(f"Invalid manifest identity: {owner_dir / manifest_name}")
    behavior_ids = manifest.get("behavior_ids")
    if not isinstance(behavior_ids, list) or not behavior_ids:
        errors.append(f"{owner_id} manifest has no behavior IDs")
        behavior_ids = []
    report_behaviors = report.get("central_behaviors")
    if not isinstance(report_behaviors, list):
        report_behaviors = []
    owner_field = "quiz_ids" if owner_id.startswith("quiz-") else "experiment_ids"
    expected_behaviors = set()
    behaviors_by_id: dict[str, dict[str, object]] = {}
    for behavior in report_behaviors:
        if not isinstance(behavior, dict):
            continue
        behavior_id = str(behavior.get("id", ""))
        behaviors_by_id[behavior_id] = behavior
        owner_values = behavior.get(owner_field)
        if isinstance(owner_values, list) and owner_id in owner_values:
            expected_behaviors.add(behavior_id)
    if set(str(value) for value in behavior_ids) != expected_behaviors:
        errors.append(f"{owner_id} behavior linkage does not match report.json")
    claim_ids = manifest.get("claim_ids")
    if not isinstance(claim_ids, list) or not claim_ids:
        errors.append(f"{owner_id} manifest has no claim IDs")
        claim_ids = []
    for claim_id in claim_ids:
        if str(claim_id) not in claims:
            errors.append(f"{owner_id} manifest references unknown claim: {claim_id}")
    normalized_claim_ids = {str(value) for value in claim_ids}
    linked_claim_union: set[str] = set()
    for behavior_id in behavior_ids:
        behavior = behaviors_by_id.get(str(behavior_id))
        behavior_claims = {
            str(value) for value in behavior.get("claim_ids", [])
        } if isinstance(behavior, dict) and isinstance(behavior.get("claim_ids"), list) else set()
        linked_claim_union.update(behavior_claims)
        if not (normalized_claim_ids & behavior_claims):
            errors.append(f"{owner_id} claims do not intersect behavior {behavior_id}")
    if not normalized_claim_ids.issubset(linked_claim_union):
        errors.append(f"{owner_id} claims are not a subset of its linked behaviors")
    if not KOREAN_RE.search(str(manifest.get("oracle_ko", ""))):
        errors.append(f"{owner_id} manifest needs a Korean oracle")
    if manifest.get("cubrid_runtime_only") is not True:
        errors.append(f"{owner_id} must declare cubrid_runtime_only=true")
    snapshot_path = manifest.get("runtime_tools_snapshot")
    snapshot, snapshot_time = verify_runtime_snapshot(
        report_dir,
        snapshot_path,
        provenance,
        errors,
        require_current=snapshot_path == active_runtime_snapshot,
    )
    snapshot_tools = snapshot.get("tools") if isinstance(snapshot, dict) else None
    snapshot_environment = snapshot.get("runtime_environment") if isinstance(snapshot, dict) else None
    expected_environment_hash = (
        sha256(json.dumps(snapshot_environment, sort_keys=True, separators=(",", ":")).encode())
        if isinstance(snapshot_environment, dict)
        else ""
    )
    if owner_id.startswith("quiz-") and snapshot_path != active_runtime_snapshot:
        errors.append(f"{owner_id} must use the active post-build runtime snapshot")
    if manifest.get("cleanup_verified") is not True:
        errors.append(f"{owner_id} cleanup is not verified")
    runner_name = str(manifest.get("runner", ""))
    runner = (owner_dir / runner_name).resolve()
    try:
        runner.relative_to(owner_dir.resolve())
    except ValueError:
        errors.append(f"{owner_id} runner escapes its directory")
        return manifest, [], []
    runner_digest = ""
    if not runner.is_file():
        errors.append(f"{owner_id} runner is missing: {runner_name}")
    else:
        digest = str(manifest.get("runner_sha256", ""))
        try:
            runner_digest = sha256(runner.read_bytes())
        except OSError as exc:
            errors.append(f"{owner_id} runner is unreadable: {exc}")
        else:
            if not HEX64_RE.fullmatch(digest) or digest != runner_digest:
                errors.append(f"{owner_id} runner hash mismatch")
    runner_argv = string_list(
        manifest.get("runner_argv"), f"{owner_id} runner_argv", errors
    )
    direct_tool = ""
    if runner_argv and isinstance(snapshot_tools, dict):
        executable = Path(runner_argv[0])
        if not executable.is_absolute():
            resolved_executable = shutil.which(
                runner_argv[0],
                path=snapshot_environment.get("PATH") if isinstance(snapshot_environment, dict) else None,
            )
            executable = Path(resolved_executable).resolve() if resolved_executable else executable
        else:
            executable = executable.resolve()
        for name in ("csql", "cubrid"):
            tool = snapshot_tools.get(name)
            if isinstance(tool, dict) and executable == Path(str(tool.get("path", ""))).resolve():
                direct_tool = name
                break
        if not direct_tool:
            errors.append(f"{owner_id} runner_argv must directly execute captured csql or cubrid")
        elif direct_tool != "csql":
            errors.append(
                f"{owner_id} mandatory v1 runner must use csql with a bound input file"
            )
        if any(value in {"--version", "--help", "-h", "-v"} for value in runner_argv[1:]):
            errors.append(f"{owner_id} runner_argv contains a short-circuit help/version option")
        resolved_runner_args = {
            (owner_dir / value).resolve()
            for value in runner_argv[1:]
            if not value.startswith("-")
        }
        if runner not in resolved_runner_args:
            errors.append(f"{owner_id} runner_argv does not pass its hashed runner")
        if direct_tool == "csql":
            input_bound = any(
                value in {"-i", "--input-file"}
                and index + 1 < len(runner_argv)
                and (owner_dir / runner_argv[index + 1]).resolve() == runner
                for index, value in enumerate(runner_argv)
            ) or any(
                value.startswith("--input-file=")
                and (owner_dir / value.split("=", 1)[1]).resolve() == runner
                for value in runner_argv
            )
            if not input_bound:
                errors.append(f"{owner_id} csql runner must be bound by -i/--input-file")
    run_ids = manifest.get("run_ids")
    if not isinstance(run_ids, list) or not run_ids:
        errors.append(f"{owner_id} manifest has no run IDs")
        return manifest, [], []
    normalized_runs = [str(value) for value in run_ids]
    if len(normalized_runs) != len(set(normalized_runs)):
        errors.append(f"{owner_id} manifest has duplicate run IDs")
    for run_id in normalized_runs:
        meta = verify_run(report_dir, run_id, errors)
        if not meta:
            continue
        if Path(str(meta.get("cwd", ""))).resolve() != owner_dir.resolve():
            errors.append(f"{owner_id} run cwd must be its artifact directory: {run_id}")
        if meta.get("expected_exit") != 0 or meta.get("actual_exit") != 0:
            errors.append(f"{owner_id} run must exit zero: {run_id}")
        argv = meta.get("argv")
        if argv != runner_argv:
            errors.append(f"{owner_id} run argv differs from exact runner_argv: {run_id}")
        if (
            meta.get("runtime_tools_snapshot") != snapshot_path
            or meta.get("runtime_environment_sha256") != expected_environment_hash
        ):
            errors.append(f"{owner_id} run did not use its sealed runtime environment: {run_id}")
        # A bound-file receipt is useful when present, but this is an internal
        # authoring workflow.  Do not turn Quiz/Experiment authoring into a
        # mandatory forensic chain-of-custody exercise.
        if runner_digest and meta.get("bound_files"):
            verify_execution_bound_runner(
                owner_id, run_id, meta, runner, runner_digest, errors
            )
        if snapshot_time is not None:
            started = parse_utc(meta.get("started_at_utc"), f"{owner_id} run {run_id}", errors)
            if started is not None and started < snapshot_time:
                errors.append(f"{owner_id} run predates its runtime snapshot: {run_id}")
    observation_runs = normalized_runs
    # Detailed setup/trigger/observation/cleanup receipts are optional.  When
    # an author chooses to supply them, validate them; otherwise trust the
    # concise manifest and the captured primary run.
    if isinstance(manifest.get("lifecycle"), dict):
        observation_runs = verify_manifest_lifecycle(
            report_dir,
            owner_dir,
            owner_id,
            manifest,
            normalized_runs,
            snapshot_path,
            expected_environment_hash,
            snapshot_time,
            errors,
        )
    if not owner_id.startswith("quiz-"):
        runtime_claims = [
            claims[claim_id]
            for claim_id in normalized_claim_ids
            if claim_id in claims
            and claims[claim_id].get("database") == "cubrid"
            and claims[claim_id].get("kind") in {"runtime", "source+runtime"}
        ]
        covered_runs: set[str] = set()
        for claim in runtime_claims:
            values = claim.get("runtime_run_ids")
            if isinstance(values, list):
                covered_runs.update(str(value) for value in values)
        if not runtime_claims or not set(observation_runs).issubset(covered_runs):
            errors.append(
                f"{owner_id} observation runs must be consumed by a linked CUBRID runtime Claim"
            )
    return manifest, normalized_runs, observation_runs


def verify_quizzes(
    report_dir: Path,
    report: dict[str, object],
    claims: dict[str, dict[str, object]],
    provenance: dict[str, object],
    active_runtime_snapshot: str,
    errors: list[str],
) -> None:
    quiz_root = report_dir / "quiz"
    quiz_dirs = sorted(
        (path for path in quiz_root.glob("quiz-*") if path.is_dir()),
        key=lambda value: int(value.name.split("-")[-1]) if value.name.split("-")[-1].isdigit() else 10**9,
    )
    if not quiz_dirs:
        errors.append("At least one quiz/quiz-N directory is required")
        return
    expected_names = [f"quiz-{number}" for number in range(1, len(quiz_dirs) + 1)]
    if [path.name for path in quiz_dirs] != expected_names:
        errors.append("Quiz directories must be contiguous from quiz-1")
    forbidden_runtime = re.compile(r"(^|[\s/])(psql|postgres|mysqld|mysql)([\s/]|$)", re.I)
    for number, quiz_dir in enumerate(quiz_dirs, 1):
        for name in ("quiz.md", "answer.md"):
            path = quiz_dir / name
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                errors.append(f"Cannot read {path}: {exc}")
                continue
            if not KOREAN_RE.search(content):
                errors.append(f"Quiz prose must contain Korean: {path}")
            if PLACEHOLDER_RE.search(content):
                errors.append(f"Quiz placeholder remains: {path}")
        runnable = [
            path for path in quiz_dir.iterdir() if path.is_file() and path.suffix in {".sql", ".sh", ".py"}
        ]
        if not runnable:
            errors.append(f"Quiz has no reproducible SQL/script: {quiz_dir}")
        for script in runnable:
            content = script.read_text(encoding="utf-8", errors="replace")
            if forbidden_runtime.search(content):
                errors.append(f"Quiz script may not require PostgreSQL/MySQL runtime: {script}")
            if script.suffix == ".sh":
                result = run(["bash", "-n", str(script)], check=False)
                if result.returncode:
                    errors.append(f"Shell syntax failed: {script}")
        # Quiz prose and a runnable SQL/script are the contract.  quiz.json is
        # optional evidence for authors who want stronger reproducibility.
        if (quiz_dir / "quiz.json").is_file():
            verify_runner_manifest(
                report_dir,
                quiz_dir,
                "quiz.json",
                quiz_dir.name,
                report,
                claims,
                provenance,
                active_runtime_snapshot,
                errors,
            )


def porcelain_paths(data: bytes) -> set[str]:
    paths: set[str] = set()
    entries = data.split(b"\0")
    index = 0
    while index < len(entries):
        entry = entries[index]
        if len(entry) >= 4:
            status = entry[:2]
            paths.add(entry[3:].decode("utf-8", "surrogateescape"))
            if b"R" in status or b"C" in status:
                index += 1
                if index < len(entries) and entries[index]:
                    paths.add(entries[index].decode("utf-8", "surrogateescape"))
        index += 1
    return paths


def diff_sections(data: bytes) -> dict[str, bytes]:
    starts = list(re.finditer(br"(?m)^diff --git a/([^\n]+) b/([^\n]+)\n", data))
    sections: dict[str, bytes] = {}
    for index, match in enumerate(starts):
        first = match.group(1).decode("utf-8", "surrogateescape")
        second = match.group(2).decode("utf-8", "surrogateescape")
        if first != second:
            continue
        end = starts[index + 1].start() if index + 1 < len(starts) else len(data)
        sections[first] = data[match.start():end]
    return sections


def build_source_bytes(
    report_dir: Path,
    meta: dict[str, object],
    name: str,
    errors: list[str],
) -> bytes:
    receipt = meta.get("build_receipt")
    snapshots = receipt.get("source_snapshots") if isinstance(receipt, dict) else None
    item = snapshots.get(name) if isinstance(snapshots, dict) else None
    if not isinstance(item, dict):
        errors.append(f"Build receipt lacks source snapshot: {name}")
        return b""
    path = (report_dir / str(item.get("path", ""))).resolve()
    try:
        path.relative_to(report_dir / "evidence" / "runs")
        data = path.read_bytes()
    except (ValueError, OSError) as exc:
        errors.append(f"Build source snapshot is invalid ({name}): {exc}")
        return b""
    if item.get("sha256") != sha256(data):
        errors.append(f"Build source snapshot hash mismatch: {name}")
    return data


def verify_experiments_and_instrumentation(
    report_dir: Path,
    report: dict[str, object],
    claims: dict[str, dict[str, object]],
    provenance: dict[str, object],
    active_runtime_snapshot: str,
    errors: list[str],
) -> None:
    experiments = sorted(
        (path for path in (report_dir / "experiments").glob("experiment-*") if path.is_dir()),
        key=lambda value: int(value.name.split("-")[-1]) if value.name.split("-")[-1].isdigit() else 10**9,
    )
    if not experiments:
        errors.append("At least one runtime experiment is required")
    expected_names = [f"experiment-{number}" for number in range(1, len(experiments) + 1)]
    if [path.name for path in experiments] != expected_names:
        errors.append("Experiment directories must be contiguous from experiment-1")
    manifest_run_ids: set[str] = set()
    experiment_snapshot_by_run: dict[str, object] = {}
    for experiment in experiments:
        for required in ("experiment.md", "expected-oracle.md"):
            if not (experiment / required).is_file():
                errors.append(f"{experiment.name} is missing {required}")
        manifest, run_ids, observation_run_ids = verify_runner_manifest(
            report_dir,
            experiment,
            "manifest.json",
            experiment.name,
            report,
            claims,
            provenance,
            active_runtime_snapshot,
            errors,
        )
        manifest_run_ids.update(observation_run_ids)
        for run_id in observation_run_ids:
            experiment_snapshot_by_run[run_id] = manifest.get("runtime_tools_snapshot")
        if type(manifest.get("repetitions")) is not int or int(manifest.get("repetitions", 0)) < 1:
            errors.append(f"{experiment.name} needs repetitions >= 1")
        for field in ("controls_ko", "alternative_explanations_ko"):
            if not KOREAN_RE.search(str(manifest.get(field, ""))):
                errors.append(f"{experiment.name} needs Korean {field}")
    run_ids = report.get("runtime_run_ids")
    if not isinstance(run_ids, list) or not run_ids:
        errors.append("report.json runtime_run_ids must contain central experiment runs")
    else:
        if set(str(value) for value in run_ids) != manifest_run_ids:
            errors.append("report.json runtime_run_ids must equal all experiment manifest runs")
    instrumentation = report.get("instrumentation")
    if not isinstance(instrumentation, dict):
        errors.append("report.json instrumentation must be an object")
        return
    status = instrumentation.get("status")
    if status == "not-used":
        if instrumentation.get("post_clean_build_run_id") or instrumentation.get("markers") or instrumentation.get("target_files"):
            errors.append("Unused instrumentation state contains transaction evidence")
        runtime = report.get("runtime")
        if isinstance(runtime, dict) and runtime.get("active_tools_snapshot") != runtime.get(
            "baseline_tools_snapshot"
        ):
            errors.append("Non-instrumented report must keep the baseline runtime snapshot active")
        for run_id, snapshot_path in experiment_snapshot_by_run.items():
            if snapshot_path != active_runtime_snapshot:
                errors.append(
                    f"Non-instrumented experiment must use the active runtime snapshot: {run_id}"
                )
        return
    if status != "used-restored":
        errors.append("Instrumentation status must be not-used or used-restored")
        return
    transaction = load_json(report_dir / "evidence" / "instrumentation.json", errors)
    repositories = provenance.get("repositories")
    cubrid_repo = repositories.get("cubrid") if isinstance(repositories, dict) else None
    if not isinstance(cubrid_repo, dict):
        errors.append("Instrumentation cannot resolve CUBRID provenance")
        return
    cubrid_root = Path(str(cubrid_repo.get("root", ""))).resolve()
    if transaction.get("schema_version") != 1:
        errors.append("Instrumentation transaction has unsupported schema")
    baseline = transaction.get("baseline")
    if not isinstance(baseline, dict):
        errors.append("Instrumentation transaction lacks baseline")
    else:
        for field in ("status_sha256", "diff_sha256", "cached_diff_sha256"):
            if baseline.get(field) != cubrid_repo.get(field):
                errors.append(f"Instrumentation baseline mismatch: {field}")
    markers = transaction.get("markers")
    if (
        not isinstance(markers, list)
        or not markers
        or not all(isinstance(value, str) and INSTRUMENT_MARKER_RE.fullmatch(value) for value in markers)
        or len(markers) != len(set(markers))
    ):
        errors.append("Instrumentation transaction needs unique markers")
        markers = []
    if instrumentation.get("markers") != markers:
        errors.append("report.json instrumentation markers differ from transaction")
    targets = transaction.get("target_files")
    if not isinstance(targets, list) or not targets:
        errors.append("Instrumentation transaction needs target files")
        targets = []
    report_targets = instrumentation.get("target_files")
    transaction_target_paths = [
        str(value.get("path", "")) for value in targets if isinstance(value, dict)
    ]
    if report_targets != transaction_target_paths:
        errors.append("report.json instrumentation targets differ from transaction")
    baseline_status_paths: set[str] = set()
    baseline_files = cubrid_repo.get("baseline_files")
    status_entry = baseline_files.get("status.porcelain-v1.z") if isinstance(baseline_files, dict) else None
    if isinstance(status_entry, dict):
        status_path = (report_dir / str(status_entry.get("path", ""))).resolve()
        try:
            status_data = status_path.read_bytes()
        except OSError as exc:
            errors.append(f"Cannot inspect instrumentation baseline status: {exc}")
        else:
            for entry in status_data.split(b"\0"):
                if len(entry) >= 4:
                    baseline_status_paths.add(entry[3:].decode("utf-8", "surrogateescape"))
    target_paths: list[str] = []
    for target in targets:
        if not isinstance(target, dict):
            errors.append("Instrumentation target must be an object")
            continue
        relative_target = str(target.get("path", ""))
        target_paths.append(relative_target)
        path = (cubrid_root / relative_target).resolve()
        try:
            path.relative_to(cubrid_root)
            data = path.read_bytes()
        except (ValueError, OSError) as exc:
            errors.append(f"Instrumentation target is invalid: {exc}")
            continue
        digest = sha256(data)
        if target.get("original_sha256") != digest or target.get("restored_sha256") != digest:
            errors.append(f"Instrumentation target was not restored: {path}")
        committed = run(
            ["git", "-C", str(cubrid_root), "show", f"{cubrid_repo.get('head')}:{relative_target}"],
            check=False,
        )
        if committed.returncode != 0 or sha256(committed.stdout) != digest:
            errors.append(f"Instrumentation target was not commit-clean at baseline: {relative_target}")
        if relative_target in baseline_status_paths:
            errors.append(f"Instrumentation target appears in baseline Git status: {relative_target}")
        text = data.decode("utf-8", "replace")
        for marker in markers:
            if str(marker) in text:
                errors.append(f"Instrumentation marker remains in target: {marker}")
    build_runs = transaction.get("build_run_ids")
    if not isinstance(build_runs, dict):
        errors.append("Instrumentation transaction lacks build run IDs")
        build_runs = {}
    build_meta: dict[str, dict[str, object]] = {}
    normalized_build_ids = [str(build_runs.get(stage, "")) for stage in ("baseline", "instrumented", "post_clean")]
    if len(set(normalized_build_ids)) != 3 or any(not value for value in normalized_build_ids):
        errors.append("Instrumentation requires three distinct build run IDs")
    for stage in ("baseline", "instrumented", "post_clean"):
        run_id = str(build_runs.get(stage, ""))
        meta = verify_run(report_dir, run_id, errors) if run_id else {}
        if not meta:
            errors.append(f"Instrumentation transaction lacks valid {stage} build")
        elif meta.get("kind") != "build" or meta.get("argv") != ["just", "build"] or Path(str(meta.get("cwd", ""))).resolve() != cubrid_root:
            errors.append(f"Instrumentation {stage} build must be `just build` in CUBRID root")
        elif meta.get("expected_exit") != 0 or meta.get("actual_exit") != 0:
            errors.append(f"Instrumentation {stage} build must exit zero")
        else:
            build_meta[stage] = meta
    if instrumentation.get("post_clean_build_run_id") != build_runs.get("post_clean"):
        errors.append("report.json post-clean build ID differs from transaction")
    patch = transaction.get("patch")
    patch_data = b""
    if not isinstance(patch, dict):
        errors.append("Instrumentation transaction lacks exact patch metadata")
    else:
        patch_path = (report_dir / str(patch.get("path", ""))).resolve()
        try:
            patch_path.relative_to(report_dir)
            patch_data = patch_path.read_bytes()
        except (ValueError, OSError) as exc:
            errors.append(f"Instrumentation patch is invalid: {exc}")
        else:
            if patch.get("sha256") != sha256(patch_data):
                errors.append("Instrumentation patch hash mismatch")
            if not patch_data.strip():
                errors.append("Instrumentation patch must not be empty")
            patch_text = patch_data.decode("utf-8", "replace")
            changed_paths = {
                match.group(1)
                for match in re.finditer(r"^diff --git a/(.+) b/\1$", patch_text, re.M)
            }
            if changed_paths != set(target_paths):
                errors.append("Instrumentation patch paths differ from declared targets")
            for marker in markers:
                if marker not in patch_text:
                    errors.append(f"Instrumentation patch lacks declared marker: {marker}")
            apply_check = run(
                ["git", "-C", str(cubrid_root), "apply", "--check", "--whitespace=nowarn", str(patch_path)],
                check=False,
            )
            if apply_check.returncode != 0:
                errors.append("Instrumentation patch cannot be reapplied to the restored source")

    if set(build_meta) == {"baseline", "instrumented", "post_clean"}:
        source_by_stage = {
            stage: {
                name: build_source_bytes(report_dir, meta, name, errors)
                for name in ("status.porcelain-v1.z", "worktree.diff", "index.diff")
            }
            for stage, meta in build_meta.items()
        }
        baseline_source = source_by_stage["baseline"]
        instrumented_source = source_by_stage["instrumented"]
        post_clean_source = source_by_stage["post_clean"]
        provenance_baseline = cubrid_repo.get("baseline_files")
        if isinstance(provenance_baseline, dict):
            for name, data in baseline_source.items():
                item = provenance_baseline.get(name)
                expected_path = (
                    (report_dir / str(item.get("path", ""))).resolve()
                    if isinstance(item, dict)
                    else None
                )
                try:
                    expected_data = expected_path.read_bytes() if expected_path else b""
                except OSError as exc:
                    errors.append(f"Cannot read frozen baseline source snapshot: {exc}")
                else:
                    if data != expected_data:
                        errors.append(f"Instrumentation baseline build source differs: {name}")
        if post_clean_source != baseline_source:
            errors.append("Post-clean build source snapshots differ from the frozen baseline")
        baseline_paths = porcelain_paths(baseline_source["status.porcelain-v1.z"])
        instrumented_paths = porcelain_paths(instrumented_source["status.porcelain-v1.z"])
        if instrumented_paths != baseline_paths | set(target_paths):
            errors.append("Instrumented build contains transient unrelated source changes")
        if instrumented_source["index.diff"] != baseline_source["index.diff"]:
            errors.append("Instrumented build changed the frozen index state")
        baseline_sections = diff_sections(baseline_source["worktree.diff"])
        instrumented_sections = diff_sections(instrumented_source["worktree.diff"])
        patch_sections = diff_sections(patch_data)
        if set(patch_sections) != set(target_paths):
            errors.append("Instrumentation patch section set differs from targets")
        expected_section_paths = set(baseline_sections) | set(target_paths)
        if set(instrumented_sections) != expected_section_paths:
            errors.append("Instrumented build diff path set is not baseline plus exact patch")
        for path, section in baseline_sections.items():
            if path not in target_paths and instrumented_sections.get(path) != section:
                errors.append(f"Unrelated baseline diff changed during instrumentation: {path}")
        for path in target_paths:
            if path in baseline_sections:
                errors.append(f"Instrumentation target was already dirty in baseline diff: {path}")
            if instrumented_sections.get(path) != patch_sections.get(path):
                errors.append(f"Instrumented build does not contain the exact patch: {path}")

    applied = parse_utc(
        transaction.get("applied_at_utc"), "Instrumentation applied_at_utc", errors
    )
    reversed_at = parse_utc(
        transaction.get("reversed_at_utc"), "Instrumentation reversed_at_utc", errors
    )
    if applied is not None and reversed_at is not None and applied >= reversed_at:
        errors.append("Instrumentation reversal must occur after application")

    instrumented_run_ids = string_list(
        transaction.get("instrumented_experiment_run_ids"),
        "Instrumentation instrumented_experiment_run_ids",
        errors,
    )
    if not set(instrumented_run_ids).issubset(manifest_run_ids):
        errors.append("Instrumented run IDs must be Experiment manifest runs")
    instrumented_run_meta = {
        run_id: verify_run(report_dir, run_id, errors) for run_id in instrumented_run_ids
    }

    def run_boundary(stage: str, field: str) -> datetime | None:
        meta = build_meta.get(stage)
        if not meta:
            return None
        return parse_utc(meta.get(field), f"Instrumentation {stage} {field}", errors)

    baseline_finished = run_boundary("baseline", "finished_at_utc")
    instrumented_started = run_boundary("instrumented", "started_at_utc")
    instrumented_finished = run_boundary("instrumented", "finished_at_utc")
    post_clean_started = run_boundary("post_clean", "started_at_utc")
    if baseline_finished and applied and baseline_finished > applied:
        errors.append("Instrumentation was applied before the baseline build finished")
    if applied and instrumented_started and applied > instrumented_started:
        errors.append("Instrumented build started before instrumentation was applied")
    if reversed_at and post_clean_started and reversed_at > post_clean_started:
        errors.append("Post-clean build started before instrumentation was reversed")
    for run_id, meta in instrumented_run_meta.items():
        if not meta:
            continue
        started = parse_utc(meta.get("started_at_utc"), f"Instrumented run {run_id} start", errors)
        finished = parse_utc(meta.get("finished_at_utc"), f"Instrumented run {run_id} finish", errors)
        if instrumented_finished and started and started < instrumented_finished:
            errors.append(f"Instrumented experiment ran before its build finished: {run_id}")
        if reversed_at and finished and finished > reversed_at:
            errors.append(f"Instrumentation was reversed before experiment finished: {run_id}")

    runtime_snapshots = transaction.get("runtime_snapshots")
    if not isinstance(runtime_snapshots, dict):
        errors.append("Instrumentation transaction lacks runtime_snapshots")
        runtime_snapshots = {}
    runtime_state = report.get("runtime") if isinstance(report.get("runtime"), dict) else {}
    if runtime_state.get("runtime_build_run_id") != build_runs.get("baseline"):
        errors.append("Instrumentation baseline build must equal runtime_build_run_id")
    if runtime_snapshots.get("baseline") != runtime_state.get("baseline_tools_snapshot"):
        errors.append("Instrumentation baseline runtime snapshot differs from report.json")
    if runtime_snapshots.get("post_clean") != runtime_state.get("active_tools_snapshot"):
        errors.append("Post-clean runtime snapshot must be the active report runtime")
    for run_id in instrumented_run_ids:
        if experiment_snapshot_by_run.get(run_id) != runtime_snapshots.get("instrumented"):
            errors.append(
                f"Instrumented experiment run uses the wrong runtime snapshot: {run_id}"
            )
    stage_runtime_snapshots: dict[str, dict[str, object]] = {}
    for stage, build_stage, require_current in (
        ("baseline", "baseline", False),
        ("instrumented", "instrumented", False),
        ("post_clean", "post_clean", True),
    ):
        snapshot, captured = verify_runtime_snapshot(
            report_dir,
            runtime_snapshots.get(stage),
            provenance,
            errors,
            require_current=require_current,
        )
        if snapshot:
            stage_runtime_snapshots[stage] = snapshot
            expected_snapshot_id = "post-clean" if stage == "post_clean" else stage
            if snapshot.get("id") != expected_snapshot_id:
                errors.append(
                    f"Instrumentation {stage} runtime snapshot has the wrong ID"
                )
        if snapshot and snapshot.get("build_run_id") != build_runs.get(build_stage):
            errors.append(f"Instrumentation {stage} runtime snapshot uses the wrong build")
        stage_finished = run_boundary(build_stage, "finished_at_utc")
        if captured and stage_finished and captured < stage_finished:
            errors.append(f"Instrumentation {stage} runtime snapshot predates its build")
    if set(stage_runtime_snapshots) == {"baseline", "instrumented", "post_clean"}:
        hashes_by_stage: dict[str, dict[str, object]] = {}
        for stage, snapshot in stage_runtime_snapshots.items():
            tools = snapshot.get("tools")
            hashes_by_stage[stage] = {
                name: tool.get("sha256")
                for name, tool in tools.items()
                if isinstance(tools, dict) and isinstance(tool, dict)
            } if isinstance(tools, dict) else {}
        if hashes_by_stage["instrumented"] == hashes_by_stage["baseline"]:
            errors.append("Instrumentation did not change any captured CUBRID binary")
        if hashes_by_stage["post_clean"] != hashes_by_stage["baseline"]:
            errors.append("Post-clean CUBRID binary hashes do not match the baseline build")

    cleanup = transaction.get("cleanup_verification")
    if not isinstance(cleanup, dict):
        errors.append("Instrumentation transaction lacks cleanup_verification")
        cleanup = {}
    cleanup_runner_value = cleanup.get("runner")
    cleanup_runner = (report_dir / str(cleanup_runner_value or "")).resolve()
    cleanup_digest = ""
    try:
        cleanup_runner.relative_to(report_dir)
        cleanup_data = cleanup_runner.read_bytes()
    except (ValueError, OSError) as exc:
        errors.append(f"Instrumentation cleanup runner is invalid: {exc}")
    else:
        cleanup_digest = sha256(cleanup_data)
        if cleanup.get("runner_sha256") != cleanup_digest:
            errors.append("Instrumentation cleanup runner hash mismatch")
    cleanup_argv = string_list(
        cleanup.get("runner_argv"), "Instrumentation cleanup runner_argv", errors
    )
    cleanup_runs = string_list(
        cleanup.get("run_ids"), "Instrumentation cleanup run IDs", errors
    )
    if not KOREAN_RE.search(str(cleanup.get("oracle_ko", ""))):
        errors.append("Instrumentation cleanup verification needs a Korean oracle")
    occupied_ids = set(normalized_build_ids) | set(instrumented_run_ids)
    if occupied_ids & set(cleanup_runs):
        errors.append("Instrumentation cleanup runs must be distinct from builds/experiments")
    for run_id in cleanup_runs:
        meta = verify_run(report_dir, run_id, errors)
        if not meta:
            continue
        if meta.get("argv") != cleanup_argv or Path(str(meta.get("cwd", ""))).resolve() != report_dir:
            errors.append(f"Instrumentation cleanup run did not execute the cleanup verifier: {run_id}")
        if meta.get("expected_exit") != 0 or meta.get("actual_exit") != 0:
            errors.append(f"Instrumentation cleanup verifier must exit zero: {run_id}")
        if cleanup_digest and meta.get("bound_files"):
            verify_execution_bound_runner(
                "instrumentation-cleanup",
                run_id,
                meta,
                cleanup_runner,
                cleanup_digest,
                errors,
            )
        started = parse_utc(meta.get("started_at_utc"), f"Cleanup run {run_id} start", errors)
        if reversed_at and started and started < reversed_at:
            errors.append(f"Cleanup verification predates instrumentation reversal: {run_id}")


def audited_material(report_dir: Path, phase: str) -> dict[str, str]:
    excluded = {
        "evidence/report-audit.json",
        "evidence/report-audit.md",
        "evidence/complete-audit.json",
        "evidence/complete-audit.md",
    }
    material: dict[str, str] = {}
    for path in sorted(value for value in report_dir.rglob("*") if value.is_file()):
        relative = path.relative_to(report_dir).as_posix()
        if relative in excluded or (phase == "report" and relative.startswith("grill/")):
            continue
        material[relative] = sha256(path.read_bytes())
    return material


def verify_audit(report_dir: Path, phase: str, errors: list[str]) -> None:
    prefix = "report-audit" if phase == "report" else "complete-audit"
    manifest = load_json(report_dir / "evidence" / f"{prefix}.json", errors)
    narrative_path = report_dir / "evidence" / f"{prefix}.md"
    try:
        lines = [
            line.strip()
            for line in narrative_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except (OSError, UnicodeError) as exc:
        errors.append(f"Cannot read {phase} completeness audit: {exc}")
        lines = []
    if not lines or lines[-1] != "VERDICT: APPROVED":
        errors.append(f"{phase} audit narrative must end with VERDICT: APPROVED")
    if not manifest:
        return
    if manifest.get("schema_version") != 1 or manifest.get("phase") != phase:
        errors.append(f"{phase} audit has invalid schema/phase")
    if manifest.get("verdict") != "APPROVED" or manifest.get("isolated_reviewer") is not True:
        errors.append(f"{phase} audit is not independently approved")
    if not str(manifest.get("reviewer_id", "")).strip():
        errors.append(f"{phase} audit has no reviewer identity")
    if type(manifest.get("round")) is not int or int(manifest.get("round", 0)) < 1:
        errors.append(f"{phase} audit has invalid round")
    parse_utc(manifest.get("timestamp_utc"), f"{phase} audit", errors)
    findings = manifest.get("findings")
    if not isinstance(findings, list):
        errors.append(f"{phase} audit findings must be a list")
    else:
        for finding in findings:
            if not isinstance(finding, dict) or not finding.get("id") or finding.get("status") != "RESOLVED":
                errors.append(f"{phase} audit has unresolved or malformed findings")
                break
    obligations = manifest.get("coverage_obligations")
    if not isinstance(obligations, list) or set(str(value) for value in obligations) != set(COVERAGE_IDS):
        errors.append(f"{phase} audit did not review every coverage obligation")
    reviewed_files = manifest.get("reviewed_files")
    try:
        expected_files = audited_material(report_dir, phase)
    except OSError as exc:
        errors.append(f"Cannot hash {phase} audit materials: {exc}")
        return
    if reviewed_files != expected_files:
        errors.append(f"{phase} audit seal does not match the current artifact set")


def print_materials(args: argparse.Namespace) -> int:
    report_dir = Path(args.report_dir).resolve()
    if not (report_dir / "provenance.json").is_file():
        raise ToolError(EXIT_REPORT, f"Not an initialized report directory: {report_dir}")
    try:
        reviewed_files = audited_material(report_dir, args.phase)
    except OSError as exc:
        raise ToolError(EXIT_REPORT, f"Could not hash audit materials: {exc}") from exc
    print(
        json.dumps(
            {
                "phase": args.phase,
                "report_dir": str(report_dir),
                "reviewed_files": reviewed_files,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def verify_grill(
    report_dir: Path,
    report: dict[str, object],
    parsed: dict[Path, BookParser],
    errors: list[str],
) -> None:
    mastery = load_json(report_dir / "grill" / "mastery.json", errors)
    if mastery.get("state") != "COMPLETE":
        errors.append("Live grill state is not COMPLETE")
    concepts = mastery.get("concepts")
    if not isinstance(concepts, dict):
        errors.append("grill/mastery.json concepts must be an object")
    else:
        for concept in MASTERY_IDS:
            if concepts.get(concept) != "MASTERED":
                errors.append(f"Live grill concept is not mastered: {concept}")
    if mastery.get("capstone") != "MASTERED":
        errors.append("Live grill capstone teach-back is not mastered")
    session_path = report_dir / "grill" / "session.jsonl"
    try:
        session_lines = [line for line in session_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, UnicodeError) as exc:
        errors.append(f"Cannot read grill session: {exc}")
        session_lines = []
    if not session_lines:
        errors.append("Live grill session is empty")
    mastered_events: set[str] = set()
    exchange_ids: set[str] = set()
    host_turn_ids: set[str] = set()
    user_turn_ids: set[str] = set()
    previous_timestamp: datetime | None = None
    attempts: dict[str, int] = {}
    failed_attempts: dict[str, int] = {}
    pending_retry: str | None = None
    expected_control_state = "SELECT_NEXT"
    report_behaviors = report.get("central_behaviors")
    if not isinstance(report_behaviors, list):
        report_behaviors = []
    relevant_refs: dict[str, set[str]] = {concept: set() for concept in MASTERY_IDS}
    all_behavior_refs: set[str] = set()
    for behavior in report_behaviors:
        if not isinstance(behavior, dict):
            continue
        chapter = str(behavior.get("chapter", ""))
        anchor = str(behavior.get("anchor", ""))
        behavior_refs = {f"{chapter}#{anchor}"}
        quiz_ids = behavior.get("quiz_ids")
        if isinstance(quiz_ids, list):
            behavior_refs.update(f"quiz/{value}" for value in quiz_ids)
        all_behavior_refs.update(behavior_refs)
        concepts_for_behavior = behavior.get("grill_concepts")
        if isinstance(concepts_for_behavior, list):
            for concept in concepts_for_behavior:
                if str(concept) in relevant_refs:
                    relevant_refs[str(concept)].update(behavior_refs)
    allowed_next = {
        "MASTERED": {"SELECT_NEXT", "CAPSTONE_TEACHBACK", "COMPLETE"},
        "PARTIAL": {"ASK_NARROWER"},
        "MISCONCEPTION": {"ASK_NARROWER"},
        "RETEACH": {"ASK_NARROWER"},
        "EVIDENCE_GAP": {"RESEARCH"},
    }
    for number, line in enumerate(session_lines, 1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid grill session line {number}: {exc}")
            continue
        if not isinstance(event, dict):
            errors.append(f"Grill event {number} is not an object")
            continue
        concept = str(event.get("concept", ""))
        was_mastered = concept in mastered_events
        if concept not in set(MASTERY_IDS) | {"capstone"}:
            errors.append(f"Grill event {number} has unknown concept: {concept}")
        question = str(event.get("question_ko", ""))
        answer = str(event.get("answer_ko", ""))
        if not KOREAN_RE.search(question):
            errors.append(f"Grill event {number} needs a Korean question")
        if not answer.strip():
            errors.append(f"Grill event {number} must preserve a nonempty learner answer")
        evaluation = str(event.get("evaluation", ""))
        if evaluation not in allowed_next:
            errors.append(f"Grill event {number} has invalid evaluation: {evaluation}")
        elif event.get("state_after") not in allowed_next[evaluation]:
            errors.append(f"Grill event {number} has illegal state transition")
        elif evaluation == "MASTERED":
            mastered_events.add(concept)
            if concept == "capstone" and event.get("state_after") != "COMPLETE":
                errors.append(f"Grill capstone event {number} must transition to COMPLETE")
            if concept != "capstone" and event.get("state_after") == "COMPLETE":
                errors.append(f"Only the capstone may transition to COMPLETE: event {number}")
        if event.get("state_before") != "WAIT_FOR_USER":
            errors.append(f"Grill event {number} must begin at WAIT_FOR_USER")
        for field, seen in (
            ("exchange_id", exchange_ids),
            ("host_turn_id", host_turn_ids),
            ("user_turn_id", user_turn_ids),
        ):
            value = str(event.get(field, ""))
            if not value or value in seen:
                errors.append(f"Grill event {number} has missing/duplicate {field}")
            seen.add(value)
        attempt = event.get("attempt")
        if type(attempt) is not int or int(attempt) < 1:
            errors.append(f"Grill event {number} has invalid attempt")
        else:
            expected_attempt = attempts.get(concept, 0) + 1
            if attempt != expected_attempt:
                errors.append(
                    f"Grill event {number} attempt must be {expected_attempt} for {concept}"
                )
            attempts[concept] = attempt
        if pending_retry is not None and concept != pending_retry:
            errors.append(
                f"Grill event {number} must continue narrower questioning for {pending_retry}"
            )
        if expected_control_state == "CAPSTONE_TEACHBACK" and concept != "capstone":
            errors.append(f"Grill event {number} must be the capstone teach-back")
        if was_mastered:
            errors.append(f"Grill event {number} repeats a mastered concept: {concept}")
        if concept == "capstone":
            if number != len(session_lines):
                errors.append("Capstone must be the final Grill event")
            if set(MASTERY_IDS) - (mastered_events - {"capstone"}):
                errors.append("Capstone began before every concept was mastered")
            if evaluation != "MASTERED" or event.get("state_after") != "COMPLETE":
                errors.append("Capstone must be MASTERED and transition to COMPLETE")
        elif evaluation == "MASTERED":
            pending_retry = None
            remaining = set(MASTERY_IDS) - mastered_events
            required_state = "CAPSTONE_TEACHBACK" if not remaining else "SELECT_NEXT"
            if event.get("state_after") != required_state:
                errors.append(
                    f"Grill event {number} must transition to {required_state}"
                )
            expected_control_state = required_state
        elif evaluation in {"PARTIAL", "MISCONCEPTION", "RETEACH", "EVIDENCE_GAP"}:
            pending_retry = concept
            expected_control_state = str(event.get("state_after", ""))
            if evaluation in {"PARTIAL", "MISCONCEPTION"}:
                failed_attempts[concept] = failed_attempts.get(concept, 0) + 1
                if failed_attempts[concept] >= 3:
                    errors.append(
                        f"Grill event {number} must mark RETEACH after three failed attempts"
                    )
            if evaluation == "RETEACH" and failed_attempts.get(concept, 0) < 2:
                errors.append(f"Grill event {number} marks RETEACH before three attempts")
            if evaluation == "RETEACH":
                failed_attempts[concept] = failed_attempts.get(concept, 0) + 1
        timestamp = parse_utc(
            event.get("timestamp_utc"), f"Grill event {number}", errors
        )
        if timestamp is not None:
            if previous_timestamp is not None and timestamp < previous_timestamp:
                errors.append(f"Grill event {number} timestamp is out of order")
            previous_timestamp = timestamp
        references = event.get("references")
        if not isinstance(references, list) or not references:
            errors.append(f"Grill event {number} has no report/quiz references")
        else:
            valid_references: set[str] = set()
            for reference in references:
                if not isinstance(reference, str):
                    errors.append(f"Grill event {number} has a non-string reference")
                    continue
                file_part, separator, fragment = reference.partition("#")
                if reference.startswith("quiz/") and not separator:
                    quiz_path = (report_dir / reference).resolve()
                    try:
                        quiz_path.relative_to(report_dir / "quiz")
                    except ValueError:
                        errors.append(f"Grill event {number} reference escapes quiz/: {reference}")
                    else:
                        if not quiz_path.is_dir() or not (quiz_path / "quiz.md").is_file():
                            errors.append(f"Grill event {number} has invalid Quiz reference: {reference}")
                        else:
                            valid_references.add(reference)
                    continue
                path = (report_dir / file_part).resolve()
                if not separator or path not in parsed or fragment not in set(parsed[path].ids):
                    errors.append(f"Grill event {number} has invalid Book reference: {reference}")
                else:
                    valid_references.add(reference)
            allowed_refs = all_behavior_refs if concept == "capstone" else relevant_refs.get(concept, set())
            if not (valid_references & allowed_refs):
                errors.append(
                    f"Grill event {number} references are unrelated to concept {concept}"
                )
    for concept in (*MASTERY_IDS, "capstone"):
        if concept not in mastered_events:
            errors.append(f"Live grill has no mastered event for: {concept}")
    summary = report_dir / "grill" / "mastery-summary.html"
    if summary not in parsed:
        errors.append("Missing or unreachable grill/mastery-summary.html")


def verify_report(args: argparse.Namespace) -> int:
    report_dir = Path(args.report_dir).resolve()
    report_errors: list[str] = []
    provenance_errors: list[str] = []
    teaching_errors: list[str] = []
    provenance = load_json(report_dir / "provenance.json", provenance_errors)
    report = load_json(report_dir / "report.json", report_errors)
    if provenance:
        verify_provenance(report_dir, provenance, provenance_errors)
    parsed, html_claim_ids = parse_book(report_dir, report_errors)
    verify_scope_and_status(report_dir, report, args.phase, report_errors)
    coverage_claim_locations = verify_coverage(report, parsed, report_dir, report_errors)
    claims = verify_claims(
        report_dir,
        provenance,
        parsed,
        html_claim_ids,
        coverage_claim_locations,
        report_errors,
    )
    verify_central_behaviors(report_dir, report, claims, parsed, report_errors)
    _, active_runtime_snapshot = verify_runtime_contract(
        report_dir, report, provenance, report_errors
    )
    verify_experiments_and_instrumentation(
        report_dir,
        report,
        claims,
        provenance,
        active_runtime_snapshot,
        report_errors,
    )
    verify_quizzes(
        report_dir,
        report,
        claims,
        provenance,
        active_runtime_snapshot,
        teaching_errors,
    )
    if args.phase == "complete":
        verify_grill(report_dir, report, parsed, teaching_errors)
    verify_audit(report_dir, args.phase, report_errors)

    categories = sum(bool(group) for group in (report_errors, provenance_errors, teaching_errors))
    ok = categories == 0
    payload = {
        "ok": ok,
        "phase": args.phase,
        "report_dir": str(report_dir),
        "errors": {
            "report": report_errors,
            "provenance": provenance_errors,
            "quiz_or_grill": teaching_errors,
        },
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if ok:
        return 0
    if categories > 1:
        return EXIT_MULTIPLE
    if provenance_errors:
        return EXIT_PROVENANCE
    if teaching_errors:
        return EXIT_TEACHING
    return EXIT_REPORT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    init = subparsers.add_parser("init", help="validate sources and initialize or resume a report")
    init.add_argument("--topic", required=True)
    init.add_argument("--cubrid-root", default=os.getcwd())
    init.add_argument("--postgres-root", default="/home/vimkim/gh/pg/postgres")
    init.add_argument("--mysql-root", default="/home/vimkim/gh/mysql/mysql-server")
    init.add_argument("--docs-root", default="/home/vimkim/gh/my-cubrid-docs")
    init.add_argument("--agent", required=True)
    init.add_argument("--output")
    init.set_defaults(func=init_report)

    record = subparsers.add_parser(
        "record",
        help="execute argv directly and capture immutable evidence",
        description=(
            "Capture one command without a shell. Put a literal -- before the command. "
            "Save pipes, redirection, environment setup, or multi-step logic in a script first."
        ),
        epilog=(
            "example: reportctl.py record --report-dir /abs/report --id run-1 "
            "--cwd /abs/work --expect-exit 0 -- bash run.sh"
        ),
    )
    record.add_argument("--report-dir", required=True)
    record.add_argument("--id", required=True)
    record.add_argument("--cwd", required=True)
    record.add_argument("--expect-exit", type=int, default=0)
    record.add_argument(
        "--runtime-tools-snapshot",
        help="relative evidence/runtime-tools-*.json whose sealed environment executes the command",
    )
    record.add_argument(
        "--bind-file",
        action="append",
        default=[],
        help="file whose before/after digest must be sealed into this run; repeat as needed",
    )
    record.add_argument("command", nargs=argparse.REMAINDER)
    record.set_defaults(func=record_command)

    build = subparsers.add_parser(
        "build", help="capture `just build` under the pinned worktree environment"
    )
    build.add_argument("--report-dir", required=True)
    build.add_argument("--id", required=True)
    build.set_defaults(func=capture_build)

    runtime_snapshot = subparsers.add_parser(
        "runtime-snapshot",
        help="bind csql/cubrid identities to a captured pinned-source build",
    )
    runtime_snapshot.add_argument("--report-dir", required=True)
    runtime_snapshot.add_argument("--id", required=True)
    runtime_snapshot.add_argument("--build-run-id", required=True)
    runtime_snapshot.set_defaults(func=snapshot_runtime)

    verify = subparsers.add_parser("verify", help="verify report or complete mastery artifacts")
    verify.add_argument("--report-dir", required=True)
    verify.add_argument("--phase", choices=("report", "complete"), required=True)
    verify.set_defaults(func=verify_report)

    materials = subparsers.add_parser(
        "materials", help="print the exact artifact digests an independent audit must seal"
    )
    materials.add_argument("--report-dir", required=True)
    materials.add_argument("--phase", choices=("report", "complete"), required=True)
    materials.set_defaults(func=print_materials)
    return parser


def main() -> int:
    parser = build_parser()
    try:
        args = parser.parse_args()
        return int(args.func(args))
    except ToolError as exc:
        print(json.dumps({"ok": False, "error": str(exc), "exit_code": exc.code}, ensure_ascii=False))
        return exc.code
    except KeyboardInterrupt:
        print(json.dumps({"ok": False, "error": "Interrupted", "exit_code": 130}))
        return 130
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"Internal validation error: {type(exc).__name__}: {exc}",
                    "exit_code": EXIT_REPORT,
                },
                ensure_ascii=False,
            )
        )
        return EXIT_REPORT


if __name__ == "__main__":
    sys.exit(main())
