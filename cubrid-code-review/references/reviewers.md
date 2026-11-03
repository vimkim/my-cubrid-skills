# Specialist reviewer contract

## Shared investigation method

Read the pinned patch and assigned source. Verify the revision before analysis. Use repository policy and the actual build configuration to determine language and platform behavior.

For each changed path, identify the relevant invariant and its owners. Trace callers, callees, shared state, error paths, and cleanup. Follow unchanged code when it determines whether the change is correct. Report an unrelated old defect separately.

List concrete failure hypotheses. Try to disprove each hypothesis before reporting it. Prefer the smallest executable reproduction when practical. A complete source argument can establish a defect without a runtime reproduction. State which form of evidence you obtained.

For concurrency, give a feasible actor schedule and identify synchronization at each step. For recovery, give the durable state before and after the crash point. For performance, identify the workload and limiting resource. Do not claim a measured regression from source inspection.

Each reviewer returns the pinned identity, assigned and inspected paths, checked invariants, commands, results, candidate findings, unresolved questions, and budget status. Use `complete`, `partial`, or `blocked` for coverage. Use `findings` or `no-confirmed-findings` for the finding result. These are separate dimensions.

Stop when assigned invariants have sufficient evidence or when the budget requires termination. Report all supported findings. Do not spend the remaining allowance on unrelated cleanup.

## Systems reviewer

Check the C/C++ execution and ownership rules that the changed code actually uses:

- Object lifetime, allocation ownership, cleanup on partial failure, and allocator pairing.
- Bounds, integer overflow, signed conversion, alignment, aliasing, and uninitialized state.
- Exception boundaries, STL operations that can throw, and conversion into CUBRID error handling.
- Linux syscall contracts, `errno` lifetime, interrupted operations, descriptor reuse, and resource cleanup.
- Relevant compile variants, including server and standalone behavior, assertions, and release builds.
- Caller contracts after signature or structure changes. Inspect serialization or ABI consequences with the responsible reviewer.

Many CUBRID `.c` files compile as C++. Confirm the actual compiler configuration. Apply the personal policy for GNU indent markers and throwing STL operations when that policy is available.

## Concurrency reviewer

Check shared state and transactional visibility:

- Lock and latch ownership, acquisition order, recursion, release, and exceptional exits.
- Atomic ordering, publication, condition-variable predicates, wakeups, cancellation, and shutdown.
- Races involving reclamation, slot reuse, thread exit, and stale object identities.
- Snapshot visibility, isolation, rollback, lock conversion, deadlocks, and transaction consistency.
- Interactions between user transactions, system operations, vacuum workers, and recovery.

For a proposed race, identify both actors and the path that permits overlap. Check whether a latch, transaction boundary, or lifetime rule prevents it. A shared variable alone does not prove a race.

## Storage and performance reviewer

Check data movement, persistence boundaries, and resource costs:

- Short reads and writes, interrupted I/O, offsets, lengths, alignment, and boundary arithmetic.
- Page and record layout, checksums, dirty flags, pin ownership, and eviction interactions.
- Write ordering, flush contracts, WAL dependencies, and behavior after I/O failure.
- CPU complexity, allocation growth, copying, lock contention, cache behavior, and false sharing.
- I/O amplification, sequential versus random access, batching, queues, and bounded resource growth.

State whether a performance concern follows from code, a model, or a benchmark. Use a representative workload and controlled before-and-after conditions for a measured claim. Record cache state, storage, configuration, build, concurrency, and errors. Keep a possible regression as an open question when evidence is insufficient.

Coordinate with recovery on the boundary between a successful syscall and a durable database state.

## Recovery reviewer

Check atomicity and durability through failures and restart:

- Log creation and ordering before dirty-page persistence. Inspect LSA and recovery-record ownership.
- Undo and redo correctness, idempotent replay, partial records, and crash points between state transitions.
- Transaction abort, nested or system operations, compensation behavior, and restart during recovery.
- Checkpoints, log truncation or archive lifetime, page reuse, and recovery record compatibility.
- Vacuum and OOS deletion, slot reuse, and undo that reinserts into a slotted page.

Write the relevant sequence of states. Identify which states are durable and which data recovery reads. Check both ordinary abort and crash restart. A successful normal commit does not validate recovery behavior.

When vacuum slot reuse and recovery insertion interact, use the applicable formal-verification skill if available. Check the model's correspondence to the pinned code. A model result covers only its stated abstraction and properties.

## HA reviewer

Check the affected replication and failover contracts:

- Log production, shipping, ordering, replay, duplicate handling, and partial application.
- Transaction visibility and durability after promotion, failover, reconnect, or restart.
- Commit acknowledgment semantics, lag, retry, timeout, and lost-connection behavior.
- Roles and fencing that prevent conflicting writers where the affected protocol requires them.
- Protocol, on-disk, log, and configuration compatibility across supported versions.
- Changes to shared records or contracts that an unchanged replica or utility still consumes.

Trace the actual producer and consumer paths. If the change cannot affect HA, give the source-based reason and mark this role not applicable. Do not invent a requirement for unsupported rolling upgrades.

## Candidate finding record

For each candidate, provide these fields:

- Stable local ID, proposed priority, and a short statement of the failure.
- Pinned file and line location, changed hunk, and relevant symbol.
- Reachable preconditions, affected configuration, actors, and input.
- Violated invariant and its authoritative source when one exists.
- Complete failure argument or reproduction command and observed result.
- How the reviewed change introduces or exposes the failure.
- User impact, scope, and a suggested fix direction.
- Evidence type, evidence paths, disproof attempts, and unresolved assumptions.

Keep stylistic preferences outside defect findings. Report a documented-standard violation separately when it materially affects this review.
