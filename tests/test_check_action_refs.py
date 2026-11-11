"""`.github/scripts/check_action_refs.py` reads workflows and judges refs.

Offline: these tests hand the checker a fixed set of remote refs instead of
calling `git ls-remote`. The pre-push hook runs the network half.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github" / "scripts" / "check_action_refs.py"

_spec = importlib.util.spec_from_file_location("check_action_refs", SCRIPT)
assert _spec and _spec.loader
check = importlib.util.module_from_spec(_spec)
# `@dataclass` resolves the module's annotations through sys.modules.
sys.modules[_spec.name] = check
_spec.loader.exec_module(check)

SHA = "68559e99cc807c1eb7e9238fd43a15bba460eec2"
OTHER = "0" * 40
REFS = {"v7": "a" * 40, "v10.3.3": SHA, "main": "b" * 40}

WORKFLOW = f"""\
jobs:
  build:
    steps:
      - uses: actions/checkout@v7
      - name: Install uv
        uses: astral-sh/setup-uv@{SHA} # v10.3.3
      - uses: "github/codeql-action/init@main"
      - uses: ./.github/actions/local
      - uses: docker://alpine:3.20
"""


def use(ref: str, comment: str | None = None) -> object:
    return check.Use("w.yml", 1, "astral-sh/setup-uv", ref, comment)


def test_reads_every_remote_use_and_skips_local_and_docker(tmp_path):
    path = tmp_path / "w.yml"
    path.write_text(WORKFLOW, encoding="utf-8")
    found = [(u.action, u.ref, u.comment, u.line) for u in check.uses_in(path)]
    assert found == [
        ("actions/checkout", "v7", None, 4),
        ("astral-sh/setup-uv", SHA, "v10.3.3", 6),
        ("github/codeql-action/init", "main", None, 7),
    ]


def test_an_action_in_a_subdirectory_resolves_against_its_repository():
    assert check.Use("w.yml", 1, "github/codeql-action/init", "main", None).repo == (
        "github/codeql-action"
    )


def test_a_tag_or_branch_that_exists_passes():
    assert check.problem(use("v7"), REFS) is None
    assert check.problem(use("main"), REFS) is None


def test_a_missing_tag_fails():
    """The failure that broke the docs workflow: setup-uv has no `v10` tag."""
    assert "no tag or branch 'v10'" in check.problem(use("v10"), REFS)


def test_a_pinned_sha_matching_its_comment_passes():
    assert check.problem(use(SHA, "v10.3.3"), REFS) is None


def test_a_pinned_sha_without_a_comment_fails():
    assert "no '# <tag>' comment" in check.problem(use(SHA), REFS)


def test_a_pinned_sha_that_its_comment_does_not_name_fails():
    assert "points to" in check.problem(use(OTHER, "v10.3.3"), REFS)
