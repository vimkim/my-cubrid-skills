---
name: cubrid-isolation-test
description: Create and run CUBRID .ctl isolation tests for MVCC/concurrency scenarios. Use when the user asks to test isolation, concurrency, MVCC, locking, or multi-session behavior for a CUBRID feature.
argument-hint: "<feature-description or CBRD-XXXXX> [--rc] [--rr] [--both]"
---

# CUBRID Isolation Test Creator & Runner

Create `.ctl` isolation tests that verify MVCC visibility, lock conflicts, and concurrent transaction behavior using CUBRID's CTP isolation test framework. Tests are run via the `qactl`/`qacsql` tools with deterministic multi-client orchestration.

## When to Use

- User asks to test isolation, concurrency, MVCC, or locking behavior
- User mentions "isolation test", ".ctl test", "concurrent access test"
- After implementing a storage/transaction feature that affects multi-session behavior
- When verifying MVCC snapshot visibility for a feature (e.g., OOS, overflow, new column types)

$ARGUMENTS

## Prerequisites

- `$CUBRID` environment variable must point to a CUBRID install directory
- Resolve CTP_HOME from the configured installation; require `$CTP_HOME/isolation/ctltool/`.
- Resolve `CUBRID_TESTCASES_DIR` and its tracked `isolation/` subtree; validate Git revision and dirty state.
- Inspect prepare/run/cleanup scripts before execution. Use a dedicated environment free of unrelated CUBRID work: current scripts stop services, broadly kill current-user processes and recreate databases. A different database name or port alone does not isolate those effects.

## Step 0: Build CTP Isolation Tools (if needed)

Check if `qacsql` and `qactl` binaries exist. If not, build them:

```bash
cd "$CTP_HOME/isolation/ctltool"
make clean && make
chmod +x timeout3.sh runone.sh prepare.sh clean.sh
```

These binaries link against `$CUBRID/lib/libcubridcs`, so they must be rebuilt if the CUBRID install changes.

## Step 1: Prepare Test Database

The isolation framework uses a database called `ctldb`:

```bash
cd "$CTP_HOME/isolation/ctltool"
sh prepare.sh qacsql ctldb log
```

This deletes/recreates `ctldb`, starts the server, and rebuilds tools if needed. Verify ownership and disposability of that database and the dedicated execution environment before running. If unrelated processes or data can be affected, arrange isolation instead of merely warning and proceeding.

## Step 2: Understand the Feature

- If a CBRD ticket is mentioned, use `/cubrid-jira` to fetch context
- If working on OOS, use `/cubrid-oos-context` to load OOS knowledge
- Read the relevant source code to understand what concurrency scenarios to test
- Identify the key MVCC/locking behaviors to verify

## Step 3: Design Test Scenarios

For any feature that stores/modifies data, design tests covering these categories:

### Required scenarios (pick what applies):

1. **MVCC UPDATE visibility**: Session 1 updates (uncommitted), Session 2 sees old value
2. **MVCC DELETE visibility**: Session 1 deletes (uncommitted), Session 2 still sees row
3. **UPDATE lock conflict**: Two sessions update same row — C2 blocks until C1 commits
4. **Concurrent UPDATE different rows**: Two sessions update different rows — no blocking
5. **REPEATABLE READ snapshot**: C2 snapshot preserved even after C1 commits

### Optional advanced scenarios:

6. **Multi-chunk/large value visibility**: Large values spanning multiple pages
7. **INSERT + DELETE interleaving**: Phantom read prevention
8. **DDL + DML concurrency**: Schema changes during active DML
9. **Deadlock detection**: Two sessions acquiring locks in reverse order

## Step 4: Write .ctl Files

### .ctl File Format

The `.ctl` format orchestrates multiple `csql` client sessions:

```
/* Header comment describing the test */
MC: setup NUM_CLIENTS = 2;

C1: set transaction lock timeout INFINITE;
C1: set transaction isolation level read committed;

C2: set transaction lock timeout INFINITE;
C2: set transaction isolation level read committed;

/* preparation */
C1: drop table if exists t;
C1: create table t(id int primary key, col1 BIT VARYING);
C1: insert into t values (1, CAST(REPEAT('AA', 1700) AS BIT VARYING));
C1: commit work;
MC: wait until C1 ready;

/* test case */
C1: update t set col1 = CAST(REPEAT('BB', 1700) AS BIT VARYING) where id = 1;
MC: wait until C1 ready;

/* C2 should see OLD value */
C2: select id, DISK_SIZE(col1), (col1 = CAST(REPEAT('AA', 1700) AS BIT VARYING)) from t where id = 1;
MC: wait until C2 ready;

C1: commit;
MC: wait until C1 ready;

C2: commit;
C1: quit;
C2: quit;
```

