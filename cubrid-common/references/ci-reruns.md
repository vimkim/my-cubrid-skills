# Rerun evidence

Read this for `suite-summary-v3` evidence produced by `/run rerun <source-run-id>`.
The command, manifest, and observation envelopes retain their existing versions.
Each summary describes its own execution. Source cases are not merged into its
counts or failure inventory.

## Validate the source

Apply the ordinary summary, raw-index, digest, provenance, failure-file, and
count checks to each linked source. For every v3 summary:

1. Require `.commit` to equal the selected Engine commit and its run/attempt to
   equal the execution being validated.
2. Derive the only permitted `.rerun.summary` path from `.rerun.run_id`,
   `.rerun.attempt`, and `.suite`:
   `providers/github-actions/runs/<run>/attempts/<attempt>/<suite>/summary.json`.
   Resolve paths beneath the evidence root and reject escapes, including symlinks.
3. Require the source summary bytes to match `.rerun.summary_sha256`, and its
   identity to match that path. Validate its v2 or v3 schema and raw index,
   including the raw index's summary digest and every recorded file digest.
4. Require all source shard build SHAs to equal the selected Engine commit. For
   a source v3 summary, also require its explicit `.commit` to match. Follow its
   own source link recursively. Reject cycles and chains longer than 32 runs.
5. Check the child's `raw/github/rerun-source.json`: source run/attempt must
   match the link, its status must be `completed`, and its `updated_at` must not
   follow the child's `raw/github/run.json.created_at`. These timestamps bound
   which source attempt the producer could have read. An updated source run
   without retained proof of the earlier attempt remains unavailable.
6. Require the child's `raw/plan/split.meta` Engine `sha` to match the selected
   commit and its `rerun_since` testcase revision to match the source plan's
   `tc_sha`. Keep both testcase revisions and branches visible when comparing
   cases.

An unavailable or invalid source leaves the rerun unvalidated. An empty plan
alone never establishes a passing suite.

## Interpret the execution

- `rerun.mode = partial`: apply the ordinary count and failure checks to the
  rerun's actual shards. These counts cover only selected cases. Keep source
  failures as a separate historical inventory, even if the rerun passes.
- `rerun.mode = carried_forward`: all current counts are zero, with empty
  shards and failures. Require the current verdict and CI state to equal the
  validated source verdict and state. Report the source execution and its
  counts separately; this execution ran no cases. The plan must contain zero
  total and parallelism, no planned or published shards, and zero
  `rerun_failed`, `rerun_unrun`, `rerun_short`, `rerun_gone`, and `rerun_changed`.

The acquisition ledger describes the requested execution. A carried suite has
no current shards; source raw evidence lives under its own run/attempt.
Source acquisition failures can prevent a rerun summary from being published.

For a FAIL-to-PASS comparison, match a source failure's full testcase path to a
passing testcase in the rerun shard's recorded raw JUnit file. Record both
executions, Engine SHAs, testcase SHAs, branches, and build configurations.
A source failure omitted by the rerun is not an observed pass. Even with an
unchanged Engine commit, a changed testcase or configuration constrains a
flakiness claim; follow the existing history and comparison contracts.

Zero-case reruns that changed or removed source cases are currently unavailable
rather than treated as a carried-forward verdict. Report that diagnostic and
keep their raw evidence separate from validated summaries.
