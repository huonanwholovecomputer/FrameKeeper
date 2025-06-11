import os
import sys
import cv2
import time
import ctypes
import pystray
import threading
import tkinter as tk
import winreg as reg
from pystray import MenuItem as item
from PIL import Image, ImageGrab, ImageDraw, ImageFilter
from tkinter import ttk, filedialog, messagebox, simpledialog

# FrameKeeper - 一个简单的屏幕截图和录屏工具
# 版本: 1.0
# 作者: huonanwholovecomputer
# 日期: 2025年6月11日
# 说明: 该工具允许用户定时捕获屏幕截图，录制指定帧数的视频，并提供托盘图标进行操作。

# --- 全局配置变量 ---
class Config:
    def __init__(self):
        self.interval = 10
        self.save_path = os.path.join(os.path.expanduser("~"), "FrameKeeper_Captures")
        self.format = "JPG"  # 修改此处：默认格式从 PNG 改为 JPG
        self.jpg_quality = 95
        self.is_running = False
        self.auto_start = False

config = Config()

# --- 核心功能 ---

def set_dpi_aware():
    """设置程序为 Per-Monitor DPI Aware"""
    try:
        # Windows 8.1+ 支持 Per-Monitor DPI
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except AttributeError:
        # Windows 7 或更早版本
        ctypes.windll.user32.SetProcessDPIAware()  # PROCESS_SYSTEM_DPI_AWARE
    except Exception as e:
        print(f"设置 DPI 感知失败: {e}")

def take_screenshot():
    """捕获全屏截图并根据配置保存。"""
    if not os.path.exists(config.save_path):
        os.makedirs(config.save_path)

    screenshot = ImageGrab.grab()
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"capture_{timestamp}.{config.format.lower()}"
    filepath = os.path.join(config.save_path, filename)

    if config.format == "JPG":
        screenshot.save(filepath, "JPEG", quality=config.jpg_quality)
    else:  # PNG格式
        # 添加 compress_level=0 来禁用PNG压缩
        screenshot.save(filepath, "PNG", compress_level=0)
    print(f"截图已保存至: {filepath}")

def screenshot_loop():
    """根据设定的间隔重复执行截图任务。"""
    while config.is_running:
        take_screenshot()
        time.sleep(config.interval)

def start_screenshotting(icon):
    if not config.is_running:
        config.is_running = True
        icon.icon = create_icon("on")
        update_menu(icon)
        thread = threading.Thread(target=screenshot_loop, daemon=True)
        thread.start()
        print("截图功能已启动。")

def stop_screenshotting(icon):
    if config.is_running:
        config.is_running = False
        icon.icon = create_icon("off")
        update_menu(icon)
        print("截图功能已停止。")

# --- 开机自启功能 (仅限Windows) ---
def get_startup_key():
    """获取Windows启动项的注册表键。"""
    return reg.HKEY_CURRENT_USER

def get_startup_path():
    """获取注册表中用于开机自启的路径。"""
    return r"Software\Microsoft\Windows\CurrentVersion\Run"

def set_auto_start():
    """将程序添加到开机启动项。"""
    try:
        key = reg.OpenKey(get_startup_key(), get_startup_path(), 0, reg.KEY_ALL_ACCESS)
        # 获取脚本的绝对路径
        script_path = os.path.abspath(sys.argv[0])
        reg.SetValueEx(key, "FrameKeeper", 0, reg.REG_SZ, f'"{sys.executable}" "{script_path}"')
        reg.CloseKey(key)
        config.auto_start = True
        messagebox.showinfo("成功", "已成功设置开机自启！")
    except Exception as e:
        messagebox.showerror("错误", f"设置开机自启失败: {e}")

def remove_auto_start():
    """从开机启动项中移除程序。"""
    try:
        key = reg.OpenKey(get_startup_key(), get_startup_path(), 0, reg.KEY_ALL_ACCESS)
        reg.DeleteValue(key, "FrameKeeper")
        reg.CloseKey(key)
        config.auto_start = False
        messagebox.showinfo("成功", "已成功取消开机自启！")
    except FileNotFoundError:
        messagebox.showinfo("提示", "程序未被设置为开机自启。")
        config.auto_start = False # 确保状态同步
    except Exception as e:
        messagebox.showerror("错误", f"取消开机自启失败: {e}")

