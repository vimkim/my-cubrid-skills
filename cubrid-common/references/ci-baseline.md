# Exact merge-base CI comparison

## Acquire with the CLI

Use this workflow before attributing a PR's failed CI to its changes. A status-only request uses `cubrid-ci status` without baseline collection. Keep the existing one-status/one-exact-head collection and validation gates intact.

```bash
# Same requested suite filters as the independently collected head.
cubrid-ci collect-base "$PR_URL" "${SUITE_ARGS[@]}" --json > "$BASE_RESULT_JSON"

# Independent historical lookup when the full Engine SHA is already known.
cubrid-ci collect-commit "$ENGINE_SHA" "${SUITE_ARGS[@]}" --json

# Explicit historical execution; still requires Engine identity validation.
cubrid-ci collect-commit "$ENGINE_SHA" --run-id "$RUN_ID" --json
```

Capture nonzero exits and JSON. Exit zero means complete collected evidence, including red suites. Unknown baseline evidence never means a baseline pass or a PR regression. An unsupported installed command is an explicit capability limitation; keep the validated head inventory usable.

`collect-base` records repository, PR number, actual head ref/SHA, target ref/tip SHA, and observation time, then uses `git merge-base --all` on pinned commits. The target tip is not itself the merge base. Missing ancestry is fetched into a dedicated bare Git cache; zero or multiple bases remain unresolved. Feature targets work through their actual target identity. Compare the recorded PR/head identity with the independent head collection; a moved head prevents comparative conclusions for that pair.

Discovery follows all paginated exact-commit statuses and GitHub Actions check links, without a `pull_request` event filter or a repository-wide workflow scan. Its recorded coverage is a limit on discovery, not proof that unobserved CI never ran. Without exact links, an explicit run ID can select a candidate; do not guess from workflow `head_sha` or a run title. Selection uses greatest run ID, then report time, source, and record ID per suite; it pins the current attempt and preserves a newer unfinished execution. Explicit run selection does not manufacture a commit-attached status.

The collector proves tested Engine identity using per-shard build provenance, independently of workflow revision and testcase revisions. A build produced by another run is valid when the consumed Engine SHA and producing execution reconcile. Synthetic merge-tree results are contextual unless their tested identity equals the requested Engine commit. Partial suites, inaccessible metadata, expired artifacts, or wrong Engine evidence leave the relevant baseline unavailable or unvalidated.

`--attempt` requires `--run-id`. Since remote suite artifacts are not attempt-addressable, an older attempt requires an already validated immutable local suite bundle under the commit evidence root. Missing cached evidence remains unavailable; digest or identity mismatches fail without a network bypass. Neither baseline lookup nor missing evidence authorizes CI triggers, cancellation, comments, source/testcase edits, or local merges.

## Validate independently

Verify the baseline with `cubrid-ci verify <saved collect-base result> --pr <pinned PR> --pr-head <pinned head>` and the same `--suite` filters. The command selects the observation behind the saved result and checks the baseline relationship against the pins (merge base equals the collected commit, same PR number and head), the observation and manifest, each completed suite's identity, digests, failure files and counts, and any rerun lineage. Its `baseline` field is `validated_exact`, `partial_exact`, `unavailable`, or `invalid`. A collector without `collect-base` or `verify`, or a run that printed no command result, leaves the baseline `unavailable`. A malformed baseline does not invalidate independent head evidence, but supports no comparison.

For partial baseline observations, only suites whose verified `summary` is `validated` are eligible for comparison; reconcile every requested suite's state. Never promote retained raw shards to complete suite verdicts. Cite the verified `observation_dir`; the root manifest can change on later collections. No automatic fallback to an older passing execution.

## Compare and bound attribution

Use full suite-relative testcase paths and actual messages, diffs, and stacks. A basename or aggregate failure count cannot establish a match. Reconcile requested-suite counts and account for every head failure once:

| Classification | Evidence needed |
|---|---|
| `also_observed_on_base` | Same exact case and matching observed failure signature in validated evidence on both sides |
| `additional_on_head` | Comparable baseline coverage of that case lacks the head signature; distinguish baseline pass from a different baseline failure |
| `uncomparable` | Missing case coverage, unvalidated identity, or insufficient signatures/inputs prevents comparison |
| `base_only` | A baseline failure absent from comparable head evidence; record separately from head totals |

Record the public and private testcase SHAs independently, suite selection, build mode, and relevant configuration/tool inputs. When testcase SHAs differ, compare exact Git objects for affected testcase files, answers, helpers, and fixtures. Equal affected files strengthen comparability; unavailable objects or unverified dependencies remain limitations. Never assert whole-repository equivalence from a few equal files. Different configuration or inputs can leave even a baseline-pass/head-fail result uncomparable.

Matching signatures support pre-existence of that signature, not identical root cause or harmlessness. Keep crashes visible and record pre-existing signatures as separate follow-up work. An additional head failure is a candidate regression or compatibility issue, not proof of an Engine defect. Preserve each hypothesis's evidence, confidence, unknowns, falsifier, and next action. If a controlled same-test-revision experiment is needed, describe it and hand triggering to the separately authorized CI workflow. Project CI requirements remain applicable.
