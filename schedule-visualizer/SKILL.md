---
name: schedule-visualizer
description: Generate a polished, single-file HTML project schedule — either a daily Excel-like calendar grid or a Gantt timeline (or both) — from a set of work items, dates, and milestones, saved under my-cubrid-docs with source-commit and AI-agent suffixes. Use this whenever the user wants to visualize, lay out, or "예쁘게 뽑아줘" a project plan, merge/release schedule, roadmap, sprint, or 일정표 as HTML; whenever they ask for a Gantt chart, timeline, calendar view, or day-by-day plan; or whenever a planning/estimation discussion produces issues + durations + a target date that would be clearer as a visual. Trigger even if the user doesn't say "HTML" — if they're organizing a schedule to send to a manager or team, offer this. Especially fits CUBRID merge/milestone planning (e.g., feat branch → develop) with JIRA issue numbers, holidays, and review-gated timelines.
argument-hint: "[gantt|calendar|both] [optional: project/branch or path to a plan doc]"
---

# Schedule Visualizer

Turn a project plan into a polished, self-contained HTML artifact a manager can
open offline, forward by email, or print. Two formats, one design system:

- **Daily calendar** — Excel-like Mon–Fri grid, one chip per task per day. Best
  for concrete day-by-day plans, holidays, "엑셀처럼 칸 나눠서".
- **Gantt timeline** — week-column bars across overlapping workstreams, with the
  critical path called out. Best for a one-glance overview.

The look is deliberately *not* generic-AI: a tuned palette, semantic color
buckets, an issue dictionary, holiday/milestone/buffer cells. The proven CSS and
structure live in the templates — your job is to gather the data and fill them
faithfully, not to redesign from scratch.

## When to use

- "일정표 HTML로 뽑아줘", "간트 차트 만들어줘", "스케줄 시각화", "달력처럼 보여줘",
  "이 계획 예쁘게 정리해서 팀장한테 보낼 수 있게"
- A planning/estimation thread just settled on issues + durations + a target date.
- CUBRID milestone/merge planning with CBRD-XXXXX issues, holidays, CI gates.

If it's a one-line "when's the deadline" question, just answer — don't build an
artifact. Reach for this when there's enough structure (several items, dates,
a milestone) that a picture genuinely beats prose.

## Artifact identity and location

Save every generated schedule under `/home/vimkim/gh/my-cubrid-docs`, never in the source worktree or current working directory:

- For a schedule centered on one CBRD ticket, use the lowercase ticket directory `/home/vimkim/gh/my-cubrid-docs/cbrd-xxxxx/`.
- For a multi-ticket or ticket-free project schedule, use `/home/vimkim/gh/my-cubrid-docs/<project-slug>/`. Derive a stable lowercase kebab-case slug from the named project; if no durable project identity is clear, ask the user before writing.
- If the docs root does not exist, stop and ask for its location. Do not fall back to `pwd`.

Resolve both filename suffixes before copying a template:

1. Set `SOURCE_COMMIT` to the commit identified by the plan, PR, or CI context. Otherwise use `git rev-parse HEAD` in the current CUBRID worktree. Never use the docs repository commit. If no relevant CUBRID commit or worktree can be identified, ask the user.
2. Validate `SOURCE_COMMIT` and take its first seven hexadecimal characters as `SHORT_SHA`.
3. Set `AGENT` from the active AI host's runtime identity. Use `codex` for Codex and `claude` for Claude Code. For another host, use its stable lowercase agent name. Do not infer the host from installed binaries because multiple AI CLIs may coexist; if runtime identity is unclear, ask the user.
4. End every basename with `_<SHORT_SHA>_<AGENT>.html`. For example: `oos-m2-merge-calendar_f5794fb_codex.html` or `oos-m2-merge-calendar_f5794fb_claude.html`.

Compute each output path once and reuse it for template filling, verification, regeneration, and handoff. When producing both formats, create separate `...-calendar_<SHORT_SHA>_<AGENT>.html` and `...-gantt_<SHORT_SHA>_<AGENT>.html` files.

## Workflow

### 1. Read the design system first
Read `references/design-system.md`. It defines the data model, the buckets and
palette, chip/bar anatomy, special cells, and the verification step. Don't skip
it — the templates assume you know the bucket semantics.

### 2. Gather the inputs
Collect the project frame (start date + weekday, working week, holidays, target/
milestone, buffer) and the work items (exact id, summary, bucket, status, day(s),
excluded?). Pull as much as you can from the current conversation and the repo
(git log, JIRA via the `cubrid-jira` skill, PRs via `gh`) before asking the user.

The schedule logic — **what's the critical path, velocity, what gates "done"** —
swings the dates more than anything. If it's not already established in the
conversation, ask. A common and important finding: when most work is already in
draft PRs, the critical path is *human review throughput*, not coding — model the
timeline around that, not around keyboard time.

Never invent or approximate an issue id. If you're unsure of an exact JIRA
summary or status, look it up.

### 3. Pick the format
- User asked for one → do that one.
- "both" → produce two files.
- Unsure → produce the **calendar** (it carries more concrete information), and
  offer the Gantt as a follow-up.

### 4. Fill the template
Resolve the final docs-tree output path using **Artifact identity and location**,
then copy the chosen template from `assets/` directly to that path (for example,
`oos-m2-merge-calendar_f5794fb_codex.html`). Then:
- Replace header/cards/meta with project facts.
- Build the week rows / workstream bars from the work items.
- Mark holidays, the milestone day, and buffer days with their cell classes.
- Fill the issue dictionary; put out-of-scope items in greyed `excl` rows.
- Trim the legend to only the buckets you used.
- Add a footer line recording the assumptions baked in ("공휴일 6/3 반영 ·
  매뉴얼 2h · 26383 제외") so the file is self-documenting out of context.

Reuse the CSS variables/classes — never hand-write new inline hex colors (that's
the corrupted-hex bug waiting to happen). If a project needs a new category, add
a `--var` + `.c-x`/`.a-x` (calendar) or `.b-x` (Gantt) pair, not a one-off color.

### 5. Verify before delivering — required
Run the bundled check:

```bash
bash <skill-dir>/scripts/verify_html.sh <output.html>
```

It catches corrupted hex colors (e.g. `#5b6personally`), unbalanced
`div`/`td`/`tr` tags, and accidental external resource references. Fix anything it
flags. These failures are invisible on a casual glance but break the render —
don't rely on eyeballing.

### 6. Deliver
Hand over the docs-tree file path, source commit, and agent name. If running in a UI that surfaces files, surface it.
Give a 2–3 line summary of what's in it, then offer the obvious next moves:
- the other format (Gantt ↔ calendar) for consistency,
- adjusting assumptions (velocity, holidays, scope) and regenerating,
- a manager-ready one-paragraph summary to paste into a reply.

## Keeping it in sync
When the user changes an assumption — removes an issue, compresses a phase,
shifts a date — **regenerate the affected file fully**. A schedule the reader has
to mentally patch is worse than none. If you produced both formats, update both
so they don't contradict each other.

## Notes
- These are static artifacts, not apps. No build step, no dependencies.
- The templates are Korean-first (font stack + example copy) but work in any
  language — swap the text, keep the structure.
- If the `frontend-design` skill is available and the user wants a bolder or
  rebranded look, you can layer it on top — but preserve the single-file,
  offline-safe, print-friendly constraints above.
