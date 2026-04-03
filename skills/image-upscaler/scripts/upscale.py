#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "Pillow>=10.0.0",
# ]
# ///
"""
upscale.py — 无损放大图片，直到文件大小达到指定目标。

使用 Lanczos 高质量重采样，支持 PNG（无损）、JPEG（最高质量）、WebP（无损）。
放大后的图片默认输出到 <输入目录>/upscaled/ 子目录，原始图片不受影响。
"""

import argparse
import math
import shutil
import sys
from pathlib import Path

from PIL import Image

EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def estimate_scale(current_bytes: int, target_bytes: int) -> float:
    """根据文件大小估算需要放大的线性倍数（面积倍数开平方）。"""
    return math.sqrt(target_bytes / current_bytes)


def save_kwargs_for(suffix: str) -> dict:
    if suffix == ".png":
        return {"format": "PNG", "optimize": False}
    elif suffix in {".jpg", ".jpeg"}:
        return {"format": "JPEG", "quality": 99, "subsampling": 0}
    elif suffix == ".webp":
        return {"format": "WEBP", "lossless": True, "quality": 100}
    return {}


def upscale_to_target(src: Path, dst: Path, target_bytes: int, verbose: bool = True) -> bool:
    """
    将 src 图片放大后保存到 dst，直到文件大小 >= target_bytes。
    返回 True 表示成功达标，False 表示达到最大迭代次数仍未达标。
    """
    img = Image.open(src)
    src_size = src.stat().st_size
    suffix = src.suffix.lower()
    kwargs = save_kwargs_for(suffix)

    if verbose:
        print(f"  原始尺寸: {img.size}  原始大小: {src_size / 1024:.1f} KB")

    if src_size >= target_bytes:
        if verbose:
            print(f"  已达到目标大小，直接复制。")
        shutil.copy2(src, dst)
        return True

    # 初始放大倍数，留 20% 余量
    scale = estimate_scale(src_size, target_bytes) * 1.2

    MAX_ITER = 8
    out_size = 0
    for attempt in range(1, MAX_ITER + 1):
        new_w = max(1, round(img.width * scale))
        new_h = max(1, round(img.height * scale))
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        resized.save(dst, **kwargs)
        out_size = dst.stat().st_size

        if verbose:
            mb = out_size / 1024 / 1024
            print(f"  [第{attempt}次] {scale:.2f}x -> {resized.size}  {mb:.2f} MB")

        if out_size >= target_bytes:
            if verbose:
                print(f"  达到目标！")
            return True

        # 未达标则追加放大，再乘 1.1 余量
        scale *= estimate_scale(out_size, target_bytes) * 1.1

    if verbose:
        print(f"  警告：{MAX_ITER} 次后仍未达标，当前 {out_size / 1024 / 1024:.2f} MB")
    return False


def main():
    parser = argparse.ArgumentParser(
        description="无损放大图片至目标文件大小",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 放大当前目录所有图片到 3MB，输出到 ./upscaled/
  uv run scripts/upscale.py ./photos

  # 指定输出目录与目标大小
  uv run scripts/upscale.py ./photos --output ./output --target-mb 5

  # 放大单张图片
  uv run scripts/upscale.py ./image.png --output ./out.png --target-mb 3
""",
    )
    parser.add_argument("input", type=Path, help="输入图片文件或包含图片的目录")
    parser.add_argument(
        "--output", "-o", type=Path, default=None,
        help="输出路径（文件或目录）。默认：输入目录下的 upscaled/ 子目录",
    )
    parser.add_argument(
        "--target-mb", "-t", type=float, default=3.0,
        help="目标文件大小（MB），默认 3.0",
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true",
        help="静默模式，不打印每张图片的处理详情",
    )
    args = parser.parse_args()

    target_bytes = int(args.target_mb * 1024 * 1024)
    verbose = not args.quiet

    # 收集待处理图片
    src_path: Path = args.input.expanduser().resolve()
    if src_path.is_file():
        images = [src_path] if src_path.suffix.lower() in EXTENSIONS else []
        default_output = src_path.parent / "upscaled" / src_path.name
    elif src_path.is_dir():
        images = sorted(p for p in src_path.iterdir()
                        if p.is_file() and p.suffix.lower() in EXTENSIONS)
        default_output = src_path / "upscaled"
    else:
        print(f"错误：路径不存在 — {src_path}", file=sys.stderr)
        sys.exit(1)

    if not images:
        print("未找到支持的图片文件（.png .jpg .jpeg .webp）。")
        sys.exit(0)

    # 确定输出目录/文件
    output: Path = (args.output.expanduser().resolve()
                    if args.output else default_output)

    # 单文件输出
    if src_path.is_file():
        output.parent.mkdir(parents=True, exist_ok=True)
        print(f"处理：{src_path.name}")
        upscale_to_target(src_path, output, target_bytes, verbose)
    else:
        output.mkdir(parents=True, exist_ok=True)
        print(f"找到 {len(images)} 张图片，目标 {args.target_mb} MB，输出：{output}\n")
        success = 0
        for src in images:
            dst = output / src.name
            print(f"处理：{src.name}")
            try:
                if upscale_to_target(src, dst, target_bytes, verbose):
                    success += 1
            except Exception as e:
                print(f"  错误：{e}", file=sys.stderr)
            print()
        print(f"完成：{success}/{len(images)} 张达标。")


if __name__ == "__main__":
    main()
