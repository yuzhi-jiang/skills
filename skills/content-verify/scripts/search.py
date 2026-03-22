#!/usr/bin/env python3
"""
通用网络搜索脚本 - 使用 SerpAPI 搜索网络信息
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from search_integration import SearchIntegration


def load_environment() -> None:
    """加载 scripts/.env（skill 本地配置）"""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)


def main() -> None:
    # Windows 控制台 UTF-8 兼容处理
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    load_environment()

    parser = argparse.ArgumentParser(description="通用网络搜索工具")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("--num", "-n", type=int, default=10, help="返回结果数量")
    parser.add_argument("--api-key", default=os.getenv("SERPAPI_API_KEY"), help="SerpAPI 密钥")
    parser.add_argument("--format", "-f", choices=["json", "text"], default="text", help="输出格式")
    args = parser.parse_args()

    if not args.api_key:
        print("错误: 请通过 --api-key 或 SERPAPI_API_KEY 环境变量提供 API 密钥", file=sys.stderr)
        sys.exit(1)

    search = SearchIntegration(api_key=args.api_key)

    if not search.enabled:
        print("错误: SerpAPI 搜索功能未启用，请检查 API 密钥与依赖", file=sys.stderr)
        sys.exit(1)

    import asyncio

    results = asyncio.run(search.search(query=args.query, num_results=args.num))

    if args.format == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    organic = results.get("organic_results", [])
    if not organic:
        print("未找到相关结果")
        return

    for i, item in enumerate(organic, 1):
        title = item.get("title", "无标题")
        link = item.get("link", "")
        snippet = item.get("snippet", "")
        source = item.get("source", "")

        print(f"\n【{i}】{title}")
        if source:
            print(f"   来源: {source}")
        if snippet:
            print(f"   摘要: {snippet}")
        if link:
            print(f"   链接: {link}")


if __name__ == "__main__":
    main()
