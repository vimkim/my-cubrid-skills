# Experiment design and validation

## Choose the question

Separate the primary acceptance metric from explanatory metrics.
For example, instructions per row can explain a scan improvement while query elapsed remains the acceptance metric.
For an absolute target, record the threshold, workload, concurrency, and required observation interval.
If the caller supplies no threshold, report measured costs and limits without inventing a pass criterion.

For a regression, identify the known reference, regressed implementation, and proposed fix separately.
If all three matter, report the fix against both the regression and the original reference.
For ordinary optimization, the unmodified current implementation can supply a local comparison.
Retain that build and its state before editing when feasible.
If the caller requests no comparison, collect and report the chosen implementation alone.

## Build and runtime identity

Use the live CUBRID build interface rather than copying generic CMake flags into the worktree.
Inspect the available presets and actual compilation and link commands.
Check optimization, assertions, allocator, LTO, PGO, sanitizer state, and target ISA.
Use matching symbols for profiling the actual optimized build.
Record frame-pointer changes as build differences when they affect generated code.

Preserve the following evidence for each implementation:

- Source commit, tracked patch, and build-relevant untracked files.
- Compiler version, effective flags, preset, configuration, and build log.
- Executable and DSO paths, hashes or build IDs, and corresponding debug files.
- Install prefix and the environment that resolves server, client, and utility binaries.
- Host CPU, kernel, tools, NUMA/SMT, virtualization, cgroup limits, and relevant storage details.

Keep optimized timing, debugging, ASan/UBSan, and TSan builds distinct.
Use ASan/UBSan and TSan in separate runs.
Debugger attachment, rr, Valgrind, and dense tracing change execution conditions.
Use their evidence to diagnose behavior, then measure performance under the intended runtime conditions.
Compare instrumented and uninstrumented runs when collection overhead can affect the conclusion.

## Match CUBRID state and workload

Discover supported commands from the selected version and its manual.
Do not substitute PostgreSQL or other DB-specific commands from a general guide.

Record these conditions when they affect the experiment:

- Client/server or standalone mode, broker path, connection reuse, and client/server placement.
- Schema, indexes, optimizer statistics, execution plan, seed, data size, distribution, and actual storage representation.
- Selected columns, predicates, result consumption, expected output, successful rows or transactions, and error behavior.
- Isolation, durability, log/flush, buffer pool, background maintenance, and relevant DB settings.
- Concurrency or offered rate, request arrival model, warmup, measurement interval, and client resource use.
- Starting database and filesystem state, restore procedure, and DB/OS/device cache conditions.

Use independent disposable databases or compatible snapshots for builds that cannot share an on-disk format.
Never run two servers against the same database files.
Restore state between write workloads so later variants do not inherit earlier mutations.
Check that the measured server uses the intended installation after each switch.

Treat DB buffer residency, OS page cache, device cache, and CPU cache as separate conditions.
Define which layer a warm or cold experiment controls.
Host-wide cache drops and global tuning require an authorized, isolated experiment.
Inspect existing affinity, governor, and NUMA policy before proposing changes.
Record changed settings and restore temporary tuning after collection.
Recheck an optimization under normal conditions when special placement or tuning reduced variance.

For fixed work, compare the same successful completion amount and result.
For fixed duration, retain completed work and report throughput and cost per successful operation.
For latency, retain request-level samples, errors, retries, timeouts, and sufficient completion counts.
Closed-loop clients reduce offered load as responses slow.
For scheduled arrivals, retain schedule lag, queuing, and requests that did not complete.
Count a returned row as a latency sample only when it represents an independently timed request.

## Compare or assess an absolute target

1. Check expected results and completion counts before interpreting timings.
2. Choose bounded warmup, repetition, and run-duration settings suitable for the workload and observed variation.
3. Run comparable variants serially. Alternate or randomize their order to reduce drift.
4. Preserve per-run commands, elapsed time, throughput, latency distribution, completion counts, stdout, and stderr.
5. Summarize the raw results with their variation. Use uncertainty estimates when the decision requires them.
6. Check the primary metric and relevant memory, tail-latency, error, or concurrency regressions.
7. Collect diagnostic profiles separately, then check whether the predicted cause changed.

With one implementation, perform these steps without the variant comparison.
Report the measured value, variation, and absolute target status.
If no valid comparison exists, report the speedup as unmeasured.

For elapsed time or another lower-is-better metric, reduction percent equals `100 * (baseline - candidate) / baseline`.
For throughput, increase percent equals `100 * (candidate - baseline) / baseline`.
Elapsed speedup equals `baseline elapsed / candidate elapsed` for the same completed work.
Keep these quantities distinct and name the reference implementation.
Retain failed runs and explain exclusions rather than hiding them in successful averages.
Avoid claiming equivalence or a gain when the experiment cannot resolve the difference.

## Microbenchmarks and internal instrumentation

Use the project's existing benchmark harness where practical.
Represent real input sizes, distributions, ownership, cache state, and error paths.
Document whether setup, allocation, process startup, result consumption, and cleanup fall inside the timed interval.
Wait for asynchronous completion when completion cost is the question.

For Google Benchmark, choose CPU time, process CPU time, or real time to match the work.
Consume outputs and inspect generated code to detect eliminated or hoisted work.
Optimization barriers alone do not prove the intended operation executes in each iteration.
Framework repetitions are not independent request p99 samples.
Random interleaving inside one benchmark binary does not randomize separate baseline and candidate process starts.

For direct timers, use monotonic elapsed time for intervals and an explicit CPU clock for CPU consumption.
Document whether scope times include child scopes, blocking, and preemption.
Avoid summing nested inclusive timers or overlapping worker intervals as request elapsed time.
Join worker threads before reading their private counters, or use a valid synchronization scheme.
Connect asynchronous work through request or operation identifiers.

## Experiment record

Record actual values and artifact paths for the relevant fields:

| Field | Required content |
| --- | --- |
| Goal | Workload, primary metric, completion unit, correctness constraints, target, and scope. |
| Mode | Named comparison, local before/after, absolute measurement, or source-only investigation. |
| Identity | Revisions, patches, binaries, DSO/debug identity, compiler, effective flags, and installation. |
| State | Input, expected output, schema/plan, seed, settings, cache state, snapshot restoration, and warmup. |
| Environment | CPU/kernel, storage, NUMA/SMT, cgroups, interference, and client/server placement. |
| Collection | Commands, working directories, intervals, PID/TID/cgroup, event support, losses, multiplexing, and collection overhead. |
| Diagnosis | Resource checks, `unknown` observations, suspected limiter, competing hypotheses, supporting and opposing evidence. |
| Change | One intervention, semantic constraints, predicted effect, and refutation condition. |
| Results | Individual values, completion counts, errors, variation, correctness checks, and relevant secondary metrics. |
| Conclusion | Measured gain or absolute status, uncertainty, applicability, raw artifact locations, and next experiment. |

Use `not applicable` for fields outside the selected mode.
Distinguish checks not run from successful checks.
Keep illustrative numbers from the guides separate from experiment results.
