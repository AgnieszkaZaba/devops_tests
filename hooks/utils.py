"""
Utils functions to reuse in different parts of the codebase
"""

import os
import pathlib
from pathlib import Path
from git import Git

from dataclasses import dataclass
from typing import Callable, Iterable, Any
import nbformat


@dataclass
class NotebookError:
    path: str
    line: int
    col: int
    code: str
    message: str

    def format(self) -> str:
        return f"{self.path}:{self.line}:{self.col}: {self.code} {self.message}"


def cell_error(path, cell_idx, code, message):
    return NotebookError(
        path=path,
        line=cell_idx + 1,
        col=1,
        code=code,
        message=message,
    )


def find_files(path_to_folder_from_project_root=".", file_extension=None):
    """
    Returns all files in a current git repo.
    The list of returned files may be filtered with `file_extension` param.
    """
    all_files = [
        path
        for path in Git(
            Git(path_to_folder_from_project_root).rev_parse("--show-toplevel")
        )
        .ls_files()
        .split("\n")
        if os.path.isfile(path)
    ]
    if file_extension is not None:
        return list(filter(lambda path: path.endswith(file_extension), all_files))

    return all_files


def repo_path():
    """returns absolute path to the repo base (ignoring .git location if in a submodule)"""
    path = pathlib.Path(__file__)
    while not (path.is_dir() and Git(path).rev_parse("--git-dir") == ".git"):
        path = path.parent
    return path


def open_and_test_notebooks(
    args,
    test_functions,
):
    """
    Run notebook tests on a list of filenames using generator-based hooks.

    Each test function should accept three arguments:
        nb_path: Path,
        nb: nbformat.NotebookNode
    and yield NotebookError objects. Extra args must be handled by wrappers.
    """
    all_errors = []

    for filename in args.filenames:
        notebook_path = Path(filename)
        try:
            with notebook_path.open(encoding="utf8") as f:
                notebook = nbformat.read(f, nbformat.NO_CONVERT)
        except Exception as exc:
            all_errors.append(
                cell_error(
                    filename,
                    0,
                    code="NB000",
                    message=f"Failed to read notebook: {exc}",
                )
            )
            continue

        for test_func in test_functions:
            try:
                for error in test_func(nb_path=notebook_path, nb=notebook):
                    all_errors.append(error)
            except Exception as exc:
                all_errors.append(
                    cell_error(
                        filename,
                        0,
                        code="NBXXX",
                        message=f"Exception in test {test_func.__name__}: {exc}",
                    )
                )

    for error in all_errors:
        print(error.format())

    return 1 if all_errors else 0
