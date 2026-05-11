---
name: pgsql-setup
description: 在 Windows 上安装 PostgreSQL server（不依赖 Docker）。当用户需要安装 PostgreSQL、pgsql、postgres 数据库服务端，或遇到"psql 未找到"、"pg_ctl 不存在"、需要本地起一个 PG 实例时使用此技能。也适用于用户说"装数据库"、"配 PG 环境"、"本地起 postgres"等场景。
---

# PostgreSQL Server Setup (Windows, No Docker)

在 Windows 上安装 PostgreSQL server，不含客户端工具链需求，聚焦服务端部署。

## 前置原则：隐私与用户确认

**所有涉及路径、密码、端口的决策都必须在询问用户后执行，不能默认写入任何固定值。**

需要用户确认的事项：
1. 安装目录（提供推荐，但由用户决定）
2. 数据目录（推荐与安装目录同级分开，方便升级）
3. PostgreSQL 版本
4. superuser `postgres` 的密码
5. 端口号（默认 5432，有冲突时需用户指定）

**推荐目录规则**：
- 优先推荐非系统盘，如 `D:\pgsql\<version>` 或用户指定的工作盘
- 数据目录推荐与安装目录分开，如 `<安装父目录>\data`，以便版本升级时数据不受影响
- 示例推荐：安装到 `D:\pgsql\17`，数据到 `D:\pgsql\17\data`
- 如果用户选择系统盘，提醒 `C:\Program Files` 可能因空格路径带来麻烦，建议用 `C:\PG<version>`

## 第一步：检查现有环境

在执行任何安装操作前，先检查是否已有 PostgreSQL：

```powershell
# 检查命令行工具
Get-Command psql -ErrorAction SilentlyContinue
Get-Command pg_ctl -ErrorAction SilentlyContinue

# 检查 Windows 服务
Get-Service *postgres* -ErrorAction SilentlyContinue | Format-Table Name, Status, DisplayName

# 检查常见安装路径
Test-Path "C:\Program Files\PostgreSQL\*\bin\pg_ctl.exe"
```

如果已有可用实例，询问用户是复用还是重新安装。

## 第二步：向用户确认安装参数

依次询问以下信息（一次性问完，减少打扰）：

1. **版本** — 推荐最新稳定版（查看 winget 或 EDB 官网确认）。提供选项如 17（最新）、16、15
2. **安装目录** — 给出推荐路径，展示可用磁盘空间作为参考
3. **数据目录** — 推荐 `<安装目录>\data`，说明分开存放的好处
4. **superuser 密码** — 如果只是本地开发，可提供 `postgres` 作为简单选项，但提醒安全影响
5. **端口** — 默认 5432，检查是否被占用

使用 AskUserQuestion 工具一次性收集所有参数，避免多次打断用户。

## 第三步：获取安装包

### 方式 A：winget（推荐，自动处理下载和哈希校验）

先搜索确认可用版本：

```powershell
winget search postgresql --accept-source-agreements
```

找到目标版本包名（如 `PostgreSQL.PostgreSQL.17`）后安装：

```powershell
winget install PostgreSQL.PostgreSQL.<版本号> --accept-package-agreements --accept-source-agreements --override "--mode unattended --prefix `<安装路径>` --datadir `<数据路径>` --superpassword <密码> --serviceaccount postgres --serverport <端口>"
```

**注意**：winget 的 `--override` 参数可能不会正确透传给 EDB 安装器。如果安装过程弹出 GUI 窗口或安装无效果，改用方式 B。

### 方式 B：直接下载 EDB 安装器（更可靠）

1. 从 EDB 官网获取最新版本的下载 URL。URL 格式为：

   ```
   https://get.enterprisedb.com/postgresql/postgresql-<版本>-windows-x64.exe
   ```

   例如 `postgresql-17.9-3-windows-x64.exe`。使用 `winget search` 的结果可确认具体版本号。

2. 下载到临时目录：

   ```powershell
   Invoke-WebRequest -Uri "https://get.enterprisedb.com/postgresql/postgresql-<版本>-windows-x64.exe" -OutFile "$env:TEMP\postgresql-installer.exe" -UseBasicParsing
   ```

## 第四步：执行安装

**安装器需要管理员权限**（创建 Windows 服务必须提权）。

在安装前确保目标目录和数据目录不存在或为空（安装器会自己初始化数据目录，已存在的非空目录可能导致失败）：

