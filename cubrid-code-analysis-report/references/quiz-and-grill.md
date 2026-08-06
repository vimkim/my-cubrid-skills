# Quiz Authoring Prompt and Live Grilling Guide

## Contents

1. Static quiz purpose
2. Quiz authoring prompt
3. Quiz content and safety
4. Lightweight self-check
5. Live grilling state machine
6. Mastery rubric

## 1. Static Quiz Purpose

Static quizzes make the reader predict, reproduce, observe, and explain mechanisms. They are not trivia and do not replace the adaptive live grill.

Cover at least one quiz per central mechanism. Across the set include:

- normal flow;
- edge or failure flow;
- concurrency or crash reasoning;
- performance or policy trade-off;
- PostgreSQL/MySQL comparison reasoning;
- a design or reimplementation task.

## 2. Quiz Authoring Prompt

Use the following as a direction prompt, not as a rigid schema:

> Create a sequence of hands-on Quizzes that helps a second-year Computer
> Science student understand the selected CUBRID mechanism, not merely recall
> names. Put each Quiz in `quiz/quiz-N/`. Write `quiz.md` and `answer.md` in
> Korean while keeping standard English technical terms and code identifiers.
> Include at least one runnable SQL or script file so the learner can reproduce
> the important observation with the local CUBRID build. SQL, commands,
> filenames, output, and identifiers may remain English.
>
> Begin with a simple prediction, then make the learner trace causality through
> the relevant data structures, functions, state transitions, concurrency or
> recovery rule, and performance trade-off. Include normal-flow questions and
> progressively harder variations such as edge cases, failure, concurrency,
> PostgreSQL/MySQL comparison, and a small redesign or implementation task when
> those variations fit the topic. Do not force every category into every Quiz.
>
> `quiz.md` must tell the learner what to run, what to observe, and what to
> explain, without leaking the answer. `answer.md` must explain why the result
> occurs, connect it to report chapters and source-level mechanisms, discuss
> plausible wrong answers, and state what the exercise does not prove. Make the
> exercise safe to rerun. Add setup, cleanup, expected output, captured output,
> or a `quiz.json` manifest only when they make the Quiz clearer or more
> reproducible. This is an internal team artifact: prefer useful teaching over
> compliance paperwork.

Use contiguous directories beginning at `quiz-1`:

```text
quiz/quiz-N/
├── quiz.md
├── answer.md
├── run.sh or one/more *.sql/*.py scripts
├── setup.sql             # optional
├── cleanup.sql           # optional
├── expected/             # optional
├── raw-output/           # optional
└── quiz.json             # optional metadata/evidence
```

`quiz.md` is Korean prose and includes:

- learning objective and prerequisites;
- expected time;
- a prediction before execution;
- exact procedure;
- what to observe;
- analysis and teach-back questions;
- safe cleanup;
- report chapter and claim IDs.

`answer.md` is Korean prose and includes:

- the answer and acceptable variation;
- the causal mechanism;
- common misconceptions and why wrong answers fail;
- related chapters and claim IDs;
- what the experiment does not prove.

English is allowed for canonical terms, code, SQL, scripts, commands, identifiers, and filenames.

## 3. Quiz Content and Safety

- Require only CUBRID binaries/runtime. PostgreSQL/MySQL questions use included report evidence and reasoning, never their servers.
- Do not leak the answer in `quiz.md`, script comments, filenames, or expected-output names.
- Use fixed, unique, quiz-owned database/object names and verify ownership before cleanup.
- Make scripts non-interactive, idempotent, and deterministic or invariant-based.
- Return nonzero on failure and clean up resources created before a partial failure.
- Never delete broad paths or pre-existing databases/objects.
- For concurrency, validate permitted invariants rather than one scheduler order.

## 4. Lightweight Self-check

For every quiz:

1. Read it as a learner: the task and expected observation should be unambiguous.
2. Run the SQL/script at least once with the local CUBRID build and confirm that `answer.md` matches what was observed.
3. Run inexpensive syntax checks such as `bash -n` where applicable.
4. Confirm that rerunning or cleanup cannot damage pre-existing user resources.
5. Confirm that the question does not reveal the answer and that the answer explains causality rather than only showing output.

Repeated runs, captured receipts, hashes, and `quiz.json` are optional. Use them for nondeterministic, concurrency-sensitive, or unusually important exercises where extra evidence helps the reader.

## 5. Live Grilling State Machine

Persist `grill/mastery.json` and append events to `grill/session.jsonl`:

```text
READY
  -> ASK_ONE
  -> WAIT_FOR_USER
  -> EVALUATE
       -> MASTERED -> SELECT_NEXT
       -> PARTIAL -> MICRO_TEACH -> ASK_NARROWER
       -> MISCONCEPTION -> CORRECT_CAUSE -> ASK_NARROWER
       -> EVIDENCE_GAP -> RESEARCH -> REVISE_REPORT -> REAUDIT
  -> CAPSTONE_TEACHBACK
  -> COMPLETE
```

Rules:

- Ask exactly one Korean question per user turn.
- Preserve English technical terms and identifiers.
- Ask for the learner's model before explaining.
- Do not expose the answer before evaluating the response.
- On a weak answer, split the causal chain into a smaller question.
- After three failed attempts on one concept, assign a precise chapter/quiz review and mark it `RETEACH`; never auto-pass.
- If an answer exposes a report defect, correct the evidence/report and re-audit before continuing.
- If the user pauses, persist `PAUSED` and state that mastery is incomplete.

Each session event follows the exact `artifact-schemas.md` exchange schema with unique host/user turn IDs, legal state transition, one Korean question, and the learner answer preserved verbatim. Do not invent or translate user answers.

Attempts are contiguous per concept. `PARTIAL`, `MISCONCEPTION`, `RETEACH`, or `EVIDENCE_GAP` keeps the next exchange on that concept. Each reference must resolve to a real chapter anchor or Quiz linked by the concept's central behavior. Only the final capstone may transition to `COMPLETE`.

## 6. Mastery Rubric

Track each as `UNSEEN`, `PARTIAL`, `RETEACH`, or `MASTERED`:

1. responsibility, scope, Interface, and seams;
2. core data ownership and lifetime;
3. main lifecycle and state transitions;
4. concurrency invariants and forbidden interleavings;
5. durability, recovery, and failure behavior;
6. policy and performance trade-offs;
7. experiment interpretation and limitations;
8. PostgreSQL/MySQL similarities and non-equivalence.

Finish only when all are `MASTERED` and the learner completes an end-to-end capstone teach-back. Write `grill/mastery-summary.html` in Korean with strengths, weak areas, and chapter/quiz recommendations.
