# FrameKeeper - 智能屏幕截图工具

FrameKeeper 是一个强大的自动化屏幕截图工具，专为需要定期捕捉屏幕内容的用户设计。它提供高效的后台截图功能，智能文件管理，以及丰富的后期处理选项，让您轻松记录电脑活动。

## 主要功能

### 🖥️ 自动化截图
- 可配置的时间间隔自动截图（默认10秒）
- 后台静默运行，不影响日常工作
- 系统托盘图标实时显示运行状态

### 📂 智能文件管理
- 自动创建编号子文件夹（每文件夹最多存储10000张图片）
- 按时间戳命名文件，方便查找
- 支持PNG（无损）和JPG（可调质量）格式

### 🧹 冗余清理
- 智能清理不符合时间间隔的冗余截图
- 生成详细清理日志（保存到桌面）
- 安全确认机制防止误删

### 🎬 视频导出
- 将截图序列转换为视频文件（MP4格式）
- 可自定义帧率（1-60 FPS）
- 实时进度显示和剩余时间估算
- 多线程优化处理速度

### ⚙️ 全面配置
- 图形化设置界面
- 可调整截图间隔、保存路径、图片格式
- JPG质量精细控制（1-100）
- 开机自启选项

## 使用说明

### 基本操作
1. 启动程序后，图标将出现在系统托盘
2. 右键点击图标打开菜单：
   - **开始截图**/停止截图
   - **清理冗余截图** - 删除不符合间隔的截图
   - **导出为视频** - 将截图序列转换为MP4
   - **设置** - 调整程序参数
   - **退出** - 关闭程序

### 首次使用
程序会自动在用户目录创建保存路径：
```
~/FrameKeeper_Captures/
   ├── 1/
   ├── 2/
   └── ... 
```

## 技术细节

### 系统要求
- Windows 操作系统
- Python 3.6+
- 支持高DPI显示

### 依赖安装
```bash
pip install opencv-python pillow pystray psutil
```

### 运行程序
```bash
python FrameKeeper.py
```

## 高级功能

### 内存优化
- 智能内存监控（95%阈值）
- 自适应处理速度
- 队列管理系统防止内存溢出

### 多线程架构
- 生产者-消费者模式
- 并行图片解码
- 高效视频编码

### 系统集成
- 注册表实现开机自启
- 单实例运行检查
- 高DPI显示支持

## 注意事项
1. 首次清理冗余截图前会要求确认
2. 视频导出过程中可随时取消
3. 程序通过系统托盘图标控制，不显示主窗口

---

FrameKeeper 是开发日志记录、教程制作、远程监控等场景的理想工具，提供稳定高效的屏幕捕捉解决方案。