```powershell
# 如果目录已存在且非空，先询问用户是否清除
Remove-Item "<安装目录>" -Recurse -Force -ErrorAction SilentlyContinue
```

执行静默安装：

```powershell
Start-Process -FilePath "$env:TEMP\postgresql-installer.exe" -ArgumentList '--mode unattended --prefix "<安装目录>" --datadir "<数据目录>" --superpassword <密码> --serviceaccount postgres --serverport <端口>' -Verb RunAs -Wait -PassThru
```

**EDB 安装器参数说明**：
| 参数 | 说明 |
|------|------|
| `--mode unattended` | 静默安装，无 GUI |
| `--prefix <path>` | 安装目录 |
| `--datadir <path>` | 数据目录 |
| `--superpassword <pw>` | postgres 用户密码 |
| `--serviceaccount <acct>` | Windows 服务运行账户，默认 `postgres` |
| `--serverport <port>` | 端口，默认 5432 |
| `--install_plpgsql 1` | 安装 PL/pgSQL 语言（默认已包含） |

**常见失败原因**：
- **未提权**：出现 "The requested operation requires elevation"，需用 `Start-Process -Verb RunAs`
- **数据目录已存在**：安装器会拒绝覆盖非空 data 目录，需先清空
- **端口被占用**：检查 `netstat -ano | findstr :5432`，如有冲突请用户换端口

## 第五步：验证安装

安装完成后逐项检查：

```powershell
# 1. 检查关键文件
Test-Path "<安装目录>\bin\pg_ctl.exe"
Test-Path "<安装目录>\bin\postgres.exe"

# 2. 检查 Windows 服务状态（服务名通常为 postgresql-x64-<主版本号>）
Get-Service *postgres* | Format-Table Name, Status, DisplayName

# 3. 用 psql 连接验证
$env:PGPASSWORD = "<密码>"
& "<安装目录>\bin\psql.exe" -U postgres -p <端口> -c "SELECT version();"
```

如果以上全部通过，安装成功。

## 第六步：收尾

1. 提醒用户 `psql` 路径（`<安装目录>\bin\psql.exe`）
2. 告知可通过运行 `<安装目录>\pg_env.bat` 将 PostgreSQL 加入当前会话 PATH
3. 清理临时安装文件：`Remove-Item "$env:TEMP\postgresql-installer.exe" -Force`
4. 提醒 Windows 服务 `postgresql-x64-<版本>` 已设为自动启动，重启后也会自动运行

## 附：数据库备份与恢复

如果用户在安装后需要从远程库迁移数据：

**从远程备份**：
```powershell
$env:PGPASSWORD = "<远程密码>"
& "<安装目录>\bin\pg_dump.exe" -h <远程IP> -U postgres -p <端口> -d <库名> -F p -f "<输出路径>.sql" --no-owner --no-privileges
```

- `--no-owner --no-privileges` 可避免因目标环境缺少源库的角色/权限导致恢复报错
- `-F p` 输出纯文本 SQL，通用性最好

**恢复到本地**：
```powershell
# 先创建目标库
$env:PGPASSWORD = "<本地密码>"
& "<安装目录>\bin\createdb.exe" -U postgres -p <本地端口> -h localhost <目标库名>

# 导入
& "<安装目录>\bin\psql.exe" -U postgres -p <本地端口> -h localhost -d <目标库名> -f "<备份文件>.sql"
```

**恢复到其他服务器**（给用户的手动命令）：
```bash
# Linux
PGPASSWORD="密码" psql -h <目标IP> -U postgres -p 5432 -d <库名> -f backup.sql

# Windows PowerShell
$env:PGPASSWORD = "密码"; psql -h <目标IP> -U postgres -p 5432 -d <库名> -f backup.sql
```

## 常见问题

### Installer 闪退或无输出
安装器静默执行时无控制台输出是正常的。检查安装目录和 Windows 服务确认是否成功。如果目录为空，通常是因为未以管理员身份运行。

### 服务存在但未启动
```powershell
Start-Service postgresql-x64-<版本>
```

如果启动失败，查看 Windows 事件查看器中的 PostgreSQL 日志，或查看 `<数据目录>\pg_log\` 下的日志文件。

### 连接被拒绝（localhost）
检查 `pg_hba.conf`（在数据目录下），确认本地连接认证方式。默认安装中 `host all all 127.0.0.1/32 scram-sha-256`。
