# Control review cost

## Set the budget

Launch the planned reviewers without waiting for a budget decision. No available harness enforces a hard spending cap, so the budget bounds each review through scope, targets, and checkpoints.

Apply each budget to the reviewer's complete logical assignment. Retries, continuation agents, specialist helpers, and verification subagents count toward that assignment. Reviewers cannot create nested agents.

| Mode | Condition | Behavior |
|---|---|---|
| Bounded, the default | The user supplied no absolute budget. | Give each reviewer a finite scope, plus a time or usage target where one is available. Set the total review envelope. Disclose in the report that no hard cap was enforced and that overshoot is possible. |
| Explicit absolute budget | The user supplied a token, credit, or currency ceiling for each reviewer or for the whole review. | Apply that ceiling as stated. Use a harness control that enforces it when one exists. Otherwise treat it as the target, checkpoint before reaching it, and disclose that it was not hard-enforced. |

A timer, polling loop, prompt instruction, context-window size, output-token limit, or reported token total is a target, not a cumulative cap. Never describe one as an enforced maximum.

Record the available telemetry: provider, allowance units, window definition, reset time, observation time, and remaining allowance. Use the provider's actual units. A message quota, credit quota, token total, and percentage indicator are different measurements. A five-hour window is not a daily window.

As optional guidance, aim each assignment at no more than 5% of the full weekly allowance or 10% of the full daily allowance when that allowance is known. This guidance shapes targets. It never blocks or delays a launch.

Account-wide usage deltas cannot attribute consumption to individual agents when other sessions are active. If attribution is unavailable, report the limitation instead of inventing per-agent usage.

## Allocate the review

Set a finite total envelope before parallel review. Include the coordinator and follow-up verification. When the user supplied no envelope, derive one from the planned assignments, record it, and proceed. Reuse that decision throughout the run.

Reserve part of the envelope for the coordinator to verify and consolidate findings. State the allocation before launching reviewers. Never allocate the whole envelope to initial exploration.

Include real-code probes and coordinator replay in that reservation. Assign shared adversarial questions to existing seats. Calling a helper skill does not grant another model panel or reset an assignment's budget. Prefer a narrow replay over another full review.

Use up to five initial reviewers. For irrelevant roles, save usage by combining assignments or marking them not applicable. Use concise context pointers and per-role source slices. Read a shared specification once and pass its path and relevant requirements.

Before adding reviewers beyond five, name the uncovered invariant and check both the assignment budget and the remaining total envelope. If no expansion fits, create a handoff. A broad PR does not authorize more spending.

Choose one checkpoint before the assigned budget ends. When reliable usage telemetry exists, use it. Otherwise use the declared time and scope checkpoints. Neither timing nor token estimates prove compliance with a usage target.

At each checkpoint, save findings, checked paths, remaining questions, commands, and evidence locations. Stop before the assignment's target or explicit limit. Keep the termination allowance inside the reservation. An agent stopped without a final report leaves a coverage gap.

Report measured usage, estimates, and unknown usage in separate fields. Include the budget mode, targets and any explicit limits, whether a hard cap was enforced, actual agent count, retries, remaining envelope, and any overshoot.
