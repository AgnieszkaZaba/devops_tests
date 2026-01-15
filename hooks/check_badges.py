#!/usr/bin/env python3
"""
Checks/repairs notebook badge headers.

This module validates that a notebook's first cell contains the three canonical
badges (GitHub preview, MyBinder, Colab). It tolerates whitespace differences and
badge order, and can optionally fix the header in-place.

Usage:
    check_badges --repo-name=devops_tests [--repo-owner=open-atmos] [--fix-header] FILES...

The functions are written to be easily unit-tested.
"""
from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import Iterable, List, Tuple

import nbformat
from nbformat import NotebookNode

REPO_OWNER_DEFAULT = "open-atmos"


def _preview_badge_markdown(absolute_path: str, repo_name: str, repo_owner: str) -> str:
    svg_badge_url = (
        "https://img.shields.io/static/v1?"
        + "label=render%20on&logo=github&color=87ce3e&message=GitHub"
    )
    link = f"https://github.com/{repo_owner}/{repo_name}/blob/main/{absolute_path}"
    return f"[![preview notebook]({svg_badge_url})]({link})"


def _mybinder_badge_markdown(
    absolute_path: str, repo_name: str, repo_owner: str
) -> str:
    svg_badge_url = "https://mybinder.org/badge_logo.svg"
    link = (
        f"https://mybinder.org/v2/gh/{repo_owner}/{repo_name}.git/main?urlpath=lab/tree/"
        + f"{absolute_path}"
    )
    return f"[![launch on mybinder.org]({svg_badge_url})]({link})"


def _colab_badge_markdown(absolute_path: str, repo_name: str, repo_owner: str) -> str:
    svg_badge_url = "https://colab.research.google.com/assets/colab-badge.svg"
    link = (
        f"https://colab.research.google.com/github/{repo_owner}/{repo_name}/blob/main/"
        + f"{absolute_path}"
    )
    return f"[![launch on Colab]({svg_badge_url})]({link})"


def expected_badges_for(
    notebook_path: Path, repo_name: str, repo_owner: str
) -> List[str]:
    """
    Return the canonical badge lines expected for notebook_path.
    The notebook_path is used to build the URL path; we convert it to a
    repo-relative posix path (best-effort).
    """
    # Build a repo-relative path: try to strip cwd if notebook is inside repo
    try:
        rel = notebook_path.relative_to(Path.cwd())
    except Exception:
        rel = notebook_path
    absolute_path = rel.as_posix()
    return [
        _preview_badge_markdown(absolute_path, repo_name, repo_owner),
        _mybinder_badge_markdown(absolute_path, repo_name, repo_owner),
        _colab_badge_markdown(absolute_path, repo_name, repo_owner),
    ]


def read_notebook(path: Path) -> NotebookNode:
    with path.open(encoding="utf8") as fp:
        return nbformat.read(fp, nbformat.NO_CONVERT)


def write_notebook(path: Path, nb: NotebookNode) -> None:
    with path.open("w", encoding="utf8") as fp:
        nbformat.write(nb, fp)


def first_cell_lines(nb: NotebookNode) -> List[str]:
    """Return list of stripped lines from the first cell if it's markdown, else []"""
    if not nb.cells:
        return []
    first = nb.cells[0]
    if first.cell_type != "markdown":
        return []
    # split preserving order, strip each line
    return [ln.strip() for ln in str(first.source).splitlines() if ln.strip() != ""]


def badges_match(
    actual_lines: Iterable[str], expected_lines: Iterable[str]
) -> Tuple[bool, str]:
    """
    Check whether the expected badge lines are present in actual_lines.
    Tolerant: ignores order, strips whitespace.
    Returns (matches, message). Message empty on match else explains which badges missing.
    """
    actual_set = {ln.strip() for ln in actual_lines}
    expected_list = list(expected_lines)
    missing = [exp for exp in expected_list if exp.strip() not in actual_set]
    if not missing:
        return True, ""
    return False, f"Missing badges: {missing}"


def test_notebook_has_at_least_three_cells(notebook_filename: str) -> None:
    """checks if all notebooks have at least three cells"""
    nb = read_notebook(Path(notebook_filename))
    if len(nb.cells) < 3:
        raise ValueError("Notebook should have at least 3 cells")


def test_first_cell_contains_three_badges(
    notebook_filename: str, repo_name: str, repo_owner: str = REPO_OWNER_DEFAULT
) -> None:
    """
    checks if the notebook's first cell contains the three badges.
    Raises ValueError on failure.
    """
    nb = read_notebook(Path(notebook_filename))
    lines = first_cell_lines(nb)
    expected = expected_badges_for(Path(notebook_filename), repo_name, repo_owner)
    ok, msg = badges_match(lines, expected)
    if not ok:
        raise ValueError(msg)


def test_second_cell_is_a_markdown_cell(notebook_filename: str) -> None:
    """checks if all notebooks have their second cell as markdown"""
    nb = read_notebook(Path(notebook_filename))
    if len(nb.cells) < 2:
        raise ValueError("Notebook has no second cell")
    if nb.cells[1].cell_type != "markdown":
        raise ValueError("Second cell is not a markdown cell")


def fix_header_inplace(
    path: Path, repo_name: str, repo_owner: str = REPO_OWNER_DEFAULT
) -> None:
    """
    Replace the first cell with the canonical 3-badge header if the header is missing
    or malformed. If the notebook has no cells, a new markdown cell is inserted.
    """
    nb = read_notebook(path)
    expected = expected_badges_for(path, repo_name, repo_owner)
    # Build markdown with one badge per line
    new_first = {"cell_type": "markdown", "metadata": {}, "source": "\n".join(expected)}
    if not nb.cells:
        nb.cells.insert(0, nbformat.from_dict(new_first))
    else:
        nb.cells[0] = nbformat.from_dict(new_first)
    write_notebook(path, nb)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-name", required=True)
    parser.add_argument("--repo-owner", default=REPO_OWNER_DEFAULT)
    parser.add_argument(
        "--fix-header",
        action="store_true",
        help="If set, attempt to fix notebooks missing the header.",
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    args = parser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        path = Path(filename)
        try:
            test_notebook_has_at_least_three_cells(filename)
            test_first_cell_contains_three_badges(
                filename, args.repo_name, args.repo_owner
            )
            test_second_cell_is_a_markdown_cell(filename)
        except Exception as exc:
            print(f"{filename}: {exc}")
            retval = 1
            if args.fix_header:
                try:
                    fix_header_inplace(path, args.repo_name, args.repo_owner)
                    print(f"{filename}: header fixed")
                    retval = 0
                except Exception as fix_exc:
                    print(f"{filename}: failed to fix header: {fix_exc}")
                    retval = 2
    return retval


if __name__ == "__main__":
    raise SystemExit(main())
