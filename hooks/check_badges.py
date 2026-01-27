# notebook_checks.py
from __future__ import annotations

import argparse
from collections.abc import Sequence

import nbformat

from .colab_header import check_colab_header


def _preview_badge_markdown(absolute_path, repo_name):
    svg_badge_url = (
        "https://img.shields.io/static/v1?"
        + "label=render%20on&logo=github&color=87ce3e&message=GitHub"
    )
    link = f"https://github.com/open-atmos/{repo_name}/blob/main/" + f"{absolute_path}"
    return f"[![preview notebook]({svg_badge_url})]({link})"


def _mybinder_badge_markdown(absolute_path, repo_name):
    svg_badge_url = "https://mybinder.org/badge_logo.svg"
    link = (
        f"https://mybinder.org/v2/gh/open-atmos/{repo_name}.git/main?urlpath=lab/tree/"
        + f"{absolute_path}"
    )
    return f"[![launch on mybinder.org]({svg_badge_url})]({link})"


def _colab_badge_markdown(absolute_path, repo_name):
    svg_badge_url = "https://colab.research.google.com/assets/colab-badge.svg"
    link = (
        f"https://colab.research.google.com/github/open-atmos/{repo_name}/blob/main/"
        + f"{absolute_path}"
    )
    return f"[![launch on Colab]({svg_badge_url})]({link})"


def test_notebook_has_at_least_three_cells(notebook_filename):
    with open(notebook_filename, encoding="utf8") as fp:
        nb = nbformat.read(fp, nbformat.NO_CONVERT)
        if len(nb.cells) < 3:
            raise ValueError("Notebook should have at least 4 cells")


def test_first_cell_contains_three_badges(notebook_filename, repo_name):
    with open(notebook_filename, encoding="utf8") as fp:
        nb = nbformat.read(fp, nbformat.NO_CONVERT)

    if nb.cells[0].cell_type != "markdown":
        raise ValueError("First cell is not a markdown cell")

    lines = nb.cells[0].source.split("\n")
    if len(lines) != 3:
        raise ValueError("First cell does not contain exactly 3 lines (badges)")

    if lines[0] != _preview_badge_markdown(notebook_filename, repo_name):
        raise ValueError("First badge does not match Github preview badge")
    if lines[1] != _mybinder_badge_markdown(notebook_filename, repo_name):
        raise ValueError("Second badge does not match MyBinder badge")
    if lines[2] != _colab_badge_markdown(notebook_filename, repo_name):
        raise ValueError("Third badge does not match Colab badge")


def test_second_cell_is_a_markdown_cell(notebook_filename):
    with open(notebook_filename, encoding="utf8") as fp:
        nb = nbformat.read(fp, nbformat.NO_CONVERT)
    if nb.cells[1].cell_type != "markdown":
        raise ValueError("Second cell is not a markdown cell")


def print_hook_summary(reformatted_files, unchanged_files):
    for f in reformatted_files:
        print(f"\nreformatted {f}")

    total_ref = len(reformatted_files)
    total_unchanged = len(unchanged_files)
    if total_ref > 0:
        print("\nAll done! ✨ 🍰 ✨")
        print(
            f"{total_ref} file{'s' if total_ref != 1 else ''} reformatted, "
            f"{total_unchanged} file{'s' if total_unchanged != 1 else ''} left unchanged."
        )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-name")
    parser.add_argument("--fix-header", action="store_true")
    parser.add_argument("--pip-install-on-colab-version")
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    args = parser.parse_args(argv)

    failed_files = False
    reformatted_files = []
    unchanged_files = []

    for filename in args.filenames:
        try:
            modified = check_colab_header(
                filename,
                repo_name=args.repo_name,
                fix=args.fix_header,
                hook_version=args.pip_install_on_colab_version,
            )
            if modified:
                reformatted_files.append(str(filename))
            else:
                unchanged_files.append(str(filename))
        except ValueError as exc:
            print(f"[ERROR] {filename}: {exc}")
            failed_files = True

        try:
            test_notebook_has_at_least_three_cells(filename)
            test_first_cell_contains_three_badges(filename, repo_name=args.repo_name)
            test_second_cell_is_a_markdown_cell(filename)
        except ValueError as exc:
            print(f"[ERROR] {filename}: {exc}")
            failed_files = True

    print_hook_summary(reformatted_files, unchanged_files)
    return 1 if (reformatted_files or failed_files) else 0


if __name__ == "__main__":
    raise SystemExit(main())