def check_auto_start():
    """检查程序是否已设置为开机自启。"""
    try:
        key = reg.OpenKey(get_startup_key(), get_startup_path(), 0, reg.KEY_READ)
        reg.QueryValueEx(key, "FrameKeeper")
        reg.CloseKey(key)
        config.auto_start = True
    except FileNotFoundError:
        config.auto_start = False

# --- UI & 托盘 ---

from PIL import Image, ImageDraw
import tkinter as tk

def get_dpi_scale(root):
    """获取当前屏幕的 DPI 缩放比例"""
    try:
        # 获取主显示器的 DPI 缩放比例
        root.update()  # 确保 root 已初始化
        dpi = root.winfo_fpixels('1i')  # 获取每英寸像素数
        scale = dpi / 96.0  # 标准 DPI 为 96
        return scale
    except Exception as e:
        print(f"获取 DPI 缩放比例失败: {e}")
        return 1.0  # 默认缩放比例为 1

def create_icon(state="off", base_size=64):
    """创建专业风格的录制工具图标"""
    # 获取 DPI 缩放比例
    root = tk.Tk()
    scale = get_dpi_scale(root)
    root.destroy()
    
    size = int(base_size * scale)
    padding = int(4 * scale)
    center = size // 2
    
    # 创建透明背景的图像
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    if state == "on":
        # 录制状态 - 红色脉冲效果
        radius = center - padding
        inner_radius = int(radius * 0.5)
        
        # 外圈红色渐变
        for i in range(radius, radius - int(5*scale), -1):
            alpha = int(200 * (i / radius))
            draw.ellipse(
                [center-i, center-i, center+i, center+i],
                fill=(255, 50, 50, alpha),
                outline=(255, 255, 255, 30)
            )
        
        # 中心实心红圈
        draw.ellipse(
            [center-inner_radius, center-inner_radius, 
             center+inner_radius, center+inner_radius],
            fill=(230, 0, 0),
            outline=(255, 255, 255)
        )
        
        # 中心白色圆点
        dot_radius = int(inner_radius * 0.3)
        draw.ellipse(
            [center-dot_radius, center-dot_radius, 
             center+dot_radius, center+dot_radius],
            fill=(255, 255, 255),
            outline=(200, 200, 200)
        )
        
    else:
        # 非录制状态 - 灰色简约设计
        radius = center - padding
        border_width = int(2 * scale)
        
        # 外圈金属质感
        draw.ellipse(
            [center-radius, center-radius, center+radius, center+radius],
            fill=(100, 100, 100),
            outline=(180, 180, 180),
            width=border_width
        )
        
        # 内圈
        inner_radius = int(radius * 0.7)
        draw.ellipse(
            [center-inner_radius, center-inner_radius, 
             center+inner_radius, center+inner_radius],
            fill=(60, 60, 60),
            outline=(120, 120, 120),
            width=border_width//2
        )
        
        # 中心红点提示
        dot_radius = int(inner_radius * 0.3)
        draw.ellipse(
            [center-dot_radius, center-dot_radius, 
             center+dot_radius, center+dot_radius],
            fill=(150, 0, 0),
            outline=(100, 0, 0)
        )
    
    # 确保radius变量已定义
    if 'radius' not in locals():
        radius = center - padding
        
    # 添加轻微阴影效果
    shadow = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.ellipse(
        [center-radius+2, center-radius+2, 
         center+radius-2, center+radius-2],
        fill=(0, 0, 0, 30)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(2))
    image = Image.alpha_composite(shadow, image)
    
    return image

def get_dpi_scale(root):
    return root.winfo_fpixels('1i') / 72.0

def on_quit(icon):
    stop_screenshotting(icon)
    icon.stop()
    root.quit()

