#!/usr/bin/env python3
# pylint: disable=duplicate-code #TODO #62
"""checks if notebook is executed and do not contain 'stderr"""

from __future__ import annotations

import argparse
from collections.abc import Sequence

import nbformat


class NotebookTestError(Exception):
    """Raised when a notebook validation test fails."""


def test_cell_contains_output(notebook):
    """checks if all notebook cells have an output present"""
    for cell_idx, cell in enumerate(notebook.cells):
        if cell.cell_type == "code" and cell.source != "":
            if cell.execution_count is None:
                raise ValueError(f"Cell {cell_idx} does not contain output")


def test_no_errors_or_warnings_in_output(notebook):
    """checks if all example Jupyter notebooks have clear std-err output
    (i.e., no errors or warnings) visible; except acceptable
    diagnostics from the joblib package"""
    for cell_idx, cell in enumerate(notebook.cells):
        if cell.cell_type == "code":
            for output in cell.outputs:
                ot = output.get("output_type")
                if ot == "error":
                    raise ValueError(
                        f"Cell [{cell_idx}] contain error or warning. \n\n"
                        f"Cell [{cell_idx}] output:\n{output}\n"
                    )
                if ot == "stream" and output.get("name") == "stderr":
                    out_text = output.get("text")
                    if out_text and not out_text.startswith("[Parallel(n_jobs="):
                        raise ValueError(f" Cell [{cell_idx}]: {out_text}")


def open_and_test_notebooks(argv, test_functions):
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    args = parser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        with open(filename, encoding="utf8") as notebook_file:
            notebook = nbformat.read(notebook_file, nbformat.NO_CONVERT)
            for func in test_functions:
                try:
                    func(notebook)
                except NotebookTestError as e:
                    print(f"{filename} : {e}")
                    retval = 1
    return retval


def main(argv: Sequence[str] | None = None) -> int:
    """test all notebooks"""
    return open_and_test_notebooks(
        argv=argv,
        test_functions=[
            test_cell_contains_output,
            test_no_errors_or_warnings_in_output,
        ],
    )


if __name__ == "__main__":
    raise SystemExit(main())
