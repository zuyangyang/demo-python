from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, HTTPException, Path, UploadFile
from fastapi.responses import Response
from PIL import Image

from app.services.room_registry import room_registry


router = APIRouter(prefix="/rooms")

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10MB
ALLOWED_FORMATS = {"PNG", "JPEG"}


@router.post("/{room_id}/image")
async def upload_image(room_id: str = Path(min_length=1), file: UploadFile | None = None) -> dict[str, bool]:
    state = await room_registry.get_room(room_id)
    if state is None:
        raise HTTPException(status_code=404, detail={"message": "room not found"})

    if file is None:
        raise HTTPException(status_code=400, detail={"message": "file is required"})

    # Read and validate size
    data = await file.read()
    if len(data) == 0:
        raise HTTPException(status_code=400, detail={"message": "empty file"})
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail={"message": "file too large"})

    # Validate type by decoding with Pillow; accept PNG or JPEG
    try:
        with Image.open(BytesIO(data)) as img:
            img_format = (img.format or "").upper()
    except Exception:
        raise HTTPException(status_code=415, detail={"message": "unsupported image type"})

    if img_format not in ALLOWED_FORMATS:
        raise HTTPException(status_code=415, detail={"message": "unsupported image type"})

    await room_registry.set_room_image(room_id, data)
    return {"ok": True}


@router.get("/{room_id}/image")
async def get_image(room_id: str = Path(min_length=1)) -> Response:
    state = await room_registry.get_room(room_id)
    if state is None:
        raise HTTPException(status_code=404, detail={"message": "room not found"})
    data = await room_registry.get_room_image(room_id)
    if not data:
        raise HTTPException(status_code=404, detail={"message": "image not found"})
    # Best effort content type guess via Pillow
    mime = "application/octet-stream"
    try:
        with Image.open(BytesIO(data)) as img:
            if (img.format or "").upper() == "PNG":
                mime = "image/png"
            elif (img.format or "").upper() == "JPEG":
                mime = "image/jpeg"
    except Exception:
        pass
    return Response(content=data, media_type=mime)


