# Parallel Research and Audit Roles

Use these semantic roles when the host provides agents. Do not hardcode model names or host-specific agent types. If agents are unavailable, run the same checklists sequentially.

## Shared Packet Contract

Pass every researcher:

- exact topic and `research/scope.md`;
- immutable source roots, commits, dirty labels, and output research directory;
- the claim schema from `research-and-evidence.md`;
- one role only;
- a read-only constraint for source and final report files.

Require a structured return containing examined files/symbols, claim candidates, call paths, unknowns, search gaps, contradictions, and suggested experiments. The main agent validates and integrates every item. Agents never vote truth into existence.

Save role packets consistently under `research/packets/` as `cubrid.md`, `postgresql.md`, `mysql.md`, `experiments-and-quizzes.md`, and `pedagogy.md`. Each packet begins with the role, topic, Declared Scope digest, repository revision(s), and timestamp; no researcher writes Book files.

## Role 1: CUBRID Source Tracer

Trace Interfaces, callers, ownership, lifecycle, state machines, success/retry/error paths, concurrency, persistence/recovery, policies, configuration, observability, and shutdown. Consult local CUBRID docs first. Identify central claims needing runtime evidence.

## Role 2: PostgreSQL Comparator

Find the nearest PostgreSQL responsibility and trace it on the shared axes. Explain split responsibilities and semantic gaps. Return source evidence only; do not require a running PostgreSQL server.

## Role 3: MySQL Comparator

Find the concrete MySQL owner, often InnoDB, then trace the same axes. Explain server/storage-engine seams and semantic gaps. Return source evidence only; do not require a running MySQL server.

## Role 4: Experiment and Quiz Designer

Turn central CUBRID claims into safe hypotheses, controls, observations, alternative explanations, cleanup steps, and Korean mechanism quizzes. Flag requests that need user-owned services or unsafe assertions.

## Role 5: Pedagogy Architect

Design the Korean learning progression from mental model to reconstruction. Detect undefined terms, missing causal links, misleading analogies, visuals that need text alternatives, and places where citations substitute for explanation.

## Independent Completeness Reviewer

Run only after the main agent writes the full report and quiz tree. Give the reviewer the raw report directory, source/provenance contract, and report contract, but not the intended verdict or prior critique.

Check:

- every mandatory obligation or evidence-backed `not-applicable` result;
- claim-to-source/runtime integrity;
- source reachability and cited hashes;
- three-database semantic mapping;
- Korean readability and standalone explanations;
- runtime reproducibility and cleanup;
- quiz safety, reproducibility appropriate to the exercise, and answer accuracy;
- instrumentation removal and post-clean build;
- reimplementation readiness within declared scope.

Return numbered findings followed by exactly `VERDICT: APPROVED` or `VERDICT: REVISE`. Approval means the report satisfies the contract, not that it is merely long.
