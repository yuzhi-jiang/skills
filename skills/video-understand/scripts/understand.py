#!/usr/bin/env python3
"""
视频理解脚本 - 使用大模型理解视频内容
"""
import os
import sys
import argparse
from pathlib import Path

from dotenv import load_dotenv


def load_environment() -> None:
    load_dotenv()

def main():
    load_environment()

    parser = argparse.ArgumentParser(description="使用大模型理解视频内容")
    parser.add_argument("--video", required=True, help="视频文件路径或URL")
    parser.add_argument("--prompt", default="描述这个视频的内容", help="提示词")
    parser.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY"), help="API密钥")
    parser.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1"), help="API Base URL")
    parser.add_argument("--model", default=os.getenv("VIDEO_MODEL", "Qwen/Qwen3.5-35B-A3B"), help="模型名称")
    parser.add_argument("--max-tokens", type=int, default=30000, help="最大令牌数")
    
    args = parser.parse_args()
    
    if not args.api_key:
        print("错误: 请通过 --api-key、OPENAI_API_KEY 环境变量或 .env 文件提供API密钥", file=sys.stderr)
        sys.exit(1)
    
    # 判断是本地文件还是URL
    video_url = args.video
    if os.path.isfile(args.video):
        print(f"本地文件: {args.video}，需要先上传到可访问的URL", file=sys.stderr)
        sys.exit(1)
    
    from openai import OpenAI
    client = OpenAI(
        api_key=args.api_key,
        base_url=args.base_url
    )
    
    response = client.chat.completions.create(
        model=args.model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": args.prompt},
                    {
                        "type": "video_url",
                        "video_url": {
                            "url": video_url,
                        }
                    },
                ],
            }
        ],
        max_tokens=args.max_tokens,
    )
    
    print(response.choices[0].message.content)

if __name__ == "__main__":
    main()
