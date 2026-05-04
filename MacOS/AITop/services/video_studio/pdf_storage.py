"""
PDF storage layer — Supabase Storage bucket `video_studio_pdfs`.

Each PDF is keyed by its sha256 (object path: `pdfs/<sha256>.pdf`) so
re-uploading the same file is a no-op and analyses are reusable across
machines.

Local cache path: ~/Library/Caches/Angelora/VideoStudio/pdfs/<sha256>.pdf
The cache is populated on download and refilled on demand if missing.
"""

from __future__ import annotations

import hashlib
import logging
import sys
from pathlib import Path
from typing import Optional
from urllib import error, request

# Add AngelaAI root to sys.path for config imports
_angela_root = str(Path(__file__).resolve().parents[4])
if _angela_root not in sys.path:
    sys.path.insert(0, _angela_root)

logger = logging.getLogger(__name__)

BUCKET = "video_studio_pdfs"
OBJECT_PREFIX = "pdfs"
CACHE_DIR = Path.home() / "Library" / "Caches" / "Angelora" / "VideoStudio" / "pdfs"

# Local fallback used when the live bucket config can't be fetched.
# The authoritative value is `file_size_limit` on the Supabase bucket.
DEFAULT_FILE_SIZE_LIMIT = 50 * 1024 * 1024


class PDFTooLargeError(RuntimeError):
    """Raised when a PDF exceeds the bucket's configured file_size_limit."""

    def __init__(self, *, size: int, limit: int):
        self.size = size
        self.limit = limit
        super().__init__(
            f"PDF is {size / 1_048_576:.1f} MB but the bucket allows max "
            f"{limit / 1_048_576:.0f} MB. Raise the limit in Supabase "
            f"(Project → Settings → Storage → Upload file size limit)."
        )


# ---------------------------------------------------------------------------
# Credential resolution (cached after first call)
# ---------------------------------------------------------------------------

_cached_creds: dict[str, str] = {}


def _resolve_creds() -> tuple[str, str]:
    """Returns (api_url, service_role_key). Reads from our_secrets via config."""
    if "url" in _cached_creds:
        return _cached_creds["url"], _cached_creds["key"]
    from config.db_url import _resolve  # type: ignore[import-not-found]
    api_url = _resolve("SUPABASE_API_URL", "supabase_api_url").rstrip("/")
    service_key = _resolve("SUPABASE_SERVICE_ROLE_KEY", "supabase_service_role_key")
    _cached_creds["url"] = api_url
    _cached_creds["key"] = service_key
    return api_url, service_key


def _auth_headers(extra: Optional[dict] = None) -> dict:
    _, key = _resolve_creds()
    h = {"apikey": key, "Authorization": f"Bearer {key}"}
    if extra:
        h.update(extra)
    return h


_cached_size_limit: Optional[int] = None


def get_file_size_limit() -> int:
    """
    Return the bucket's configured `file_size_limit` in bytes. Falls back to
    `DEFAULT_FILE_SIZE_LIMIT` when the bucket config can't be read (e.g.
    network error, missing creds). Cached after first successful fetch.
    """
    global _cached_size_limit
    if _cached_size_limit is not None:
        return _cached_size_limit
    import json
    try:
        api_url, _ = _resolve_creds()
        url = f"{api_url}/storage/v1/bucket/{BUCKET}"
        req = request.Request(url, headers=_auth_headers({}))
        with request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        limit = int(data.get("file_size_limit") or DEFAULT_FILE_SIZE_LIMIT)
    except Exception as exc:
        logger.warning("Could not fetch bucket size limit, using default: %s", exc)
        limit = DEFAULT_FILE_SIZE_LIMIT
    _cached_size_limit = limit
    return limit


# ---------------------------------------------------------------------------
# sha256 + object-path helpers
# ---------------------------------------------------------------------------

