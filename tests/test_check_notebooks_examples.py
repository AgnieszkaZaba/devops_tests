# pylint: disable=missing-function-docstring
"""
Unit tests for hooks/check_notebooks.py: good and bad notebook examples.

These tests create in-memory notebooks with nbformat and call the
validation functions exported by hooks.check_notebooks to ensure they
accept valid notebooks and raise on invalid ones.
"""

import pytest
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell

from hooks import check_notebook_output as no
from hooks import check_notebooks as cn
from hooks import check_notebook_using_jupyter_utils as nuju


def test_good_notebook_passes_all_checks(tmp_path):
    nb = new_notebook(
        cells=[
            new_markdown_cell("Intro"),
            new_code_cell(
                source="x = 1\nprint(x)",
                execution_count=1,
                outputs=[{"output_type": "stream", "name": "stdout", "text": "1\n"}],
            ),
        ]
    )
    assert no.test_cell_contains_output(tmp_path, nb)
    assert no.test_no_errors_or_warnings_in_output(tmp_path, nb)
    assert cn.test_jetbrains_bug_py_66491(tmp_path, nb)
    assert nuju.test_show_plot_used_instead_of_matplotlib(tmp_path, nb)
    assert nuju.test_show_anim_used_instead_of_matplotlib(tmp_path, nb)


def test_cell_missing_execution_count_raises(tmp_path):
    nb = new_notebook(
        cells=[new_code_cell(source="print(1)", execution_count=None, outputs=[])]
    )
    errors = list(no.test_cell_contains_output(tmp_path, nb))
    assert len(errors) == 1
    assert errors[0].code == "NB001"


def test_stderr_output_raises(tmp_path):
    nb = new_notebook(
        cells=[
            new_code_cell(
                source="print('oops')",
                execution_count=1,
                outputs=[
                    {"output_type": "stream", "name": "stderr", "text": "Traceback..."}
                ],
            )
        ]
    )
    errors = list(no.test_no_errors_or_warnings_in_output(tmp_path, nb))
    assert len(errors) == 1
    assert errors[0].code == "NB002"


def test_using_matplotlib_show_without_show_plot_raises(tmp_path):
    nb = new_notebook(
        cells=[
            new_code_cell(
                source="import matplotlib.pyplot as plt\nplt.plot([1,2,3])\nplt.show()",
                execution_count=1,
                outputs=[],
            )
        ]
    )
    errors = list(nuju.test_show_plot_used_instead_of_matplotlib(tmp_path, nb))
    assert len(errors) == 1
    assert errors[0].code == "NB400"


def test_animation_without_show_anim_raises(tmp_path):
    nb = new_notebook(
        cells=[
            new_code_cell(
                source="from matplotlib import animation\nanimation.FuncAnimation(...)",
                execution_count=1,
                outputs=[],
            )
        ]
    )
    errors = list(nuju.test_show_anim_used_instead_of_matplotlib(tmp_path, nb))
    assert len(errors) == 1
    assert errors[0].code == "NB401"


def test_missing_execution_count_key_raises(tmp_path):
    nb = new_notebook(
        cells=[new_code_cell(source="1+1", execution_count=1, outputs=[])]
    )
    del nb.cells[0]["execution_count"]
    errors = list(cn.test_jetbrains_bug_py_66491(tmp_path, nb))
    assert len(errors) == 1
    assert errors[0].code == "NB000"