### Key .ctl Commands

| Command | Purpose |
|---------|---------|
| `MC: setup NUM_CLIENTS = N` | Initialize N client sessions |
| `MC: wait until C1 ready` | Wait for C1 to finish current command |
| `MC: wait until C2 blocked` | Wait for C2 to be blocked on a lock |
| `MC: sleep N` | Sleep N seconds |
| `C1: <SQL>` | Execute SQL on client 1 |
| `C1: commit` / `C1: rollback` | Transaction control |
| `C1: quit` | Close client session |

### Data and storage assertions

Choose values that exercise the intended behavior in the current build. For OOS-specific placement/size assertions, use `cubrid-oos-context` and verify actual source/configuration thresholds and resulting placement. Avoid hardcoded claims that one value size always triggers OOS, or that DISK_SIZE overhead is constant across layouts. The concurrency example above illustrates orchestration; its payload alone does not prove OOS activation.

### File Location Convention

Place test files based on isolation level and category:

```
cubrid-testcases/isolation/
├── _01_ReadCommitted/issues/<jira_id>_<feature>/
│   ├── <test_name>.ctl
│   └── answer/<test_name>.answer
├── _02_RepeatableRead/issues/<jira_id>_<feature>/
│   ├── <test_name>.ctl
│   └── answer/<test_name>.answer
├── _04_RepeatableRead_ReadCommitted/  (mixed isolation)
└── _05_ReadCommitted_RepeatableRead/  (mixed isolation)
```

**Naming**: `<feature>_<scenario>_NN.ctl` (e.g., `oos_update_visibility_01.ctl`)

## Step 5: Run Tests and Capture Answers

### First run (no answer file yet)

```bash
cd "$CTP_HOME/isolation/ctltool"
sh runone.sh /path/to/<test>.ctl 120
```

A missing answer normally produces NOK. Preserve every attempt and inspect the actual output before defining a new oracle:

```bash
cat /path/to/result/<test>.log
```

### Verify the output is correct

Analyze the `.log` output:
- Check row counts match expectations
- Check value equality columns (should be `1` for true)
- Check DISK_SIZE values are reasonable
- Verify blocking behavior occurred where expected (no timeout)

### Create answer file from verified output

For a new testcase only, capture the exact log after validating its behavior against the intended specification. For an existing regression answer, require a justified, authorized expectation change; do not bless a failing run by copying it:

```bash
cp /path/to/result/<test>.log /path/to/answer/<test>.answer
```

The framework does an exact `diff` between `.log` and `.answer`, so even whitespace differences cause failure.

### Verify test passes with answer file

```bash
sh runone.sh /path/to/<test>.ctl 120
```

Require the selected testcase to execute and report `flag: OK`, with the intended binary and configuration. Inspect all attempts: the installed runone.sh may retry until OK, so its last flag alone can conceal earlier failures. Preserve those failures and investigate instability.

## Step 6: Run All Tests

After all tests are created and have answer files, verify them all:

```bash
cd "$CTP_HOME/isolation/ctltool"
for ctl in /path/to/test_dir/*.ctl; do
  sh runone.sh "$ctl" 120 > "$ctl.run.log" 2>&1
  cat "$ctl.run.log"
done
```

All selected tests must execute and pass. Retain the complete logs and inspect earlier retries; do not reduce evidence to the last flag.

## Step 7: Summary

Present results in this format:

| Test | Scenario | Isolation | Result |
|------|----------|-----------|--------|
| `<name>` | What it tests | RC/RR | OK/NOK |

Include:
- Total pass/fail count
- Any unexpected behaviors discovered
- Files created (`.ctl` + `.answer` paths)

## Troubleshooting

### Exit code 126 on first run
Permission issue. Run:
```bash
chmod +x "$CTP_HOME/isolation/ctltool"/*.sh
```

### "ctldb is unknown" error
Database doesn't exist. Run `prepare.sh` again.

### Test hangs / timeout
- Check if CUBRID server is still running: `cubrid server status`
- Lock timeout is INFINITE — a deadlock or missed `wait until` can hang forever
- Use shorter timeout in `runone.sh` (e.g., 60 instead of 120)
- Check for `MC: wait until C2 blocked` on operations that don't actually block

### DISK_SIZE returns unexpected values
Inspect the current type representation, compression settings and record layout. Compare the intended value and actual placement; avoid assuming a fixed overhead or changing types solely to obtain an expected number.

### "find: CUBRID/log: No such file or directory"
Inspect the installed runner and emitted binary/log paths. A hardcoded path can indicate that cleanup or execution used a different installation; establish the effect before accepting the test result.
