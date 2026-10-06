# CUBRID Skills

Terms used by the CUBRID development skills.

## Language

### Pull request publication

**PR body draft**:
The saved text proposed for a pull request's description, available for the user to read and edit before publication.
_Avoid_: Draft PR, when referring to this text

**Draft PR**:
A pull request published on GitHub in draft status.
_Avoid_: PR body draft, when referring to the GitHub pull request

**Detailed explanation**:
An optional companion document for technical context that exceeds the short PR body's scope.

**Publication confirmation**:
The user's explicit approval of the reviewed PR material and the listed operations needed to publish it.
_Avoid_: Skill invocation, as a synonym for approval

**Draft context**:
The source revision, publication destination, and proposed operations associated with a saved PR body draft.
_Avoid_: Approval record, because context alone does not establish authorization

### CI comparison

**Exact merge-base baseline**:
CI evidence for the merge-base Engine commit resolved from a pinned PR head and pinned target tip. Evidence from a nearby commit is contextual evidence, not this baseline.
_Avoid_: Latest target CI, target-tip baseline

**Pre-existing failure signature**:
A failure at the same testcase path with matching observed messages, diffs, or stacks on both the baseline and PR head. This describes observed evidence without asserting identical root causes.
_Avoid_: Proven unrelated failure

**Additional head failure**:
A failure observed on the PR head with comparable baseline evidence that does not show the same failure. It is a candidate for investigation, not proof of an Engine regression.
_Avoid_: Proven PR regression