def open_settings_window(icon):
    """打开详细设置窗口。"""
    settings_window = tk.Toplevel()
    settings_window.title("FrameKeeper 设置")
    settings_window.geometry("400x350")
    settings_window.resizable(False, False)

    main_frame = ttk.Frame(settings_window, padding="10")
    main_frame.pack(fill="both", expand=True)

    # 截图间隔
    ttk.Label(main_frame, text="截图间隔 (秒):").grid(row=0, column=0, sticky="w", pady=5)
    interval_var = tk.IntVar(value=config.interval)
    ttk.Entry(main_frame, textvariable=interval_var).grid(row=0, column=1, sticky="ew")

    # 保存路径
    ttk.Label(main_frame, text="保存路径:").grid(row=1, column=0, sticky="w", pady=5)
    path_var = tk.StringVar(value=config.save_path)
    path_entry = ttk.Entry(main_frame, textvariable=path_var)
    path_entry.grid(row=1, column=1, sticky="ew")
    def select_path():
        path = filedialog.askdirectory()
        if path:
            path_var.set(path)
    ttk.Button(main_frame, text="浏览...", command=select_path).grid(row=1, column=2, padx=5)

    # 图片格式
    ttk.Label(main_frame, text="图片格式:").grid(row=2, column=0, sticky="w", pady=5)
    format_var = tk.StringVar(value=config.format)
    format_menu = ttk.Combobox(
        main_frame, textvariable=format_var,
        values=["PNG", "JPG"], state="readonly"
    )
    format_menu.grid(row=2, column=1, sticky="ew")

    # JPG 质量控件
    jpg_frame = ttk.Frame(main_frame)
    jpg_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=5)
    
    # 修复：为"JPG 压缩质量"文本标签创建一个变量引用
    quality_label_text = ttk.Label(jpg_frame, text="JPG 压缩质量:")
    quality_label_text.pack(side="left")
    
    # 滑动条（占据剩余空间）
    quality_var = tk.IntVar(value=config.jpg_quality)
    quality_scale = ttk.Scale(
        jpg_frame, from_=1, to=100, orient="horizontal",
        variable=quality_var
    )
    quality_scale.pack(side="left", expand=True, fill="x", padx=5)
    
    # 固定宽度的数值输入框
    quality_entry = ttk.Entry(jpg_frame, width=4, justify="center")
    quality_entry.pack(side="left")
    quality_entry.insert(0, str(config.jpg_quality))  # 初始值
    
    # 绑定滑动条和输入框的双向同步
    def update_entry_from_scale(val):
        """滑动条拖动时更新输入框"""
        quality_entry.delete(0, tk.END)
        quality_entry.insert(0, str(int(float(val))))
    
    def update_scale_from_entry(event=None):
        """输入框编辑时更新滑动条（需验证输入合法性）"""
        try:
            val = int(quality_entry.get())
            if 1 <= val <= 100:
                quality_var.set(val)
            else:  # 超出范围
                # 回退到有效值
                quality_entry.delete(0, tk.END)
                quality_entry.insert(0, str(quality_var.get()))
        except ValueError:  # 输入非数字
            quality_entry.delete(0, tk.END)
            quality_entry.insert(0, str(quality_var.get()))
    
    quality_scale.config(command=update_entry_from_scale)
    quality_entry.bind("<Return>", update_scale_from_entry)  # 按回车键生效
    quality_entry.bind("<FocusOut>", update_scale_from_entry)  # 失去焦点时生效

    # 切换格式时更新所有JPG质量控件的可用状态
    def toggle_jpg_quality_state(event=None):
        """根据格式选择来禁用或启用 JPG 质量设置"""
        if format_var.get() == "PNG":
            # 禁用所有控件（包括文字标签）
            quality_scale.state(["disabled"])
            quality_entry.state(["disabled"])
            quality_label_text.config(foreground="gray")  # 修复：文字变灰
        else:
            # 启用所有控件
            quality_scale.state(["!disabled"])
            quality_entry.state(["!disabled"])
            quality_label_text.config(foreground="")  # 恢复默认颜色
    
    # 绑定格式选择事件
    format_menu.bind("<<ComboboxSelected>>", toggle_jpg_quality_state)
    # 初始状态设置
    toggle_jpg_quality_state()

    # 开机自启
    auto_start_var = tk.BooleanVar(value=config.auto_start)
    def toggle_auto_start():
        if auto_start_var.get():
            set_auto_start()
        else:
            remove_auto_start()
        check_auto_start()
        auto_start_var.set(config.auto_start)

    ttk.Checkbutton(main_frame, text="开机自启", variable=auto_start_var, command=toggle_auto_start).grid(row=4, column=0, columnspan=2, sticky="w", pady=10)

    # 保存按钮
    def save_settings():
        config.interval = interval_var.get()
        config.save_path = path_var.get()
        config.format = format_var.get()
        config.jpg_quality = quality_var.get()
        messagebox.showinfo("成功", "设置已保存！")
        settings_window.destroy()

    ttk.Button(main_frame, text="保存并关闭", command=save_settings).grid(row=5, column=0, columnspan=3, pady=20)

    main_frame.columnconfigure(1, weight=1)
    
