"""The citation on the homepage and in the README matches CITATION.cff.

CITATION.cff is the record GitHub's "Cite this repository" button reads. The
README and the docs homepage print the dataset citation by hand, once as APA
text and once as BibTeX. These tests rebuild both from the dataset entry in
CITATION.cff and fail when a page drifts from it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
PAGES = [REPO / "README.md", REPO / "docs" / "index.qmd"]


def dataset_reference() -> dict:
    cff = yaml.safe_load((REPO / "CITATION.cff").read_text(encoding="utf-8"))
    (reference,) = [r for r in cff["references"] if r["type"] == "data"]
    return reference


def apa_authors(authors: list[dict]) -> str:
    names = [f"{a['family-names']}, {a['given-names'][0]}." for a in authors]
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + ", & " + names[-1]


def expected_apa(reference: dict) -> str:
    return (
        f"{apa_authors(reference['authors'])} ({reference['year']}). "
        f"*{reference['title']}* [Data set]. {reference['publisher']['name']}. "
        f"<{reference['url']}>"
    )


def bibtex_fields(text: str) -> dict[str, str]:
    match = re.search(r"```bibtex\n(@misc\{.*?\n\})\n```", text, re.DOTALL)
    assert match, "no BibTeX block"
    fields = dict(re.findall(r"^\s+(\w+)\s+= \{(.*)\},?$", match.group(1), re.M))
    return fields


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_apa_citation_matches_citation_cff(page: Path) -> None:
    text = page.read_text(encoding="utf-8")
    assert f"> {expected_apa(dataset_reference())}\n" in text


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_bibtex_matches_citation_cff(page: Path) -> None:
    reference = dataset_reference()
    fields = bibtex_fields(page.read_text(encoding="utf-8"))
    authors = " and ".join(
        f"{a['family-names']}, {a['given-names']}" for a in reference["authors"]
    )
    # BibTeX writes an en dash as `--` and protects capitals with braces.
    title = fields["title"].replace("{", "").replace("}", "").replace("--", "–")
    assert fields["author"] == authors
    assert title == reference["title"]
    assert fields["year"] == str(reference["year"])
    assert fields["publisher"] == reference["publisher"]["name"]
    assert fields["url"] == reference["url"]


def test_both_pages_print_the_same_citation() -> None:
    blocks = []
    for page in PAGES:
        match = re.search(r"## Cite\n.*?```\n", page.read_text("utf-8"), re.DOTALL)
        assert match, f"no Cite section in {page.name}"
        blocks.append(match.group(0))
    assert blocks[0] == blocks[1]
