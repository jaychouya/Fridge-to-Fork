from __future__ import annotations

import hashlib
import io
from pathlib import Path

from PIL import Image


def load_and_compress_image(image_path: str, max_edge: int, quality: int) -> bytes:
    img = Image.open(image_path).convert("RGB")
    img.thumbnail((max_edge, max_edge))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def perceptual_hash(image_path: str) -> str:
    try:
        import imagehash

        img = Image.open(Path(image_path))
        return str(imagehash.phash(img))
    except ModuleNotFoundError:
        data = Path(image_path).read_bytes()
        return hashlib.sha1(data).hexdigest()
