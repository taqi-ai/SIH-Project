import uuid
from pathlib import Path

from app.config import settings
from app.security import sanitize_filename


class LocalStorage:
    """Local-disk document storage. Swappable for a MinIO/S3 backend later —
    callers only depend on save()/path_for()/read(), not the underlying medium."""

    def __init__(self, root: Path | None = None):
        self.root = root or settings.upload_dir

    def save(self, bid_id: str, filename: str, content: bytes) -> str:
        safe_name = sanitize_filename(filename)
        unique_name = f"{uuid.uuid4().hex[:8]}_{safe_name}"
        bid_dir = self.root / bid_id
        bid_dir.mkdir(parents=True, exist_ok=True)
        dest = bid_dir / unique_name
        dest.write_bytes(content)
        return str(dest.relative_to(self.root))

    def full_path(self, relative_path: str) -> Path:
        return self.root / relative_path

    def read(self, relative_path: str) -> bytes:
        return self.full_path(relative_path).read_bytes()


storage = LocalStorage()
