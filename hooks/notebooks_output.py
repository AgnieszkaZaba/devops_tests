#!/usr/bin/env python3
"""checks if notebook is executed and do not contain 'stderr"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from .utils import open_and_test_notebooks, cell_error


def test_cell_contains_output(nb_path, nb):
    """checks if all notebook cells have an output present"""
    for cell_idx, cell in enumerate(nb.cells):
        if cell.cell_type == "code" and cell.source != "":
            if cell.execution_count is None:
                yield cell_error(
                    nb_path,
                    cell_idx,
                    code="NB001",
                    message="Cell does not contain output",
                )


def test_no_errors_or_warnings_in_output(nb_path, nb):
    """checks if all example Jupyter notebooks have clear std-err output
    (i.e., no errors or warnings) visible; except acceptable
    diagnostics from the joblib package"""
    for cell_idx, cell in enumerate(nb.cells):
        if cell.cell_type == "code":
            for output in cell.outputs:
                ot = output.get("output_type")
                is_error = ot == "error"
                is_stderr = (
                    ot == "stream"
                    and output.get("name") == "stderr"
                    and (text := output.get("text"))
                    and not text.startswith("[Parallel(n_jobs=")
                )

                if is_error or is_stderr:
                    yield cell_error(
                        nb_path,
                        cell_idx,
                        code="NB002",
                        message=(
                            "Cell contains execution error or warning.\n\n"
                            f"Cell output:\n{output}\n"
                        ),
                    )


def main(argv: Sequence[str] | None = None) -> int:
    """Test all notebooks"""
    p = argparse.ArgumentParser()
    p.add_argument("filenames", nargs="*", help="Filenames to check.")
    args = p.parse_args(argv)

    return open_and_test_notebooks(
        args,
        test_functions=[
            test_cell_contains_output,
            test_no_errors_or_warnings_in_output,
        ],
    )


if __name__ == "__main__":
    raise SystemExit(main())
