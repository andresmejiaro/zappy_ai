# Zappy AI — Dev Setup (src layout)

use with server: https://github.com/PepeSegura/zappy
and graphic client: https://github.com/Tagamydev/ZAPPY_GC


Minimal instructions to **install**, **uninstall/recompile**, and **run**.

---

## Prereqs

* Python ≥ 3.10
* Virtual env recommended

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
```

---

## Project layout (expected)

```
zappy_ai/                  # repo root
  pyproject.toml
  src/
    zappy_ai/
      __init__.py
      client.py            # launcher module (preferred)
      ...                  # other modules
```

> Imports should be package-qualified, e.g. `from zappy_ai.foo import bar`.

---

## Install (editable)

Installs the package so imports work from anywhere in the repo.

```bash
pip install -e .
```

Verify:

```bash
python -c "import zappy_ai, sys; print('OK:', zappy_ai.__file__)"
```

---

## Run

Preferred (module):

```bash
python -m zappy_ai.client
```

---

## Uninstall / “recompile” (clean rebuild)

Use this when entry points or package metadata changed, or if imports look stale.

```bash
pip uninstall -y zappy_ai
pip install -e .
```

If things still look weird:

```bash
find . -maxdepth 2 -name "*.egg-info" -print -delete
pip cache purge
pip install -e .
```

---

## Common errors

**`ModuleNotFoundError: No module named 'zappy_ai'`**

* Ensure `src/zappy_ai/__init__.py` exists.
* Check `pyproject.toml` includes:

  ```toml
  [tool.setuptools]
  package-dir = {"" = "src"}

  [tool.setuptools.packages.find]
  where = ["src"]
  include = ["zappy_ai*"]
  ```
* Re-run the clean rebuild steps above.

**Relative imports fail when running files directly**

* Run with `-m`: `python -m zappy_ai.client` (don’t `python src/zappy_ai/client.py`).

---

## Dev tip (optional)

For ad-hoc scripts/tests without reinstalling:

```bash
PYTHONPATH=src python -m pytest   # or: PYTHONPATH=src python your_script.py
```
