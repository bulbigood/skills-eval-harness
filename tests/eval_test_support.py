from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_eval_module(name: str):
    path = ROOT / f"tests/eval/{name}.py"
    return load_module(path, f"iwe_eval_{name}")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_script_module(name: str):
    return load_module(ROOT / f"scripts/{name}.py", f"iwe_script_{name}")


def load_runner():
    return load_module(ROOT / "tests/eval/run.py", "iwe_eval_scoring")
