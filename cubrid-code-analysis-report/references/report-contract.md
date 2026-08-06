# Korean HTML Book Contract

## Contents

1. Audience and language
2. Artifact tree
3. Mandatory coverage
4. Chapter writing pattern
5. Visual and navigation rules
6. Reimplementation readiness

## 1. Audience and Language

Write for a second-year university CS student who understands C/C++, data structures, operating-system basics, and introductory databases but not DBMS internals.

- All final visible prose, navigation, captions, alt text, quiz questions/answers, and mastery summaries are Korean.
- Preserve canonical English technical terms, identifiers, SQL, scripts, commands, and paths.
- Define each acronym and CUBRID-specific term on first use.
- Use one idea per sentence. Start with a concrete example before abstraction.
- Never use childish language to achieve accessibility.

## 2. Artifact Tree

Use this shape; split or combine chapters only through `report.json` while retaining every obligation:

```text
<report-dir>/
├── index.html
├── provenance.json
├── report.json
├── assets/report.css
├── chapters/*.html
├── evidence/
│   ├── claims.jsonl
│   ├── report-audit.{md,json}
│   ├── complete-audit.{md,json}
│   ├── runs/<id>/meta.json
│   └── raw/
├── experiments/experiment-N/
├── research/
├── quiz/quiz-N/
└── grill/
```

The book must work offline. Do not load remote CSS, JavaScript, fonts, images, iframes, or Mermaid. Do not use `<script>`, `<style>`, `style` attributes, `srcdoc`, `data:` resources, or active embedded content; put presentation in `assets/report.css`. The v1 Book needs only semantic HTML, native `<details>`, local CSS, tables, and inline SVG. Every published HTML file is subject to the same checks; raw HTML under `evidence/`, `research/`, `experiments/`, or a Quiz `raw-output`/`observed`/`expected` directory is evidence rather than a Book page.

## 3. Mandatory Coverage

Each item appears in `report.json` with status, chapter/anchor, and supporting claim IDs. If irrelevant, keep the item and give an evidence-backed `not-applicable` explanation.

1. **orientation**: topic, declared scope, audience, learning goals, reading paths, key conclusions, limitations, all three exact revisions, and dirty-state provenance.
2. **mental-model**: problem, responsibility, input/output, one concrete scenario, whole-system picture, and glossary seed.
3. **scope-interface-seams**: callers, dependencies, public/internal Interfaces, pre/postconditions, ownership, ordering, errors, configuration, performance, and neighboring responsibility.
4. **data-ownership-lifetime**: core structures/fields, identity, lookup keys, allocation, ownership, lifetime, reclamation, volatile/persistent state, invariants, and layouts/formulas where needed.
5. **lifecycle-state-machines**: startup, steady state, shutdown, abort, restart, legal/illegal transitions, guards, actions, failure, and state diagrams consistent with tables.
6. **core-workflows**: end-to-end fast, slow, miss, retry, and failure paths with narrative, call flow, sequence diagram, and complete pseudocode branches.
7. **concurrency**: thread/process roles, protected state, mutex/latch/lock/atomic rules, ordering, wait/wakeup, retry, happens-before, permitted/forbidden interleavings, starvation/deadlock/race defenses.
8. **storage-durability-recovery**: volatile/durable state, WAL/LSA/LSN equivalents, dirty tracking, write ordering, checkpoint/flush/recovery, crash matrix, restart reconstruction, idempotence, and partial failure.
9. **policies-algorithms**: replacement/selection/scheduling rules, thresholds, configuration, cost/complexity, full pseudocode, pathological cases, and trade-offs.
10. **errors-resource-pressure**: allocation/I/O/corruption/timeout/full-disk/cancellation/shutdown-race behavior, assertion boundaries, propagation, cleanup, retry, and degraded mode.
11. **performance-observability**: hot paths, contention, CPU/cache/I/O characteristics, memory formula, scaling limits, metrics, counters, logs, utilities, debugger landmarks, tuning mechanisms, and measurement caveats.
12. **experimental-validation**: hypotheses, exact commands, raw results, controls, repetitions, interpretation, alternatives, cleanup, and observer effect.
13. **postgresql-analysis**: nearest analogue and all applicable shared comparison axes with semantic gaps.
14. **mysql-analysis**: concrete engine owner, nearest analogue, shared axes, and semantic gaps.
15. **cross-database-comparison**: terminology map, shared-scenario flows, responsibility/policy table, evidence for every substantive cell, and `equivalent`/`partial analogy`/`no equivalent` labels.
16. **reimplementation-blueprint**: complete Interface contract, abstract data model, initialization/shutdown, total transitions, algorithms, concurrency, recovery, errors, configuration, dependency seams, implementation order, and conformance tests.
17. **glossary-evidence-unknowns**: Korean glossary, complete source/evidence index, experiment transcript, coverage matrix, known unknowns, compatibility limits, and readiness declaration.
18. **teaching-map**: chapters and claim IDs mapped to static quizzes and live mastery areas.

