#!/usr/bin/env python3
# pylint: disable=missing-function-docstring
"""
Checks whether notebooks contain badges and ensures a consistent Colab header.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import re

import nbformat

_PIP_INSTALL_RE = re.compile(
    r"pip_install_on_colab\(\s*"
    r"['\"](?P<examples>[^'\"]+)['\"]\s*,\s*"
    r"['\"](?P<main>[^'\"]+)['\"]\s*\)"
)


def extract_versions(cell_source: str, repo_name: str):
    """
    Extract versions from both arguments:
      pip_install_on_colab('repo-examples{v}', 'repo{v}')

    Returns:
        (examples_version, main_version) or (None, None) if invalid.
    """
    m = _PIP_INSTALL_RE.search(cell_source)
    if not m:
        return None, None

    examples_pkg = m.group("examples")
    main_pkg = m.group("main")

    if not examples_pkg.startswith(f"{repo_name}-examples") or not main_pkg.startswith(
        repo_name
    ):
        return None, None

    return examples_pkg[len(f"{repo_name}-examples") :], main_pkg[len(repo_name) :]


def resolve_version(existing: str | None, hook_version: str | None) -> str:
    """
    Precedence:
      1. Version in notebook
      2. Hook version
      3. No version
    """
    if existing:
        return existing
    if hook_version:
        return hook_version
    return ""


HEADER_KEY_PATTERNS = [
    "install open-atmos-jupyter-utils",
    "google.colab",
    "pip_install_on_colab",
]


def build_header(repo_name: str, version: str) -> str:
    return f"""import os, sys
os.environ['NUMBA_THREADING_LAYER'] = 'workqueue'
if 'google.colab' in sys.modules:
    !pip --quiet install open-atmos-jupyter-utils
    from open_atmos_jupyter_utils import pip_install_on_colab
    pip_install_on_colab('{repo_name}-examples{version}', '{repo_name}{version}')
"""


def looks_like_header(cell_source: str) -> bool:
    return all(pat in cell_source for pat in HEADER_KEY_PATTERNS)


def check_colab_header(notebook_path, repo_name, fix, hook_version):
    nb = nbformat.read(notebook_path, as_version=nbformat.NO_CONVERT)

    if len(nb.cells) < 3:
        raise ValueError("Notebook should have at least 3 cells")

    # Find existing header if present
    header_index = None
    for idx, cell in enumerate(nb.cells):
        if cell.cell_type == "code" and looks_like_header(cell.source):
            header_index = idx
            break

    # Build final header
    if header_index is None:
        final_version = resolve_version(None, hook_version)
        header_source = build_header(repo_name, final_version)
        nb.cells.insert(2, nbformat.v4.new_code_cell(header_source))
        nbformat.write(nb, notebook_path)
        return True

    header_cell = nb.cells[header_index]
    examples_version, main_version = extract_versions(header_cell.source, repo_name)

    if examples_version is None or main_version is None:
        raise ValueError("Colab header is malformed")

    if examples_version != main_version:
        raise ValueError(
            f"Version mismatch in header: {examples_version!r} != {main_version!r}"
        )

    final_version = resolve_version(main_version, hook_version)
    header_source = build_header(repo_name, final_version)

    modified = False

    if header_cell.source != header_source:
        if not fix:
            raise ValueError("Colab header is incorrect")
        header_cell.source = header_source
        modified = True

    if header_index != 2:
        nb.cells.insert(2, nb.cells.pop(header_index))
        modified = True

    if modified:
        nbformat.write(nb, notebook_path)

    return modified


# -------------------------------------------------------------------
# Badge checks
# -------------------------------------------------------------------


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
