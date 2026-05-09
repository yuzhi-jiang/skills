---
name: android-sdk-setup
description: 在 Windows 上不依赖 Android Studio 安装 Android SDK + JDK 环境。当用户遇到 ERR_SDK_NOT_FOUND、Android SDK 找不到、cap run android 失败、或需要配通安卓构建环境时使用此技能。也适用于用户明确说"装 SDK"、"配安卓环境"、"不用 Android Studio 跑 Android 项目"等场景。
---

# Android SDK Setup (Windows, No Android Studio)

在 Windows 上安装 JDK + Android SDK 命令行工具，无需安装 Android Studio。

## 前置判断

经用户同意后，检查当前环境：

```powershell
java -version
echo $env:JAVA_HOME
echo $env:ANDROID_HOME
echo $env:ANDROID_SDK_ROOT
Get-PSDrive -PSProvider FileSystem
if ($env:ANDROID_HOME) { Test-Path $env:ANDROID_HOME; Get-ChildItem $env:ANDROID_HOME -ErrorAction SilentlyContinue }
```

如果 `npx cap run android` 报 `ERR_SDK_NOT_FOUND`，说明 ANDROID_HOME 未设置或路径无效。

**隐私与用户确认原则**：

- 不能直接替用户决定安装位置、下载位置、环境变量值、PATH 顺序，或是否复用已有 SDK/JDK。
- 任何会读取用户磁盘、列出目录、下载文件、解压文件、删除/覆盖文件、修改环境变量、修改 PATH 的操作，都应先说明目的并询问用户确认。
- 可以根据现有 `JAVA_HOME`、`ANDROID_HOME`、`ANDROID_SDK_ROOT`、磁盘剩余空间、项目路径和已有 SDK 目录推荐安装位置，但必须让用户决定是否使用。
- 如果发现已有可用 SDK/JDK，优先询问用户是否复用，而不是直接安装新的副本。
- 推荐目录时避免暴露不必要的个人路径信息；只展示完成决策所需的路径和空间信息。

在执行任何检查或安装命令前，向用户确认：

1. 是否允许检查现有 JDK/Android SDK 环境变量和磁盘空间。
2. 推荐安装目录是否可以使用，或用户希望改用哪个目录。
3. 是否允许下载和解压 JDK / Android SDK cmdline-tools。
4. 是否允许接受 Android SDK 许可协议并安装对应 SDK 组件。
5. 是否允许修改用户级环境变量和 PATH。

## 第一步：确定项目需要的 SDK 版本

读取项目的 `android/variables.gradle` 获取 `compileSdkVersion`，同时查看 `android/build.gradle`（或 `capacitor.build.gradle`）中的 `JavaVersion.VERSION_XX` 确定 JDK 版本要求。

- AGP 8.x 通常需要 JDK 17+，但 Capacitor 新版自带 `VERSION_21` → 需要 JDK 21
- compileSdkVersion 决定要安装 `platforms;android-XX`
- build-tools 选对应主版本号的最新稳定版

## 第二步：确认安装目录

根据前置检查结果向用户推荐目录，例如：

- 如果已有有效 `JAVA_HOME` 且版本满足项目要求，推荐复用该 JDK。
- 如果已有有效 `ANDROID_HOME` 或 `ANDROID_SDK_ROOT`，推荐复用该 Android SDK。
- 如果没有可用环境，推荐选择剩余空间充足的非系统盘，例如 `<用户确认的根目录>\jdk` 和 `<用户确认的根目录>\android-sdk`。
- 如果只能使用系统盘，提醒用户 SDK 会占用较多空间，并让用户确认。

不要在未确认的情况下默认使用 `D:\SDK`、用户目录、项目目录或任何其他路径。

后续命令中的路径都用占位符表示：

- `<JDK_DIR>`：用户确认的 JDK 安装目录
- `<ANDROID_SDK_DIR>`：用户确认的 Android SDK 安装目录
- `<DOWNLOAD_DIR>`：用户确认的临时下载目录

## 第三步：安装 JDK

用户确认目录和下载权限后，从 Adoptium 下载 JDK（优先 JDK 21，除非项目明确要其他版本）：

```powershell
# 下载（PowerShell）
Invoke-WebRequest -Uri 'https://api.adoptium.net/v3/binary/latest/21/ga/windows/x64/jdk/hotspot/normal/eclipse?project=jdk' -OutFile '<DOWNLOAD_DIR>\jdk.zip'

# 解压
Expand-Archive -Force -LiteralPath '<DOWNLOAD_DIR>\jdk.zip' -DestinationPath '<DOWNLOAD_DIR>\jdk_tmp'

# 整理到目标目录（jdk 解压后有一层版本号子目录，挪到父级）
# 如果目标目录已有内容，必须先询问用户是否覆盖、清空或改用其他目录
Move-Item '<DOWNLOAD_DIR>\jdk_tmp\<jdk-version>\*' '<JDK_DIR>\'
Remove-Item -Recurse -Force '<DOWNLOAD_DIR>\jdk_tmp', '<DOWNLOAD_DIR>\jdk.zip'
```

验证：`<JDK_DIR>\bin\java.exe -version`

## 第四步：安装 Android SDK

### 3.1 下载 cmdline-tools

用户确认 Android SDK 目录和下载权限后，下载 cmdline-tools：

