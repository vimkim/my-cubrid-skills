---
name: cubrid-qa-fetch
description: Fetch and analyze authenticated pages from CUBRID's internal QA portal at qahome.cubrid.org. Use when the user gives a qahome.cubrid.org/qaresult URL, asks to read or parse shell/SQL/medium/functional QA result pages, asks for NOK lists or core stacks from qahome, or describes a portal navigation path such as cubrid / Recent builds(72h) / 11.5.0.2268-2c66b9a. The portal requires login; unauthenticated WebFetch or curl usually returns only the login form. Also use when resolving build tree ids, showstat pages, showFuntionRes summaries, showFailResult details, viewShellTestResult pages, or qahome frame/tree navigation.
---

# Fetch qahome QA Pages

`qahome.cubrid.org/qaresult/*.nhn` is login-protected. Fetch pages with a logged-in `JSESSIONID`, save HTML under `/tmp`, verify that the saved file is not the login form, then parse it locally.

Credentials must come from environment variables:

| Variable | Meaning |
| --- | --- |
| `CUBRID_QA_USER` | qahome username |
| `CUBRID_QA_PASS` | qahome password |

Never ask the user to paste the password into chat. If either variable is missing, stop the live fetch and tell the user to export them, then restart or relaunch the session if the current process does not inherit them.

```sh
export CUBRID_QA_USER='vimkim'
export CUBRID_QA_PASS='...'
```

## Guardrails

- Only send these credentials to exactly `qahome.cubrid.org`.
- Do not echo `CUBRID_QA_PASS`, write it to files, include it in command output, or put it in output filenames.
- Keep the cookie jar temporary and remove it when done.
- Prefer one shell invocation for login plus all related fetches so the same cookie jar is reused.
- Do not trust a small HTML file. Login pages are usually around 3 KB and contain `name="loginform"`.

## Direct URL Fetch

Use this for a concrete qahome URL such as `viewShellTestResult.nhn`, `showFailResult.nhn`, `showFuntionRes.nhn`, `showstat.nhn`, or `showfile.nhn`.

```bash
URL='<qahome-url>'
case "$URL" in
  https://qahome.cubrid.org/*|http://qahome.cubrid.org/*) ;;
  *) echo "refusing: URL must be on qahome.cubrid.org"; exit 2 ;;
esac
: "${CUBRID_QA_USER:?CUBRID_QA_USER not set}"
: "${CUBRID_QA_PASS:?CUBRID_QA_PASS not set}"

BASE='https://qahome.cubrid.org/qaresult'
JAR=$(mktemp /tmp/cubrid_qa_cookies.XXXXXX.txt)
LOGIN_RESP=$(mktemp /tmp/cubrid_qa_login.XXXXXX.html)
UA='Mozilla/5.0 (X11; Linux x86_64) cubrid-qa-fetch/2'

cleanup() { rm -f "$JAR" "$LOGIN_RESP"; }
trap cleanup EXIT

safe_name() {
  printf '%s' "$1" |
    sed -E 's|^https?://qahome\.cubrid\.org/||; s|[/?&=:#%+]|_|g; s|_+|_|g; s|_$||'
}

OUT="/tmp/cubrid_qa_$(safe_name "$URL").html"

curl -sS -c "$JAR" -b "$JAR" -o /dev/null \
  -H "User-Agent: $UA" \
  "$BASE/index.nhn"

curl -sS -c "$JAR" -b "$JAR" -o "$LOGIN_RESP" -L \
  -H "User-Agent: $UA" \
  -H "Referer: $BASE/user.nhn" \
  --data-urlencode 'm=login' \
  --data-urlencode "user_id=${CUBRID_QA_USER}" \
  --data-urlencode "pwd=${CUBRID_QA_PASS}" \
  --data-urlencode 'backUrl=' \
  "$BASE/user.nhn"

if grep -q 'name="loginform"' "$LOGIN_RESP"; then
  echo "login failed - check CUBRID_QA_USER / CUBRID_QA_PASS"
  exit 3
fi

curl -sS -c "$JAR" -b "$JAR" -o "$OUT" -L \
  -H "User-Agent: $UA" \
  -H "Referer: $BASE/index.nhn" \
  -w 'HTTP=%{http_code} size=%{size_download}\n' \
  "$URL"

SZ=$(stat -c %s "$OUT")
if [ "$SZ" -lt 4096 ] && grep -q 'name="loginform"' "$OUT"; then
  echo "got login form back from $URL - authenticated session was rejected"
  exit 4
fi

echo "OUT=$OUT size=$SZ"
```

