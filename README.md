# 今日头条视频下载器 - Android APK

使用 Kivy + Buildozer 构建的 Android 应用，支持在手机上直接下载今日头条视频。

## 功能

- ✅ 粘贴分享链接自动解析
- ✅ 支持短链接 (`m.toutiao.com/is/xxxxx`)
- ✅ 自动提取视频标题作为文件名
- ✅ 一键下载到手机存储

## 项目结构

```
toutiao-apk/
├── main.py              # 主程序 (Kivy UI)
├── buildozer.spec       # Buildozer 打包配置
├── .github/
│   └── workflows/
│       └── build-apk.yml    # GitHub Actions 自动打包
└── README.md
```

## 本地打包

### 环境要求

- Python 3.8+
- Ubuntu 20.04+ (推荐) 或 Docker
- Java JDK 17

### 步骤

```bash
# 1. 安装依赖
pip install buildozer cython

# 2. 安装 Android 依赖 (Ubuntu)
sudo apt-get update
sudo apt-get install -y git zip unzip openjdk-17-jdk \
    python3-pip autoconf libtool pkg-config zlib1g-dev \
    libncurses5-dev libncursesw5-dev libtinfo5 cmake \
    libffi-dev libssl-dev automake

# 3. 构建 APK
buildozer android debug

# 4. 输出文件在 bin/ 目录
```

## GitHub Actions 自动打包

1. **Fork 本仓库** 到你的 GitHub 账号

2. **启用 GitHub Actions**: 进入仓库 Settings → Actions → General → 选择 "Allow all actions and reusable workflows"

3. **触发构建**:
   - 推送代码到 `main` 分支会自动触发
   - 或手动触发: 进入 Actions 标签 → 选择 "Build Android APK" → 点击 "Run workflow"

4. **下载 APK**:
   - 构建完成后，进入 Actions 页面 → 点击最新的 workflow run
   - 在 Artifacts 区域下载 `toutiao-downloader-apk`
   - 或在 Releases 页面下载

## 安装使用

1. 下载 APK 文件到手机
2. 允许安装未知来源应用
3. 安装后授予存储权限
4. 打开应用，粘贴今日头条分享链接即可下载

## 注意事项

- 首次启动可能需要几秒钟加载
- 下载的视频保存在手机 Download 目录
- 需要网络连接和存储权限

## 技术栈

- [Kivy](https://kivy.org/) - Python GUI 框架
- [Buildozer](https://github.com/kivy/buildozer) - Android 打包工具
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 视频下载引擎
- [python-for-android](https://github.com/kivy/python-for-android) - Python Android 工具链
