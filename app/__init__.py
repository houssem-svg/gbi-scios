from pathlib import Path

backend_app = Path(__file__).resolve().parents[1] / "build-a-production-grade-fastapi-backend" / "app"
if backend_app.exists():
    __path__.insert(0, str(backend_app))
