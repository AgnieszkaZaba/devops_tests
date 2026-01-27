# colab_header.py
from __future__ import annotations

import re
import nbformat

_PIP_INSTALL_RE = re.compile(
    r"pip_install_on_colab\(\s*"
    r"['\"](?P<examples>[^'\"]+)['\"]\s*,\s*"
    r"['\"](?P<main>[^'\"]+)['\"]\s*\)"
)

HEADER_KEY_PATTERNS = [
    "install open-atmos-jupyter-utils",
    "google.colab",
    "pip_install_on_colab",
]


def extract_versions(cell_source: str, repo_name: str):
    """
    Extract version info from cell source
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


def build_header(repo_name: str, version: str) -> str:
    return f"""import os, sys
os.environ['NUMBA_THREADING_LAYER'] = 'workqueue'  # PySDM & PyMPDATA don't work with TBB; OpenMP has extra dependencies on macOS
if 'google.colab' in sys.modules:
    !pip --quiet install open-atmos-jupyter-utils
    from open_atmos_jupyter_utils import pip_install_on_colab
    pip_install_on_colab('{repo_name}-examples{version}', '{repo_name}{version}')"""


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

    # If header doesn't exist, create it
    if header_index is None:
        final_version = resolve_version(None, hook_version)
        header_source = build_header(repo_name, final_version)
        nb.cells.insert(2, nbformat.v4.new_code_cell(header_source))
        nbformat.write(nb, notebook_path)
        return True

    # If header exists, validate and optionally fix
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
