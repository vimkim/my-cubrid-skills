# Source guides

This skill adapts four guides from `vimkim/my-docs`, reviewed at commit `4053ba6` on 2026-10-28.
The workflow references contain the operational guidance needed for ordinary use.
Read a full source guide when its examples or broader tool coverage help the current investigation.

| Guide | Role in this skill |
| --- | --- |
| [Linux DB and systems performance survey](https://github.com/vimkim/my-docs/blob/4053ba6/linux-performance/2026-10-28-linux-db-performance-survey.md) | Resource/error checks, server measurement boundaries, tool selection, collection quality, and FlameGraph generation. |
| [C++/DB investigation walkthrough](https://github.com/vimkim/my-docs/blob/4053ba6/linux-performance/2026-10-28-performance-investigation-walkthrough.md) | Competing hypotheses, equal-work costs, refutation conditions, one-change experiments, and scaling models. |
| [Linux C++ debugging and benchmark workflow](https://github.com/vimkim/my-docs/blob/4053ba6/linux-performance/2026-10-28-cpp-debug-benchmark-workflow.md) | Build identity, correctness tools, representative microbenchmarks, internal instrumentation, generated code, and repeatable A/B validation. |
| [Gregg material coverage review](https://github.com/vimkim/my-docs/blob/4053ba6/linux-performance/2026-10-28-gregg-performance-coverage-review.md) | Method before tool inventories, active benchmarking, thread-state analysis, and evidence for the limiting component. |

Local copies normally reside under `/home/vimkim/gh/my-docs/linux-performance/` with the same filenames.
The coverage review describes gaps in an earlier survey revision.
Use it as methodological context rather than a current defect list.
The investigation walkthrough uses fictional measurements and function names.
Its example numbers are not CUBRID performance evidence.

The guides link primary tool documentation.
Check the installed version's help and supported events before executing version-sensitive commands.
For CUBRID behavior and runtime setup, follow current `CUBRID.md`, repository instructions, source, and version-specific manuals.