## 4. Chapter Writing Pattern

Every chapter includes:

1. Korean learning goals.
2. A concrete scenario or question.
3. The intuitive model.
4. Exact mechanics with claim IDs.
5. Invariants, edge cases, and failure paths.
6. One or more useful visuals when relationships warrant them.
7. A short Korean recap.
8. A transition to the next chapter.

For every main workflow, combine:

- prose explaining why each step exists;
- a call-flow or sequence visual;
- pseudocode detailed enough to preserve all meaningful branches;
- a table of state before/after, locks, mutations, I/O, result, and claim IDs.

Source excerpts must remain short and subordinate to explanation. The reader should not need them to reconstruct the mechanism.

## 5. Visual and Navigation Rules

- Every HTML file declares `<!doctype html>`, `<html lang="ko">`, UTF-8, viewport, a unique `<title>`, one `<h1>`, and a `<main>` landmark.
- `index.html` links every chapter. Every chapter links index, previous, and next chapters.
- All local links and fragments resolve; IDs are unique per page.
- Tables use headers and captions. Diagrams have Korean text alternatives.
- Use accessible contrast, visible keyboard focus, responsive overflow for tables/code, and print styles.
- Mark evidence status with both text and color; color alone never conveys meaning.
- Use these labels consistently: `Source-confirmed`, `Runtime-observed`, `Inferred`, `Unknown`, `Partial analogy`, and `Not applicable`.
- Do not hide central explanations in collapsed elements.

## 6. Reimplementation Readiness

The last chapter declares exactly one:

- `READY WITHIN DECLARED SCOPE`
- `PARTIALLY READY`
- `NOT READY`

`PARTIALLY READY` and `NOT READY` are honest declarations for an incomplete `DRAFT` handoff only. This skill's report/complete verifiers intentionally hard-stop unless the declaration is `READY WITHIN DECLARED SCOPE`; an incomplete draft cannot be promoted to `REPORT_READY` merely because it labels its gaps.

`READY WITHIN DECLARED SCOPE` requires that an independent implementer can answer, without reopening source:

- What is the Interface and every caller obligation?
- Who owns each state object and when is it reclaimed?
- What state exists before and after every operation and branch?
- What are all retry, wait, and failure conditions?
- What protects each mutable state and in what acquisition order?
- What survives an I/O error or crash and how is state reconstructed?
- What persistent layouts and compatibility rules are in declared scope?
- What is startup, shutdown, abort, and recovery order?
- In what implementation order can the Module be rebuilt?
- Which conformance tests prove behavioral compatibility?

Any required “read the source” answer, unsupported central claim, hidden unknown, unresolved concurrency/recovery rule, or missing conformance oracle prevents `READY`.

The readiness declaration applies only to the explicit scope. It does not imply drop-in, ABI, byte-format, timing, or performance equivalence unless those are separately proved.
