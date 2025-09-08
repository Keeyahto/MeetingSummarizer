import json
from pathlib import Path
from typing import Dict

from .config import settings


def within_data_dir(p: Path) -> bool:
    base = Path(settings.DATA_DIR).resolve()
    try:
        p = p.resolve()
    except Exception:
        return False
    return str(p).startswith(str(base))


def ensure_job_dirs(job_id: str) -> Dict[str, Path]:
    base = Path(settings.DATA_DIR) / "uploads" / job_id
    in_dir = base / "in"
    work_dir = base / "work"
    out_dir = base / "out"
    for d in (in_dir, work_dir, out_dir):
        d.mkdir(parents=True, exist_ok=True)
    return {"job_dir": base, "in_dir": in_dir, "work_dir": work_dir, "out_dir": out_dir}


def job_paths(job_id: str) -> Dict[str, Path]:
    base = Path(settings.DATA_DIR) / "uploads" / job_id
    return {"job_dir": base, "in_dir": base / "in", "work_dir": base / "work", "out_dir": base / "out"}


def read_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

