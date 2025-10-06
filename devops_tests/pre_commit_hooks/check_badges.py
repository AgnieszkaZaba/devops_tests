from __future__ import annotations

import argparse
from collections.abc import Sequence

import nbformat

from .utils import relative_path, repo_path

COLAB_HEADER = f"""import sys
if 'google.colab' in sys.modules:
    !pip --quiet install open-atmos-jupyter-utils
    from open_atmos_jupyter_utils import pip_install_on_colab
    pip_install_on_colab('{repo_path().name}-examples')"""


def test_at_least_three_cells(notebook):
    if len(notebook.cells) < 3:
        raise Exception(f"Expected at least 3 cells, got {len(notebook.cells)}")


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


def test_first_cell_contains_three_badges(notebook_filename, notebook_content):
    """checks if all notebooks feature GitHub preview, mybinder and Colab badges
    (in the first cell)"""

    asserts = ""
    if notebook_content.cells[0].cell_type != "markdown":
        asserts += "First cell is not a markdown\n"

    lines = notebook_content.cells[0].source.split("\n")
    if len(lines) != 3:
        raise Exception(f"Expected 3 lines, got {len(lines)}")

    preview_badge = _preview_badge_markdown(notebook_filename)
    mybinder_badge = _mybinder_badge_markdown(notebook_filename)
    colab_badge = _colab_badge_markdown(notebook_filename)

    if lines[0] != preview_badge:
        asserts += f"First badge should be {preview_badge}\n"
    if lines[1] != mybinder_badge:
        asserts += f"Second badge should be {mybinder_badge}\n"
    if lines[2] != colab_badge:
        asserts += f"Third badge should be {colab_badge}\n"

    if asserts:
        raise Exception(asserts)


def test_second_cell_is_a_markdown_cell(notebook):
    """checks if all notebooks have their second cell with some markdown
    (hopefully clarifying what the example is about)"""
    cell_type = notebook.cells[0].cell_type
    if cell_type != "markdown":
        raise Exception(f"Expected a markdown cell, got {cell_type}")


def test_third_cell_contains_colab_header(notebook):
    """checks if all notebooks feature a Colab-magic cell"""
    cell_type = notebook.cells[2].cell_type
    cell_source = notebook.cells[2].source
    if cell_type != "code" or cell_source != COLAB_HEADER:
        raise Exception(
            f"Expected a code sell with Colab-magic, got cell type: {cell_type},\n cell source: {notebook.cells[2].source}"
        )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    args = parser.parse_args(argv)

    retval = 0
    test_functions = [
        test_first_cell_contains_three_badges,
        test_second_cell_is_a_markdown_cell,
        test_third_cell_contains_colab_header,
    ]
    for filename in args.filenames:
        with open(filename, encoding="utf8") as notebook_file:
            notebook = nbformat.read(notebook_file, nbformat.NO_CONVERT)
            try:
                test_at_least_three_cells(notebook)
            except Exception as e:
                print(f"{filename} : {e}")
                retval = 1

            for func in test_functions:
                try:
                    if func == test_first_cell_contains_three_badges:
                        func(filename, notebook)
                    else:
                        func(notebook)
                except Exception as e:
                    print(f"{filename} : {e}")
                    retval = 1
    return retval


if __name__ == "__main__":
    raise SystemExit(main())
