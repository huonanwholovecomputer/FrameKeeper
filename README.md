markdown
# FrameKeeper

![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)

FrameKeeper 是一款轻量级的、基于系统托盘的 Windows 应用程序，专为按固定间隔自动捕获屏幕截图而设计。它是为您工作创建延时视频、监控长时间运行的进程或保留屏幕活动的可视化日志的理想工具。捕获的帧按项目进行组织，并可以轻松导出为视频文件。

## 目录

- [主要功能](#主要功能)
- [工作原理](#工作原理)
- [安装指南](#安装指南)
- [使用方法](#使用方法)
  - [系统托盘菜单](#系统托盘菜单)
- [配置](#配置)
- [依赖项](#依赖项)
- [许可证](#许可证)

## 主要功能

-   **自动截图**: 按用户定义的时间间隔捕获整个屏幕。
-   **系统托盘运行**: 在系统托盘中静默运行，方便访问所有功能，而不会使任务栏变得混乱。
-   **项目化管理**: 将捕获的截图保存在不同的项目文件夹中，方便管理不同的录制会话。
-   **优化的视频导出**: 使用 FFmpeg 将捕获的图像合成为 MP4 视频，采用多线程处理以提高速度，并动态计算比特率以获得最佳质量和文件大小。
-   **帧清理功能**: 提供一个实用工具，可以根据捕获间隔删除冗余帧，从而节省磁盘空间。
-   **可自定义配置**: 轻松调整截图间隔、图像格式 (JPG/PNG)、JPG 质量和保存位置等设置。
-   **开机自启**: 可配置在系统启动时自动运行。
-   **高DPI支持**: 用户界面和图标会根据高分辨率显示器进行缩放。
-   **单实例运行**: 使用锁文件机制防止应用程序的多个实例同时运行。

## 工作原理

FrameKeeper 作为一个后台进程运行，可从 Windows 系统托盘访问。激活后，它会按指定的时间间隔进行屏幕截图。

这些截图被保存在一个结构化的文件夹系统中。基础目录默认为您用户文件夹下的 `FrameKeeper_Captures`。在此目录中，会为每个“项目”创建一个文件夹。在项目文件夹内，图像存储在编号的子文件夹中（例如，“1”，“2”，...）。为了确保高效的文件系统性能，每捕获 10,000 张图像后就会创建一个新的子文件夹。

## 安装指南

**1. 前提条件:**

-   **Python 3**: 确保您的系统上已安装 Python 3。您可以从 [python.org](https://www.python.org/) 下载。
-   **FFmpeg**: FrameKeeper 的视频导出功能需要 FFmpeg。
    -   从 [ffmpeg.org](https://ffmpeg.org/download.html) 下载 FFmpeg。
    -   下载后，在 `FrameKeeper.py` 脚本所在的目录中创建一个名为 `_internal` 的文件夹。
    -   解压下载的 FFmpeg 文件，并将 `ffmpeg.exe` 放入 `_internal` 文件夹中。最终路径应如下所示：`.../FrameKeeper/_internal/ffmpeg.exe`。

**2. 克隆仓库 (可选):**

如果您从 Git 仓库获取代码，可以执行以下操作：
```bash
git clone [https://github.com/your-username/FrameKeeper.git](https://github.com/your-username/FrameKeeper.git)
cd FrameKeeper
````

**3. 安装 Python 依赖:**

使用 pip 安装所需的 Python 库。可以创建一个包含以下内容的 `requirements.txt` 文件：

```
opencv-python-headless
psutil
pystray
numpy
Pillow
```

运行以下命令进行安装：

```bash
pip install -r requirements.txt
```

## 使用方法

要运行该应用程序，请执行主 Python 脚本：

```bash
python FrameKeeper_0.6.1(为打包作准备：FFmpeg相对路径、代码注释).py
```

应用程序启动后，一个图标将出现在您的系统托盘中。主窗口默认是隐藏的。右键单击托盘图标以访问菜单。

### 系统托盘菜单

  - **状态**: 显示截图功能是 `运行中` 还是 `已停止`。
  - **开始/停止截图**: 启动或停止屏幕捕获过程。托盘图标会改变以指示状态（红色表示运行，灰色表示停止）。
  - **切换项目**: 允许您在不同的项目文件夹之间切换以保存截图。通过在您的 `base_save_path` 中创建一个新文件夹即可创建新项目。
  - **清理冗余截图**: 扫描当前项目文件夹，并删除那些捕获速度快于配置间隔的图像，只保留任何快速序列中的第一张图片。包含已删除文件详细信息的日志文件将保存到您的桌面。
  - **导出为视频**: 打开一个对话框，选择一个项目文件夹，然后将其所有截图编译成一个 MP4 视频文件。系统将提示您为输出视频设置帧率（FPS）。
  - **设置**: 打开设置窗口，您可以在其中配置应用程序。
  - **退出**: 停止应用程序并从系统托盘中移除图标。

## 配置

设置存储在位于 `%APPDATA%/FrameKeeper/` 的 `config.ini` 文件中。这些设置可以通过应用程序中的“设置”窗口进行修改。

  - **截图间隔 (秒)**: 每次截图之间等待的时间。
  - **程序储存目录**: 存储所有项目文件夹的根目录。
  - **图片格式**: 在 `JPG`（文件更小）和 `PNG`（无损质量）之间选择。
  - **JPG 压缩质量**: JPG 图像质量的值，范围从 1 到 100。值越高，质量越好，文件也越大。如果选择 PNG，此设置将被禁用。
  - **开机自启**: 如果选中，应用程序将被添加到 Windows 注册表，以便在启动时自动运行。

## 依赖项

### Python 库

  - `re`
  - `os`
  - `sys`
  - `cv2` (OpenCV)
  - `time`
  - `queue`
  - `psutil`
  - `ctypes`
  - `shutil`
  - `pystray`
  - `tempfile`
  - `threading`
  - `subprocess`
  - `numpy`
  - `configparser`
  - `tkinter`
  - `winreg`
  - `PIL` (Pillow)

### 外部程序

  - **FFmpeg**: “导出为视频”功能所必需。

## 许可证

该项目根据 MIT 许可证授权。有关详细信息，请参阅 LICENSE 文件。
