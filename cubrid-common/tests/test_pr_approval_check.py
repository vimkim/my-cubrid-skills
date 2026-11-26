import io
import json
import runpy
import subprocess
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch


CHECKER = Path(__file__).resolve().parents[1] / "scripts" / "cubrid-pr-approval-check"
PULL = "repos/CUBRID/cubrid/pulls/1"
EVENTS = "repos/CUBRID/cubrid/issues/1/events"
TEAM_MEMBERS = "orgs/CUBRID/teams/dev/members"


def user(login, kind="User"):
    return {"login": login, "type": kind}


def request(number, *, login=None, team=None, removed=False, day=1, kind="User"):
    return {
        "event": "review_request_removed" if removed else "review_requested",
        "id": number,
        "created_at": f"2026-11-{day:02}T00:00:00Z",
        "requested_reviewer": user(login, kind) if login else None,
        "requested_team": {"slug": team} if team else None,
    }


def review(login, state, day=2, commit_id=None):
    data = {
        "user": user(login),
        "state": state,
        "submitted_at": f"2026-11-{day:02}T00:00:00Z",
    }
    if commit_id is not None:
        data["commit_id"] = commit_id
    return data


class ApprovalCheckTests(unittest.TestCase):
    def run_checker(self, responses, extra_args=()):
        endpoints = {
            PULL: {"user": user("Author")},
            f"{PULL}/reviews": [[]],
            f"{PULL}/requested_reviewers": {"users": [], "teams": []},
            EVENTS: [[]],
            **responses,
        }

        def gh_api(command, **_):
            self.assertEqual(command[:6], ["gh", "api", "--hostname", "github.com", "--method", "GET"])
            endpoint = command[6]
            expected_options = (
                ["--paginate", "--slurp"]
                if endpoint in (f"{PULL}/reviews", EVENTS, TEAM_MEMBERS)
                else []
            )
            self.assertEqual(command[7:], expected_options)
            response = endpoints[endpoint]
            if isinstance(response, str):
                return subprocess.CompletedProcess(command, 1, "", response)
            return subprocess.CompletedProcess(command, 0, json.dumps(response), "")

        stdout, stderr = io.StringIO(), io.StringIO()
        with (
            patch("sys.argv", [str(CHECKER), "--repo", "CUBRID/cubrid", "--pr", "1", *extra_args]),
            patch("subprocess.run", side_effect=gh_api),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
            self.assertRaises(SystemExit) as exit_status,
        ):
            runpy.run_path(str(CHECKER), run_name="__main__")
        return exit_status.exception.code, stdout.getvalue().splitlines(), stderr.getvalue()

    def test_blocks_reviewers_individually_across_pages_and_ignores_removed_requests(self):
        status, lines, error = self.run_checker({
            EVENTS: [
                [
                    request(1, login="dismissed"),
                    request(2, login="changes"),
                    request(3, login="commented"),
                    request(4, login="pending"),
                    request(5, login="rerequested"),
                    request(6, login="removed"),
                    request(7, login="author"),
                    request(8, login="automation", kind="Bot"),
                    request(9, team="old-team"),
                ],
                [
                    request(10, login="rerequested", day=3),
                    request(11, login="removed", removed=True),
                    request(12, team="old-team", removed=True),
                    request(13, team="dev"),
                ],
            ],
            f"{PULL}/reviews": [
                [
                    review("dismissed", "APPROVED"),
                    review("changes", "APPROVED"),
                    review("pending", "APPROVED"),
                    review("rerequested", "APPROVED"),
                    review("commented", "COMMENTED"),
                ],
                [
                    review("dismissed", "DISMISSED", day=3),
                    review("changes", "CHANGES_REQUESTED", day=3),
                    review("rerequested", "COMMENTED", day=4),
                    review("team-approved", "APPROVED"),
                ],
            ],
            f"{PULL}/requested_reviewers": {"users": [user("Pending")], "teams": [{"slug": "dev"}]},
            TEAM_MEMBERS: [[user("team-approved")], [user("team-missing"), user("Commented")]],
        })
        self.assertEqual((status, error), (1, ""))
        self.assertEqual(lines, [
            "CUBRID/cubrid#1",
            "changes CHANGES_REQUESTED",
            "commented COMMENTED",
            "dismissed DISMISSED",
            "pending APPROVED (pending request)",
            "rerequested APPROVED (request at or after approval)",
            "team-approved APPROVED",
            "team-missing no review",
            "BLOCKED",
        ])

    def test_approval_after_renewed_request_survives_a_later_comment(self):
        status, lines, error = self.run_checker({
            EVENTS: [[
                request(1, login="Reviewer"),
                request(2, login="reviewer", removed=True, day=2),
                request(3, login="Reviewer", day=3),
            ]],
            f"{PULL}/reviews": [[
                review("reviewer", "CHANGES_REQUESTED"),
                review("Reviewer", "APPROVED", day=4),
                review("Reviewer", "COMMENTED", day=5),
                review("unsolicited", "CHANGES_REQUESTED", day=5),
            ]],
        })
        self.assertEqual((status, lines, error), (0, ["CUBRID/cubrid#1", "Reviewer APPROVED", "PASS"], ""))

    def test_no_enlisted_reviewer_blocks_the_merge(self):
        status, lines, error = self.run_checker({
            f"{PULL}/reviews": [[review("unsolicited", "APPROVED")]],
        })
        self.assertEqual((status, lines, error), (1, ["CUBRID/cubrid#1", "No enlisted reviewers", "BLOCKED"], ""))

    def test_unreadable_team_membership_blocks_the_check(self):
        status, lines, error = self.run_checker({
            f"{PULL}/requested_reviewers": {"users": [], "teams": [{"slug": "dev"}]},
            TEAM_MEMBERS: "HTTP 404",
        })
        self.assertEqual((status, lines), (2, []))
        self.assertIn("orgs/CUBRID/teams/dev/members: HTTP 404", error)

    def test_head_pin_accepts_current_head_approval_case_insensitively(self):
        head = "a" * 40
        status, lines, error = self.run_checker(
            {
                PULL: {"user": user("Author"), "head": {"sha": head}},
                EVENTS: [[request(1, login="Reviewer")]],
                f"{PULL}/reviews": [[review("Reviewer", "APPROVED", commit_id=head)]],
            },
            extra_args=["--head", head.upper()],
        )
        self.assertEqual((status, lines, error), (0, ["CUBRID/cubrid#1", "Reviewer APPROVED", "PASS"], ""))

    def test_head_pin_blocks_stale_and_missing_commit_approvals(self):
        old_head = "1" * 40
        curr_head = "2" * 40
        status, lines, error = self.run_checker(
            {
                PULL: {"user": user("Author"), "head": {"sha": curr_head}},
                EVENTS: [[request(1, login="stale"), request(2, login="nocommit")]],
                f"{PULL}/reviews": [[
                    review("stale", "APPROVED", commit_id=old_head),
                    review("nocommit", "APPROVED"),
                ]],
            },
            extra_args=["--head", curr_head],
        )
        self.assertEqual((status, error), (1, ""))
        self.assertEqual(lines, [
            "CUBRID/cubrid#1",
            "nocommit APPROVED (not at current head)",
            "stale APPROVED (not at current head)",
            "BLOCKED",
        ])

    def test_without_flags_behavior_stays_unchanged(self):
        old_head = "1" * 40
        curr_head = "2" * 40
        status, lines, error = self.run_checker({
            PULL: {"user": user("Author"), "head": {"sha": curr_head}},
            EVENTS: [[request(1, login="Reviewer"), request(2, login="vimkim")]],
            f"{PULL}/reviews": [[
                review("Reviewer", "APPROVED", commit_id=old_head),
                review("vimkim", "APPROVED", commit_id=old_head),
            ]],
        })
        self.assertEqual(
            (status, lines, error),
            (0, ["CUBRID/cubrid#1", "Reviewer APPROVED", "vimkim APPROVED", "PASS"], ""),
        )

    def test_head_moved_and_invalid_head_exit_2(self):
        live_head = "a" * 40
        given_head = "b" * 40
        status, lines, error = self.run_checker(
            {PULL: {"user": user("Author"), "head": {"sha": live_head}}},
            extra_args=["--head", given_head],
        )
        self.assertEqual((status, lines), (2, []))
        self.assertIn(f"head moved: {live_head} != {given_head}", error)

        status, lines, error = self.run_checker({}, extra_args=["--head", "not-a-sha"])
        self.assertEqual((status, lines), (2, []))
        self.assertIn("--head must be a 40-hex commit SHA", error)

    def test_exclude_drops_only_reviewer_case_insensitively_and_blocks(self):
        status, lines, error = self.run_checker(
            {
                EVENTS: [[request(1, login="VimKim")]],
                f"{PULL}/reviews": [[review("VimKim", "APPROVED")]],
            },
            extra_args=["--exclude", "vimkim"],
        )
        self.assertEqual((status, lines, error), (1, ["CUBRID/cubrid#1", "No enlisted reviewers", "BLOCKED"], ""))

    def test_exclude_is_repeatable_across_direct_and_team_reviewers(self):
        status, lines, error = self.run_checker(
            {
                EVENTS: [[request(1, login="VimKim"), request(2, team="dev")]],
                f"{PULL}/requested_reviewers": {"users": [], "teams": [{"slug": "dev"}]},
                TEAM_MEMBERS: [[user("peer"), user("kept")]],
                f"{PULL}/reviews": [[
                    review("VimKim", "APPROVED"),
                    review("peer", "CHANGES_REQUESTED"),
                    review("kept", "APPROVED"),
                ]],
            },
            extra_args=["--exclude", "vimkim", "--exclude", "PEER"],
        )
        self.assertEqual((status, lines, error), (0, ["CUBRID/cubrid#1", "kept APPROVED", "PASS"], ""))
