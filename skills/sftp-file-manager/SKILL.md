---
name: sftp-file-manager
description: 通过 SFTP/FTP/FTPS 管理 NAS 文件，支持上传、下载、删除、目录浏览。适用于 Windows/Linux，通常只需 Python 依赖即可使用。
metadata: {"openclaw": {"requires": {"bins": ["uv"]}, "env": ["FILE_PROTOCOL", "SFTP_HOST", "SFTP_USER", "SFTP_PASSWORD", "FTP_HOST", "FTP_USER", "FTP_PASSWORD", "SFTP_KEY_FILE", "SFTP_KEY_PASSPHRASE", "SFTP_REMOTE_ROOT", "FTP_REMOTE_ROOT", "REMOTE_ROOT"]}, "primaryEnv": "FILE_PROTOCOL"}
---

# SFTP/FTP File Manager

通过 `scripts/sftp_files.py` 使用 SFTP/FTP/FTPS 管理 NAS 文件，支持：
- 上传（`upload`）
- 下载（`download`）
- 删除（`delete`）
- 浏览目录（`list`）

## 协议支持

- `sftp`（SSH File Transfer Protocol，常见端口 `22`）
- `ftp`（明文 FTP，常见端口 `21`）
- `ftps`（FTP over TLS，常见端口 `21` 显式 / `990` 隐式）

建议优先使用 `sftp` 或 `ftps`。

可通过两种方式指定协议：
- `--protocol sftp|ftp|ftps`
- `--host sftp://...` / `ftp://...` / `ftps://...`（自动识别）


## 依赖

在技能目录执行：

```bash
uv sync
```

## 配置

可选配置文件：`scripts/.env`（由 `scripts/.env.example` 复制）

支持变量：
- `FILE_PROTOCOL`（`sftp`/`ftp`/`ftps`）
- `SFTP_HOST`
- `SFTP_PORT`（SFTP 默认 `22`）
- `SFTP_USER`
- `SFTP_PASSWORD`
- `FTP_HOST`
- `FTP_PORT`（FTP/FTPS 默认 `21`）
- `FTP_USER`
- `FTP_PASSWORD`
- `SFTP_KEY_FILE`
- `SFTP_KEY_PASSPHRASE`
- `SFTP_REMOTE_ROOT`（默认 `/`）
- `FTP_REMOTE_ROOT`（默认 `/`）
- `REMOTE_ROOT`（默认 `/`，通用）

优先级：CLI 参数 > 系统环境变量 > `scripts/.env`。

## 命令

### 列目录（FTPS）

```bash
uv run scripts/sftp_files.py --protocol ftps list --remote "."
```

### 上传文件（FTP）

```bash
uv run scripts/sftp_files.py --protocol ftp upload --local "C:/tmp/a.txt" --remote "upload/a.txt"
```

### 下载文件（SFTP）

```bash
uv run scripts/sftp_files.py --protocol sftp download --remote "upload/a.txt" --local "C:/tmp/a.txt"
```

### 删除文件

```bash
uv run scripts/sftp_files.py --protocol ftp delete --remote "upload/a.txt"
```

### 目录操作

目录上传、下载、删除都需要显式传 `--recursive`。

## Agent 执行说明

当用户提出这些意图时激活本技能：
- 上传文件到 NAS
- 从 NAS 下载文件
- 删除 NAS 文件或目录
- 查看 NAS 目录内容

执行流程：
1. 确认连接参数（`host/user/password` 或 `key-file`）。
2. 执行对应命令。
3. 将 JSON 输出整理成摘要，重点展示状态、源路径、目标路径。
4. 目录类删除操作保持谨慎，确认后使用 `--recursive`。

## 常见问题

### `Error reading SSH protocol banner`

通常表示目标端口不是 SFTP/SSH 服务，例如把 FTPS（`21`）当成了 SFTP。

可按下面排查：
1. 确认 NAS 是否开启了 SSH/SFTP 服务。
2. 如果 NAS 是 FTPS，请在命令中设置 `--protocol ftps`（或 `FILE_PROTOCOL=ftps`）。
3. 如果 NAS 是 FTP，请使用 `--protocol ftp`。

