"""PDF upload endpoints for receiving forms from the frontend."""

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Accept a PDF file, store it, and return a handle + download URL."""
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted",
        )

    file_id = uuid4().hex
    save_path = UPLOAD_DIR / f"{file_id}.pdf"

    data = await file.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    save_path.write_bytes(data)

    return {
        "file_id": file_id,
        "original_filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": save_path.stat().st_size,
        "url": f"/upload/pdf/{file_id}",
    }


@router.get("/pdf/{file_id}")
async def get_pdf(file_id: str):
    """Return a previously uploaded PDF by its id."""
    path = UPLOAD_DIR / f"{file_id}.pdf"
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF not found",
        )

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=path.name,
        headers={"Content-Disposition": f"inline; filename={path.name}"},
    )
