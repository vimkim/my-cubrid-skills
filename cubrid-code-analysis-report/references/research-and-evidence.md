# Research and Evidence Contract

## Contents

1. Evidence authority
2. Provenance freeze
3. Source-tracing method
4. Claim ledger
5. Three-database comparison
6. Completeness and uncertainty

## 1. Evidence Authority

Use this order when claims conflict:

1. Exact pinned source plus reachable call path proves implementation behavior for that revision.
2. Reproducible runtime evidence proves the observed build/configuration/input case.
3. Project manual or normative specification proves documented intent, not necessarily implementation.
4. Tests prove the covered cases and invariants.
5. Local design notes, JIRA, comments, commit messages, and prior reports provide context.
6. Agent reasoning supplies hypotheses only until primary evidence confirms them.

Keep direct source facts, documented intent, runtime observations, and inference visibly separate. A report may reconcile them; it must not blur them.

## 2. Provenance Freeze

Before research, record for CUBRID, PostgreSQL, and MySQL:

- absolute root;
- full `HEAD` commit and branch or detached state;
- remote URLs;
- `git status --porcelain=v1 -z` hash;
- `git diff --binary --no-ext-diff` hash;
- whether cited content is commit-clean or `WORKTREE` evidence.

The initializer preserves exact status, worktree-diff, and index-diff bytes under `evidence/baseline/`; their paths and hashes live in `provenance.json`. Do not edit these snapshots.

For CUBRID also record binaries, versions, build preset, configuration, OS, and experiment environment. A dirty tree remains usable, but a claim derived from a dirty file must include its content hash and `WORKTREE` label.

At finalization, recheck all revisions, fingerprints, and cited-file hashes. Re-research any affected claim.

## 3. Source-Tracing Method

For each operation:

1. Locate external callers and the Module's Interface.
2. Trace the full reachable call chain through success, retry, and error paths.
3. Record inputs, output, ownership, lifetime, side effects, locks/latches, state mutation, I/O, and errors at each step.
4. Trace startup, shutdown, abort, restart, and cleanup paths separately.
5. Follow data structures from allocation through reclamation.
6. Follow persistent state through logging, ordering, flush, checkpoint, and recovery where applicable.
7. Search tests, configuration, diagnostics, metrics, utilities, and manual text.
8. Record unknowns and the search performed; do not silently omit them.

Read complete functions and enough caller/callee context to establish reachability. Search results, comments, names, and type declarations are leads, not conclusions.

For a negative claim, record the repository areas, symbols, alternate terminology, and call paths checked. “No equivalent” needs stronger search evidence than “not found by one `rg`.”

## 4. Claim Ledger

Store one JSON object per line in `evidence/claims.jsonl`. Use stable IDs such as `CUBRID-C001`, `PG-C001`, `MYSQL-C001`, and `CMP-C001`.

Required fields:

```json
{
  "id": "CUBRID-C001",
  "claim_ko": "Korean explanation of one substantive claim",
  "database": "cubrid",
  "revision": "40-hex commit",
  "kind": "source",
  "confidence": "SOURCE-CONFIRMED",
  "source_refs": [
    {
      "path": "relative/path.c",
      "symbol": "function_name",
          "line_start": 1,
          "line_end": 20,
          "file_sha256": "64-hex hash",
          "evidence_state": "COMMIT"
    }
  ],
  "runtime_run_ids": [],
  "limitations_ko": "Korean limitations or an empty string",
  "report_locations": ["chapters/05-core-workflows.html#claim-CUBRID-C001"]
}
```

Allowed `database` values are `cubrid`, `postgresql`, `mysql`, and `comparison`.

Allowed `kind` values:

- `source`: direct pinned-source behavior;
- `runtime`: observed behavior;
- `source+runtime`: both agree for the tested case;
- `documented-intent`: manual/spec requirement;
- `inference`: reasoned but not directly proved;
- `unknown`: an unresolved material question;
- `analogy`: cross-database relationship.

Allowed `confidence` values:

- `SOURCE-CONFIRMED`
- `RUNTIME-OBSERVED`
- `SOURCE+RUNTIME-CONFIRMED`
- `DOCUMENTED`
- `INFERRED`
- `UNKNOWN`

Rules:

- Every substantive paragraph, diagram edge, state transition, pseudocode branch, numeric constant, ordering rule, and comparison-table conclusion must expose one or more claim IDs.
- A citation supports but never replaces the Korean mechanism explanation.
- Runtime claims name captured run IDs. Measured claims include environment, input, repetitions, and variability.
- Concurrency, durability, and crash guarantees should have both source and runtime/test evidence where feasible.
- An inference states its premises and a falsifier. An unknown states why it remains unknown.
- Comparison claims cite evidence from every participating database.
- A comparison Claim uses `kind=analogy`, cites all three databases, and sets `analogy_class` to `equivalent`, `partial analogy`, or `no equivalent`.
- A source reference sets `evidence_state=COMMIT` only when the cited bytes match the pinned commit; otherwise it sets `WORKTREE` and keeps the exact file hash.
- `source`, `runtime`, and `source+runtime` kinds carry the matching evidence and confidence class; do not label a source-only Claim as runtime-confirmed.
- The cited `symbol` must occur inside the cited line range.
- A central `INFERRED` or `UNKNOWN` claim lowers the readiness declaration.
- Every central behavior carries direct CUBRID, PostgreSQL, MySQL, and comparison Claims. An Experiment/Quiz manifest may cite only Claims already owned by its linked central behavior, and each Experiment run must appear in a cited CUBRID `runtime` or `source+runtime` Claim.
- Verify each stored source path, line range, symbol, revision, and hash at finalization.

## 5. Three-Database Comparison

First define a shared scenario and comparison axes. Use the same axes for all three systems:

- responsibility and Module boundary;
- Interface and caller obligations;
- identity, ownership, and lifetime;
- states and transitions;
- concurrency protocol;
- durability and recovery;
- policy/algorithm;
- errors and resource pressure;
- configuration and observability;
- performance trade-offs.

For MySQL, name the actual owner such as InnoDB instead of treating the SQL server as one uniform storage implementation.

Classify mappings:

- `equivalent`: responsibility, Interface semantics, and central invariants substantially match;
- `partial analogy`: it helps explain one axis but differs materially elsewhere;
- `no equivalent`: responsibility is absent, split, or located at a different layer.

Explain every mismatch. Similar names do not establish equivalence. When two systems place responsibility in different Modules, compare the responsibility flow, not merely similarly named functions.

## 6. Completeness and Uncertainty

Maintain `report.json` coverage for every obligation in `report-contract.md`. Use `covered`, `not-applicable`, or `blocked` only after recording chapter/anchor and evidence claim IDs. `not-applicable` requires positive evidence about why the topic does not exercise that concern.

The final report must answer the mechanism in its own prose even with all source citations closed. If a required answer is “read the source,” the report is incomplete.

Do not promise:

- ABI or source compatibility;
- on-disk byte compatibility;
- every race/crash interleaving;
- identical error codes, timing, or performance;
- undocumented bit-for-bit behavior.

Declare those only when an explicit compatibility matrix and conformance suite prove them.
