#!/usr/bin/env python3
"""Select the strongest safe analyzer report mode from validated bundle facts."""

import json
import sys
from pathlib import Path


EXPECTED_KEYS = {
    "identity",
    "observation",
    "manifest",
    "requested_summaries",
    "result_matches_observation",
    "requested_suites_reconciled",
}


def fail(message: str) -> None:
    print(f"report_mode: {message}", file=sys.stderr)
    raise SystemExit(2)


def load_assessment(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        fail(str(error))
    if not isinstance(value, dict) or set(value) not in (EXPECTED_KEYS, EXPECTED_KEYS | {"baseline"}):
        fail("assessment must contain the documented head fields and optional baseline state")
    allowed = {
        "identity": {"established", "unknown"},
        "observation": {
            "complete",
            "incomplete",
            "interrupted",
            "failed",
            "unvalidated",
        },
        "manifest": {"validated", "missing", "invalid"},
        "requested_summaries": {"validated", "partial", "none", "invalid"},
    }
    for field, choices in allowed.items():
        if value[field] not in choices:
            fail(f"{field} must be one of {', '.join(sorted(choices))}")
    for field in ("result_matches_observation", "requested_suites_reconciled"):
        if not isinstance(value[field], bool):
            fail(f"{field} must be boolean")
    value.setdefault("baseline", "not_assessed")
    if not isinstance(value["baseline"], str) or value["baseline"] not in {"not_assessed", "validated_exact", "partial_exact", "unavailable", "invalid"}:
        fail("baseline must be not_assessed, validated_exact, partial_exact, unavailable, or invalid")
    return value


def decide(value: dict[str, object]) -> dict[str, object]:
    if value["identity"] != "established":
        mode = "stop"
    elif (
        value["observation"] == "complete"
        and value["manifest"] == "validated"
        and value["requested_summaries"] == "validated"
        and value["result_matches_observation"] is True
        and value["requested_suites_reconciled"] is True
    ):
        mode = "full"
    else:
        mode = "warning"
    scope = "none"
    if mode == "full" and value.get("baseline") in {"validated_exact", "partial_exact"}:
        scope = "validated_cases_only"
    return {
        "mode": mode,
        "regression_conclusions_allowed": scope != "none",
        "comparison_scope": scope,
    }


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: report_mode.py ASSESSMENT.json")
    print(json.dumps(decide(load_assessment(Path(sys.argv[1]))), separators=(",", ":")))


if __name__ == "__main__":
    main()
