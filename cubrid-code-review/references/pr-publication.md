# Publish a PR review

Use this workflow for an explicit PR-review request after saving and adjudicating the pinned review. The authorization and local-only exception are defined in `SKILL.md`. Publish partial or budget-limited results with their actual verdict and remaining work.

## Publish the documents first

1. Inspect `/home/vimkim/gh/my-cubrid-docs`: branch, worktrees, status, remotes, and applicable `AGENTS.md` and documentation procedures. Use a separate documentation worktree based on `main`; preserve unrelated changes. Search existing ticket and topic directories before choosing the report path.
2. Promote the durable report into that worktree. Include coverage, handoff, and supporting evidence only as needed to read or substantiate the report. Keep raw logs and scratch material in the review run directory. Follow the documentation repository's placement, README index, link, and commit checks. Preserve separately cited historical snapshots. Published explanations must contain the essential evidence; local-only paths do not provide evidence to PR readers.
3. Prepare the Korean comment from the saved report using the format below. Retain its body and publication progress in the run directory. Record the PR identity, full reviewed SHAs, documentation paths, and later the pushed documentation commit and comment URL so an interrupted run can resume.
4. Review the documentation diff, run the repository's required checks, and commit only the intended review documents. Before integration, verify the destination checkout is clean and on `main`. Fetch its configured remote and reconcile `main` with the remote tip using fast-forward updates. Audit the outgoing history and diff so the push contains only authorized work.
5. Rebase the documentation task branch onto the current destination `main`. Recheck the resulting diff and proportionate documentation checks. From the destination checkout, integrate with `git merge --ff-only <rebased-task-commit>`, then push the configured remote's `main`. A remote advance requires fetching, reconciling, and repeating the rebase and fast-forward under the same authorization. Use ordinary pushes; preserve work and report the blocker when conflicts or unrelated outgoing changes prevent a safe publication.
6. Verify the remote `main` contains the documentation commit and the report file at its published path. Build the report URL from the verified GitHub repository and URL-encoded path: `https://github.com/<owner>/my-cubrid-docs/blob/main/<report-path>`. Check that the intended PR readers can access it. If publication or link access fails, retain the prepared comment and report the pending step before posting it.

The PR comment follows a verified documentation push. Its report link must use `blob/main/`; a task-branch URL, local path, or personal viewing URL does not satisfy this workflow. The report itself keeps full source revision SHAs and commit-specific source links.

## Post the Korean summary

Write a concise PR-page comment in Korean. Keep code symbols, paths, finding IDs, and command names as written in the source. The report's language follows the report contract; a Korean summary alone does not change it.

Use the report's verdict with these Korean labels:

| Report verdict | Korean label |
|---|---|
| `changes-required` | 수정 필요 |
| `no-confirmed-findings` | 확인된 결함 없음 |
| `incomplete` | 검토 미완료 |

Use this format, replacing all placeholders and omitting inapplicable finding rows:

```markdown
### 코드 리뷰 요약

- **판정:** {한글 판정}. 확인된 결함 {N}건 ({심각도별 건수}).
- **검토 대상:** base `{base-short}` / head `{head-short}` (공통 조상 `{merge-base-short}`).

**주요 발견**

1. **[{P등급}] {발견 ID}: {문제}** — {발생 조건과 영향}. {필요한 조치}. [근거]({보고서의 해당 항목 또는 검토 커밋의 소스 링크})

- **검증:** {실제로 수행한 주요 검사와 결과}.
- **한계·미확인 위험:** {미검증 범위와 확인되지 않은 우려, 또는 없음}.
- **후속 검토:** {필요/불필요 및 이유. 필요하면 다음 확인 항목}.
- **전체 보고서:** [리뷰 보고서]({검증된 my-cubrid-docs/blob/main/ 경로})

<!-- cubrid-code-review: {owner}/{repo}#{pr-number} base={full-base-sha} head={full-head-sha} -->
```

List at most three confirmed findings in impact order. Count all confirmed findings by severity and point to the report for the remainder. Each finding states a concrete trigger, consequence, and needed action. Keep unverified concerns in the separate risk line. Coverage gaps and required follow-up remain visible even when the verdict is `changes-required`.

When there are zero confirmed findings, omit the severity breakdown and replace the findings block with: `검토한 범위에서 확인된 결함은 없습니다. 이 결과가 PR의 병합 안전성을 보장하지는 않습니다.` Keep the actual verdict, limitations, and follow-up; zero findings can still mean `검토 미완료` or `예산 설정 필요`.

Recheck the PR's base and head before posting. If it moved, preserve the reviewed snapshot, record the required delta review in the report and handoff, and publish those updates before the comment. State prominently in the summary: `검토 이후 PR이 변경되어 현재 커밋에 대한 추가 검토가 필요합니다.` Do not restart the review automatically.

Use an available GitHub connector to create or update the PR-page comment. If it lacks that capability, use `gh pr comment --repo <owner/repo> <number> --body-file <saved-comment-file>`. Read back the posted body and verify the report link and snapshot marker. On a retry or uncertain write result, inspect existing comments first. Update only a comment authored by the authenticated account with the same PR, full base, and full head marker. A different snapshot receives a new comment so earlier review results remain attributable.

After the merge, perform the documentation repository's required cleanup from outside the merged task worktree. Remove only this review's worktree and branch without force, preserving valuable local material. Report any cleanup obstacle separately from successful publication. Completion requires the verified report URL, comment URL, and explicit status of any unfinished step.
