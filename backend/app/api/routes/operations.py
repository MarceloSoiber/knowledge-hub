from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from ...core.settings import get_settings
from ...schemas.operations import RestoreResult
from ...services.backup import BackupOperationError, create_database_backup, restore_database_backup

router = APIRouter(prefix="/operations", tags=["operations"])

@router.get("/backup")
async def download_backup() -> FileResponse:
    settings = get_settings()
    try: path = await create_database_backup(settings.postgres_dsn, settings.backup_directory)
    except BackupOperationError as exc: raise HTTPException(status_code=503, detail=str(exc)) from exc
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")

@router.post("/restore", response_model=RestoreResult)
async def restore_backup(file: UploadFile = File(...), confirmation: str = Form(...)) -> RestoreResult:
    settings = get_settings()
    if not file.filename or not file.filename.endswith(".dump"): raise HTTPException(status_code=422, detail="Envie um backup .dump.")
    content = await file.read()
    if not content or len(content) > settings.operations_restore_max_bytes: raise HTTPException(status_code=413, detail="Arquivo de backup inválido ou grande demais.")
    with tempfile.NamedTemporaryFile(prefix="restore-", suffix=".dump", delete=False) as temporary: temporary.write(content); path = Path(temporary.name)
    try: safety = await restore_database_backup(settings.postgres_dsn, settings.backup_directory, path, confirmation)
    except BackupOperationError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally: path.unlink(missing_ok=True)
    return RestoreResult(message="Base restaurada. Recarregue a aplicação.", safety_backup=safety.name)
