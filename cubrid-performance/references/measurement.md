# Measurement and bottleneck diagnosis

## Establish the target and interval

Identify the actual server, broker, client, utility, and worker threads relevant to the question.
Inspect process executable paths, command lines, loaded libraries, and cgroups.
Measuring a client command and its children excludes an already-running independent DB server.
Select explicit PIDs or an appropriate dedicated cgroup for server costs.
Use system-wide collection when host behavior is the question and the caller authorizes that scope.

Align counter start/end with the measured workload phase.
Record warmup, steady work, shutdown, idle periods, and background work that the interval includes.
Normalize counters using successful completed work from that same interval.
For strict boundaries, use supported counter enable/disable controls or internal counters.
Keep separate profiling runs identifiable rather than merging their values into a timing run.

## Resource and thread checks

Check workload errors, retries, and timeouts alongside kernel and DB logs for the relevant interval.
Compare counter deltas rather than lifetime totals.
Unavailable tools or permissions mean `unknown`, not zero errors or zero pressure.

| Resource | Utilization | Saturation | Errors |
| --- | --- | --- | --- |
| CPU and quota | Per-CPU and request-worker CPU time. | Run queue, runnable delay, and cgroup throttling deltas. | Hardware errors and observable limit failures. |
| Memory capacity | Available memory, RSS/PSS, and cgroup memory. | Reclaim, swap, and memory pressure. | OOM, allocation failures, and memory events. |
| Storage and filesystem | Bytes, IOPS, busy time, space, and inodes. | Queues, latency distributions, and I/O pressure. | I/O errors, resets, full volumes, and DB failures. |
| Network | Interface traffic and client/server utilization. | Queues, drops, and processing delays. | NIC errors, retransmissions, and connection failures. |
| Interconnect | Supported bandwidth and uncore counters. | Supported stall or contention evidence. | Platform logs and available error counters. |
| Software limits | Workers, connections, file descriptors, and user locks. | Queued demand and acquisition or service wait. | Rejections, retries, exhaustion, and timeouts. |

Use `vmstat`, `mpstat`, `pidstat`, `iostat`, `/proc`, cgroup statistics, and existing DB instrumentation as available.
Check kernel messages for the problem's time range.
Check slab accounting when host memory growth lacks a process-heap explanation.
Observe the load generator while benchmarking to identify client-side limits.

Classify request-related thread intervals as running, runnable awaiting CPU, blocked, or idle awaiting work.
Large off-CPU totals from idle workers do not identify a request bottleneck.
Parallel worker times can overlap and exceed request elapsed time when summed.
Use request identity and phase boundaries when attribution crosses workers.

## Select the next discriminating observation

| Hypothesis | Next observation | Interpretation limit |
| --- | --- | --- |
| More CPU work per completed operation | Instructions/work, CPU/work, call paths, and call counts. | Samples measure cost distribution, not call frequency. |
| Similar work executes less efficiently | Cycles/work, supported PMU metrics, memory samples, and generated code. | IPC alone cannot identify dependency, cache, frequency, or mixed causes. |
| Requests wait for CPU | Runnable delay, quota throttling, CPU balance, and request-worker state. | Aggregate off-CPU time includes other waits. |
| User locks or latches limit progress | Acquisition wait, hold time, owners, spin paths, and DB wait statistics. | Futex misses successful user-space acquisition and spin. `perf lock` primarily concerns kernel locks. |
| Cache sharing limits concurrency | Supported `perf c2c` evidence, struct layout, field ownership, and accessor code. | A shared line or HITM sample does not establish false sharing. |
| Allocation or memory growth dominates | Allocation stacks/counts, pool counters, RSS/PSS, reclaim, NUMA placement, and slab data. | RSS is not heap ownership. Placement statistics are not measured remote-load counts. |
| Filesystem or device I/O delays completion | DB I/O, matching FS operations, block issue/completion, and request correlation. | Syscall, FS, block, and durability boundaries differ. |
| Network or client constrains throughput | Client CPU, socket queues, retransmissions, NIC and request timing. | Host network counters can include unrelated traffic. |
| Brief interference drives tail latency | Request samples and aligned time-series or event traces. | A whole-run CPU graph can hide a rare blocked request. |

