"""
Utils functions to reuse in different parts of the codebase
"""

import os
import pathlib

from git.cmd import Git


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


def relative_path(absolute_path):
    """returns a path relative to the repo base (converting backslashes to slashes on Windows)"""
    relpath = os.path.relpath(absolute_path, repo_path().absolute())
    posixpath_to_make_it_usable_in_urls_even_on_windows = pathlib.Path(
        relpath
    ).as_posix()
    return posixpath_to_make_it_usable_in_urls_even_on_windows


def repo_path():
    """returns absolute path to the repo base (ignoring .git location if in a submodule)"""
    path = pathlib.Path(__file__)
    while not (path.is_dir() and Git(path).rev_parse("--git-dir") == ".git"):
        path = path.parent
    return path
