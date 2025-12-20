#!/usr/bin/env python3

from __future__ import annotations


def test_cell_contains_output(notebook):
    """checks if all notebook cells have an output present"""
    for cell in notebook.cells:
        if cell.cell_type == "code" and cell.source != "":
            if cell.execution_count is None:
                raise Exception("Cell does not contain output!")


def test_no_errors_or_warnings_in_output(notebook):
    """checks if all example Jupyter notebooks have clear std-err output
    (i.e., no errors or warnings) visible; except acceptable
    diagnostics from the joblib package"""
    for cell in notebook.cells:
        if cell.cell_type == "code":
            for output in cell.outputs:
                if "name" in output and output["name"] == "stderr":
                    if not output["text"].startswith("[Parallel(n_jobs="):
                        raise Exception(output["text"])


def main(argv: Sequence[str] | None = None) -> int:
    """test all notebooks"""
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    args = parser.parse_args(argv)

    retval = 0
    test_functions = [
        test_cell_contains_output,
        test_no_errors_or_warnings_in_output,
    ]
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


if __name__ == "__main__":
    raise SystemExit(main())
