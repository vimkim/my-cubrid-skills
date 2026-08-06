# Artifact Schemas

Use JSON schema version `1`. `reportctl.py verify` rejects missing links, hashes, or identities; do not satisfy it with self-attested placeholders.

## `report.json`

Lifecycle:

```text
DRAFT -> REPORT_READY -> COMPLETE
           |
           +-> GRILL_PAUSED
```

Only `REPORT_READY` can pass `--phase report`; only `COMPLETE` can pass `--phase complete`.

`report.json.runtime` binds the mandatory pinned-source build and active runtime:

```json
{
  "runtime_build_run_id": "runtime-baseline-build",
  "baseline_tools_snapshot": "evidence/runtime-tools-baseline.json",
  "active_tools_snapshot": "evidence/runtime-tools-baseline.json"
}
```

After instrumentation, `active_tools_snapshot` names the post-clean snapshot. The baseline build is mandatory whether or not instrumentation is used.

Freeze `scope.path`, `scope.sha256`, and `scope.frozen=true` before research. A central behavior has:

```json
{
  "id": "page-fix-miss",
  "name_ko": "page miss 이후 fix 흐름",
  "claim_ids": ["CUBRID-C001", "PG-C001", "MYSQL-C001", "CMP-C001"],
  "coverage_ids": ["core-workflows", "concurrency"],
  "experiment_ids": ["experiment-1"],
  "quiz_ids": ["quiz-1"],
  "chapter": "chapters/05-core-workflows.html",
  "anchor": "page-fix-miss",
  "grill_concepts": ["lifecycle-state-machines", "concurrency"]
}
```

Every central behavior needs direct/non-weak Claims, at least one Experiment, at least one Quiz, a real Book anchor, and Live Grill concepts.

When instrumentation is unused, use `instrumentation.status="not-used"` with empty markers/targets and no post-clean build. When used and restored, use `status="used-restored"`, point to the post-clean build, and create `evidence/instrumentation.json` as described in `experiments-and-safety.md`.

## Experiment Manifest

Each `experiments/experiment-N/manifest.json` contains:

```json
{
  "schema_version": 1,
  "id": "experiment-1",
  "behavior_ids": ["page-fix-miss"],
  "claim_ids": ["CUBRID-C001"],
  "runner": "experiment.sql",
  "runner_sha256": "64-hex",
  "runner_argv": ["/absolute/built/csql", "--input-file", "experiment.sql"],
  "run_ids": ["page-fix-miss-run-1"],
  "oracle_ko": "관찰해야 하는 invariant",
  "controls_ko": "positive/negative control",
  "alternative_explanations_ko": "관찰을 설명할 다른 원인",
  "repetitions": 3,
  "cubrid_runtime_only": true,
  "runtime_tools_snapshot": "evidence/runtime-tools-baseline.json",
  "cleanup_verified": true
}
```

Also include `experiment.md`, `expected-oracle.md`, and the hashed runner. Every declared run exactly matches `runner_argv`, executes captured `csql` under the sealed runtime environment, consumes the SQL runner via `-i`/`--input-file`, exits zero, and uses the Experiment directory as cwd. The manifest Claim IDs are a subset of its linked central-behavior Claims; every Experiment run is consumed by a linked CUBRID `runtime` or `source+runtime` Claim.

## Optional Quiz Manifest

`quiz.json` is optional. Use it only when a Quiz benefits from machine-readable links or captured runtime evidence. When present, it may reuse the Experiment identity/link/runner/oracle fields and list one or more observed `run_ids`. Do not manufacture hashes, repeated runs, or cleanup claims merely to fill the manifest.

## Instrumentation Transaction

`evidence/instrumentation.json` records:

- the three baseline CUBRID status/diff hashes from provenance;
- nonempty unique `CUBRID_CODE_ANALYSIS_*` markers;
- target paths with identical `original_sha256` and `restored_sha256` matching both current source and the pinned commit;
- an exact nonempty patch path and hash whose paths and markers match the declaration;
- `applied_at_utc`, `reversed_at_utc`, and `instrumented_experiment_run_ids`;
- three distinct `baseline`, `instrumented`, and `post_clean` build run IDs, each literally `just build` in the pinned CUBRID root;
- `baseline`, `instrumented`, and `post_clean` runtime snapshot paths bound to those builds;
- `cleanup_verification` with a hashed runner, exact argv, Korean oracle, and distinct captured run IDs.

Never set `used-restored` until source fingerprints, targets, processes, and the post-clean binary build are all proved restored.

## Completeness Audit Seal

Run:

```bash
python3 "<skill-dir>/scripts/reportctl.py" materials \
  --report-dir "<report-dir>" --phase report
```

Use `--phase complete` for the post-grill audit. The isolated reviewer writes the corresponding `report-audit.json` or `complete-audit.json`:

```json
{
  "schema_version": 1,
  "phase": "report",
  "reviewer_id": "stable isolated reviewer identity",
  "isolated_reviewer": true,
  "round": 2,
  "timestamp_utc": "ISO-8601",
  "verdict": "APPROVED",
  "findings": [{"id": "F-1", "status": "RESOLVED"}],
  "coverage_obligations": ["all 18 exact IDs"],
  "reviewed_files": {"relative/path": "sha256 from materials output"}
}
```

The paired Markdown audit ends with `VERDICT: APPROVED`. Any material change invalidates the seal and requires a new isolated review.

The verifier proves the seal, verdict schema, and reviewed-file hashes. `isolated_reviewer=true` remains a host trust boundary unless the host supplies an independently verifiable task receipt; never describe the JSON boolean alone as cryptographic proof of reviewer independence.

## Live Grill Event

Append one paired exchange per JSONL line. Preserve the learner answer verbatim, even when it contains only English identifiers or code.

```json
{
  "timestamp_utc": "ISO-8601",
  "exchange_id": "unique",
  "host_turn_id": "unique",
  "user_turn_id": "unique",
  "concept": "one mastery ID or capstone",
  "attempt": 1,
  "state_before": "WAIT_FOR_USER",
  "state_after": "SELECT_NEXT",
  "question_ko": "한 개의 한국어 질문",
  "answer_ko": "verbatim learner answer",
  "evaluation": "MASTERED",
  "references": ["chapters/05-core-workflows.html#page-fix-miss"]
}
```

Allowed evaluations and next states:

- `MASTERED` -> `SELECT_NEXT`, `CAPSTONE_TEACHBACK`, or `COMPLETE`
- `PARTIAL`, `MISCONCEPTION`, `RETEACH` -> `ASK_NARROWER`
- `EVIDENCE_GAP` -> `RESEARCH`

The capstone `MASTERED` event must transition to `COMPLETE`. Host/user turn IDs must be unique, enforcing one recorded question per turn. Attempts increase contiguously per concept. A weak evaluation requires the next event to continue the same concept; the third failed attempt is recorded as `RETEACH`. Every reference resolves to an existing chapter anchor or `quiz/quiz-N` linked to that concept. Only the final capstone event may transition to `COMPLETE`.