def sha256_of(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def object_path_for(sha: str) -> str:
    return f"{OBJECT_PREFIX}/{sha}.pdf"


def cache_path_for(sha: str) -> Path:
    return CACHE_DIR / f"{sha}.pdf"


# ---------------------------------------------------------------------------
# Storage operations (REST)
# ---------------------------------------------------------------------------

def object_exists(sha: str) -> bool:
    """
    List the bucket folder and look for `<sha>.pdf`. Supabase strips the
    folder prefix from result names, so we list `OBJECT_PREFIX` and match
    on the bare filename. The substring `search` param scopes the listing
    so this stays O(1) regardless of bucket size.
    """
    import json
    api_url, _ = _resolve_creds()
    url = f"{api_url}/storage/v1/object/list/{BUCKET}"
    body = json.dumps({
        "prefix": OBJECT_PREFIX,
        "search": sha,
        "limit": 1,
    }).encode()
    req = request.Request(
        url, data=body, method="POST",
        headers=_auth_headers({"Content-Type": "application/json"}),
    )
    with request.urlopen(req, timeout=15) as resp:
        items = json.loads(resp.read())
    return any(it.get("name") == f"{sha}.pdf" for it in items)


def upload(local_pdf: str | Path, sha: Optional[str] = None) -> str:
    """
    Upload a PDF (idempotent). Returns the sha256 used as the object key.
    Skips network if the bucket already has the object.
    """
    local_pdf = Path(local_pdf)
    if not local_pdf.exists():
        raise FileNotFoundError(f"PDF not found: {local_pdf}")
    sha = sha or sha256_of(local_pdf)

    # Always populate local cache so subsequent reads are free.
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache = cache_path_for(sha)
    if not cache.exists() or cache.stat().st_size != local_pdf.stat().st_size:
        cache.write_bytes(local_pdf.read_bytes())

    if object_exists(sha):
        logger.info("PDF already in bucket: sha=%s", sha[:12])
        return sha

    api_url, _ = _resolve_creds()
    url = f"{api_url}/storage/v1/object/{BUCKET}/{object_path_for(sha)}"
    body = local_pdf.read_bytes()
    headers = _auth_headers({
        "Content-Type": "application/pdf",
        "x-upsert": "false",  # we already checked existence
        "cache-control": "max-age=31536000, immutable",
    })
    req = request.Request(url, data=body, method="POST", headers=headers)
    try:
        with request.urlopen(req, timeout=120) as resp:
            if resp.status not in (200, 201):
                raise RuntimeError(f"upload failed: HTTP {resp.status}")
    except error.HTTPError as e:
        # Supabase returns HTTP 400 with a JSON body whose `statusCode` is
        # the real status. 409 = duplicate (another writer or stale check)
        # — treat as success since the bytes are addressed by content hash.
        body_text = ""
        try:
            body_text = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        if '"statusCode":"409"' in body_text or e.code == 409:
            logger.info("PDF already in bucket (409 on upload): sha=%s", sha[:12])
            return sha
        if '"statusCode":"413"' in body_text or "exceeded the maximum allowed size" in body_text:
            raise PDFTooLargeError(
                size=local_pdf.stat().st_size,
                limit=get_file_size_limit(),
            ) from e
        raise RuntimeError(f"upload failed: HTTP {e.code} {body_text}") from e
    logger.info("Uploaded PDF to bucket: sha=%s size=%d", sha[:12], len(body))
    return sha


def ensure_local(sha: str) -> Path:
    """
    Return a local path to the PDF, downloading from the bucket if the
    cache is cold. Used by the analysis pipeline.
    """
    cache = cache_path_for(sha)
    if cache.exists() and cache.stat().st_size > 0:
        return cache
    api_url, _ = _resolve_creds()
    url = f"{api_url}/storage/v1/object/{BUCKET}/{object_path_for(sha)}"
    req = request.Request(url, method="GET", headers=_auth_headers())
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with request.urlopen(req, timeout=120) as resp:
        cache.write_bytes(resp.read())
    logger.info("Downloaded PDF from bucket: sha=%s", sha[:12])
    return cache


def delete(sha: str) -> None:
    """Remove an object from the bucket. Used for cleanup, not in normal flow."""
    api_url, _ = _resolve_creds()
    url = f"{api_url}/storage/v1/object/{BUCKET}/{object_path_for(sha)}"
    req = request.Request(url, method="DELETE", headers=_auth_headers())
    with request.urlopen(req, timeout=15) as resp:
        if resp.status not in (200, 204):
            raise RuntimeError(f"delete failed: HTTP {resp.status}")