```powershell
Invoke-WebRequest -Uri 'https://dl.google.com/android/repository/commandlinetools-win-13114758_latest.zip' -OutFile '<DOWNLOAD_DIR>\cmdline-tools.zip'

Expand-Archive -Force -LiteralPath '<DOWNLOAD_DIR>\cmdline-tools.zip' -DestinationPath '<ANDROID_SDK_DIR>\cmdline-tools'
```

**关键**：解压后需要将内层目录重命名为 `latest`：

```powershell
# 解压后结构为 <ANDROID_SDK_DIR>\cmdline-tools\cmdline-tools\
# 必须移到 <ANDROID_SDK_DIR>\cmdline-tools\latest\
Move-Item '<ANDROID_SDK_DIR>\cmdline-tools\cmdline-tools' '<ANDROID_SDK_DIR>\cmdline-tools\latest'
Remove-Item -Force '<DOWNLOAD_DIR>\cmdline-tools.zip'
```

### 3.2 安装 SDK 组件

先用 `--list` 确认包名，然后安装：

```powershell
# 设置临时环境变量供此命令使用
$env:JAVA_HOME='<JDK_DIR>'
$env:ANDROID_SDK_ROOT='<ANDROID_SDK_DIR>'

# 列出可用包（可选）
& '<ANDROID_SDK_DIR>\cmdline-tools\latest\bin\sdkmanager.bat' --sdk_root='<ANDROID_SDK_DIR>' --list
```

安装（根据 compileSdkVersion 替换版本号）。只有在用户确认接受 Android SDK 许可协议后，才能管道 `y`：

```powershell
$env:JAVA_HOME='<JDK_DIR>'
"y" | & '<ANDROID_SDK_DIR>\cmdline-tools\latest\bin\sdkmanager.bat' --sdk_root='<ANDROID_SDK_DIR>' "platforms;android-<compileSdk>" "build-tools;<latest-build-tools>" "platform-tools"
```

示例（compileSdkVersion=36）：
```powershell
"y" | & '<ANDROID_SDK_DIR>\cmdline-tools\latest\bin\sdkmanager.bat' --sdk_root='<ANDROID_SDK_DIR>' "platforms;android-36" "build-tools;36.1.0" "platform-tools"
```

## 第五步：设置环境变量

修改环境变量前必须再次向用户确认将写入的具体值：

- `JAVA_HOME=<JDK_DIR>`
- `ANDROID_HOME=<ANDROID_SDK_DIR>`
- `ANDROID_SDK_ROOT=<ANDROID_SDK_DIR>`
- PATH 增加 `<JDK_DIR>\bin`、`<ANDROID_SDK_DIR>\platform-tools`、`<ANDROID_SDK_DIR>\cmdline-tools\latest\bin`

```powershell
# JAVA_HOME
[System.Environment]::SetEnvironmentVariable("JAVA_HOME", "<JDK_DIR>", "User")

# ANDROID_HOME 和 ANDROID_SDK_ROOT
[System.Environment]::SetEnvironmentVariable("ANDROID_HOME", "<ANDROID_SDK_DIR>", "User")
[System.Environment]::SetEnvironmentVariable("ANDROID_SDK_ROOT", "<ANDROID_SDK_DIR>", "User")

# 更新 PATH（添加到用户 PATH；添加到前面还是后面需要询问用户）
$currentPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
$entries = @("<JDK_DIR>\bin", "<ANDROID_SDK_DIR>\platform-tools", "<ANDROID_SDK_DIR>\cmdline-tools\latest\bin")
foreach ($e in $entries) {
  if ($currentPath -notlike "*$e*") {
    $currentPath = "$e;$currentPath"
  }
}
[System.Environment]::SetEnvironmentVariable("PATH", $currentPath, "User")
```

## 第六步：验证

```powershell
$env:JAVA_HOME='<JDK_DIR>'
$env:ANDROID_HOME='<ANDROID_SDK_DIR>'
$env:PATH="$env:JAVA_HOME\bin;$env:ANDROID_HOME\platform-tools;$env:ANDROID_HOME\cmdline-tools\latest\bin;$env:PATH"

java -version
adb version
Get-ChildItem "$env:ANDROID_HOME\platforms\"
Get-ChildItem "$env:ANDROID_HOME\build-tools\"
```

然后尝试编译：

```powershell
$env:JAVA_HOME='<JDK_DIR>'
$env:ANDROID_HOME='<ANDROID_SDK_DIR>'
Set-Location android
.\gradlew compileDebugJavaWithJavac
```

## 第七步：提示用户

安装完成后明确告知用户：
1. **必须重启终端** — 新设的环境变量只在新窗口生效
2. **需要安卓设备** — `cap run android` 需要连接真机（USB 调试）或启动模拟器
3. **模拟器需 Android Studio** — 目前没有独立的 AVD Manager，要跑模拟器还是要装 Android Studio

## 常见问题

### `无效的源发行版：21` / `source release 21`
JDK 版本太低，项目要求 JDK 21。下载 JDK 21 替换。

### `sdkmanager: command not found`
sdkmanager 是 Windows `.bat` 文件，在 Git Bash 中需要用 `powershell` 或 `cmd /c` 调用，不能直接执行。

### 许可协议未接受导致安装失败
sdkmanager 会提示 `Accept? (y/N):`。先询问用户是否接受许可协议；用户确认后，再用 `"y" | & sdkmanager.bat ...` 的方式传入确认。

### `No valid Android SDK root found`
ANDROID_HOME 未设置或指向的路径不存在有效的 SDK 目录结构（必须有 `platforms/`、`build-tools/` 等子目录）。