After fetching, report the saved path, size, and what the page appears to contain, then do the user's requested parsing or analysis.

## Portal Tree Navigation

Use this when the user gives a browser path instead of a direct URL, for example:

```text
https://qahome.cubrid.org/qaresult/index.nhn
  cubrid
  Recent builds(72h)
  11.5.0.2268-2c66b9a
```

The left pane is not in the initial frameset. `index.nhn?m=showLeft` creates a dhtmlx tree and loads XML from:

```text
index.nhn?m=showTree&id=0
```

Known real nodes:

| Node | Meaning |
| --- | --- |
| `0` | root; contains `cubrid` |
| `740` | `cubrid` |
| `3473` | `Recent builds(72h)` under `cubrid` |

Do not rely on bare `showstat.nhn` or the first default page after login. It may point to an older build. Also avoid `showMain.nhn`; it may hang and is not needed for result extraction.

### Find a build by text or commit suffix

Run the login flow once, then fetch the tree XML nodes and search them. The example below searches `cubrid -> Recent builds(72h)` for a build containing `2c66b9a`.

```bash
GROUP_TEXT='Recent builds(72h)'
BUILD_QUERY='2c66b9a'
BASE='https://qahome.cubrid.org/qaresult'
: "${CUBRID_QA_USER:?CUBRID_QA_USER not set}"
: "${CUBRID_QA_PASS:?CUBRID_QA_PASS not set}"

JAR=$(mktemp /tmp/cubrid_qa_cookies.XXXXXX.txt)
LOGIN_RESP=$(mktemp /tmp/cubrid_qa_login.XXXXXX.html)
UA='Mozilla/5.0 (X11; Linux x86_64) cubrid-qa-fetch/2'
cleanup() { rm -f "$JAR" "$LOGIN_RESP"; }
trap cleanup EXIT

fetch_rel() {
  rel=$1
  out=$2
  curl -sS -c "$JAR" -b "$JAR" -o "$out" -L \
    -H "User-Agent: $UA" \
    -H "Referer: $BASE/index.nhn" \
    "$BASE/$rel"
  if [ "$(stat -c %s "$out")" -lt 4096 ] && grep -q 'name="loginform"' "$out"; then
    echo "got login form while fetching $rel"
    exit 4
  fi
}

find_item() {
  xml=$1
  query=$2
  python3 - "$xml" "$query" <<'PY'
import sys
import xml.etree.ElementTree as ET
from html import unescape

xml_path, query = sys.argv[1], sys.argv[2]
root = ET.parse(xml_path).getroot()
for item in root.iter("item"):
    text = unescape(item.attrib.get("text", ""))
    if query in text:
        url = ""
        for child in item:
            if child.tag == "userdata" and child.attrib.get("name") == "url":
                url = unescape(child.text or "")
        print(f"{item.attrib.get('id','')}\t{text}\t{url}")
        break
PY
}

curl -sS -c "$JAR" -b "$JAR" -o /dev/null -H "User-Agent: $UA" "$BASE/index.nhn"
curl -sS -c "$JAR" -b "$JAR" -o "$LOGIN_RESP" -L \
  -H "User-Agent: $UA" \
  -H "Referer: $BASE/user.nhn" \
  --data-urlencode 'm=login' \
  --data-urlencode "user_id=${CUBRID_QA_USER}" \
  --data-urlencode "pwd=${CUBRID_QA_PASS}" \
  --data-urlencode 'backUrl=' \
  "$BASE/user.nhn"
if grep -q 'name="loginform"' "$LOGIN_RESP"; then
  echo "login failed - check CUBRID_QA_USER / CUBRID_QA_PASS"
  exit 3
fi

ROOT_XML=/tmp/cubrid_qa_tree_0.xml
CUBRID_XML=/tmp/cubrid_qa_tree_740.xml
GROUP_XML=/tmp/cubrid_qa_tree_group.xml

fetch_rel 'index.nhn?m=showTree&id=0' "$ROOT_XML"
CUBRID_ROW=$(find_item "$ROOT_XML" 'cubrid')
CUBRID_ID=$(printf '%s' "$CUBRID_ROW" | cut -f1)
[ -n "$CUBRID_ID" ] || { echo "could not find cubrid node"; exit 5; }

fetch_rel "index.nhn?m=showTree&id=$CUBRID_ID" "$CUBRID_XML"
GROUP_ROW=$(find_item "$CUBRID_XML" "$GROUP_TEXT")
GROUP_ID=$(printf '%s' "$GROUP_ROW" | cut -f1)
[ -n "$GROUP_ID" ] || { echo "could not find group: $GROUP_TEXT"; exit 5; }

fetch_rel "index.nhn?m=showTree&id=$GROUP_ID" "$GROUP_XML"
BUILD_ROW=$(find_item "$GROUP_XML" "$BUILD_QUERY")
BUILD_ID=$(printf '%s' "$BUILD_ROW" | cut -f1)
BUILD_TEXT=$(printf '%s' "$BUILD_ROW" | cut -f2)
BUILD_URL=$(printf '%s' "$BUILD_ROW" | cut -f3-)
[ -n "$BUILD_ID" ] || { echo "could not find build containing: $BUILD_QUERY"; exit 6; }

echo "BUILD_ID=$BUILD_ID"
echo "BUILD_TEXT=$BUILD_TEXT"
echo "BUILD_URL=$BUILD_URL"
```

