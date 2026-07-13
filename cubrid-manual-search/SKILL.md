---
name: cubrid-manual-search
description: "Search the local CUBRID reStructuredText manual and answer natural-language questions with file-and-line evidence. Use when the user explicitly asks to consult the CUBRID manual, or when SQL syntax, configuration, utilities, APIs, PL/CSQL, HA, security, or release-specific behavior requires authoritative manual evidence. Do not use this skill as proof of undocumented source-code behavior. Triggers on phrases like 'search the CUBRID manual', 'what does the manual say about JSON_TABLE', 'find max_clients in the CUBRID docs', 'CUBRID backupdb syntax', or '매뉴얼에서 백업 문법 찾아줘'."
---

# CUBRID Manual Search

Answer from the checked-out English and Korean RST manual. Treat it as documentation evidence, not proof of behavior the manual does not describe.

## 1. Resolve the checkout

Use the first candidate containing both `en/` and `ko/`: `$CUBRID_MANUAL_ROOT`, the current Git root, then `$HOME/gh/cubrid-manual`.

```bash
git_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
manual_root=
for candidate in "${CUBRID_MANUAL_ROOT:-}" "$git_root" "$HOME/gh/cubrid-manual"; do
  if [ -n "$candidate" ] && [ -d "$candidate/en" ] && [ -d "$candidate/ko" ]; then
    manual_root="$(cd -- "$candidate" && pwd -P)"
    break
  fi
done
test -n "$manual_root"
```

If the final command fails, ask for the checkout path. Never substitute web search silently.

## 2. Build safe search terms

Search `ko` first for a Korean question and `en` first otherwise. Assign those literal values to `primary_lang` and `secondary_lang`. Build `search_terms` as a Bash array chosen from the question:

- Preserve exact identifiers and commands, such as `max_clients`, `JSON_TABLE`, `cubrid backupdb`, and `CCI_ER_DBMS`.
- Add literal spelling, spacing, and established terminology variants as separate elements.
- Add a broader concept only when exact terms are too narrow.

Never evaluate or interpolate raw user text as shell syntax. Use only agent-chosen array elements and quote every expansion.

## 3. Find candidate sections

Search both pages and included fragments, using literal case-insensitive matching. Keep these variables and the checkout-resolution command in the same shell invocation, or redeclare them in each later invocation.

```bash
search_lang() {
  local lang="$1"
  for term in "${search_terms[@]}"; do
    rg --color never -n -i -F -C 3 -g '*.rst' -g '*.inc' -- "$term" "$manual_root/$lang" || true
  done
}
search_lang "$primary_lang"
```

If the primary results are missing, ambiguous, or incomplete, run:

```bash
search_lang "$secondary_lang"
```

Rank candidates by:

1. Exact identifier in a definition or section heading.
2. A focused topic page under `sql/`, `admin/`, `api/`, `pl/`, or a relevant top-level page.
3. Explanatory body text.
4. `release_note/`, unless the question is explicitly version-specific.

Use filenames and nearby RST headings to disambiguate common words. Never answer from match lines alone.

## 4. Read complete RST evidence

Set `matched_file`, `start_line`, and `end_line` from a candidate, then read numbered context:

```bash
nl -ba "$matched_file" | sed -n "${start_line},${end_line}p"
```

Expand through the complete section as needed to capture syntax, defaults, conditions, examples, warnings, notes, limitations, and version markers.

For an include, read the directive and resolve its path relative to the including file:

```bash
rg --color never -n '^\.\. include::' "$matched_file"
include_file="$(cd -- "$(dirname -- "$matched_file")" && realpath -- "$include_path")"
test -f "$include_file"
nl -ba "$include_file"
```

For a relevant `:ref:` target, extract its label as `ref_name`, set `matched_lang` from the candidate path, locate the definition in that language tree, and read that section:

```bash
rg --color never -n -F -g '*.rst' -g '*.inc' -- ".. _$ref_name:" "$manual_root/$matched_lang"
```

Check the other language when it clarifies meaning. Report material English/Korean differences instead of silently choosing one.

For version-sensitive answers, inspect the checkout identity:

```bash
git -C "$manual_root" branch --show-current
git -C "$manual_root" describe --tags --always --dirty
git -C "$manual_root" rev-parse --short HEAD
```

A branch or tag identifies the documentation checkout; it does not prove server behavior. Give precedence to explicit in-page version statements and qualify release-note-only claims with their documented version.

## 5. Answer with evidence

Lead with the documented answer. Include syntax or a short example only when useful.

- Cite every material claim at its most specific source line. Build a Markdown local-file link whose label is the path relative to `manual_root` and whose target is the absolute `matched_file` followed by the evidence line number; enclose a target containing spaces in angle brackets. Cite an `.inc` directly when it contains the evidence.
- Prefer substantive sections over indexes and search-result lines.
- Label synthesis or inference explicitly. Keep quotations short and otherwise paraphrase.
- State the checkout branch or tag for a version-sensitive answer.

If the manual does not answer the question, say so plainly. List the languages, literal terms, and likely topic areas checked; offer only the closest documented information. Do not fill the gap from memory or silently browse the web.
