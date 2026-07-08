from __future__ import annotations

import json
import logging
from pathlib import Path

from .assets import download_assets_and_rewrite, unique_dir_name
from .client import YuqueClient, TocItem
from .config import Config, resolve_book_dir_name

logger = logging.getLogger(__name__)


class YuqueExporter:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.client = YuqueClient(
            cookie=config.cookie,
            username=config.username,
            project=config.project,
        )
        self.book_output_dir: Path | None = None

    def run(self) -> None:
        logger.info("正在获取文档目录: %s", self.config.book_url)
        toc_items, app_data, summary = self.client.fetch_toc(self.config.book_url)

        book_dir_name = resolve_book_dir_name(app_data, self.config.project)
        self.book_output_dir = self.config.output_dir / book_dir_name
        self.book_output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("导出目录: %s", self.book_output_dir)
        self._save_app_data(app_data)

        logger.info(
            "目录统计: 可导出文档 %d 篇, 目录标题 %d 个, TOC 节点共 %d 个"
            "（book.items_count=%s）",
            summary.doc_count,
            summary.title_count,
            summary.total_nodes,
            summary.items_count,
        )
        if summary.items_count is not None and summary.doc_count != summary.items_count:
            logger.warning(
                "TOC 文档数 (%d) 与 book.items_count (%d) 不一致，"
                "请查看 appData.json 排查。",
                summary.doc_count,
                summary.items_count,
            )

        if not toc_items:
            logger.warning("未找到可导出的文档。")
            return

        logger.info("共找到 %d 篇文档，开始导出。", len(toc_items))

        used_titles: set[str] = set()
        success_count = 0

        for index, item in enumerate(toc_items, start=1):
            try:
                self._export_one(item, used_titles)
                success_count += 1
                logger.info("[%d/%d] 导出成功: %s", index, len(toc_items), item.title)
            except Exception as exc:
                logger.error(
                    "[%d/%d] 导出失败: %s (doc_id=%s, uuid=%s) — %s",
                    index,
                    len(toc_items),
                    item.title,
                    item.doc_id,
                    item.uuid,
                    exc,
                )

        logger.info("导出完成，成功 %d / %d。", success_count, len(toc_items))

    def _save_app_data(self, app_data: dict) -> None:
        path = self.book_output_dir / "appData.json"
        path.write_text(
            json.dumps(app_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info("已保存 appData: %s", path)

    def _export_one(self, item: TocItem, used_titles: set[str]) -> None:
        export_url = self.client.export_markdown_url(item.doc_id)
        markdown = self.client.download_text(export_url)

        dir_name = unique_dir_name(item.title, used_titles)
        doc_dir = self.book_output_dir / dir_name
        assets_dir = doc_dir / "assets"
        md_path = doc_dir / "index.md"

        markdown = download_assets_and_rewrite(
            markdown,
            assets_dir,
            self.client.download_bytes,
        )

        doc_dir.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown, encoding="utf-8")
