---
name: cubrid-qa-fetch
description: Fetch and analyze authenticated pages from CUBRID's internal QA portal at qahome.cubrid.org. Use when the user gives a qahome.cubrid.org/qaresult URL, asks to read or parse shell/SQL/medium/functional QA result pages, asks for NOK lists or core stacks from qahome, or describes a portal navigation path such as cubrid / Recent builds(72h) / 11.5.0.2268-2c66b9a. The portal requires login; unauthenticated WebFetch or curl usually returns only the login form. Also use when resolving build tree ids, showstat pages, showFuntionRes summaries, showFailResult details, viewShellTestResult pages, or qahome frame/tree navigation.
---

# Fetch qahome QA Pages

Use the local qahome fetcher tool first:

```text
/home/vimkim/temp/cubrid-qahome-fetcher
```

The tool handles authenticated login, qahome host allowlisting, build-tree traversal, raw page saving, detail-page fetching, and report generation. Do not reimplement the login flow with ad hoc `curl` unless this tool is missing or broken and the user still wants a best-effort manual fetch.

## Credentials

`qahome.cubrid.org/qaresult/*.nhn` is login-protected. The fetcher reads credentials only from environment variables:

| Variable | Meaning |
| --- | --- |
| `CUBRID_QA_USER` | qahome username |
| `CUBRID_QA_PASS` | qahome password |

Never ask the user to paste the password into chat. If either variable is missing, stop the live fetch and tell the user to export them, then restart or relaunch the session if the current process does not inherit them.

```sh
export CUBRID_QA_USER='vimkim'
export CUBRID_QA_PASS='...'
```

Check the environment without printing secret values:

```bash
cd /home/vimkim/temp/cubrid-qahome-fetcher
just check-env
```

## Guardrails

- Only send qahome credentials to exactly `qahome.cubrid.org`.
- Do not echo `CUBRID_QA_PASS`, write it to files, include it in command output, or put it in output filenames.
- Use the fetcher commands from `/home/vimkim/temp/cubrid-qahome-fetcher`; they reject non-qahome hosts and non-`/qaresult/` URLs.
- Treat unauthenticated WebFetch/curl output as suspicious. Login pages are usually around 3 KB and contain `name="loginform"`.
- Do not silently analyze a neighboring build. Match the requested build text or commit suffix, or report that the target build was not found.

## Direct URL Fetch

Use this for a concrete qahome URL such as `viewShellTestResult.nhn`, `showFailResult.nhn`, `showFuntionRes.nhn`, `showstat.nhn`, or `showfile.nhn`.

```bash
cd /home/vimkim/temp/cubrid-qahome-fetcher
uv run cubrid-qahome fetch-url --json '<qahome-url>'
```

Relative `/qaresult/...` paths and endpoint-relative paths are also accepted:

```bash
cd /home/vimkim/temp/cubrid-qahome-fetcher
uv run cubrid-qahome fetch-url --json 'viewShellTestResult.nhn?shellTestId=...&resultType=NOK'
```

The command writes a run directory under `runs/` with:

- `manifest.json`: fetched URL, saved raw page path, status code, size, content type
- `raw/<page>.html`: fetched HTML

After fetching, report the run directory, saved raw page path, file size/status from `manifest.json`, and what the page appears to contain. Then continue with the user's requested parsing or analysis.

## Build Lookup

Use this when the user gives a browser path or build identifier, for example:

```text
https://qahome.cubrid.org/qaresult/index.nhn
  cubrid
  Recent builds(72h)
  11.5.0.2268-2c66b9a
```

Find a build by text or commit suffix:

```bash
cd /home/vimkim/temp/cubrid-qahome-fetcher
uv run cubrid-qahome find-build --query '<commit-or-build-substring>' --json
```

The resolver checks `Recent builds(72h)` first, then scans branch groups under `cubrid`. Force a group when the user names one or when auto-detection is ambiguous:

```bash
cd /home/vimkim/temp/cubrid-qahome-fetcher
uv run cubrid-qahome find-build --query '<commit-or-build-substring>' --group 'RB-11.5.0-Manual' --json
```

The `just` wrappers are equivalent:

```bash
cd /home/vimkim/temp/cubrid-qahome-fetcher
just find '<commit-or-build-substring>'
just find '<commit-or-build-substring>' 'RB-11.5.0-Manual'
```

If the target build is not found, say so. Do not use bare `showstat.nhn`, `showMain.nhn`, or the first default page after login as a substitute; qahome can point those pages at stale builds.

## Fetch Build Results

Use this for normal QA result analysis. It resolves the build, fetches `showstat.nhn`, derives and fetches the misspelled functional summary endpoint `showFuntionRes.nhn?tree_id=...&buildId=...`, verifies the expected build text, fetches NOK detail pages by default, and writes deterministic reports.

