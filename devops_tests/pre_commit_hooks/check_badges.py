from __future__ import annotations

import argparse
from collections.abc import Sequence

import nbformat
from utils import relative_path, repo_path

COLAB_HEADER = f"""import sys
if 'google.colab' in sys.modules:
    !pip --quiet install open-atmos-jupyter-utils
    from open_atmos_jupyter_utils import pip_install_on_colab
    pip_install_on_colab('{repo_path().name}-examples')"""


def _preview_badge_markdown(absolute_path):
    svg_badge_url = (
        "https://img.shields.io/static/v1?"
        + "label=render%20on&logo=github&color=87ce3e&message=GitHub"
    )
    link = (
        f"https://github.com/open-atmos/{repo_path().name}/blob/main/"
        + f"{relative_path(absolute_path)}"
    )
    return f"[![preview notebook]({svg_badge_url})]({link})"


def _mybinder_badge_markdown(absolute_path):
    svg_badge_url = "https://mybinder.org/badge_logo.svg"
    link = (
        f"https://mybinder.org/v2/gh/open-atmos/{repo_path().name}.git/main?urlpath=lab/tree/"
        + f"{relative_path(absolute_path)}"
    )
    return f"[![launch on mybinder.org]({svg_badge_url})]({link})"


def _colab_badge_markdown(absolute_path):
    svg_badge_url = "https://colab.research.google.com/assets/colab-badge.svg"
    link = (
        f"https://colab.research.google.com/github/open-atmos/{repo_path().name}/blob/main/"
        + f"{relative_path(absolute_path)}"
    )
    return f"[![launch on Colab]({svg_badge_url})]({link})"


def test_first_cell_contains_three_badges(notebook_filename):
    """checks if all notebooks feature Github preview, mybinder and Colab badges
    (in the first cell)"""
    with open(notebook_filename, encoding="utf8") as fp:
        nb = nbformat.read(fp, nbformat.NO_CONVERT)
        assert len(nb.cells) > 0
        assert nb.cells[0].cell_type == "markdown"
        lines = nb.cells[0].source.split("\n")
        assert len(lines) == 3
        assert lines[0] == _preview_badge_markdown(notebook_filename)
        assert lines[1] == _mybinder_badge_markdown(notebook_filename)
        assert lines[2] == _colab_badge_markdown(notebook_filename)


def test_second_cell_is_a_markdown_cell(notebook_filename):
    """checks if all notebooks have their second cell with some markdown
    (hopefully clarifying what the example is about)"""
    with open(notebook_filename, encoding="utf8") as fp:
        nb = nbformat.read(fp, nbformat.NO_CONVERT)
        assert len(nb.cells) > 1
        assert nb.cells[1].cell_type == "markdown"


def test_third_cell_contains_colab_header(notebook_filename):
    """checks if all notebooks feature a Colab-magic cell"""
    with open(notebook_filename, encoding="utf8") as fp:
        nb = nbformat.read(fp, nbformat.NO_CONVERT)
        assert len(nb.cells) > 2
        assert nb.cells[2].cell_type == "code"
        assert nb.cells[2].source == COLAB_HEADER


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    args = parser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        try:
            test_first_cell_contains_three_badges(filename)
            test_second_cell_is_a_markdown_cell(filename)
            test_third_cell_contains_colab_header(filename)
        except ValueError as exc:
            retval = 1
    return retval


if __name__ == "__main__":
    raise SystemExit(main())
