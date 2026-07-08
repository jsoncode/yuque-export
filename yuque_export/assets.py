from __future__ import annotations

import hashlib
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

CDN_URL_PATTERN = re.compile(
    r"https://cdn\.nlark\.com/yuque/[^\s\"'<>)\]]+",
    re.IGNORECASE,
)


def sanitize_filename(name: str, max_length: int = 80) -> str:
    invalid_chars = r'<>:"/\\|?*'
    cleaned = "".join("_" if ch in invalid_chars else ch for ch in name)
    cleaned = cleaned.strip().strip(".")
    if not cleaned:
        cleaned = "untitled"
    return cleaned[:max_length]


def unique_dir_name(base: str, used: set[str]) -> str:
    name = sanitize_filename(base)
    if name not in used:
        used.add(name)
        return name

    index = 2
    while True:
        candidate = f"{name}_{index}"
        if candidate not in used:
            used.add(candidate)
            return candidate
        index += 1


def _guess_extension(url: str, content_type: str | None) -> str:
    path = unquote(urlparse(url).path)
    suffix = Path(path).suffix
    if suffix and len(suffix) <= 8:
        return suffix

    mapping = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
        "application/pdf": ".pdf",
    }
    if content_type:
        normalized = content_type.split(";", 1)[0].strip().lower()
        return mapping.get(normalized, ".bin")
    return ".bin"


def _local_asset_name(url: str, content_type: str | None) -> str:
    parsed = urlparse(url)
    basename = Path(unquote(parsed.path)).name
    if basename and "." in basename:
        return sanitize_filename(basename, max_length=120)

    digest = hashlib.md5(url.encode("utf-8")).hexdigest()[:12]
    ext = _guess_extension(url, content_type)
    return f"{digest}{ext}"


def download_assets_and_rewrite(
    markdown: str,
    assets_dir: Path,
    download_bytes,
) -> str:
    assets_dir.mkdir(parents=True, exist_ok=True)
    url_to_local: dict[str, str] = {}

    def replace_url(match: re.Match[str]) -> str:
        url = match.group(0).rstrip(")")
        if url in url_to_local:
            return url_to_local[url]

        content, content_type = download_bytes(url)
        local_name = _local_asset_name(url, content_type)
        target = assets_dir / local_name

        if target.exists():
            stem = target.stem
            suffix = target.suffix
            index = 2
            while target.exists():
                target = assets_dir / f"{stem}_{index}{suffix}"
                index += 1

        target.write_bytes(content)
        local_ref = f"./assets/{target.name}"
        url_to_local[url] = local_ref
        return local_ref

    return CDN_URL_PATTERN.sub(replace_url, markdown)
