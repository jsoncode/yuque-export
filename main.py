from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from yuque_export.config import load_config
from yuque_export.exporter import YuqueExporter


def main() -> int:
    parser = argparse.ArgumentParser(description="语雀知识库 Markdown 导出工具")
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="配置文件路径，默认 config.yaml",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="输出详细日志",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    try:
        config = load_config(Path(args.config))
        YuqueExporter(config).run()
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        logging.error("%s", exc)
        return 1
    except KeyboardInterrupt:
        logging.warning("用户中断导出。")
        return 130

    return 0


if __name__ == "__main__":
    sys.exit(main())
