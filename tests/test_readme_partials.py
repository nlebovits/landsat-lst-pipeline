"""The README sections hold the author's text, word for word.

The dataset description used to be the repository README. It now lives as one
file per section under `docs/_readme/`, because the documentation site
includes each section on its own page and `cog_catalog.published_readme` joins
them back into the catalog README. The author asked that the split change no
word of the text. Only the link targets may move, because the site resolves
`/about/known-issues.qmd` where the README had `#known-issues`.

`tests/fixtures/readme_pre_split.md` is the README as it stood before the
split, byte for byte. Every comparison here reads it as the reference. A word
edited in a section fails here, and so does a sentence lost at a section edge.

Two sections of that README appear nowhere: the example notebook and the
development notes. The site's tutorial replaces the first, and the second
addresses a contributor rather than a reader of the data.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from lst import cog_catalog

ROOT = Path(__file__).resolve().parent.parent
PARTIALS = ROOT / cog_catalog.README_PARTIALS_DIR
FIXTURE = ROOT / "tests" / "fixtures" / "readme_pre_split.md"

#: The headings of the fixture sections that no partial carries.
DROPPED = ("### Example notebook", "## Development")

_IMAGE = re.compile(r"!\[([^\]]*)\]\([^)\s]+\)")
_LINK = re.compile(r"\[([^\]]*)\]\([^)\s]+\)")
_LINK_TARGET = re.compile(r"\]\([^)\s]+\)")
_COMMENT = re.compile(r"^<!--.*-->$")


def without_comments(markdown: str) -> str:
    """The Markdown with every comment line gone and the ends trimmed.

    The Vale markers are the only comments in these files. Each section
    carries a pair, and the fixture carries one pair and a note above it.
    """
    lines = [line for line in markdown.splitlines() if not _COMMENT.match(line)]
    return "\n".join(lines).strip()


def visible(markdown: str) -> str:
    """What a reader sees: each image by its alt text, each link by its text."""
    return _LINK.sub(r"\1", _IMAGE.sub(r"\1", without_comments(markdown)))


def targets_blanked(markdown: str) -> str:
    """The Markdown with every link target emptied and everything else kept.

    Stricter than `visible`. It also fails a section that dropped a link and
    kept the link's words.
    """
    return _LINK_TARGET.sub("]()", without_comments(markdown))


def partial_names() -> list[str]:
    return sorted(path.stem for path in PARTIALS.glob("*.md"))


def fixture_lines() -> list[str]:
    return FIXTURE.read_text(encoding="utf-8").splitlines()


def first_line(name: str) -> str:
    """The first line of a section's text, after its opening Vale marker."""
    return without_comments((PARTIALS / f"{name}.md").read_text(encoding="utf-8"))


def section_starts() -> set[str]:
    """Every fixture line that opens a section, kept or dropped."""
    return {first_line(name).splitlines()[0] for name in partial_names()} | set(DROPPED)


def fixture_span(name: str) -> str:
    """The fixture text the named section was cut from.

    It runs from the section's first line to the next line that opens another
    section, or to the end of the file.
    """
    lines = fixture_lines()
    opening = first_line(name).splitlines()[0]
    assert opening in lines, f"{name}.md opens with a line the README never had"
    start = lines.index(opening)
    others = section_starts() - {opening}
    end = next(
        (index for index in range(start + 1, len(lines)) if lines[index] in others),
        len(lines),
    )
    return "\n".join(lines[start:end])


def fixture_without_dropped_sections() -> str:
    """The fixture with each dropped section cut to the next section start."""
    lines = fixture_lines()
    starts = section_starts()
    kept: list[str] = []
    dropping = False
    for line in lines:
        if line in starts:
            dropping = line in DROPPED
        if not dropping:
            kept.append(line)
    return "\n".join(kept)


def test_the_fixture_is_the_pre_split_readme():
    """The reference has to be the README the author wrote, not a later one.

    Its first heading and its two dropped sections are what identify it. A
    fixture regenerated from the new link page would hold neither.
    """
    lines = fixture_lines()
    assert "# Landsat LST P95 composites (2021–2025)" in lines
    for heading in DROPPED:
        assert heading in lines


@pytest.mark.parametrize("name", partial_names())
def test_each_section_reads_as_the_readme_did(name):
    text = (PARTIALS / f"{name}.md").read_text(encoding="utf-8")
    assert visible(text) == visible(fixture_span(name))


@pytest.mark.parametrize("name", partial_names())
def test_each_section_changed_only_link_targets(name):
    text = (PARTIALS / f"{name}.md").read_text(encoding="utf-8")
    assert targets_blanked(text) == targets_blanked(fixture_span(name))


@pytest.mark.parametrize("name", partial_names())
def test_each_section_wraps_itself_in_vale_markers(name):
    """The site includes one section at a time, so each carries its own pair."""
    text = (PARTIALS / f"{name}.md").read_text(encoding="utf-8")
    assert text.startswith("<!-- vale off -->\n")
    assert text.endswith("<!-- vale on -->\n")


def test_every_section_says_where_it_goes():
    """A new section reaches the catalog, or says that it stays on the site."""
    published = set(cog_catalog.PUBLISHED_README_PARTIALS)
    site_only = set(cog_catalog.SITE_ONLY_README_PARTIALS)
    assert not published & site_only
    assert set(partial_names()) == published | site_only


def test_no_section_is_site_only_yet():
    """Every section the README had, apart from the two dropped, publishes."""
    assert cog_catalog.SITE_ONLY_README_PARTIALS == ()


def test_the_joined_sections_are_the_readme_without_two_sections():
    assembled = cog_catalog.assemble_readme(PARTIALS)
    expected = fixture_without_dropped_sections()
    assert visible(assembled) == visible(expected)
    assert targets_blanked(assembled) == targets_blanked(expected)
    for heading in DROPPED:
        assert heading not in assembled


def test_the_sections_join_in_the_readme_order():
    """The published order is the order the sections had in the README."""
    lines = fixture_lines()
    positions = [
        lines.index(first_line(name).splitlines()[0])
        for name in cog_catalog.PUBLISHED_README_PARTIALS
    ]
    assert positions == sorted(positions)
