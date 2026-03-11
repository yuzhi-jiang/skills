# Skills

Skills 是一组可复用的任务能力包（说明文档、脚本与资源），可被 Agent 动态加载，用于稳定完成某类专业任务。

本仓库是一个本地 Skills 示例集合，当前已配置 Marketplace 入口并包含多个可直接使用的技能。

更多资料：
- [What are skills?](https://support.claude.com/en/articles/12512176-what-are-skills)
- [Using skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude)
- [How to create custom skills](https://support.claude.com/en/articles/12512198-creating-custom-skills)

# About This Repository

这个仓库包含本地可用的技能实现，每个技能都放在独立目录中，并通过 `SKILL.md` 描述何时触发、如何执行和输出约定。

当前已提供：
- `skills/memos`：连接 Memos 笔记系统，支持创建、搜索、更新、删除与标签管理
- `skills/video-understand`：使用多模态模型理解视频内容并按提示输出结果
- `skills/sftp-file-manager`：通过 SFTP 管理 NAS 文件（上传、下载、删除、目录浏览），跨平台且仅需 Python 依赖

Marketplace 配置位于：
- `.claude-plugin/marketplace.json`

# Skill Sets

- [./skills](./skills)：本地技能目录
- [./.claude-plugin/marketplace.json](./.claude-plugin/marketplace.json)：Marketplace 注册与插件定义

# Try in Claude Code

如果你的环境支持 Plugin Marketplace，可将本项目作为本地市场来源使用，并安装插件中声明的技能。

典型流程：
1. 确保运行环境可读取 `.claude-plugin/marketplace.json`
2. 安装本地市场中的目标插件（如 `memos-skills`、`video-understand-skill`、`sftp-file-manager-skill`）
3. 调用技能时，参考对应目录下的 `SKILL.md`（如 `skills/sftp-file-manager/SKILL.md`）

# Creating a Basic Skill

创建 Skill 的最小结构通常是一个目录 + 一个 `SKILL.md`：

```markdown
---
name: my-skill-name
description: 说明技能做什么、什么时候用
---

# My Skill Name

在这里写执行步骤、约束、示例与失败处理。
```

建议字段：
- `name`：唯一标识（小写，短横线分隔）
- `description`：明确触发场景与目标产物

# Disclaimer

这些技能用于示例与本地自动化实践。实际效果会受运行环境、依赖安装、外部平台限制和网络状态影响。在生产场景使用前，请先在你的环境中充分验证。

# Reference

- Anthropic skills repository: https://github.com/anthropics/skills
- Anthropic README: https://github.com/anthropics/skills/blob/main/README.md
- Anthropic marketplace example: https://github.com/anthropics/skills/blob/main/.claude-plugin/marketplace.json
