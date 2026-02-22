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

## 0xx -> Execution Problems

These errors relate to notebook execution state and structural integrity.

- **NB000** – Missing execution count
- **NB001** – Empty execution
- **NB002** – Cell contains execution error
- **NB003** – Insufficient number of cells (minimum required not met)
- **NB004** – Invalid or missing required content in first cell

---

## 1xx -> Badge Problems

These errors relate to required badges in the first notebook cell.

- **NB100** - Incorrect GitHub preview badge
- **NB101** – Incorrect MyBinder badge
- **NB102** – Incorrect Colab badge

---

## 2xx -> Markdown Problems

These errors relate to required markdown structure in the second notebook cell.

- **NB200** – Required markdown cell missing
- **NB201** – Invalid markdown structure
- **NB202** – Required markdown section missing

---

## 3xx -> Colab Header Problems

These errors relate to the required Colab setup header.

- **NB300** – Header missing
- **NB301** – Header version mismatch
- **NB302** – Invalid header content
- **NB303** – Header in incorrect position

---

## 4xx -> `open-atmos-jupyter-utils` Problems

These errors relate to the usage of `show_anim()` and `show_plot()`
functions from `open-atmos-jupyter-utils` package required when matplotlib is used.

- **NB400** - show_plot not used
- **NB401** - show_anim not used
