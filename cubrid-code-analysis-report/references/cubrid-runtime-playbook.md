# CUBRID Runtime Observation Playbook

Field lessons from real Report Runs. Read this before planning Step 5 experiments; every item below cost real wall-clock time to discover. Each lesson states the trap, the detection signal, and the proven pattern.

## 1. Build gate vs. a busy CUBRID environment

**Trap**: `reportctl.py build` (`just build`) fails with recipe exit 75 when the target install environment has live processes (`cub_master`, `cub_server`, `cub_pl`). The build compiles fine; the *install* step refuses to replace busy binaries.

**Rule**: Before the gate, list survivors with `ps` and compare against the pinned env's install root. If user-owned servers are running, stop for authorization (experiments-and-safety §2 — never stop services merely for convenience). After approval: `cubrid service stop` scoped to that environment, rebuild, then restart exactly what was running (`cubrid server start <db>` — note the db names first with `ps -fp <pid>`).

**Run-ID immutability**: a failed gate run permanently occupies its ID (`Run ID already exists`). Retry under `runtime-baseline-build-2` and bind `report.json.runtime.runtime_build_run_id` to the new ID; the canonical name in the docs is a default, not a requirement.

## 2. The stats_on gate: counters are OFF by default

**Trap**: `cubrid statdump <db>` prints all zeros even after heavy workloads. `stats_on` is a hidden (`PRM_HIDDEN`) server parameter, default `false`, not changeable online; perfmon accumulates **only while a watcher is attached** (`perf_monitor.c` — `PRM_ID_STATS_ON` adds a permanent watcher; otherwise `n_watchers` must be > 0).

**Watcher options**:
- csql per-transaction histogram — the canonical self-contained observation (see §3);
- `cubrid statdump -i <sec> -o <file> <db>` kept alive in the background (global counters, includes daemon threads);
- `stats_on=yes` in cubrid.conf (requires restart; conf is shared across databases of the env — avoid for skill-owned experiments).

**Global counters persist after the watcher detaches, but only increments made *while attached* are ever counted.** Order matters: attach watcher → run workload → read counters → detach.

## 3. Canonical csql observation runner

The verifier demands the mandatory observation run be `csql ... -i <hashed.sql>`. The strongest pattern embeds the observation *inside* that same run, so the receipt carries its own evidence:

```sql
;set communication_histogram=yes
;.hist on

-- workload here --

;.dump_hist
```

`;.dump_hist` prints the full perfmon array for this transaction to stdout (captured by `reportctl record`). Caveats:
- per-transaction histograms count only this session's server thread — **daemon-thread work (checkpoint, page flush daemon) is invisible here**; use the interval-statdump watcher for those;
- `;checkpoint` requires `csql --sysadm`;
- promote counters, btree counters, dirty counters all show up per-tran; physical flush counters do not (see §5).

## 4. Forcing a flush you can observe

**Trap 1**: sysadm `;checkpoint` is an *asynchronous request*; the checkpoint daemon paces itself and may not finish for minutes on a debug build (`Num_log_start_checkpoints` ticks, `..._end_checkpoints` stays 0). Nothing lands in your per-tran histogram either way (§3).

**Trap 2**: waiting/polling wastes the run. **Proven trigger**: `cubrid backupdb -D <scratch> -C -r <db>` forces a synchronous checkpoint as part of backup and returns when done. Keep the scratch dir outside both the worktree and the report dir; `-r` skips archive retention.

## 5. Counter names lie: verify increment sites before choosing oracles

`Num_data_page_flushed` increments **only** in `pgbuf_flush_victim_candidates` — victim flushes. Checkpoint flushes never move it (EPIC CBRD-27193 defect D6; reproduced at runtime). Physical data-page writes are counted at the DWB layer as `Num_data_page_iowrites` (`double_write_buffer.cpp`). `Num_file_iowrites` includes log volumes — too coarse.

**Rule**: for every oracle counter, `rg` its `PSTAT_*` ID and read every increment site before trusting the name. State the verified meaning in `expected-oracle.md`.

## 6. `cubrid` CLI wrappers spawn children: pid files are not enough

**Trap**: `nohup cubrid statdump -i 60 ... & echo $! > watcher.pid` records the *wrapper* pid; the real `statdump` child survives `kill $(cat watcher.pid)` and re-parents to init. A cleanup script can report success while the watcher lives on.

**Rule**: clean up by exact cmdline match, not pid file: `pgrep -f "statdump -i 60 -o <your-unique-output-path> <db>"`, verify each `/proc/<pid>/cmdline` contains your experiment-unique path before killing, then assert zero remain. Make the output filename experiment-unique so the match cannot touch foreign processes.

## 7. Worktree fingerprint hygiene

**Trap**: provenance freezes `git status` byte-for-byte. Any stray file the run drops into the CUBRID worktree (a nohup log, a pid file, a backup archive) changes the status hash and can hard-stop finalization. Two easy ways to slip: `direnv exec <worktree> bash -c '... &'` runs with the worktree as cwd, and some shells reset cwd between tool calls.

**Rule**: give every side-effect an absolute path under the scratchpad or the report dir. After any background/dry-run work, `git -C <worktree> status --porcelain` and delete anything you created before proceeding.

## 8. Debug-build patience budget

`cub_server` start on a debug build can exceed 2–5 minutes when recovering a previously loaded database; `createdb` takes ~1 min. Run these via background tasks with generous timeouts and poll `cubrid server status` instead of blocking the whole turn. Never interleave another environment-mutating step while a recorded setup command is still running.

## 9. Shell portability of orchestration commands

The host shell may be non-POSIX (e.g. nushell): `echo ===` parses as an operator, glob flags differ (`--include` vs `-g`). Keep captured evidence immune by putting all logic in `bash` scripts executed as files (`bash script.sh`) — which the evidence contract already prefers — and keep interactive probing commands single-purpose.

## 10. Fastest deterministic promote workload

For B-tree promotion evidence: one csql session, monotonically increasing PRIMARY KEY inserts via `INSERT ... SELECT LEVEL, ... FROM db_root CONNECT BY LEVEL <= N`. N=20,000 yields ~4.4 promotions per insert (≈88k successes) with `promote_fail = 0` (single session ⇒ in-place branch). Deterministic-enough across reruns (±1%); treat magnitude + fail=0 as the oracle, never the exact count. Promotion failures require concurrent sessions and are timing-dependent — do not promise them in an oracle.
