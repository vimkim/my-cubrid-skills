# Experiments and Instrumentation Safety

## Contents

1. Experiment standard
2. Owned runtime resources
3. Evidence capture
4. Instrumentation decision
5. Safe instrumentation transaction
6. Hard stops

## 1. Experiment Standard

Runtime experiments are mandatory; source instrumentation is not. Every experiment records:

```text
Question -> Hypothesis -> Setup -> Action -> Observation
-> Interpretation -> Alternative explanations -> Cleanup
```

Also record exact build/runtime versions, configuration, inputs, repetition count, warm/cold state, nondeterminism, raw outputs, and claim IDs. Separate raw observation from interpretation.

Use positive and negative controls where possible. For timing-sensitive behavior, repeat and evaluate an invariant or distribution rather than one exact schedule/value.

## 2. Owned Runtime Resources

- Use uniquely named skill-owned databases, directories, files, processes, ports, and objects.
- Record ownership before cleanup.
- Never delete a pre-existing database or broad directory.
- Never stop the global CUBRID service merely for convenience.
- Use assertions only in an isolated disposable environment where a forced crash cannot harm user data.
- Stop only processes started and recorded by this experiment.

If an experiment needs a user-owned service or data mutation beyond the request, ask before proceeding.

## 3. Evidence Capture

Save scripts before executing them. Use `reportctl.py record` so argv, cwd, timestamps, expected/actual exit, stdout, and stderr are retained atomically under a stable ID.

Before the first Experiment, capture a successful `runtime-baseline-build` (`just build` in the pinned CUBRID root), then create `evidence/runtime-tools-baseline.json` with `reportctl.py runtime-snapshot`. This gate is mandatory even when instrumentation is not used. It resolves through the pinned worktree's `direnv` environment, requires an absolute `$CUBRID`, rejects tools outside `$CUBRID`, and binds the built source root/HEAD, build evidence, runtime environment, exact `csql`/`cubrid` hashes, the non-executed `cub_server` engine-binary hash, and successful `cubrid_rel` release output.

Every mandatory observation run passes `--runtime-tools-snapshot`, declares an exact `runner_argv`, and in schema v1 directly executes captured `csql` with the hashed SQL runner bound through `-i` or `--input-file`. `reportctl.py record` executes it under the sealed worktree runtime environment. A shell script or `cubrid` utility may perform separately captured preparation or cleanup, but an inert filename argument and an unverified claim about child commands do not prove the required CUBRID observation.

For every experiment store:

```text
experiments/experiment-N/
├── experiment.md
├── manifest.json
├── run.sh and/or *.sql
├── expected-oracle.md
└── observed/ or links to evidence/runs/
```

The experiment description and final Korean chapter must disclose instrumentation observer effects and alternative explanations.

## 4. Instrumentation Decision

Instrument only after naming a central evidence gap that cannot be closed with:

- SQL-visible behavior;
- existing CUBRID utilities;
- existing logs, counters, or trace facilities;
- tests;
- debugger observation;
- an unmodified controlled runtime.

Prefer a uniquely prefixed log over an assertion. Include relevant thread, transaction, page/object, state, and event identifiers. Add the smallest possible patch at a stable observation point.

## 5. Safe Instrumentation Transaction

The main agent performs these steps serially. Research agents never modify source.

1. Save baseline `git status --porcelain=v1 -z` and `git diff --binary --no-ext-diff` byte-for-byte.
2. Require every target source file to be clean relative to the baseline. If already changed, use a different point or ask; do not overlap user edits.
3. Use the already captured baseline `just build` and baseline runtime snapshot. If either is missing or failed, stop before instrumentation.
4. Save original file hashes and an exact instrumentation patch with a unique marker such as `CUBRID_CODE_ANALYSIS_<run-id>`.
5. Apply only that patch. Confirm the diff contains no unintended indentation-only changes. Preserve CUBRID indentation exactly; wrap C++-specific syntax in legacy `.c`/`.h` files with `/* *INDENT-OFF* */` and `/* *INDENT-ON* */` when required.
6. Run and capture a distinct `just build`, then capture the `instrumented` runtime snapshot.
7. Run the controlled experiment and capture raw evidence.
8. Verify target files have not changed unexpectedly since instrumentation.
9. Reverse only the exact patch after `git apply -R --check`. Never use `git reset`, `git checkout`, `git restore`, `git clean`, or stash as cleanup.
10. Confirm original file hashes, baseline status bytes, baseline binary diff bytes, and absence of instrumentation markers.
11. Run and capture a third, distinct `just build` so installed binaries no longer contain instrumentation, then capture the `post-clean` runtime snapshot and make it the active report runtime.
12. Run a hashed cleanup-verification script from the report directory. Stop only experiment-owned instrumented processes and confirm none remain.

When instrumentation is used, save `evidence/instrumentation.json` with baseline status/diff hashes; target original/restored hashes; exact nonempty patch path/hash; unique `CUBRID_CODE_ANALYSIS_*` markers; application/reversal timestamps; instrumented Experiment run IDs; the three distinct build IDs; all three runtime-snapshot paths; and the hashed cleanup runner/argv/run IDs. Every target must have been tracked and commit-clean at initialization. The patch must touch exactly the declared targets, contain every marker, and reapply cleanly to the restored source. At least one captured CUBRID binary hash must change in the instrumented snapshot, and every post-clean binary hash must match its baseline hash. Set `report.json.instrumentation.status=used-restored` only after every check succeeds. If instrumentation is not used, keep `status=not-used`; do not pre-label cleanup as verified.

`just build` is personal local tooling. In CUBRID-organization-facing explanations, describe standard build concepts rather than presenting `just` as project workflow.

## 6. Hard Stops

Stop immediately and report exact files/processes when:

- the baseline build fails;
- a target file overlaps pre-existing work;
- an unexpected diff or file hash appears;
- a patch cannot reverse exactly;
- baseline status/diff is not restored byte-for-byte;
- the post-clean build fails;
- a process still runs instrumented code;
- cleanup ownership is uncertain;
- the observation cannot be reproduced or distinguished from an alternative explanation.

Do not continue report generation as though source or binaries were restored. Preserve all captured evidence for diagnosis.
