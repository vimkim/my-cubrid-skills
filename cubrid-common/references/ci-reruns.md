# Rerun evidence

Read this for `suite-summary-v3` evidence produced by `/run rerun <source-run-id>`.
The command, manifest, and observation envelopes retain their existing versions.
Each summary describes its own execution. Source cases are not merged into its
counts or failure inventory.

## Validate the source

`cubrid-ci verify` validates each v3 summary's source chain from retained
files. It checks the derived source path, the pinned source digest, the ordinary
summary, raw-index, provenance, failure-file, and count checks on every source,
the selected Engine commit, cycles and chains longer than 32 runs, source
completion before the rerun started, and the `split.meta` Engine and testcase
revisions. Its `rerun_sources` lists the validated chain, nearest source first.
A suite whose verified `summary` is not `validated` has an unavailable or invalid
source and remains unvalidated. Keep both testcase revisions and branches
visible when comparing cases.

An empty plan alone never establishes a passing suite.

## Interpret the execution

- `rerun.mode = partial`: the counts cover only the rerun's selected cases.
  Keep source failures as a separate historical inventory, even if the rerun
  passes.
- `rerun.mode = carried_forward`: all current counts are zero, with empty
  shards and failures, and the verdict and CI state equal the validated
  source's. `verify` checks the empty plan and the zero rerun counters. Report
  the source execution and its counts separately; this execution ran no cases.

The acquisition ledger describes the requested execution. A carried suite has
no current shards; source raw evidence lives under its own run/attempt.
Source acquisition failures can prevent a rerun summary from being published.
An acquisition failure stops new shards only in the affected suite; independent
suites continue under the shared concurrency ceiling. Validate and report their
completed evidence separately, while keeping the overall incomplete observation
in warning mode.

For a FAIL-to-PASS comparison, match a source failure's full testcase path to a
passing testcase in the rerun shard's recorded raw JUnit file. Record both
executions, Engine SHAs, testcase SHAs, branches, and build configurations.
A source failure omitted by the rerun is not an observed pass. Even with an
unchanged Engine commit, a changed testcase or configuration constrains a
flakiness claim; follow the existing history and comparison contracts.

Zero-case reruns that changed or removed source cases are currently unavailable
rather than treated as a carried-forward verdict. Report that diagnostic and
keep their raw evidence separate from validated summaries.
