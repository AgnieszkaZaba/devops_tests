# devops_tests
pytest test routines asserting for GitHub issue-linked TO-DO labelling in the code, README link consistency and some Jupyter notebook sanity checks

## Pre-commit hooks:
### `check_notebook_open_atmos_structure`
Check Jupyter notebooks structure default for `open-atmos` projects.
Required:
- three badges in the first cell:

[![preview notebook](https://img.shields.io/static/v1?label=render%20on&logo=github&color=87ce3e&message=GitHub)](https://github.com/open-atmos/devops_tests/blob/main/tests/examples/good.ipynb)
[![launch on mybinder.org](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/open-atmos/devops_tests.git/main?urlpath=lab/tree/tests/examples/good.ipynb)
[![launch on Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/open-atmos/devops_tests/blob/main/tests/examples/good.ipynb)

- markdown type of the second cell
- Colab-header in the third cell
```
import os, sys
os.environ['NUMBA_THREADING_LAYER'] = 'workqueue'  # PySDM & PyMPDATA don't work with TBB; OpenMP has extra dependencies on macOS
if 'google.colab' in sys.modules:
    !pip --quiet install open-atmos-jupyter-utils
    from open_atmos_jupyter_utils import pip_install_on_colab
    pip_install_on_colab('devops_tests-examples', 'devops_tests')
```

## Error and warning labeling
### **0xx -> Execution problems**
- NB000 missing execution count
- NB001 empty execution
- NB002 cell contains error

### **1xx -> Badges problems**
- NB100 wrong GitHub preview badge
- NB101 wrong mybinder badge
- NB102 wrong Colab badge

### **2xx -> Markdown problems**
- NB200 markdown cell missing

### **3xx -> Colab header problems**
- NB300 header missing
- NB301 version mismatch
- NB302 header in wrong position
