---
name: android-sdk-setup
description: 在 Windows 上不依赖 Android Studio 安装 Android SDK + JDK 环境。当用户遇到 ERR_SDK_NOT_FOUND、Android SDK 找不到、cap run android 失败、或需要配通安卓构建环境时使用此技能。也适用于用户明确说"装 SDK"、"配安卓环境"、"不用 Android Studio 跑 Android 项目"等场景。
---

# Android SDK Setup (Windows, No Android Studio)

在 Windows 上安装 JDK + Android SDK 命令行工具，无需安装 Android Studio。

## 前置判断

先检查当前环境：

```bash
java -version
echo $JAVA_HOME
echo $ANDROID_HOME
ls "$ANDROID_HOME" 2>/dev/null
```

如果 `npx cap run android` 报 `ERR_SDK_NOT_FOUND`，说明 ANDROID_HOME 未设置或路径无效。

## 第一步：确定项目需要的 SDK 版本

读取项目的 `android/variables.gradle` 获取 `compileSdkVersion`，同时查看 `android/build.gradle`（或 `capacitor.build.gradle`）中的 `JavaVersion.VERSION_XX` 确定 JDK 版本要求。

- AGP 8.x 通常需要 JDK 17+，但 Capacitor 新版自带 `VERSION_21` → 需要 JDK 21
- compileSdkVersion 决定要安装 `platforms;android-XX`
- build-tools 选对应主版本号的最新稳定版

## 第二步：安装 JDK

从 Adoptium 下载 JDK（优先 JDK 21，除非项目明确要其他版本）：

```bash
# 下载（PowerShell）
powershell -Command "Invoke-WebRequest -Uri 'https://api.adoptium.net/v3/binary/latest/21/ga/windows/x64/jdk/hotspot/normal/eclipse?project=jdk' -OutFile 'D:\SDK\jdk.zip'"

# 解压
powershell -Command "Expand-Archive -Force -LiteralPath 'D:\SDK\jdk.zip' -DestinationPath 'D:\SDK\jdk_tmp'"

# 整理到目标目录（jdk 解压后有一层版本号子目录，挪到父级）
# 如果目标目录已有旧版本，先清空
rm -rf /d/SDK/jdk/*
mv /d/SDK/jdk_tmp/<jdk-version>/* /d/SDK/jdk/
rm -rf /d/SDK/jdk_tmp /d/SDK/jdk.zip
```

验证：`/d/SDK/jdk/bin/java -version`

## 第三步：安装 Android SDK

### 3.1 下载 cmdline-tools

```bash
powershell -Command "Invoke-WebRequest -Uri 'https://dl.google.com/android/repository/commandlinetools-win-13114758_latest.zip' -OutFile 'D:\SDK\cmdline-tools.zip'"

powershell -Command "Expand-Archive -Force -LiteralPath 'D:\SDK\cmdline-tools.zip' -DestinationPath 'D:\SDK\android-sdk\cmdline-tools'"
```

**关键**：解压后需要将内层目录重命名为 `latest`：

```bash
# 解压后结构为 D:\SDK\android-sdk\cmdline-tools\cmdline-tools\
# 必须移到 D:\SDK\android-sdk\cmdline-tools\latest\
mv /d/SDK/android-sdk/cmdline-tools/cmdline-tools /d/SDK/android-sdk/cmdline-tools/latest
rm /d/SDK/cmdline-tools.zip
```

### 3.2 安装 SDK 组件

先用 `--list` 确认包名，然后安装：

```bash
# 设置临时环境变量供此命令使用
export JAVA_HOME=/d/SDK/jdk
export ANDROID_SDK_ROOT=/d/SDK/android-sdk

# 列出可用包（可选）
powershell -Command '$env:JAVA_HOME="D:\SDK\jdk"; & "D:\SDK\android-sdk\cmdline-tools\latest\bin\sdkmanager.bat" --sdk_root="D:\SDK\android-sdk" --list' | grep -E "platforms;android-<XX>|build-tools;<XX>|platform-tools"
```

安装（根据 compileSdkVersion 替换版本号）。**必须管道 `y` 接受许可协议**：

```bash
powershell -Command '$env:JAVA_HOME="D:\SDK\jdk"; "y" | & "D:\SDK\android-sdk\cmdline-tools\latest\bin\sdkmanager.bat" --sdk_root="D:\SDK\android-sdk" "platforms;android-<compileSdk>" "build-tools;<latest-build-tools>" "platform-tools"'
```

示例（compileSdkVersion=36）：
```bash
powershell -Command '"y" | & "D:\SDK\android-sdk\cmdline-tools\latest\bin\sdkmanager.bat" --sdk_root="D:\SDK\android-sdk" "platforms;android-36" "build-tools;36.1.0" "platform-tools"'
```

## 第四步：设置环境变量

```bash
# JAVA_HOME
powershell -Command '[System.Environment]::SetEnvironmentVariable("JAVA_HOME", "D:\SDK\jdk", "User")'

# ANDROID_HOME 和 ANDROID_SDK_ROOT
powershell -Command '[System.Environment]::SetEnvironmentVariable("ANDROID_HOME", "D:\SDK\android-sdk", "User")'
powershell -Command '[System.Environment]::SetEnvironmentVariable("ANDROID_SDK_ROOT", "D:\SDK\android-sdk", "User")'

# 更新 PATH（添加到用户 PATH 前面，避免与其他 Java 冲突）
powershell -Command '
  $currentPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
  $entries = @("D:\SDK\jdk\bin", "D:\SDK\android-sdk\platform-tools", "D:\SDK\android-sdk\cmdline-tools\latest\bin")
  foreach ($e in $entries) {
    if ($currentPath -notlike "*$e*") {
      $currentPath = "$e;$currentPath"
    }
  }
  [System.Environment]::SetEnvironmentVariable("PATH", $currentPath, "User")
'
```

## 第五步：验证

```bash
export JAVA_HOME=/d/SDK/jdk
export ANDROID_HOME=/d/SDK/android-sdk
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"

java -version
adb version
ls "$ANDROID_HOME/platforms/"
ls "$ANDROID_HOME/build-tools/"
```

然后尝试编译：

```bash
export JAVA_HOME=/d/SDK/jdk
export ANDROID_HOME=/d/SDK/android-sdk
cd android && ./gradlew compileDebugJavaWithJavac
```

## 第六步：提示用户

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
sdkmanager 会提示 `Accept? (y/N):`，必须管道 `y` 进去。用 `"y" | & sdkmanager.bat ...` 的方式自动接受。

### `No valid Android SDK root found`
ANDROID_HOME 未设置或指向的路径不存在有效的 SDK 目录结构（必须有 `platforms/`、`build-tools/` 等子目录）。