def run_in_main_thread(func, *args):
    root.after(0, func, *args)

def export_to_video(icon):
    temp_window = tk.Toplevel()
    temp_window.withdraw()  # 隐藏临时窗口
    source_dir = filedialog.askdirectory(
        title="选择包含截图的文件夹",
        initialdir=config.save_path,
        parent=temp_window  # 指定父窗口
    )
    if not source_dir:
        temp_window.destroy()
        return

    images = [img for img in os.listdir(source_dir) if img.endswith((".png", ".jpg", ".jpeg"))]
    if not images:
        messagebox.showwarning("无图片", "所选文件夹中没有找到图片文件。", parent=temp_window)
        temp_window.destroy()
        return
    
    images.sort()

    save_path = filedialog.asksaveasfilename(
        defaultextension=".mp4",
        filetypes=[("MP4 files", "*.mp4")],
        title="保存视频文件",
        initialdir=config.save_path,
        parent=temp_window
    )
    if not save_path:
        temp_window.destroy()
        return

    frame_rate = simpledialog.askinteger("帧率", "请输入视频帧率 (FPS):", 
                                         initialvalue=10, minvalue=1, maxvalue=60, 
                                         parent=temp_window)
    if not frame_rate:
        temp_window.destroy()
        return

    first_image_path = os.path.join(source_dir, images[0])
    frame = cv2.imread(first_image_path)
    height, width, layers = frame.shape

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(save_path, fourcc, frame_rate, (width, height))

    for image in images:
        image_path = os.path.join(source_dir, image)
        video.write(cv2.imread(image_path))

    video.release()
    messagebox.showinfo("导出成功", f"视频已成功导出至: {save_path}", parent=temp_window)
    temp_window.destroy()

def set_interval(icon, interval):
    """通过菜单快捷设置截图间隔。"""
    def inner():
        config.interval = interval
        print(f"截图间隔已更改为 {interval} 秒。")
        if config.is_running:
            stop_screenshotting(icon)
            start_screenshotting(icon)
    return inner

def update_menu(icon):
    status_text = "运行中" if config.is_running else "已停止"
    start_stop_item = item('停止截图' if config.is_running else '开始截图',
                           lambda: stop_screenshotting(icon) if config.is_running else start_screenshotting(icon))

    icon.menu = pystray.Menu(
        item(f'状态: {status_text}', None, enabled=False),
        pystray.Menu.SEPARATOR,
        start_stop_item,
        item('快速更改时间间隔', pystray.Menu(
            item('5 秒', set_interval(icon, 5)),
            item('10 秒', set_interval(icon, 10)),
            item('30 秒', set_interval(icon, 30)),
            item('60 秒', set_interval(icon, 60))
        )),
        item('导出为视频', lambda: run_in_main_thread(export_to_video, icon)),
        item('设置', lambda: open_settings_window(icon)),
        pystray.Menu.SEPARATOR,
        item('退出', lambda: on_quit(icon))
    )
    
def main():
    set_dpi_aware()  # 设置 DPI 感知
    global root
    root = tk.Tk()
    root.withdraw()

    check_auto_start()

    icon_image = create_icon("off")
    icon = pystray.Icon("FrameKeeper", icon_image, "FrameKeeper")
    
    update_menu(icon)

    def run_icon(icon):
        icon.run()

    pystray_thread = threading.Thread(target=run_icon, args=(icon,), daemon=True)
    pystray_thread.start()

    root.mainloop()

if __name__ == "__main__":
    try:
        temp_dir = os.environ.get("TEMP", os.path.expanduser("~"))
        lock_file_path = os.path.join(temp_dir, "framekeeper.lock")
        if os.path.exists(lock_file_path):
            print("FrameKeeper 可能已在运行。如果不是，请删除 lock 文件。")
            ctypes.windll.user32.MessageBoxW(0, "FrameKeeper 已在运行中。", "错误", 0x10)
            sys.exit(1)
        
        with open(lock_file_path, "w") as f:
            f.write(str(os.getpid()))

        main()

    finally:
        if os.path.exists(lock_file_path):
            os.remove(lock_file_path)