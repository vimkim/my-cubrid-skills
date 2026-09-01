# Focused CUBRID Probe Safety

Read this reference only when a survey needs runtime observation or temporary source instrumentation.

## Worktree Fidelity

- Capture `git status --porcelain=v1 -z` and `git diff --binary --no-ext-diff` before instrumentation.
- Instrument only tracked files that are clean at baseline. Choose another observation point when a target overlaps user work.
- Keep every scratch file, log, backup, and pid record outside the CUBRID worktree.
- Preserve indentation exactly. Treat an unrelated indentation-only diff as a failed patch.
- Reverse only the exact probe patch. Use no reset, checkout, restore, clean, or stash as cleanup.
- After reversal, require the status and binary diff to match the baseline and require every probe marker to be absent.

## Owned Runtime Resources

- Use unique survey-owned database, directory, file, process, port, and object names.
- Record ownership before cleanup, then delete or stop only those resources.
- Ask before stopping user-owned CUBRID services. Note the running databases and restart exactly what was authorized and previously running.
- Use assertions only in an isolated disposable environment. Prefer a uniquely prefixed log for ordinary probes.
- Verify child command lines before killing processes; a `cubrid` wrapper pid may exit while its child remains.

## Reliable Observations

- Attach a watcher before counter-based work. CUBRID performance counters may remain zero while `stats_on` is false and no watcher is attached.
- A csql communication histogram observes its transaction's server thread, not daemon-thread work. Use an interval `statdump` watcher for daemon activity.
- Search every increment site of a chosen `PSTAT_*` counter before trusting its name. State the actual increment semantics in the survey.
- Treat `;checkpoint` as an asynchronous request. When the observation requires a completed checkpoint, use a controlled synchronous operation such as `cubrid backupdb -C` with survey-owned output.
- For timing or concurrency, repeat the probe and evaluate an invariant or distribution rather than one exact schedule or count.

## Instrumentation Transaction

1. State the evidence gap and why existing behavior, logs, counters, tests, and debugger observation cannot close it.
2. Capture a successful clean `just build`. If installation is blocked by running processes, ask before stopping them.
3. Save the original target hashes and exact probe patch with a unique `CUBRID_CODE_SURVEY_<id>` marker.
4. Add only the identifiers needed to interpret the event, such as thread, transaction, page/object, state, and event.
5. Build, run the narrow reproducer, and save the decisive output.
6. Verify the target did not change unexpectedly, reverse the exact patch, and confirm original hashes.
7. Build again so no installed binary contains the probe, then confirm no survey-owned or instrumented process remains.

Stop when a build fails, ownership is uncertain, the patch cannot reverse exactly, the baseline diff is not restored, a process may still run instrumented code, or the result cannot distinguish the hypothesis from an alternative explanation.
