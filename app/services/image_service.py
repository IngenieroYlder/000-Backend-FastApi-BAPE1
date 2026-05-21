"""Image upload + compression helpers shared by product and service routes."""
from __future__ import annotations

import io
import os
import uuid
from typing import Tuple

from fastapi import HTTPException, UploadFile
from PIL import Image, ImageOps

UPLOAD_ROOT = os.environ.get("UPLOAD_ROOT", "static/uploads")

MAX_BYTES = 8 * 1024 * 1024  # 8 MB hard cap on the raw upload
MAX_DIM = 1200               # main image, max width/height
THUMB_DIM = 400              # thumbnail, max width/height
WEBP_QUALITY = 80            # good size/quality tradeoff
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
}


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _open_image(data: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Archivo no es una imagen válida: {exc}")
    # Honor EXIF orientation, then flatten alpha (WebP supports alpha but JPEG decoders
    # downstream may not, and we want a single predictable format).
    img = ImageOps.exif_transpose(img)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "A" in img.mode else "RGB")
    return img


def _save_webp(img: Image.Image, full_path: str, max_dim: int) -> None:
    work = img.copy()
    work.thumbnail((max_dim, max_dim), Image.LANCZOS)
    save_kwargs = {"format": "WEBP", "quality": WEBP_QUALITY, "method": 6}
    if work.mode == "RGBA":
        work.save(full_path, **save_kwargs)
    else:
        work.convert("RGB").save(full_path, **save_kwargs)


async def save_upload(
    upload: UploadFile,
    category: str,
    company_id: int,
) -> Tuple[str, str]:
    """Persist an uploaded image as compressed WebP + thumbnail.

    Returns (image_url, thumbnail_url) relative to the static mount, e.g.
    ("/static/uploads/products/1/abc.webp", "/static/uploads/products/1/abc_thumb.webp").

    The on-disk root defaults to ``static/uploads`` (override with UPLOAD_ROOT
    env var) — mount that path as a Docker volume in production to survive
    redeploys.
    """
    if upload.content_type and upload.content_type.lower() not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido: {upload.content_type}",
        )

    data = await upload.read()
    if not data:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")
    if len(data) > MAX_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"La imagen excede el máximo permitido de {MAX_BYTES // (1024 * 1024)} MB.",
        )

    img = _open_image(data)

    target_dir_fs = os.path.join(UPLOAD_ROOT, category, str(company_id))
    _ensure_dir(target_dir_fs)

    name = f"{uuid.uuid4().hex}"
    main_fs = os.path.join(target_dir_fs, f"{name}.webp")
    thumb_fs = os.path.join(target_dir_fs, f"{name}_thumb.webp")

    _save_webp(img, main_fs, MAX_DIM)
    _save_webp(img, thumb_fs, THUMB_DIM)

    # URL paths use forward slashes regardless of OS
    public_root = UPLOAD_ROOT.replace("\\", "/").lstrip("./")
    main_url = f"/{public_root}/{category}/{company_id}/{name}.webp"
    thumb_url = f"/{public_root}/{category}/{company_id}/{name}_thumb.webp"
    return main_url, thumb_url


def delete_local_image(url: str | None) -> None:
    """Best-effort cleanup of an image previously stored by save_upload.

    Silently ignores external URLs and missing files so callers can use it
    eagerly on update/delete without extra checks.
    """
    if not url or not url.startswith("/"):
        return
    public_root = UPLOAD_ROOT.replace("\\", "/").lstrip("./")
    prefix = f"/{public_root}/"
    if not url.startswith(prefix):
        return
    relative = url[len(prefix):]
    fs_path = os.path.join(UPLOAD_ROOT, *relative.split("/"))
    try:
        if os.path.isfile(fs_path):
            os.remove(fs_path)
        # also remove thumbnail companion if we were given the main url
        if fs_path.endswith(".webp") and "_thumb" not in fs_path:
            thumb = fs_path[:-5] + "_thumb.webp"
            if os.path.isfile(thumb):
                os.remove(thumb)
    except Exception:
        pass
