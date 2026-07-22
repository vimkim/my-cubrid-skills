#!/usr/bin/env bash

set -euo pipefail

usage ()
{
  echo "Usage: bash $0 <github-pr-url|pr-number> [circleci-job-name] [new-output-dir]" >&2
  echo "Example: bash $0 https://github.com/CUBRID/cubrid/pull/6864 test_shell" >&2
}

for command_name in gh curl jq
do
  if ! command -v "$command_name" >/dev/null 2>&1
  then
    echo "Required command not found: $command_name" >&2
    exit 1
  fi
done

pr_input=${1:-}
requested_job=${2:-test_shell}
output_dir=${3:-}

if [[ -z "$pr_input" ]]
then
  usage
  exit 2
fi

if [[ "$pr_input" =~ ^https://github\.com/([^/]+)/([^/]+)/pull/([0-9]+)/?([?#].*)?$ ]]
then
  repo="${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
  pr_number=${BASH_REMATCH[3]}
elif [[ "$pr_input" =~ ^[0-9]+$ ]]
then
  repo=${CUBRID_CI_REPO:-CUBRID/cubrid}
  pr_number=$pr_input
else
  echo "Expected a GitHub PR URL or numeric PR number, got: $pr_input" >&2
  exit 2
fi

if [[ -z "$output_dir" ]]
then
  output_dir=$(mktemp -d -t "cubrid-pr${pr_number}-${requested_job}.XXXXXX")
elif [[ -e "$output_dir" ]]
then
  echo "Output path already exists; choose a new directory: $output_dir" >&2
  exit 2
else
  mkdir -p -- "$output_dir"
fi

pr_json=$(gh pr view "$pr_number" --repo "$repo" \
  --json number,title,url,state,headRefName,headRefOid,baseRefName,updatedAt)
head_sha=$(jq -er '.headRefOid' <<<"$pr_json")
pr_url=$(jq -er '.url' <<<"$pr_json")

combined_status=$(gh api "repos/$repo/commits/$head_sha/status")
status_context="ci/circleci: $requested_job"
circle_status=$(jq -cer --arg context "$status_context" '
  [.statuses[] | select(.context == $context)]
  | sort_by(.updated_at)
  | last
' <<<"$combined_status") || {
  echo "No current-head GitHub status named '$status_context' for $head_sha" >&2
  exit 3
}

status_state=$(jq -er '.state' <<<"$circle_status")
target_url=$(jq -er '.target_url' <<<"$circle_status")

if [[ "$status_state" == "pending" ]]
then
  echo "Current-head status '$status_context' is still pending: $target_url" >&2
  exit 3
fi

if [[ "$target_url" =~ /([0-9]+)(/tests)?/?$ ]]
then
  build_number=${BASH_REMATCH[1]}
else
  echo "Cannot extract a CircleCI build number from: $target_url" >&2
  exit 3
fi

job_api="https://circleci.com/api/v1.1/project/github/$repo/$build_number"
tests_api="${job_api}/tests"
curl --fail --location --silent --show-error "$job_api" -o "$output_dir/job.json"
curl --fail --location --silent --show-error "$tests_api" -o "$output_dir/tests.json"

job_sha=$(jq -er '.vcs_revision' "$output_dir/job.json")
job_name=$(jq -er '.workflows.job_name' "$output_dir/job.json")
job_build_number=$(jq -er '.build_num' "$output_dir/job.json")

if [[ "$job_sha" != "$head_sha" ]]
then
  echo "Refusing stale/mismatched CircleCI job: PR head is $head_sha, job revision is $job_sha" >&2
  exit 4
fi

if [[ "$job_name" != "$requested_job" ]]
then
  echo "Refusing mismatched CircleCI job: requested $requested_job, metadata says $job_name" >&2
  exit 4
fi

if [[ "$job_build_number" != "$build_number" ]]
then
  echo "Refusing mismatched CircleCI response: URL job is $build_number, metadata says $job_build_number" >&2
  exit 4
fi

jq -e '.tests | type == "array"' "$output_dir/tests.json" >/dev/null
jq '[.tests[] | select(.result == "failure")]' "$output_dir/tests.json" \
  > "$output_dir/failed-tests.json"
jq -r '.tests[] | select(.result == "failure") | .name' "$output_dir/tests.json" \
  > "$output_dir/failed-tc.txt"

jq -n \
  --arg repo "$repo" \
  --argjson pr_number "$pr_number" \
  --arg pr_url "$pr_url" \
  --arg head_sha "$head_sha" \
  --arg status_context "$status_context" \
  --arg status_state "$status_state" \
  --arg target_url "$target_url" \
  --argjson build_number "$build_number" \
  --arg job_api "$job_api" \
  --arg tests_api "$tests_api" \
  --slurpfile tests "$output_dir/tests.json" '
  {
    repo: $repo,
    pr_number: $pr_number,
    pr_url: $pr_url,
    head_sha: $head_sha,
    status_context: $status_context,
    status_state: $status_state,
    circleci_url: $target_url,
    circleci_build_number: $build_number,
    job_api: $job_api,
    tests_api: $tests_api,
    test_count: ($tests[0].tests | length),
    result_counts: (
      $tests[0].tests
      | group_by(.result)
      | map({key: .[0].result, value: length})
      | from_entries
    )
  }
' > "$output_dir/summary.json"

echo "output_dir=$output_dir"
jq '{pr_url,head_sha,status_context,status_state,circleci_build_number,test_count,result_counts,tests_api}' \
  "$output_dir/summary.json"
echo "failed_tc=$output_dir/failed-tc.txt"
echo "failed_tests=$output_dir/failed-tests.json"
echo "all_tests=$output_dir/tests.json"
