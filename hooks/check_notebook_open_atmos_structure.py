#!/usr/bin/env python3
"""
Checks notebook structure required in open-atmos projects.
Requirements:
- first cell contains three correct badges
- second cell is of type markdown
- third cell is Colab magick cell
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence, Iterable
from pathlib import Path
from typing import Optional, List, Tuple

import nbformat
from nbformat import NotebookNode

from .utils import cell_error, open_and_test_notebooks
from .open_atmos_colab_header import check_colab_header

REPO_OWNER_DEFAULT = "open-atmos"

logger = logging.getLogger(__name__)


def resolve_repo_root(
    start_path: Path,
    *,
    explicit_root: Path | None,
    prefer_git: bool,
) -> Path:
    """Resolve the repository root for the given path."""
    if explicit_root is not None:
        return explicit_root
    if prefer_git:
        try:
            # Import locally so the module doesn't hard-depend on GitPython at import time
            from git import Repo  # pylint: disable=import-outside-toplevel

            try:
                repo = Repo(start_path, search_parent_directories=True)
                if repo.working_tree_dir:
                    root = Path(repo.working_tree_dir)
                    logger.debug("Discovered git repository root: %s", root)
                    return root
            except Exception as exc:  # pylint: disable=broad-exception-caught
                repo = None
                logger.debug("Git repo detection failed for %s: %s", start_path, exc)
        except ImportError as exc:
            logger.debug("GitPython not available or import failed: %s", exc)

    cwd = Path.cwd()
    logger.debug("Using current working directory as repo root: %s", cwd)
    return cwd


def relative_path(absolute_path, repo_root):
    """Return the path relative to the repository root."""
    absolute_path = Path(absolute_path).resolve()
    repo_root = Path(repo_root).resolve()

    try:
        relpath = absolute_path.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(
            f"{absolute_path} is not inside repo root {repo_root}"
        ) from exc

    return relpath.as_posix()


def preview_badge_markdown(relpath: str, repo_name: str, repo_owner: str) -> str:
    """Create markdown for the GitHub-preview badge."""
    url = (
        "https://img.shields.io/static/v1?"
        + "label=render%20on&logo=github&color=87ce3e&message=GitHub"
    )
    link = f"https://github.com/{repo_owner}/{repo_name}/blob/main/{relpath}"
    return f"[![preview notebook]({url})]({link})"


def mybinder_badge_markdown(relpath: str, repo_name: str, repo_owner: str) -> str:
    """Create markdown for the Binder badge."""
    url = "https://mybinder.org/badge_logo.svg"
    link = (
        f"https://mybinder.org/v2/gh/{repo_owner}/{repo_name}.git/main?urlpath=lab/tree/"
        + f"{relpath}"
    )
    return f"[![launch on mybinder.org]({url})]({link})"


def colab_badge_markdown(relpath: str, repo_name: str, repo_owner: str) -> str:
    """Create markdown for the Colab badge."""
    url = "https://colab.research.google.com/assets/colab-badge.svg"
    link = (
        f"https://colab.research.google.com/github/{repo_owner}/{repo_name}/blob/main/"
        + f"{relpath}"
    )
    return f"[![launch on Colab]({url})]({link})"


def expected_badges_for(
    notebook_path: Path,
    repo_name: str,
    repo_owner: str,
    repo_root: Optional[Path],
) -> List[str]:
    """
    Return the canonical badge lines expected for notebook_path.
    If repo_root is provided, attempt to build a relative path from it; otherwise
    find repository root automatically (using find_repo_root).
    """
    relpath = relative_path(notebook_path, repo_root)
    args = (relpath, repo_name, repo_owner)
    return [
        preview_badge_markdown(*args),
        mybinder_badge_markdown(*args),
        colab_badge_markdown(*args),
    ]


def first_cell_lines(nb: NotebookNode) -> List[str]:
    if not nb.cells or nb.cells[0].cell_type != "markdown":
        return []
    return [ln.strip() for ln in str(nb.cells[0].source).splitlines() if ln.strip()]


def badges_match(
    actual_lines: Iterable[str], expected_lines: Iterable[str]
) -> Tuple[bool, str]:
    actual_set = {ln.strip() for ln in actual_lines}
    missing = [exp for exp in expected_lines if exp.strip() not in actual_set]
    if not missing:
        return True, ""
    return False, f"Missing badges: {missing}"


def test_notebook_has_at_least_three_cells(nb_path, nb) -> Iterable:
    """checks if all notebooks have at least three cells"""
    if len(nb.cells) < 3:
        yield cell_error(
            nb_path,
            0,
            code="NB003",
            message="Insufficient number of cells (minimum required is 3).",
        )


def test_first_cell_contains_three_badges(
    nb_path,
    nb,
    *,
    repo_name,
    repo_owner,
    repo_root,
):
    lines = first_cell_lines(nb)
    expected = expected_badges_for(nb_path, repo_name, repo_owner, repo_root)
    ok, msg = badges_match(lines, expected)
    if not ok:
        yield cell_error(notebook_filename, 0, code="NB004", message=msg)


def test_second_cell_is_a_markdown_cell(nb_path, nb):
    if len(nb.cells) < 2:
        yield cell_error(
            nb_path, 1, code="NB200", message="Notebook has no second cell."
        )
    elif nb.cells[1].cell_type != "markdown":
        yield cell_error(
            nb_path,
            1,
            code="NB201",
            message="Second cell is not a markdown cell",
        )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-name", required=True)
    p.add_argument("--repo-owner", default=REPO_OWNER_DEFAULT)
    p.add_argument(
        "--fix-header",
        action="store_true",
        help="Attempt to fix notebooks missing header",
    )
    p.add_argument(
        "--no-git", action="store_true", help="Do not detect git repo root, use cwd()"
    )
    p.add_argument("--repo-root", help="Explicit repository root path")
    p.add_argument("--verbose", action="store_true", help="Enable debug logging")
    p.add_argument("filenames", nargs="*", help="Notebooks to check")
    return p


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging(args.verbose)

    explicit_repo_root = Path(args.repo_root) if args.repo_root else None
    prefer_git = not args.no_git

    repo_root = None
    if explicit_repo_root or prefer_git:
        if args.filenames:
            repo_root = resolve_repo_root(
                Path(args.filenames[0]),
                explicit_root=explicit_repo_root,
                prefer_git=prefer_git,
            )

    def wrap_first_cell_badges(nb_path, nb):
        yield from test_first_cell_contains_three_badges(
            nb_path,
            nb,
            repo_name=args.repo_name,
            repo_owner=args.repo_owner,
            repo_root=repo_root,
        )

    def wrap_colab_header(nb_path, nb):
        yield from check_colab_header(
            nb_path,
            nb,
            repo_name=args.repo_name,
            fix=args.fix_header,
            hook_version=None,
        )

    return open_and_test_notebooks(
        args,
        test_functions=[
            test_notebook_has_at_least_three_cells,
            wrap_first_cell_badges,
            test_second_cell_is_a_markdown_cell,
            wrap_colab_header,
        ],
    )


if __name__ == "__main__":
    raise SystemExit(main())
