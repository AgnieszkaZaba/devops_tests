import sys

if sys.platform == "win32" and sys.version_info[:2] >= (3, 7):
    import asyncio

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import gc
import os
import warnings

import nbformat
import pytest

from .utils import find_files

with warnings.catch_warnings():
    warnings.filterwarnings("ignore")
    from nbconvert.preprocessors import ExecutePreprocessor


@pytest.fixture(
    params=find_files(file_extension=".ipynb"),
    name="notebook_filename",
)
def _notebook_filename(request):
    return request.param


def test_run_notebooks(notebook_filename, tmp_path):
    """executes a given notebook"""
    os.environ["JUPYTER_PLATFORM_DIRS"] = "1"

    executor = ExecutePreprocessor(timeout=15 * 60, kernel_name="python3")

    with open(notebook_filename, encoding="utf8") as notebook_file:
        # https://github.com/pytest-dev/pytest-asyncio/issues/212
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="There is no current event loop")
            executor.preprocess(
                nbformat.read(notebook_file, as_version=4),
                {"metadata": {"path": tmp_path}},
            )

    # so that nbconvert perplexities are reported here, and not at some dtor test later on
    gc.collect()
