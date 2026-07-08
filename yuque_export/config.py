from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Config:
    username: str
    project: str
    cookie: str
    output_dir: Path

    @property
    def book_url(self) -> str:
        return f"https://www.yuque.com/{self.username}/{self.project}"


def resolve_book_dir_name(app_data: dict, fallback_slug: str) -> str:
    from .assets import sanitize_filename

    book = app_data.get("book") or {}
    name = (book.get("name") or "").strip()
    if name:
        return sanitize_filename(name, max_length=120)
    return sanitize_filename(fallback_slug, max_length=120)


def load_config(path: str | Path) -> Config:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(
            f"配置文件不存在: {config_path}\n"
            f"请复制 config.example.yaml 为 config.yaml 并填写配置。"
        )

    with config_path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    required = ("username", "project", "cookie")
    missing = [key for key in required if not raw.get(key)]
    if missing:
        raise ValueError(f"配置文件缺少必填项: {', '.join(missing)}")

    return Config(
        username=str(raw["username"]).strip(),
        project=str(raw["project"]).strip(),
        cookie=str(raw["cookie"]).strip(),
        output_dir=Path(raw.get("output_dir", "./output")),
    )