If the target build is not found under `Recent builds(72h)`, say so and fetch the relevant branch node instead, such as `RB-11.5.0` or `RB-11.5.0-Manual`. Do not silently analyze a neighboring build.

### Fetch the functional summary for a build node

For a build node, first fetch its `showstat.nhn?treeId=<id>&treeName=<build>` URL. The useful function page is usually exposed by JavaScript inside `showstat.nhn`:

```text
showFuntionRes.nhn?tree_id=<id>&buildId=<build>
```

The endpoint is misspelled `showFuntionRes`, and the parameter is `tree_id`, not `treeId`. `showFunctionSummaryReport.nhn?treeId=<id>` can return an empty report for a valid build.

Extract and fetch the function URL from the saved `showstat` page:

```bash
SHOWSTAT_OUT="/tmp/cubrid_qa_${BUILD_ID}_showstat.html"
FUNCTION_OUT="/tmp/cubrid_qa_${BUILD_ID}_showFuntionRes.html"
fetch_rel "$BUILD_URL" "$SHOWSTAT_OUT"

FUNCTION_REL=$(python3 - "$SHOWSTAT_OUT" <<'PY'
import re
import sys
text = open(sys.argv[1], errors="replace").read()
m = re.search(r"showFuntionRes\.nhn\?tree_id=\s*'\s*\+\s*treeid\s*\+\s*\"&buildId=([^\"]+)\"", text)
if m:
    build = m.group(1)
    tree = re.search(r"var\s+treeid\s*=\s*'([^']+)'", text)
    if tree:
        print(f"showFuntionRes.nhn?tree_id={tree.group(1)}&buildId={build}")
        raise SystemExit
m = re.search(r"(showFuntionRes\.nhn\?tree_id=[^'\"<> ]+)", text)
if m:
    print(m.group(1).replace("&amp;", "&"))
PY
)
[ -n "$FUNCTION_REL" ] || { echo "could not derive showFuntionRes URL from $SHOWSTAT_OUT"; exit 7; }
fetch_rel "$FUNCTION_REL" "$FUNCTION_OUT"
echo "FUNCTION_OUT=$FUNCTION_OUT"
```

