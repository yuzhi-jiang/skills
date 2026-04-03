---
name: image-upscaler
description: 无损放大图片至指定文件大小。当用户需要：1) 将图片放大到 3MB / 5MB 等目标大小；2) 批量处理目录下所有图片；3) 保持图片视觉质量的同时增大文件体积（如用于展板、打印、展示）时使用此 skill。支持 PNG（无损）、JPEG（最高质量）、WebP（无损）格式。
metadata: {"openclaw": {"requires": {"bins": ["uv"]}}}
---

# Image Upscaler

使用 Pillow Lanczos 重采样算法无损放大图片，并通过迭代自适应缩放确保输出文件大小达到目标值。

## 快速上手

```bash
# 放大目录内所有图片到 3MB（默认），输出到 ./upscaled/
uv run scripts/upscale.py ./photos

# 指定目标大小（MB）
uv run scripts/upscale.py ./photos --target-mb 5

# 指定输出目录
uv run scripts/upscale.py ./photos --output ./output

# 放大单张图片
uv run scripts/upscale.py ./image.png --output ./image_big.png --target-mb 3

# 静默模式（只显示汇总）
uv run scripts/upscale.py ./photos --quiet
```

## 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `input` | — | 输入图片文件或目录（必填） | — |
| `--output` | `-o` | 输出路径（文件或目录） | `<输入目录>/upscaled/` |
| `--target-mb` | `-t` | 目标文件大小（MB） | `3.0` |
| `--quiet` | `-q` | 静默模式 | 否 |

## 支持格式

| 格式 | 保存方式 |
|------|----------|
| `.png` | 无损 PNG |
| `.jpg` / `.jpeg` | JPEG quality=99，无色度子采样 |
| `.webp` | WebP 无损模式 |

## 工作原理

1. 估算达到目标文件大小所需的线性放大倍数（$\text{scale} = \sqrt{\text{target} / \text{current}}$）
2. 预留 20% 余量后执行第一次放大
3. 若未达标，按实际差距重新计算倍数，最多迭代 8 次
4. 输出文件不覆盖原始图片

## 示例输出

```
找到 8 张图片，目标 3.0 MB，输出：./upscaled

处理：banner.png
  原始尺寸: (1920, 1080)  原始大小: 270.2 KB
  [第1次] 4.05x -> (7771, 4374)  2.84 MB
  [第2次] 4.58x -> (8793, 4949)  3.37 MB
  达到目标！

完成：8/8 张达标。
```