```bash
cd /home/vimkim/temp/cubrid-qahome-fetcher
uv run cubrid-qahome fetch-build --query '<commit-or-build-substring>' --json
```

Force a branch/group when needed:

```bash
cd /home/vimkim/temp/cubrid-qahome-fetcher
uv run cubrid-qahome fetch-build --query '<commit-or-build-substring>' --group 'RB-11.5.0-Manual' --json
```

Use `--summary-only` when the user only needs `showstat`, `showFuntionRes`, and summary counts without detail pages:

```bash
cd /home/vimkim/temp/cubrid-qahome-fetcher
uv run cubrid-qahome fetch-build --query '<commit-or-build-substring>' --summary-only --json
```

Use `--all-result-types` only when the user asks for non-NOK shell detail pages too. The default is `--nok-only`.

The `just` wrappers are equivalent:

```bash
cd /home/vimkim/temp/cubrid-qahome-fetcher
just fetch '<commit-or-build-substring>'
just fetch-summary '<commit-or-build-substring>'
just fetch '<commit-or-build-substring>' 'RB-11.5.0-Manual'
```

Each run directory contains:

- `manifest.json`: command arguments, resolved build, fetched page provenance, warnings, build-text verification
- `summary.json` and `summary.md`: compact extracted facts
- `failure-report.md`: human-readable categorized diagnosis
- `failure-report.json`: structured version of the failure report
- `raw/`: saved showstat, showFuntionRes, and detail pages

Report the run directory and the key report path, usually `runs/<run-id>/failure-report.md`. Summarize the relevant findings for the user instead of dumping the whole report.

## Existing Run Parsing

Regenerate summaries and failure reports from an existing run directory:

```bash
cd /home/vimkim/temp/cubrid-qahome-fetcher
uv run cubrid-qahome summarize 'runs/<run-id>'
```

Convenience views:

```bash
cd /home/vimkim/temp/cubrid-qahome-fetcher
just report 'runs/<run-id>'
just latest-report
```

Use `summary.json`, `failure-report.json`, and raw pages for precise analysis. The markdown files are the quickest human-readable view.

## qahome Semantics To Preserve

- The useful functional summary endpoint is spelled `showFuntionRes`, not `showFunctionRes`.
- The function endpoint parameter is `tree_id`, not `treeId`.
- `showFunctionSummaryReport.nhn?treeId=...` can return an empty report for a valid build.
- Shell NOK details are usually under `viewShellTestResult.nhn?...resultType=NOK`.
- Common detail links include `showFailResult.nhn?m=showFailVerifyItem&statid=...`, `report/errorReport.nhn?m=showErrorInfo&srctb=resultstat&key=...`, `viewCCIForSQL.nhn`, `viewHAREPLTestResult.nhn`, and `viewCDCREPLTestResult.nhn`.

## Failure Modes

| Symptom | Meaning | Action |
| --- | --- | --- |
| `missing: CUBRID_QA_USER, CUBRID_QA_PASS` | Current process has no credentials. | Ask the user to set env vars and restart/relaunch if needed. |
| `login failed` or qahome returns a login form | Wrong credentials, expired session, or account issue. | Have the user verify in a browser; do not print the password. |
| `Only qahome.cubrid.org URLs are allowed` | The input URL is not on the qahome host. | Refuse to fetch it with this skill. |
| `Only /qaresult qahome URLs are allowed` | The input is outside the QA result portal. | Ask for a `/qaresult/` URL or path. |
| Expected build text is missing | Resolved/fetched page does not match the requested build. | Stop and report the mismatch; do not analyze it as the requested build. |
| Target build absent from auto-detection | The recent window moved or the build is under a specific branch node. | Retry with the relevant `--group` if known, otherwise report the miss. |
| `curl: (60) SSL certificate problem` or HTTP client CA errors | Local CA/proxy issue. | Use the correct CA bundle; do not default to insecure TLS bypass. |

## Manual Fallback

Only use manual `curl` login and page parsing if `/home/vimkim/temp/cubrid-qahome-fetcher` is unavailable or broken and the user agrees to a best-effort fallback. Preserve the same guardrails: environment-only credentials, qahome host allowlist, temporary cookie jar, login-form detection, explicit build matching, and no password output.

## Reporting

Always tell the user:

- Which URL, build query, or tree path was fetched
- The run directory under `/home/vimkim/temp/cubrid-qahome-fetcher/runs/`
- The key raw/report paths and page size/status when relevant
- Any build-id mismatch, missing target-build finding, parser warning, or credential/environment problem

Then continue with the requested analysis, such as extracting NOK tests, grouping crash signatures, or summarizing failure categories.