Verify the build before parsing. Wrong default pages can look valid but contain a different build marker, such as `MAXVERSION=11.5.0.2261-ca3508c`.

```bash
if grep -q 'MAXVERSION=' "$FUNCTION_OUT" && ! grep -q "$BUILD_TEXT" "$FUNCTION_OUT"; then
  echo "warning: page has MAXVERSION but does not mention expected build $BUILD_TEXT"
fi
```

## Detail Pages

Functional summary pages contain links to detail pages such as:

- `showFailResult.nhn?m=showFailVerifyItem&statid=...`
- `report/errorReport.nhn?m=showErrorInfo&srctb=resultstat&key=...`
- `viewShellTestResult.nhn?shellTestId=...&resultType=`
- `viewCCIForSQL.nhn`, `viewHAREPLTestResult.nhn`, `viewCDCREPLTestResult.nhn`

Extract relevant `href` values, normalize `&amp;` to `&`, prepend `https://qahome.cubrid.org` for absolute `/qaresult/...` paths, and fetch them with the same cookie jar. Add `resultType=NOK` to shell result URLs when the user asks only for failures.

## Parsing Shell NOK Pages

`viewShellTestResult.nhn?...resultType=NOK` pages usually contain one block per failed test:

- Numbered `<b>N. <a ... filePath=...>FULL_PATH</a></b>`
- `EnvId=...`
- A following `<pre>...</pre>` log block
- Core dumps with `CORE ANALYZER`, `SUMMARY : [...]`, and `DETAIL STACK:`

Parser skeleton:

```python
import html
import re
from pathlib import Path

text = Path("/tmp/saved_qahome_page.html").read_text(errors="replace")
pat = re.compile(
    r'<b>(\d+)\. <a[^>]*filePath=([^&"]+)[^>]*>([^<]+)</a></b>\s*'
    r'\(<i>EnvId=([^[]+)\[([^\]]+)\]</I>\)\s*</span>\s*<pre>(.*?)</pre>',
    re.DOTALL,
)
for m in pat.finditer(text):
    n, _file_path, full_path, _env, host, body = m.groups()
    body = html.unescape(body)
    summary = (re.search(r"SUMMARY\s*:\s*\[([^\]]+)\]", body) or [None, ""])[1]
    first_nok = next((line.strip() for line in body.splitlines() if "NOK" in line), "")
    print(f"{int(n):2}. {full_path} [{host}]")
    if first_nok:
        print(f"    nok: {first_nok[:200]}")
    if summary:
        print(f"    crash: {summary}")
```

## Failure Modes

| Symptom | Meaning | Action |
| --- | --- | --- |
| `CUBRID_QA_USER not set` or `CUBRID_QA_PASS not set` | Current process has no credentials. | Ask the user to set env vars and restart/relaunch if needed. |
| `login failed` | Wrong credentials or account issue. | Have the user verify in a browser; do not print the password. |
| Fetched page is around 3 KB and contains `loginform` | Session was rejected or expired. | Re-login and retry once. |
| `showstat.nhn` resolves to a valid but older build | Default tree selection is stale. | Traverse `index.nhn?m=showTree&id=...` explicitly and match the build text or commit suffix. |
| `showFunctionSummaryReport.nhn?treeId=...` is blank | Wrong endpoint for that build. | Fetch `showstat.nhn`, then the `showFuntionRes.nhn?tree_id=...&buildId=...` URL from its JavaScript. |
| Target build absent from `Recent builds(72h)` | The cache/window moved or the build is under a branch node. | Search `RB-*` nodes or report that the live tree does not contain the requested build. |
| `curl: (60) SSL certificate problem` | Local CA/proxy issue. | Use the correct CA bundle or `--cacert`; do not default to `-k`. |

## Reporting

Always tell the user:

- Which URL or tree path was fetched
- The saved path under `/tmp`
- File size and a one-line content check
- Any build-id mismatch or missing target-build finding

Then continue with the requested analysis, such as extracting NOK tests, grouping crash signatures, or summarizing failure categories.
