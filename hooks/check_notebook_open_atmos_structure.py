#!/usr/bin/env python3
"""
Checks notebooks structure required in open-atmos projects.
Requirements:
- first cell contains three correct badges
- second cell is of type markdown
- third cell is Colab magick cell
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Iterable, List, Tuple, Optional

import nbformat
from nbformat import NotebookNode

from .open_atmos_colab_header import check_colab_header
from .utils import NotebookTestError

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
    svg_badge_url = (
        "https://img.shields.io/static/v1?"
        + "label=render%20on&logo=github&color=87ce3e&message=GitHub"
    )
    link = f"https://github.com/{repo_owner}/{repo_name}/blob/main/{relpath}"
    return f"[![preview notebook]({svg_badge_url})]({link})"


def mybinder_badge_markdown(relpath: str, repo_name: str, repo_owner: str) -> str:
    """Create markdown for the Binder badge."""
    svg_badge_url = "https://mybinder.org/badge_logo.svg"
    link = (
        f"https://mybinder.org/v2/gh/{repo_owner}/{repo_name}.git/main?urlpath=lab/tree/"
        + f"{relpath}"
    )
    return f"[![launch on mybinder.org]({svg_badge_url})]({link})"


def colab_badge_markdown(relpath: str, repo_name: str, repo_owner: str) -> str:
    """Create markdown for the Colab badge."""
    svg_badge_url = "https://colab.research.google.com/assets/colab-badge.svg"
    link = (
        f"https://colab.research.google.com/github/{repo_owner}/{repo_name}/blob/main/"
        + f"{relpath}"
    )
    return f"[![launch on Colab]({svg_badge_url})]({link})"


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


def read_notebook(path: Path) -> NotebookNode:
    """Read a Jupyter notebook without format conversion."""
    with path.open(encoding="utf8") as fp:
        return nbformat.read(fp, nbformat.NO_CONVERT)


def write_notebook(path: Path, nb: NotebookNode) -> None:
    """Write a Jupyter notebook to disk."""
    with path.open("w", encoding="utf8") as fp:
        nbformat.write(nb, fp)


def first_cell_lines(nb: NotebookNode) -> List[str]:
    """Return list of stripped lines from the first cell if it's markdown, else []"""
    if not nb.cells:
        return []
    first = nb.cells[0]
    if first.cell_type != "markdown":
        return []
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
    notebook_filename: str,
    repo_name: str,
    repo_owner: str = REPO_OWNER_DEFAULT,
    repo_root: Optional[Path] = None,
) -> None:
    """
    checks if the notebook's first cell contains the three badges.
    Raises ValueError on failure.

    The optional repo_root can be provided to control how the notebook path is
    converted into the remote URL. If None, the module will attempt to detect
    a git repo root and fall back to cwd().
    """
    nb = read_notebook(Path(notebook_filename))
    lines = first_cell_lines(nb)
    expected = expected_badges_for(
        Path(notebook_filename), repo_name, repo_owner, repo_root
    )
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


def build_parser() -> argparse.ArgumentParser:
    """Build parser for command line arguments."""
    p = argparse.ArgumentParser()
    p.add_argument("--repo-name", required=True)
    p.add_argument("--repo-owner", default=REPO_OWNER_DEFAULT)
    p.add_argument(
        "--fix-header",
        action="store_true",
        help="If set, attempt to fix notebooks missing the header.",
    )
    p.add_argument(
        "--no-git",
        action="store_true",
        help="Do not attempt to detect git repo root; use cwd()",
    )
    p.add_argument(
        "--repo-root", help="Explicit repository root to use when building URLs"
    )
    p.add_argument("--verbose", action="store_true", help="Enable debug logging")
    p.add_argument("filenames", nargs="*", help="Filenames to check.")
    return p


def configure_logging(verbose: bool) -> None:
    """Configure logging with --verbose flag"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def main(argv: Sequence[str] | None = None) -> int:
    """Test notebook structure:
    - first cell with 3 correct badges,
    - second cell is of type markdown (best if with notebook description),
    - third cell is a Colab magick cell.
    """
    args = build_parser().parse_args(argv)
    configure_logging(args.verbose)
    explicit_repo_root = Path(args.repo_root) if args.repo_root else None
    prefer_git = not args.no_git

    failed = False
    for filename in args.filenames:
        path = Path(filename)
        try:
            repo_root = resolve_repo_root(
                path,
                explicit_root=explicit_repo_root,
                prefer_git=prefer_git,
            )
            test_notebook_has_at_least_three_cells(filename)
            test_first_cell_contains_three_badges(
                filename, args.repo_name, args.repo_owner, repo_root
            )
            test_second_cell_is_a_markdown_cell(filename)
            check_colab_header(path, args.repo_name, args.fix_header, "")
            logger.info("%s: OK", path)

        except NotebookTestError as exc:
            logger.error("%s: %s", path, exc)
            failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
