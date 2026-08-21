---
name: pp
description: Proceed with the pending task or previously proposed action.
disable-model-invocation: true
---

# Proceed

1. Continue the current unfinished task. If the immediately preceding assistant message requested permission for a specific action, treat this invocation as approval for exactly that action.
2. Keep all work within that already-stated scope.
3. If no pending task or specific proposed action is clear, ask what the user wants to proceed with.
4. Continue until the task is complete or genuinely blocked, then report the outcome.
