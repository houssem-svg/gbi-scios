from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "build-a-production-grade-fastapi-backend"
BACKEND_MAIN = (
    BACKEND_ROOT
    / "app"
    / "main.py"
)

sys.path.insert(0, str(BACKEND_ROOT))

spec = importlib.util.spec_from_file_location("gbi_scios_backend_main", BACKEND_MAIN)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load backend app from {BACKEND_MAIN}")

backend_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend_main)

app = backend_main.app
create_app = backend_main.create_app
