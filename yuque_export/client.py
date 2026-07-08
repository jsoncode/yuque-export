from __future__ import annotations

import json
import re
from dataclasses import dataclass
from urllib.parse import unquote

import requests

APP_DATA_PATTERN = re.compile(
    r'window\.appData\s*=\s*JSON\.parse\(decodeURIComponent\("([^"]+)"\)\)'
)


@dataclass
class TocItem:
    doc_id: str
    title: str
    uuid: str | None = None


@dataclass
class TocSummary:
    doc_count: int
    title_count: int
    total_nodes: int
    items_count: int | None


def _resolve_doc_id(node: dict) -> str | None:
    """导出 API 使用数值 id/doc_id，而非 uuid。"""
    for key in ("doc_id", "id"):
        value = node.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return None


class YuqueClient:
    def __init__(self, cookie: str, username: str, project: str) -> None:
        self.username = username
        self.project = project
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "X-Requested-With": "XMLHttpRequest",
                "Cookie": cookie,
            }
        )
        csrf_token = self._extract_cookie_value(cookie, "_csrf_token")
        if csrf_token:
            self.session.headers["x-csrf-token"] = csrf_token

    @staticmethod
    def _extract_cookie_value(cookie: str, name: str) -> str | None:
        for part in cookie.split(";"):
            part = part.strip()
            if part.startswith(f"{name}="):
                return part.split("=", 1)[1]
        return None

    def fetch_book_page(self, book_url: str) -> dict:
        response = self.session.get(book_url, timeout=30)
        response.raise_for_status()

        match = APP_DATA_PATTERN.search(response.text)
        if not match:
            raise RuntimeError("未在页面中找到 appData，请检查 Cookie 是否有效。")

        return json.loads(unquote(match.group(1)))

    def fetch_toc(self, book_url: str) -> tuple[list[TocItem], dict, TocSummary]:
        app_data = self.fetch_book_page(book_url)
        book = app_data.get("book") or {}
        toc = book.get("toc") or []
        items, summary = self._flatten_toc(toc, book.get("items_count"))
        return items, app_data, summary

    def _flatten_toc(
        self, items: list[dict], items_count: int | None = None
    ) -> tuple[list[TocItem], TocSummary]:
        result: list[TocItem] = []
        doc_count = 0
        title_count = 0
        total_nodes = 0

        def walk(nodes: list[dict]) -> None:
            nonlocal doc_count, title_count, total_nodes
            for node in nodes:
                total_nodes += 1
                node_type = node.get("type")
                title = (node.get("title") or "").strip()

                if node_type == "DOC":
                    doc_count += 1
                    doc_id = _resolve_doc_id(node)
                    if doc_id and title:
                        result.append(
                            TocItem(
                                doc_id=doc_id,
                                title=title,
                                uuid=node.get("uuid"),
                            )
                        )
                elif node_type == "TITLE":
                    title_count += 1

                children = node.get("children") or []
                if children:
                    walk(children)

        walk(items)
        summary = TocSummary(
            doc_count=doc_count,
            title_count=title_count,
            total_nodes=total_nodes,
            items_count=items_count,
        )
        return result, summary

    def export_markdown_url(self, doc_id: str) -> str:
        url = f"https://www.yuque.com/api/docs/{doc_id}/export"
        referer = f"https://www.yuque.com/{self.username}/{self.project}"
        payload = {
            "type": "markdown",
            "force": 0,
            "options": '{"latexType":2}',
        }

        response = self.session.post(
            url,
            json=payload,
            headers={"Referer": referer, "Origin": "https://www.yuque.com"},
            timeout=60,
        )
        response.raise_for_status()
        body = response.json()

        data = body.get("data") or {}
        if data.get("state") != "success" or not data.get("url"):
            raise RuntimeError(f"导出失败 (doc_id={doc_id}): {body}")

        return data["url"]

    def download_text(self, url: str) -> str:
        response = self.session.get(url, timeout=60)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or "utf-8"
        return response.text

    def download_bytes(self, url: str) -> tuple[bytes, str | None]:
        response = self.session.get(url, timeout=60)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type")
        return response.content, content_type
