# pylint: disable=missing-function-docstring
"""Tests for utils functions used across hooks."""

from hooks.utils import NotebookError


def test_error_format():
    err = NotebookError(
        path="test.ipynb",
        line=2,
        col=1,
        code="NB002",
        message="Something went wrong",
    )
    assert err.format() == "test.ipynb:2:1: NB002 Something went wrong"