Record the observation that would weaken each leading hypothesis.
Choose the next tool for that observation rather than collecting every available profile.

## CPU collection examples

Use these commands from a new experiment artifact directory after identifying the actual server PID.
Assign `DBPID` to that PID first.
Run `perf list` and inspect local help before selecting supported events and options.
Check capabilities, user/kernel scope, container restrictions, and the actual failure when collection fails.
`perf_event_paranoid` alone does not determine access.
Use authorized privileges when available rather than changing host security settings as a routine step.

```bash
perf version
perf list
cat /proc/sys/kernel/perf_event_paranoid
ps -L -p "$DBPID" -o pid,tid,psr,comm

perf stat -p "$DBPID" \
  -e task-clock,cycles,instructions,context-switches,page-faults \
  -o perf-stat.txt -- sleep 30

perf record -F 99 -e cycles --call-graph dwarf,16384 \
  -p "$DBPID" -o perf-cpu.data -- sleep 30
perf report --stdio -i perf-cpu.data > perf-report.txt
```

The 30-second windows and 99 Hz frequency are starting examples.
Adapt them to the workload and collection budget.
These are separate fixed-time diagnostic runs against an already-loaded server.
Retain successful completion counts for each interval.
For a self-contained utility, replace PID attachment with `--` followed by its exact command and arguments.

Use `perf annotate --stdio` for the actual hot symbol when source/assembly detail is necessary.
Preserve the executable, DSOs, and matching symbols used during collection.
Choose frame-pointer unwinding only when the relevant call paths preserve frame pointers.
Check DWARF stack truncation, unknown symbols, lost samples, and counter running/enabled time.
Reduce event sets or collection cost when multiplexing or loss prevents interpretation.
Mark unsupported or uncounted events as unavailable.
Supported software events can still provide useful evidence when hardware PMU access is absent.
They cannot supply unavailable cycle counts or IPC.

CPU profiles show on-CPU sample distribution.
Compare self and inclusive cost, completed work, and absolute CPU time before ranking a regression.
A function's percentage can rise because another function becomes faster.
Check actual compiler output for inlining, vectorization, alias assumptions, and runtime dispatch.

## Wait, I/O, and memory collection

For runnable delay, use supported `perf sched` or BPF scheduler observations.
For blocking, combine off-CPU stacks with request state and DB waits.
Use targeted user-space probes or internal counters when custom latches remain invisible.
Prefer aggregated counters and histograms over per-event output for frequent events.
Bound trace duration and check event loss and overhead.

Correlate requests, workers, files, and asynchronous operation IDs when crossing layers.
Time proximity alone does not attribute a writeback worker's I/O to a specific SQL request.
DB logical fetches, DB physical I/O, process I/O, and block I/O are separate measures.
OS page-cache hits can avoid device access after a DB buffer miss.
Device busy percentage and average latency alone do not establish a storage throughput ceiling.

Use heaptrack, allocator statistics, or logical pool counters for allocation hypotheses.
Use NUMA and bandwidth evidence when memory placement or traffic is the proposed limit.
Callgrind and Cachegrind can isolate a small path when appropriate.
Keep their simulated counts and execution times distinct from real PMU events and native elapsed time.

## Scaling and visual evidence

Sweep one variable, such as worker count or offered rate, while controlling the workload definition.
Record throughput, request latency, CPU/work, errors, and waits at each point.
Compare low- and high-concurrency profiles near a plateau or regression.
Use that evidence to distinguish serial work, contention, client limits, bandwidth, and quota effects.

For fixed work, Amdahl's ideal model is `S(N) = 1 / (f + (1-f)/N)`.
State its assumptions before interpreting a serial fraction `f`.
A high-concurrency lock-sample percentage is not a measured serial fraction.
For stable averages at one system boundary, Little's law is `L = throughput * mean response time`.
It does not predict p99 or prescribe a worker count.

Generate FlameGraphs or scaling plots when they clarify the finding.
For a FlameGraph, use the survey's stack conversion instructions from [sources.md](sources.md).
Label graph width as samples or the actual selected event weight.
Graph width is neither call count, chronological time, nor request latency.
Use request distributions over time when intermittent behavior matters.
Produce files or viewer links and keep all analysis headless on the remote host.
