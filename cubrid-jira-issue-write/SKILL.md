---
name: cubrid-jira-issue-write
description: Write a CUBRID JIRA issue report in Korean with English section headers (##). Top of issue is an Issue Triage block — 목적 (필수) + 이유 (필수, 현재 동작·한계와 그 영향 두 축을 모두 포함) + 방안 (합의된 스펙은 구체적으로, 미결정은 TBD) — written in whatever format reads best (short prose, mini-tables, ASCII call-flow diagrams, callouts — NOT forced dot-lists), followed by an explicitly separated AI-Generated Context block. Favors diagrams and comparison tables for call flows and option trade-offs. Writes structured markdown to /home/vimkim/gh/my-cubrid-jira/issues/. Use when the user wants to write up a JIRA issue, document a bug finding, or create a feature/task report for CUBRID.
---

# CUBRID JIRA Issue Writer

Write a structured JIRA issue saved as markdown to `/home/vimkim/gh/my-cubrid-jira/issues/`.

Two goals govern every issue:

1. **A reviewer can triage it in 10 seconds** from the top block alone.
2. **A new hire who reads C/C++ but has never opened this subsystem can follow the whole thing on one read** — through the writing itself, never by announcing that it was written to be readable.

These two goals fight verbosity from both ends: the triage block stays tiny, the body stays plain, and **no fact is told twice**. The single most common failure of this skill is the same "why" appearing in the triage, then the Summary, then the Description. The **Layer Ownership** rule below is the cure — read it before drafting.

## When to Use

- User says "write a jira issue", "jira로 작성", "이슈 작성", "리포트 작성"
- User has analysis/findings to document, or wants to formalize a bug report, feature request, or task

## Hard Constraints (non-negotiable)

- **Save location**: `/home/vimkim/gh/my-cubrid-jira/issues/CBRD-XXXXX-short-slug.md`. If the directory does not exist, **stop and tell the user** to clone/create the repo. Do NOT create it yourself. No ticket number yet -> ask, or use a descriptive slug.
- **No emoji and no non-BMP (4-byte UTF-8) characters.** The CUBRID JIRA API rejects 4-byte characters, and emoji (🚀 ✅ ❌ 😀 …) read as AI-slop regardless of plane. Everything in the BMP is allowed — Korean/CJK, and ordinary typographic symbols when they aid readability: `★` (flow-diagram limit marker), box-drawing (`└ ├ │`), `→`, `✓`. ASCII forms (`->`, `[x]`/`[ ]`, `-`/`*`) are equally fine — use whichever reads cleaner, not because the API forces it.
- **Headers (`##`) in English. Subheaders (`###`) and all body text in Korean** (평어/한다체, never 합니다/입니다). Code, function names, file paths, identifiers stay as-is.
- **Never state the issue's own audience or readability target in the body.** No "신입도 읽을 수 있게 작성", no "독자 대상: ...", no reading-grade note, no "고등학생도 이해할 수 있도록". Readability is writer-side guidance; the reader benefits from it silently. Any sentence describing the doc's own clarity instead of the bug/feature gets deleted.

## Issue Types

Reference: https://dev.cubrid.org/dev-process/jira/open — determine the type **first**; section structure depends on it.

| Type | When | Korean |
|------|------|--------|
| **Correct Error** | bug / error fix | 버그·에러 수정 |
| **Improve Function/Performance** | enhance existing feature, perf | 기능·성능 개선 |
| **Development Subject** | new feature | 신규 기능 개발 |
| **Internal Management** | version bumps, infra, internal-only | 내부 관리 |

`Refactoring` uses the Improve template; `Task` is a discouraged fallback; `Sub-task` is a child issue. If the type is unclear, ask before drafting.

## Output Structure

Every issue is two stacked layers separated by an explicit divider:

```markdown
# [TAG] 한국어 제목

## Issue Triage

**이슈 수행 목적** (필수): <결과 상태 1-2 문장. 분석/메커니즘 금지.>

**이슈 수행 이유** (필수): <현재 동작·한계 + 영향, 두 축을 모두. 형식 자유.>

**이슈 수행 방안**: <합의된 결정은 구체적으로, 미결정은 TBD.>

---

## AI-Generated Context

> 아래는 AI 가 코드/맥락을 분석해 작성한 상세 자료다. 빠른 triage 에는 위 Issue Triage 블록만으로 충분하며, 본문은 구현/리뷰 단계에서 참고하면 된다.

### Summary

- **변경 범위 / 영향**: 영향받는 모듈·파일·사용자·호환성. (문제/원인/제안을 여기서 다시 적지 않는다 — Layer Ownership 참고.)

---

<type-specific sections below>
```

Fill `<...>` slots. The three triage concerns — **목적 / 이유 / 방안** — are required; their *formatting is free* (short prose, mini-table, ASCII flow diagram, callout — whatever reads in one pass). Do not force every field into a `-` dot-list.

### Layer Ownership (the de-duplication rule — read before drafting)

Each layer owns **different content for a different reader**. Verbosity comes from layers repeating the same "why". Stop it at the source:

| Layer | Owns (the only thing it carries) | Must NOT contain |
|-------|----------------------------------|------------------|
| **Issue Triage** (목적/이유/방안) | the *decision* — result state, justification, agreed plan. Human register, 10-sec read. | mechanism, code, `file:line`, repro, step-by-step. |
| **AI Context — Summary** | *orthogonal* facts the triage skips — affected modules/files, compatibility, blast radius. | restated 문제/원인/제안 (that is the triage's job). |
| **Description** | the full root-cause *narrative* with glosses — the "why", told in depth once. | sentences copied verbatim from the triage. |
| **Implementation** | code flow, data structures, diffs, algorithm. | re-explaining the "why" already in Description. |
| **Repro / Expected / Actual** | executable commands/SQL and observed output. | prose narrative. |

The litmus test: **Triage = conclusions, Description = mechanism, Summary = scope.** If a sentence fits two of those, it belongs in exactly one — pick the strongest and cut the others.

**Post-draft check (mandatory):** re-read and find any sentence/fact appearing in 2+ layers. Keep the strongest location, delete the rest. The old `### Summary` 4-bullet `문제/원인/제안/영향` pattern is banned precisely because 문제/원인/제안 duplicate the triage — Summary now carries scope/impact only.

### Type-specific sections (go below the `## AI-Generated Context` divider)

**Correct Error:**

```markdown
## Description
(버그 개요 + 근본 원인 narrative)

## Test Build
(예: `CUBRID-11.0.0.0248-b53ae4a`, OS 포함)

## Repro
(복붙으로 재현 가능한 명령/SQL. 서술 금지.)

## Expected Result
## Actual Result
## Additional Information
(스택 트레이스, 로그, 관련 이슈 링크)
```

**Improve / Development Subject / Refactoring:**

```markdown
## Description
(배경, 목적, 문제 정의)

## Specification Changes
(변경 스펙. QA/매뉴얼 갱신용. 변경 없으면 N/A)

## Implementation
(설계·구현. 코드 흐름, 자료구조, 알고리즘)

## Acceptance Criteria
- [ ] 수락 조건 1

## Definition of done
- [ ] 위 A/C 충족
- [ ] QA 통과
- [ ] 문서/매뉴얼 반영
```

**Internal Management / Task:** just `## Description`.

**Section rules:** Patch/Revision versions go in the description explicitly (JIRA UI shows only Major.Minor). Don't delete unused official sections — fill `N/A`. Use `TBD` for unknowns. Optional tail add-ons: `## 참고 코드` (key source refs), `## Remarks` (follow-ups, PR links, related tickets).

## Triage Rules (목적 / 이유 / 방안)

- **목적 (필수)**: result state, 1-2 sentences. Analysis/background belongs in 이유, not here.
- **이유 (필수)**: cover both axes —
  - **현재 동작 / 배경**: cite thresholds/params/conditions by their code name (`DB_PAGESIZE/8`, `LZ4_MAX_INPUT_SIZE`, `pgbuf_fix`), ideally with file:line. No "약 512 바이트" hand-waving; expanding a macro in parens is encouraged (`LZ4_MAX_INPUT_SIZE`(0x7E000000, 약 2.11GB)).
  - **영향**: pick the one applicable category (고객 장애 · QA 실패 · 성능 저하 · 설계 의도 훼손 · 기술 부채) with a concrete example. Listing all five is menu-padding. Abstract one-liners ("일관성 유지", "성능 개선 필요") are rejected.
  - **Correct Error 특례**: 현재 동작 = one-line repro summary, 영향 = the failure mode the user sees. Still write them as two separate items.
- **방안**: state already-decided spec concretely; leave only the undecided as TBD.
  - "합의된" = quotable concrete decision from this session's user messages · a quotable JIRA comment · an explicit design doc. Nothing else (analogy to a sibling ticket, plausible AI inference) counts. When citing a user message, quote the original fragment ("사용자 인용: \"...\"").
  - TBD markers: `TBD - ANALYSIS 단계에서 결정` when deferral is itself agreed; `TBD - 합의 미확인` when even the existence of a decision is unclear (default to this when unsure so the reviewer catches it). In an interactive session, just ask the user.
  - Detailed code flow / data structures go to `## Implementation`, not here. 방안 says only *what was decided*.

**Triage structure-label exception:** only these five bold labels are exempt from the "no English-direct labels" rule (they are slot identifiers, not prose): `**이슈 수행 목적**`, `**이슈 수행 이유**`, `**이슈 수행 방안**`, `**현재 동작 / 배경**`, `**영향**`. Any other label (`**Fact**:`, `**Risk**:`, `**무엇을**:`) follows the natural-Korean rules everywhere.

**Triage anti-patterns:** merging 목적 into 이유 in one sentence; an abstract 이유 with no number/threshold/condition; a pure-TBD 방안 when decisions exist (under-writing) OR an AI-invented plan in 방안 (over-guessing); reflexively dot-listing all three fields (see 닷 리스트 강박 below); pulling AI analysis up into the triage block (it lives under `## AI-Generated Context`).

**Worked example (OOS migration policy — Improve):**

```markdown
## Issue Triage

**이슈 수행 목적**: heap 레코드의 큰 가변 컬럼이 OOS 의도대로 일관되게 외부로 이관되도록 한다.

**이슈 수행 이유**:

- **현재 동작 / 배경**: 현재 코드는 레코드 총 길이가 `DB_PAGESIZE/8` 을 넘는 경우에만 512 바이트 초과 가변 컬럼을 OOS 로 보내므로, 511 바이트 가변 컬럼만 있는 레코드는 임계치에 못 미친 채 overflow 경로로 빠진다 (개발 편의용 임시 임계치).
- **영향**: 설계 의도 훼손 — 511 바이트 가변 컬럼 페이로드가 OOS 대상에서 누락된 채 heap 내부 overflow 로 빠져 OOS 도입 효과가 무력화된다.

**이슈 수행 방안**:

- 레코드 총 길이가 `DB_PAGESIZE/4` 를 넘으면 가장 큰 가변 컬럼부터 순차 OOS 이관하며, `DB_PAGESIZE/4` 이하가 될 때까지 반복한다.
- OOS 이관 시 lz4 압축 적용, P 사 기본값 EXTENDED 모드 차용.
- P 사의 다른 정책(MAIN, EXTERNAL, PLAIN)은 범위 밖이며 CBRD-26536 으로 분리한다.
- lz4 압축 레벨 세부값: `TBD - 합의 미확인`.
```

핵심: 이유가 임계치를 매크로 이름으로 인용하고 영향을 한 카테고리 + 구체 시나리오로 좁혔으며, 방안이 합의된 결정만 적되 범위 밖은 별도 티켓으로 분리하고 미확인은 보수적 마커로 표기했다. 이 방안은 평면 목록이라 bullet 이 맞다 — 후보 비교였다면 아래 toolkit 의 ranked 표를 썼을 것이다.

## Readability Toolkit — 닷 리스트 대신 (모델: CBRD-26890, CBRD-26788)

불릿은 평면 목록 한 종류에만 맞는다. 내용에 구조가 있으면 아래 도구를 골라 쓴다. 막히면 CBRD-26890 / CBRD-26788 을 펼쳐 형식을 베낀다.

**1. ASCII 호출 흐름도** — 압축/해제, scan, 복구 같은 호출 체인. `★` 로 한계 지점·분기점을 표시 (CBRD-26890 §압축 코드 흐름).

````markdown
```
[압축] 직렬화(DB_VALUE -> 디스크)
 mr_data_writeval_string()                  object_primitive.c
   └ pr_do_db_value_string_compression()
        └ cubcompress::compress<LZ4>()       compressor.hpp
 ★ 크기 게이트: charlen > LZ4_MAX_INPUT_SIZE -> 압축 스킵, 원본 저장
```
````

**2. Ranked 후보 비교 표** — 방안이 "여러 선택지 중 고르기" 일 때. 권장 순서대로 행을 놓고 마지막 칸에 권장 이유/고려사항 (CBRD-26890 §상세 내용).

```markdown
| 순위 | 후보 | 권장 이유 / 고려사항 |
|------|------|---------------------|
| 1 | zstd 도입 | 4GB+ 단일 호출 처리, DB 채택 검증. 외부 의존성 추가 비용. |
| 2 | LZ4 frame 청킹 | 라이브러리 교체 없음. 스트리밍 해제 설계 필요. |
| 3 | 비압축 fallback | 가장 단순. 압축 이득 포기 — 단기 baseline. |
```

**3. 현황 조사 표** — 타입/경로/조건별 상태를 한눈에 (CBRD-26890 §현황 조사).

```markdown
| 가변 타입 | 최대 길이 | 압축 적용 |
|-----------|-----------|-----------|
| VARCHAR | 약 1 GiB (0x3fffffff) | O (LZ4) |
| internal LOB (신규) | 4 GB | 대상이나 LZ4 로는 불가 |
```

**4. 요지 callout** — 표/도식 뒤에 한 문단으로 핵심을 박는다. JIRA `{panel:title=요지}` 의 markdown 대응은 blockquote.

```markdown
> **요지**: 컬럼 값 압축 대상은 ~1 GiB 라 LZ4 한계 안이었다. 4GB LOB 만 한계를 넘어 새 방안을 요구한다.
```

조사/설계 이슈(CBRD-26788 류)는 `## 주요 검토 항목` 을 번호 매긴 `###` 소제목으로 펼치고, 결정 못 한 부분은 `## Open Questions` 로 모은다 — 억지로 방안 bullet 에 욱여넣지 않는다.

## New-hire Readability (silent — never stated)

Readers include the CTO and senior peers, but also QA, CS, and an engineer who joined last month and has never opened this module. Write so that last reader follows on one pass — *without ever telling them you did so* (see Hard Constraints).

- **Gloss internal terms on first use, once, in one clause** — acronyms and module-specific identifiers (`OOS`, `recdes`, `pgbuf_*`, `OR_VAR_*`, `WAL`, `MVCC`, `latch`, `sysop`, heap/btree policy names, build-mode names). Then use the term raw.
  - "`OOS` (Out-of-row Storage — heap 의 큰 가변 컬럼을 외부 페이지로 분리하는 저장 방식)"
  - "`pgbuf_fix` (페이지 버퍼 풀에서 페이지를 잠가 가져오는 함수)"
  - Skip the gloss for universal C/DB terms (`malloc`, `mutex`, `assert`).
- **Every threshold/magic number gets a one-clause rationale.** "`DB_PAGESIZE/8` 미만이면 OOS 이관이 일어나지 않아 큰 가변 컬럼이 heap 내부로 흘러든다" beats a bare "`DB_PAGESIZE/8`".
- **Short sentences, one idea each. Lead with what changed, then where, then why.** "heap 의 OOS 이관 임계치를 `DB_PAGESIZE/8` 에서 `DB_PAGESIZE/4` 로 올린다 (`heap_file.c:12300` 부근) — 511 바이트 가변 컬럼이 OOS 대상에서 빠지는 문제 때문" reads in one pass.
- **Concrete over abstract.** "에러 코드 6곳을 모두 갱신해야 한다" beats "전반적인 일관성을 유지해야 한다." Name the file, the function, the number.
- **No tutorial mode.** A 1-line gloss is fine; a paragraph explaining what a heap is, is not. No meta-labels in headers (`### 왜 (한 번만 설명)`). No obvious-statement filler — if the diff or Repro makes it obvious, drop it.
- **Reproducible Repro.** Copy-pasteable commands/SQL, not narrative.

## Natural Korean (avoid translationese / AI cadence)

The biggest tell of LLM prose is rhythm. After drafting, hunt and rewrite:

- **Translationese**: "에러가 ... 흘러간다" -> "결과셋에 섞여 나간다"; "측면도/측면에서는" -> restructure; "수용한다"(limitation) -> "그대로 둔다"; "위함이다" -> "위해서다".
- **Lockstep cadence**: several short "...한다." sentences in a row. Vary with `-므로`, `-기 때문에`, `-라`, `-도록`, longer subordinate clauses.
- **English-direct labels**: `**무엇을**: / **어떻게**: / **왜**:` and header `### 왜` -> Korean (`**변경**:`, `**부수 수정**:`, `### 배경`). (Triage's five slot labels are the only exception — see above.)
- **`Fact: / Effect: / Ops 결론:` bullet labels** (RFC/ITIL parody) -> peer-to-peer prose.
- **명사구 종결** ("...없음.", "...불필요.") OK in table cells, NOT in body prose.
- **존댓말 leak**: fix any `합니다`/`입니다` to 평어.
- **닷 리스트 강박**: 목적/이유/방안을 무조건 `-` 불릿으로 쪼개지 말 것. 불릿이 4개를 넘거나, 한 불릿이 두 줄을 넘거나, 항목 간에 비교·순위·흐름 관계가 있으면 표·흐름도·산문으로 가라는 신호다.

## Local-only Tooling (keep issues portable)

JIRA issues are read by devs, QA, and CS who do not share the author's local setup. Keep every command runnable on a fresh CUBRID dev VM.

- **Never write `just <recipe>` in an issue body, Repro, A/C, or table.** The `justfile` is local; a reader running `just shell-debug` gets `command not found`. Substitute the underlying command (e.g. `ctp.sh shell -c shell_ci.conf`, plus a 1-line note on pointing the conf's `scenario` at the test path).
- **Same for personal aliases/functions/dotfiles** (`my-rerun`, `cb`, custom helpers). If it isn't in the public CTP/CUBRID toolchain, it doesn't belong in the issue.
- **Acceptable wrappers** (universal to a CUBRID engineer): `ctp.sh`, `cubrid`, `csql`, `make`, `cmake`, `gh`, raw `bash`/`sh`. Prefer these.
- **If a personal recipe is the easiest repro for the author**, paraphrase the underlying command in the issue; keep the `just`/alias form in private notes only. Never put both.
- **Pre-upload scan**: `rg -nP '\bjust\s+\w' file.md` must return zero hits.

## Reference Examples

**Read these first for the free-form, diagram-rich style:**

- `CBRD-26890-lob-compression-algorithm.md` — canonical readability model. ASCII call-flow diagrams with `★` markers, type/limit survey table, `> **요지**` callout, ranked candidate-comparison table.
- `CBRD-26788-scan-prefetch-mechanism.md` — investigation/design model. Numbered `###` review items; undecided parts collected, not forced into a 방안 bullet list.
- `CBRD-26824-bug-bts-14917-regression.md` — strong new-hire glossing and clean separation of plain narrative from a `## 엔지니어용 기술 참고` deep-dive. (Note: this file states its readability target at the top — that opening note is exactly what the Hard Constraints now forbid; copy its *glossing and structure*, not that banner.)

**On-disk convention examples** (English `##`, Korean body): `CBRD-26637-refactor-error-handling.md`, `CBRD-26630-oos-inline-length.md` (before/after tables), `CBRD-26609-oos-physical-delete.md` (call-flow + WAL design), `CBRD-26769-heap-attrvalue-point-variable-int-return.md` (Case 1..N taxonomy).

## Execution Steps

1. **Check output directory** exists (else stop — see Hard Constraints).
2. **Determine issue type** (section structure depends on it; ask if unclear).
3. **Gather context**: read source, prior analysis, `/jira CBRD-XXXXX`, repro logs.
4. **Draft the Issue Triage block first** — forces a clear thesis and the 10-second triage path.
5. **Add the `## AI-Generated Context` divider** + caveat note; all AI-written detail goes below it.
6. **Write the body** from the type template, applying **Layer Ownership** so nothing repeats.
7. **Run the two mandatory checks**: (a) Layer-Ownership de-dup grep — no fact in 2+ layers; (b) `rg -nP '\bjust\s+\w'` returns zero.
8. **Save** to `CBRD-XXXXX-slug.md`.
9. **Show the user** the path, the chosen type, and the Issue Triage block so they can sanity-check the framing.

## Arguments

- `/write-jira-issue CBRD-26583 OOS compact analysis` — write issue for a specific ticket
- `/write-jira-issue` — interactive mode, ask for details

## Mandatory: Iterate with Grill-with-Docs

Every draft goes through `/grill-with-docs` before being filed — no single-pass issues. Single-pass drafts drift toward filler, non-executable Repro, unsupported root-cause claims, and triage blocks collapsed into one sentence. This applies to every issue regardless of size or perceived triviality. The **only** valid skip is the user explicitly saying so in the triggering message ("skip grill", "no grill", "just push it"). If in doubt, grill.

Hand off with: ticket number + issue type + output path (same file, revised in place) + source material. Review angle:

- Technical accuracy; Repro is executable; CUBRID conventions (Korean body, English `##`, no emoji/non-BMP).
- **Issue Triage** present, all three fields filled, not collapsed into one sentence. 이유 cites code-named thresholds AND names impact (abstract one-liners = reject). 방안 states decided spec concretely; pure-TBD when decisions exist = reject; AI-invented plan = reject.
- **Layer Ownership**: no fact repeated across Triage / Summary / Description (the prime reject — this is the verbosity bug).
- **Format matches content**: triage fields not reflexively dot-listed; comparisons -> table, call chains -> ASCII diagram with `★`, single thesis -> prose.
- **New-hire readability**: every internal acronym glossed once on first use; every threshold has a one-clause rationale. Untreated insider shorthand = reject. The readability target itself must NEVER appear in the body (audience/grade-level note = reject).
- **Natural Korean**: pass the "New-hire Readability" and "Natural Korean" sections to the reviewer verbatim.

Round cap: default 5.
