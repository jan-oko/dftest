# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What dftest is

dftest is a pytest-inspired Python library for auditing data quality in pandas DataFrames. Users write test predicates that run over a DataFrame, and dftest produces a coverage report showing which columns were tested, which rows failed, and validity rates. Full user-facing documentation lives in `README.ipynb`.

## Commands

```bash
# Install in editable mode (development)
pip install -e .

# Run the example suite against MetObjects.csv (must run from tests/: tests.conf refers to the `test_funcs` module by import path)
cd tests && python main.py

# Run the synthetic-data example
cd tests && python notebook.py

# CLI (installed from bin/dftest)
dftest --dataframe tests/College.csv --files tests/test_funcs.py -p
dftest --dataframe data.csv --files tests.py -d results.dill   # dump results with dill
dftest --results results.dill -c SomeColumn -g summary validity  # reload a dump, view one column
```

There is no automated test suite. `tests/` holds example scripts and sample data, not pytest tests. `tests/MetObjects.csv` is a Git LFS pointer.

Don't confuse `tests/` with `dftest/tests.py`, the library's built-in test factories (`in_range_test`, `match_test`, `in_list_test`, `simple_type_test`, `non_equal_test`, `dftest_not_null`).

`dftest.options` resolves to the `options()` decorator, not the submodule (`__init__.py` re-exports it under the same name). Use `from dftest.options import ...` to reach the module.

## Architecture

### Core data flow

1. User creates a `DFTests(df)` wrapper around a pandas DataFrame
2. Tests are added via `add_concrete_test()`, `add_generic_test()`, `load_files()`, or `load_config()`
3. `DFTests.run()` executes each `Test` over the DataFrame and returns a `DFTestResults`
4. Results can be printed (`print()`), serialized (`to_json()`), or graphed (matplotlib/seaborn, shown via `results.plt.show()`)

### Two test types

**Concrete test**: `def my_test(row)` tests a specific row. dftest autodetects which columns it accesses via `sys.settrace` (see `Test.test()` in `Test.py`).

**Generic test**: `def my_test(column, df)` is a template applied to multiple columns. `add_generic_test()` expands it into one concrete test per column using `functools.partial`.

Everywhere (`load_files`, `load_config`), concrete and generic are told apart only by `func.__code__.co_argcount` (1 or 2).

### Test return types

The return value of a test predicate determines what kind of result is produced (`Test.run()` in `Test.py`):
- `bool` → `BooleanTestResult` (whole-dataframe pass/fail)
- `Number` → `NumberTestResult` (count of valid rows)
- `list[int]` or `np.ndarray[bool]` → `IndexTestResult` (indices of invalid rows)

### Result hierarchy

All result classes live in `DFTests.py` alongside `DFTests`:
- `DFTestResults`: full run results. Holds all `TestResult`s and generates summary graphs
- `ColumnResults`: view of results filtered to one column, created lazily by `DFTestResults.get_column_results(column)`
- `RowResults`: view of results filtered to one row index

### Test discovery (via `load_files`)

Functions are detected by the regex `^[Dd][Ff][_]?[Tt]est[A-Z_]`, so names like `dfTestFoo`, `DFTest_bar`, `df_TestBaz` match. Each file is imported with `importlib` under a synthetic module name (`somemodule_{i}`). Directories are searched recursively for `.py` files.

### Configuration: two paths with different keys

- **INI config file** (`load_config()`): section names are dotted import paths (`module.function`), resolved with `utils.get_func_from_addr`. Keys: `name`, `include`, `exclude`, `autodetect`, `autodetect_ignore`, `ignore` (generic tests), and `tested_columns` (concrete tests). Lists are comma-separated, and `\,` escapes a comma.
- **`@options()` decorator** (`dftest/options.py`, read by `load_files()`): kwargs map directly to `add_*_test` parameters: `name`, `ignore_columns`, `success_threshold`, `tested_columns`, `include`, `include_dtypes`, `exclude`, `column_autodetect`.

Both paths call `add_generic_test` / `add_concrete_test` with keyword arguments. Keep it that way: the generic signature has several adjacent optional list parameters that are easy to misalign positionally.

### Style system

`StyleFile` (JSON, example in `tests/style.json`) and `Style` (`style.py`) control heatmap color palettes. The `__DATAFRAME__` and `__DEFAULT__` keys set the global and default column styles. Any other key sets a per-column style. Style values are ordered `[{color: threshold}, ...]` pairs.

### Environment detection

At import time, `DFTests.py` switches matplotlib to `TkAgg` (falling back to `Agg` when headless) unless `utils.in_colab()` (`COLAB_GPU` env var) or `utils.in_notebook()` (`ipykernel` loaded) is true. pandasgui support was removed entirely. Don't reintroduce GUI dependencies.

## Packaging and release

- `requirements.txt` is read by `setup.py` as `install_requires`. It lists direct dependencies only, using `~=` to set a floor within a major version, and explicit `>=X,<Y` ranges where more than one major version is supported (pandas 2–3, numpy 1–2, termcolor 2–3). Never paste a `pip freeze` there: exact transitive pins made the package uninstallable. When changing bounds, check both `uv pip install --resolution lowest-direct` and the newest versions.
- pandas 2 caches each column on first access (`DataFrame._item_cache`), and cached reads skip the `Index.__getitem__` call that column autodetection traces. `Test.test()` therefore runs traced predicates under Copy-on-Write (`_bypass_column_cache`), which bypasses the cache. pandas 3 always uses Copy-on-Write and deprecates the option, so the wrapper is a no-op there.
- `dftest/__init__.py` `__version__` is the single source of truth. `setup.py` regex-parses it rather than importing the package.
- Build locally: `uvx --from build pyproject-build && uvx twine check --strict dist/*`. `MANIFEST.in` must keep `requirements.txt` in the sdist, or building a wheel from the sdist fails.
- Release: bump `__version__`, push, then manually run the "Publish to PyPI" workflow (`.github/workflows/publish.yml`, `workflow_dispatch`). It uses the `PYPI_API_TOKEN` repo secret.
