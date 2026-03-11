---
name: video-understand
description: 使用大模型理解视频内容并提取信息。当用户需要：1) 让AI观看视频并描述内容；2) 从视频中提取字幕或翻译；3) 分析视频场景、人物、对话等；4) 视频问答时使用此skill。
metadata: {"openclaw": {"requires": {"bins": ["uv"], "env": ["OPENAI_API_KEY"]}, "primaryEnv": "OPENAI_API_KEY"}}
---

# Video Understand

使用大模型理解视频内容的skill。

## 使用方法

### 基本命令

```bash
cd video-understand

# 推荐：使用 .env 文件（可从示例复制）
cp scripts/.env.example scripts/.env
# 然后编辑 scripts/.env 填入真实值

python scripts/understand.py --video "<视频URL>" --prompt "<提示词>"
```

说明：脚本会自动读取 `scripts/.env`，同时也支持系统环境变量。

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--video` | 视频URL（必须） | - |
| `--prompt` | 提示词 | "描述这个视频的内容" |
| `--api-key` | API密钥 | `.env`/环境变量 OPENAI_API_KEY |
| `--base-url` | API地址 | `.env`/环境变量 OPENAI_BASE_URL 或 https://api.siliconflow.cn/v1 |
| `--model` | 模型名称 | `.env`/环境变量 VIDEO_MODEL 或 Qwen/Qwen3.5-35B-A3B |
| `--max-tokens` | 最大令牌数 | 30000 |

### 常用提示词

- **描述内容**: "描述这个视频的内容"
- **提取字幕翻译**: "提取视频中的语音字幕并翻译为中文，只要翻译后的文本，不要原文字幕"
- **分析场景**: "详细描述视频中的场景、人物、动作"
- **回答问题**: "根据视频内容回答问题：xxx"

### 示例

```bash
# 描述视频内容
python scripts/understand.py \
  --video "https://example.com/video.mp4" \
  --prompt "描述这个视频的内容"

# 提取并翻译字幕
python scripts/understand.py \
  --video "https://example.com/video.mp4" \
  --prompt "提取视频中的语音字幕并翻译为中文，只要翻译后的文本"

# 使用自定义模型和API
python scripts/understand.py \
  --video "https://example.com/video.mp4" \
  --api-key "sk-xxxxx" \
  --base-url "https://api.openai.com/v1" \
  --model "gpt-4o" \
  --prompt "详细描述这个视频"
```

## 环境变量

支持两种方式：

1. 在 `scripts/.env` 中配置（推荐）
2. 设置系统环境变量

优先级：命令行参数 `>` 系统环境变量 `>` `.env` 文件 `>` 代码默认值。

示例（系统环境变量）：

```bash
export OPENAI_API_KEY="sk-xxxxx"           # API密钥
export OPENAI_BASE_URL="https://api.siliconflow.cn/v1"  # API地址
export VIDEO_MODEL="Qwen/Qwen3.5-35B-A3B"   # 模型名称
```

## 注意事项

1. **视频URL**: 当前版本仅支持在线URL，不支持本地文件（需要自行托管或使用video-download下载）
2. **API支持**: 支持OpenAI兼容的任何API（如硅基流动、OpenAI API等）
3. **模型支持**: 推荐使用支持视频输入的模型，如Qwen3.5-35B-A3B、GPT-4o等
