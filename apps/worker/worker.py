from kits.kit_common.config import settings
from kits.kit_common.paths import write_json
from kits.kit_pipeline.pipeline import run_pipeline


def worker_entry(payload: dict):
    job_id = payload.get("job_id")
    from kits.kit_common.paths import job_paths
    
    try:
        # Обновляем статус на "processing"
        paths = job_paths(job_id)
        write_json(paths["work_dir"] / "status.json", {"job_id": job_id, "status": "processing", "progress": 10})
        
        # Запускаем pipeline
        result = run_pipeline(payload)
        
        # Обновляем статус на "done"
        write_json(paths["work_dir"] / "status.json", {"job_id": job_id, "status": "done", "progress": 100})
        
        return {"job_id": job_id, "status": "done", "result": result}
    except Exception as e:
        # Best-effort update of status file
        try:
            paths = job_paths(job_id)
            write_json(paths["work_dir"] / "status.json", {"job_id": job_id, "status": "error", "error": str(e)})
        except Exception:
            pass
        raise

