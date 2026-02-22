"""Extract version from existing header and check if header is correct"""

from __future__ import annotations

import re
import nbformat
from pygments.styles.dracula import yellow

from .utils import cell_error

_PIP_INSTALL_RE = re.compile(
    r"pip_install_on_colab\(\s*"
    r"['\"](?P<examples>[^'\"]+)['\"]\s*,\s*"
    r"['\"](?P<main>[^'\"]+)['\"]\s*\)"
)


def extract_versions(cell_source: str, repo_name: str):
    """
    Extract version info from cell source
    Returns:
        (examples_version, main_version) or (None, None) if invalid.
    """
    text_found = _PIP_INSTALL_RE.search(cell_source)
    if not text_found:
        return None, None

    examples_pkg = text_found.group("examples")
    main_pkg = text_found.group("main")

    if not main_pkg.startswith(repo_name) or not examples_pkg.startswith(
        f"{repo_name}-examples"
    ):
        return None, None
    print(examples_pkg, main_pkg)
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


def build_header(repo_name: str, version: str) -> str:
    """required header pattern in open-atmos notebooks"""
    return f"""import os, sys
os.environ['NUMBA_THREADING_LAYER'] = 'workqueue'  # PySDM & PyMPDATA don't work with TBB; OpenMP has extra dependencies on macOS
if 'google.colab' in sys.modules:
    !pip --quiet install open-atmos-jupyter-utils
    from open_atmos_jupyter_utils import pip_install_on_colab
    pip_install_on_colab('{repo_name}-examples{version}', '{repo_name}{version}')"""


HEADER_REQUIRED_PATTERNS = [
    "google.colab",
    "open-atmos-jupyter-utils",
    "pip_install_on_colab",
]


def looks_like_header(cell_source: str) -> bool:
    """check if the cell source looks like required header"""
    return all(pat in cell_source for pat in HEADER_REQUIRED_PATTERNS)


def check_colab_header(nb_path, nb, *, repo_name, fix, hook_version):
    """check if colab header is correct"""
    header_index = None
    for idx, cell in enumerate(nb.cells):
        if cell.cell_type == "code" and looks_like_header(cell.source):
            header_index = idx
            break

    if header_index is None:
        final_version = resolve_version(None, hook_version)
        header_source = build_header(repo_name, final_version)
        nb.cells.insert(2, nbformat.v4.new_code_cell(header_source))
        nbformat.write(nb, nb_path)
        return

    header_cell = nb.cells[header_index]
    examples_version, main_version = extract_versions(header_cell.source, repo_name)

    if examples_version != main_version:
        yield cell_error(
            nb_path,
            header_index,
            "NB301",
            f"\nVersion mismatch in header: {examples_version!r} != {main_version!r}",
        )

    final_version = resolve_version(main_version, hook_version)
    correct_header = build_header(repo_name, final_version)

    modified = False
    if header_cell.source != correct_header:
        if not fix:
            yield cell_error(
                notebook_path,
                header_index,
                "NB302",
                f"Incorrect Colab cell, expected header:\n---\n{correct_header}\n---",
            )
        else:
            header_cell.source = correct_header
            modified = True

    if header_index != 2:
        if not fix:
            yield cell_error(
                nb_path,
                header_index,
                code="NB303",
                message="Colab header in wrong position. Expected cell index: 2.",
            )
        else:
            nb.cells.insert(2, nb.cells.pop(header_index))
            modified = True

    if modified:
        nbformat.write(nb, nb_path)
    return modified
