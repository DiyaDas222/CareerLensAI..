"""
Render fix for missing optional dependency:

Some deployed versions of backend/app.py may still contain:
  from dotenv import load_dotenv

If `python-dotenv` is not installed on the Render instance, that import
crashes at startup before our optional-import fallback can run.

Python automatically imports `sitecustomize` (if present on sys.path)
during interpreter startup, so we provide a tiny stub `dotenv` module
to make `from dotenv import load_dotenv` safe.

If `python-dotenv` is installed, this stub will not override it.
"""

import sys
import types


def _ensure_dotenv_stub() -> None:
    try:
        import dotenv  # noqa: F401
        return  # real module exists
    except Exception:
        pass

    stub = types.ModuleType("dotenv")

    def load_dotenv(*args, **kwargs):
        return False

    stub.load_dotenv = load_dotenv
    sys.modules["dotenv"] = stub


_ensure_dotenv_stub()
