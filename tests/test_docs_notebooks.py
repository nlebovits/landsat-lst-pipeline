"""The docs workflow picks the right notebooks and catches a stale freeze.

`.github/scripts/docs_notebooks.py` decides which notebooks a pull request
executes, and fails the render job when a notebook's inputs outside its own
source changed after its freeze was recorded. These tests build a small git
repository with the same layout as `docs/` and check both decisions, then
check that this repository's own record is current.
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github" / "scripts" / "docs_notebooks.py"

_spec = importlib.util.spec_from_file_location("docs_notebooks", SCRIPT)
assert _spec and _spec.loader
docs_notebooks = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(docs_notebooks)

NOTEBOOK = "---\ntitle: x\n---\n\n```{python}\nprint(1)\n```\n"
PAGE = "---\ntitle: x\n---\n\nText only.\n"


def run(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def write(repo: Path, path: str, text: str) -> None:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def commit(repo: Path, message: str) -> None:
    run(repo, "add", "-A")
    run(repo, "commit", "-q", "-m", message)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    run(tmp_path, "init", "-q", "-b", "main")
    run(tmp_path, "config", "user.name", "test")
    run(tmp_path, "config", "user.email", "test@example.com")
    for path, text in {
        "docs/quickstart.qmd": NOTEBOOK,
        "docs/about/methods.qmd": PAGE,
        "docs/tutorials/city.qmd": NOTEBOOK,
        "docs/tutorials/data/city.parquet": "rows",
        "docs/tutorials/_metadata.yml": "format: {}\n",
        "docs/_plotting.py": "STYLE = 1\n",
        "docs/fonts/Plex.ttf": "glyphs",
        "docs/styles.scss": "a {}\n",
        "pyproject.toml": '[dependency-groups]\ndocs = ["quarto-cli"]\n',
    }.items():
        write(tmp_path, path, text)
    commit(tmp_path, "base")
    return tmp_path


def picked_after(repo: Path, path: str, text: str) -> list[str]:
    write(repo, path, text)
    commit(repo, f"change {path}")
    return docs_notebooks.pick(repo, "pull_request")[0]


class TestPick:
    def test_finds_only_pages_with_python_cells(self, repo):
        files = docs_notebooks.tracked(repo)
        assert docs_notebooks.notebooks(repo, files) == [
            "docs/quickstart.qmd",
            "docs/tutorials/city.qmd",
        ]

    def test_a_site_file_in_docs_selects_no_notebook(self, repo):
        """`docs/quickstart.qmd` owns no directory. A stylesheet beside it is
        not one of its inputs."""
        assert picked_after(repo, "docs/styles.scss", "a { color: red }\n") == []

    def test_a_tutorial_data_file_selects_that_tutorial(self, repo):
        picked = picked_after(repo, "docs/tutorials/data/city.parquet", "new rows")
        assert picked == ["docs/tutorials/city.qmd"]

    def test_directory_metadata_selects_nothing(self, repo):
        assert (
            picked_after(repo, "docs/tutorials/_metadata.yml", "format: {a: 1}\n") == []
        )

    @pytest.mark.parametrize(
        "path", ["docs/_plotting.py", "docs/fonts/Plex.ttf", "uv.lock"]
    )
    def test_a_shared_input_selects_every_notebook(self, repo, path):
        assert len(picked_after(repo, path, "changed")) == 2

    def test_the_docs_dependency_group_selects_every_notebook(self, repo):
        text = '[dependency-groups]\ndocs = ["quarto-cli", "geopandas"]\n'
        assert len(picked_after(repo, "pyproject.toml", text)) == 2

    def test_a_notebook_source_selects_itself(self, repo):
        picked = picked_after(repo, "docs/quickstart.qmd", NOTEBOOK + "\nMore.\n")
        assert picked == ["docs/quickstart.qmd"]

    def test_a_scheduled_run_selects_every_notebook(self, repo):
        assert len(docs_notebooks.pick(repo, "schedule")[0]) == 2


class TestRecord:
    def test_no_record_means_every_notebook_is_stale(self, repo):
        assert docs_notebooks.stale(repo) == [
            "docs/quickstart.qmd",
            "docs/tutorials/city.qmd",
        ]

    def test_a_fresh_record_is_current(self, repo):
        docs_notebooks.record(repo)
        assert docs_notebooks.stale(repo) == []

    def test_changed_data_stales_only_its_notebook(self, repo):
        docs_notebooks.record(repo)
        write(repo, "docs/tutorials/data/city.parquet", "new rows")
        commit(repo, "data")
        assert docs_notebooks.stale(repo) == ["docs/tutorials/city.qmd"]

    def test_changed_plotting_stales_every_notebook(self, repo):
        docs_notebooks.record(repo)
        write(repo, "docs/_plotting.py", "STYLE = 2\n")
        commit(repo, "style")
        assert len(docs_notebooks.stale(repo)) == 2

    def test_a_source_or_page_change_leaves_the_record_current(self, repo):
        """`freeze: auto` covers the notebook's own source."""
        docs_notebooks.record(repo)
        write(repo, "docs/tutorials/city.qmd", NOTEBOOK + "\nMore.\n")
        write(repo, "docs/styles.scss", "a { color: red }\n")
        commit(repo, "edit")
        assert docs_notebooks.stale(repo) == []


def test_this_repository_records_current_inputs():
    """Run `python3 .github/scripts/docs_notebooks.py record` after you
    execute a notebook whose inputs changed, and commit the manifest."""
    assert docs_notebooks.stale(ROOT) == []
