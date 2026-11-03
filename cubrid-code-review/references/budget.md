# Control review cost

## Interpret the requested ceiling

Apply the ceiling to each reviewer's complete logical assignment. Retries, continuation agents, specialist helpers, and verification subagents count toward that assignment. Reviewers cannot create nested agents.

Use 5% of the full weekly allowance or 10% of the full daily allowance. These percentages refer to allowance consumed during the assignment. They do not refer to the fraction remaining when it starts. If both comparable limits exist, satisfy both. Record this conservative interpretation before execution.

Record the provider, account, allowance units, window definition, reset time, observation time, and remaining allowance. Use the provider's actual units. A message quota, credit quota, token total, and percentage indicator are different measurements.

A five-hour window is not a daily window. Missing daily telemetry does not authorize relabeling another window. If only the weekly ceiling is measurable and enforceable, use that ceiling and disclose the missing daily measure.

When allowance units are tokens, the per-agent token ceiling is the smaller applicable value:

```text
floor(0.05 * weekly_token_allowance)
floor(0.10 * daily_token_allowance)
```

Use this calculation only for known token allowances. Never estimate a token allowance from a subscription price or an unexplained dashboard percentage.

Five agents at their ceilings can consume 25% of a weekly allowance or 50% of a daily allowance. The coordinator consumes additional usage. Treat each per-agent ceiling as a maximum, not a target.

## Select an execution mode

| Mode | Required condition | Behavior |
|---|---|---|
| Strict, the default | A verified mechanism can enforce the requested ceiling before spending beyond it. | Launch only assignments covered by that mechanism. |
| Explicit absolute budget | The user authorizes a token, credit, or currency ceiling as a replacement for the percentage ceiling. The harness can enforce it. | Apply the authorized ceiling. State that percentage compliance remains unknown when conversion is unavailable. |
| Best effort | The user explicitly accepts estimates and the absence of a hard cap. | Set a finite per-agent scope, time target, usage target, and total review envelope. Disclose possible overshoot. |

If the requested ceiling cannot be enforced, prepare scope and artifacts with the coordinator. Do not launch paid reviewers under strict mode. Report `needs-budget` and ask for an enforceable budget or explicit best-effort authorization. Preserve the prepared work for resumption.

Do not silently weaken strict mode. A timer, polling loop, prompt instruction, context-window size, output-token limit, or reported token total is not a cumulative spending cap.

An enforcement mechanism must account for repeated input, cached input at applicable rates, reasoning, output, and concurrent requests. It must reserve enough for in-flight work. Record which units the mechanism actually bounds. An API spending cap does not establish subscription-quota compliance without a valid conversion.

Account-wide usage deltas cannot attribute consumption to individual agents when other sessions are active. Shared hard limits require coordinated reservations. If attribution is unavailable, report the limitation instead of inventing per-agent usage.

## Allocate the review

Agree a finite total envelope before parallel review. Include the coordinator and follow-up verification. If the user supplied only per-agent ceilings, request the total envelope with any missing budget decision. Reuse that decision throughout the run.

Reserve part of the envelope for the coordinator to verify and consolidate findings. State the allocation before launching reviewers. Never allocate the whole envelope to initial exploration.

Use up to five initial reviewers. For irrelevant roles, save usage by combining assignments or marking them not applicable. Use concise context pointers and per-role source slices. Read a shared specification once and pass its path and relevant requirements.

Before adding reviewers beyond five, name the uncovered invariant and check both the assignment ceiling and the remaining total envelope. If no expansion fits, create a handoff. A broad PR does not authorize more spending.

Choose one checkpoint before the assigned budget ends. When reliable usage telemetry exists, use it. Otherwise best-effort mode uses its declared time and scope checkpoints. Neither timing nor token estimates prove percentage compliance.

At each checkpoint, save findings, checked paths, remaining questions, commands, and evidence locations. Stop before an enforced limit. Keep the termination allowance inside the reservation. An agent stopped without a final report leaves a coverage gap.

Report measured usage, estimates, and unknown usage in separate fields. Include the enforcement mechanism, limits, actual agent count, retries, remaining envelope, and any overshoot. Never describe a prompt target as an enforced maximum.
