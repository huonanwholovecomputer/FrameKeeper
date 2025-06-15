import os  # 操作系统接口 - 文件和目录操作
import sys  # 系统相关功能 - 命令行参数、退出程序等
import cv2  # OpenCV库 - 计算机视觉和图像处理
import time  # 时间相关功能 - 延时、计时等
import queue  # 队列 - 线程间通信
import ctypes  # C语言兼容库 - 调用Windows API
import shutil  # 高级文件操作 - 复制、移动、删除等
import pystray  # 系统托盘图标创建和管理
import tempfile  # 临时文件和目录管理
import traceback  # 错误追踪 - 获取异常信息
import threading  # 多线程编程支持
import subprocess  # 子进程管理 - 运行外部程序
import numpy as np  # 数值计算库 - 数组操作等
import configparser  # 配置文件解析器
import tkinter as tk  # GUI工具包 - 创建图形界面
import winreg as reg  # Windows注册表操作
from pystray import MenuItem as item  # 系统托盘菜单项
from PIL import Image, ImageGrab, ImageDraw, ImageFilter  # Python图像处理库 - 图像捕获、编辑等
from tkinter import ttk, filedialog, messagebox, simpledialog  # Tkinter扩展组件 - 文件对话框、消息框等

# 新建一个配置类，用于管理应用程序的配置
class Config:
    # 初始化配置类
    def __init__(self, config_file):
        self.config_file = config_file  # 配置文件路径
        self.config = configparser.ConfigParser()  # 创建配置解析器
        self.interval = 5  # 默认截图间隔为5秒
        self.base_save_path = os.path.join(os.path.expanduser("~"), "FrameKeeper_Captures_2")  # 默认保存路径为用户目录下的FrameKeeper_Captures文件夹
        self.format = "JPG"  # 默认图片格式为JPG
        self.jpg_quality = 95  # 默认JPG压缩质量为95
        self.current_subfolder = "1"  # 当前子文件夹名称
        self.current_file_count = 0   # 当前子文件夹中的文件计数
        self.is_running = False  # 截图是否正在运行
        self.auto_start = False  # 是否开机自启
        self.load_config()  # 加载配置文件
        self.initialize_folder_counter()  # 初始化文件夹计数器

    # 加载配置文件
    def load_config(self):
        if os.path.exists(self.config_file):  # 检查配置文件是否存在
            self.config.read(self.config_file)  # 读取配置文件
            self.interval = self.config.getint("DEFAULT", "interval", fallback=5)  # 获取截图间隔，默认为5秒
            self.base_save_path = self.config.get("DEFAULT", "save_path", fallback=self.base_save_path)
            self.current_subfolder = self.config.get("DEFAULT", "current_subfolder", fallback="1")
            self.format = self.config.get("DEFAULT", "format", fallback="JPG")  # 获取图片格式，默认为JPG
            self.jpg_quality = self.config.getint("DEFAULT", "jpg_quality", fallback=95)  # 获取JPG压缩质量，默认为95
            self.auto_start = self.config.getboolean("DEFAULT", "auto_start", fallback=False)  # 获取是否开机自启，默认为False
        else:  # 如果配置文件不存在，则使用默认值
            self.save_config()  # 保存默认配置到文件

    # 保存配置到文件
    def save_config(self):
        self.config["DEFAULT"] = {"interval": self.interval, "save_path": self.base_save_path, "current_subfolder": self.current_subfolder, "format": self.format, "jpg_quality": self.jpg_quality, "auto_start": self.auto_start}  # 设置默认配置
        with open(self.config_file, "w") as configfile:  # 打开配置文件进行写入
            self.config.write(configfile)  # 写入配置内容

def initialize_folder_counter(self):
    if not os.path.exists(self.base_save_path):
        os.makedirs(self.base_save_path)
    
    try:
        subfolders = [f for f in os.listdir(self.base_save_path) 
                      if os.path.isdir(os.path.join(self.base_save_path, f)) and f.isdigit()]
    except Exception as e:
        print(f"Error listing subfolders in {self.base_save_path}: {e}")
        subfolders = []
    
    if not subfolders:
        self.current_subfolder = "1"
        self.current_file_count = 0
        os.makedirs(self.get_current_save_path(), exist_ok=True)
        return
    
    max_folder = max(subfolders, key=int)
    current_path = os.path.join(self.base_save_path, max_folder)
    
    try:
        self.current_file_count = len([f for f in os.listdir(current_path) 
                                      if os.path.isfile(os.path.join(current_path, f))])
    except Exception as e:
        print(f"Error counting files in {current_path}: {e}")
        self.current_file_count = 0
    
    if self.current_file_count >= 10000:
        new_folder = str(int(max_folder) + 1)
        self.current_subfolder = new_folder
        self.current_file_count = 0
        os.makedirs(self.get_current_save_path(), exist_ok=True)
    else:
        self.current_subfolder = max_folder

    def get_current_save_path(self):
        """获取当前保存路径"""
        return os.path.join(self.base_save_path, self.current_subfolder)

    def increment_file_count(self):
        """增加文件计数并检查是否需要创建新文件夹"""
        self.current_file_count += 1
        if self.current_file_count >= 10000:
            new_folder = str(int(self.current_subfolder) + 1)
            self.current_subfolder = new_folder
            self.current_file_count = 0
            os.makedirs(self.get_current_save_path(), exist_ok=True)
            self.save_config()  # 更新配置文件

# 检查指定的进程ID是否正在运行
def is_pid_running(pid):
    try:
        output = subprocess.check_output(f'tasklist /FI "PID eq {pid}"', shell=True, encoding="oem")  # 使用tasklist命令检查进程
        return str(pid) in output  # 如果输出中包含PID，则进程正在运行
    except subprocess.CalledProcessError:  # 如果命令执行失败，说明进程不存在
        return False

# 设置进程为DPI感知，以支持高分辨率显示
def set_dpi_aware():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # 设置为系统级DPI感知
    except AttributeError:  # 如果系统不支持SetProcessDpiAwareness，使用SetProcessDPIAware作为备选方案
        ctypes.windll.user32.SetProcessDPIAware()  # 设置为应用程序级DPI感知
    except Exception as e:  # 捕获其他异常
        pass  # 忽略异常，继续执行

# 截图函数，捕获屏幕并保存为图片
def take_screenshot():
    current_save_path = config.get_current_save_path()
    if not os.path.exists(current_save_path):
        os.makedirs(current_save_path)
    screenshot = ImageGrab.grab()
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"capture_{timestamp}.{config.format.lower()}"
    filepath = os.path.join(current_save_path, filename)
    try:
        if config.format == "JPG":
            screenshot.save(filepath, "JPEG", quality=config.jpg_quality)
        else:
            screenshot.save(filepath, "PNG", compress_level=0)
        config.increment_file_count()
    except Exception as e:
        print(f"Error saving screenshot to {filepath}: {e}")

# 截图循环函数，不断捕获屏幕截图
def screenshot_loop():
    while config.is_running:  # 如果截图功能正在运行
        take_screenshot()  # 调用截图函数
        time.sleep(config.interval)  # 等待指定的间隔时间

# 启动截图功能
def start_screenshotting(icon):
    if not config.is_running:  # 如果截图功能未运行
        config.is_running = True  # 设置为运行状态
        icon.icon = create_icon("on")  # 更新托盘图标为“开启”状态
        update_menu(icon)  # 更新托盘菜单
        thread = threading.Thread(target=screenshot_loop, daemon=True)  # 创建一个后台线程执行截图循环
        thread.start()  # 启动线程

# 停止截图功能
def stop_screenshotting(icon):
    if config.is_running:  # 如果截图功能正在运行
        config.is_running = False  # 设置为未运行状态
        icon.icon = create_icon("off")  # 更新托盘图标为“关闭”状态
        update_menu(icon)  # 更新托盘菜单

# 获取注册表的HKEY_CURRENT_USER键
def get_startup_key():
    return reg.HKEY_CURRENT_USER  # 获取注册表的HKEY_CURRENT_USER键，用于设置开机自启

# 获取开机自启的注册表路径
def get_startup_path():
    return r"Software\Microsoft\Windows\CurrentVersion\Run" # 返回开机自启的注册表路径

# 设置开机自启
def set_auto_start():
    try:
        key = reg.OpenKey(get_startup_key(), get_startup_path(), 0, reg.KEY_ALL_ACCESS)  # 打开注册表键
        script_path = os.path.abspath(sys.argv[0])  # 获取当前脚本的绝对路径
        reg.SetValueEx(key, "FrameKeeper", 0, reg.REG_SZ, f"'{sys.executable}' '{script_path}'")  # 设置注册表值，指定开机自启的命令
        reg.CloseKey(key)  # 关闭注册表键
        config.auto_start = True  # 更新配置为开机自启状态
        config.save_config()  # 保存配置到文件
        messagebox.showinfo("成功", "已成功设置开机自启！")  # 显示成功消息
    except Exception as e:  # 捕获异常
        messagebox.showerror("错误", f"设置开机自启失败: {e}")  # 显示错误消息

# 取消开机自启
def remove_auto_start():
    try:
        key = reg.OpenKey(get_startup_key(), get_startup_path(), 0, reg.KEY_ALL_ACCESS)  # 打开注册表键
        reg.DeleteValue(key, "FrameKeeper")  # 删除开机自启的注册表值
        reg.CloseKey(key)  # 关闭注册表键
        config.auto_start = False  # 更新配置为未开机自启状态
        config.save_config()  # 保存配置到文件
        messagebox.showinfo("成功", "已成功取消开机自启！")  # 显示成功消息
    except FileNotFoundError:  # 如果注册表值不存在
        messagebox.showinfo("提示", "程序未被设置为开机自启。")  # 显示提示消息
        config.auto_start = False  # 更新配置为未开机自启状态
        config.save_config()  # 保存配置到文件
    except Exception as e:  # 捕获其他异常
        messagebox.showerror("错误", f"取消开机自启失败: {e}")  # 显示错误消息

# 检查当前是否已设置开机自启
def check_auto_start():
    try:
        key = reg.OpenKey(get_startup_key(), get_startup_path(), 0, reg.KEY_READ)  # 打开注册表键
        reg.QueryValueEx(key, "FrameKeeper")  # 查询开机自启的注册表值
        reg.CloseKey(key)  # 关闭注册表键
        config.auto_start = True  # 更新配置为开机自启状态
    except FileNotFoundError:  # 如果注册表值不存在
        config.auto_start = False  # 更新配置为未开机自启状态

# 获取DPI缩放比例
def get_dpi_scale(root):
    try:
        root.update()  # 确保窗口已更新
        dpi = root.winfo_fpixels("1i")  # 获取每英寸像素数
        scale = dpi / 96.0  # 计算缩放比例，96 DPI为标准DPI
        return scale  # 返回缩放比例
    except Exception as e:  # 捕获异常
        return 1.0  # 如果获取失败，返回默认缩放比例1.0

# 创建托盘图标
def create_icon(state="off", base_size=64):
    root = tk.Tk()  # 创建一个临时Tkinter窗口以获取DPI缩放比例
    scale = get_dpi_scale(root)  # 获取DPI缩放比例
    root.destroy()  # 销毁临时窗口
    size = int(base_size * scale)  # 根据缩放比例计算图标大小
    padding = int(4 * scale)  # 设置图标边距
    center = size // 2  # 计算图标中心位置
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))  # 创建一个透明背景的图像
    draw = ImageDraw.Draw(image)  # 创建绘图对象
    if state == "on":  # 如果状态为“开启”
        radius = center - padding  # 计算外圆半径
        inner_radius = int(radius * 0.5)  # 计算内圆半径
        for i in range(radius, radius - int(5*scale), -1):  # 绘制外圆的渐变效果
            alpha = int(200 * (i / radius))  # 计算透明度
            draw.ellipse([center-i, center-i, center+i, center+i], fill=(255, 50, 50, alpha), outline=(255, 255, 255, 30))
        draw.ellipse([center-inner_radius, center-inner_radius, center+inner_radius, center+inner_radius], fill=(230, 0, 0), outline=(255, 255, 255))  # 绘制内圆
        dot_radius = int(inner_radius * 0.3)  # 计算中心点圆点半径
        draw.ellipse([center-dot_radius, center-dot_radius, center+dot_radius, center+dot_radius], fill=(255, 255, 255), outline=(200, 200, 200))  # 绘制中心点圆点
    else:  # 如果状态为“关闭”
        radius = center - padding  # 计算外圆半径
        border_width = int(2 * scale)  # 设置边框宽度
        draw.ellipse([center-radius, center-radius, center+radius, center+radius], fill=(100, 100, 100), outline=(180, 180, 180), width=border_width)  # 绘制外圆
        inner_radius = int(radius * 0.7)  # 计算内圆半径
        draw.ellipse([center-inner_radius, center-inner_radius, center+inner_radius, center+inner_radius], fill=(60, 60, 60), outline=(120, 120, 120), width=border_width//2)  # 绘制内圆
        dot_radius = int(inner_radius * 0.3)  # 计算中心点圆点半径
        draw.ellipse([center-dot_radius, center-dot_radius, center+dot_radius, center+dot_radius], fill=(150, 0, 0), outline=(100, 0, 0))  # 绘制中心点圆点
    if "radius" not in locals():  # 如果没有定义radius变量
        radius = center - padding  # 计算外圆半径
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))  # 创建一个透明背景的阴影图像
    shadow_draw = ImageDraw.Draw(shadow)  # 创建绘图对象
    shadow_draw.ellipse([center-radius+2, center-radius+2, center+radius-2, center+radius-2], fill=(0, 0, 0, 30))  # 绘制阴影外圆
    shadow = shadow.filter(ImageFilter.GaussianBlur(2))  # 应用高斯模糊以创建阴影效果
    image = Image.alpha_composite(shadow, image)  # 将阴影与图像合成
    return image  # 返回最终的图标图像

# 退出程序时的处理函数
def on_quit(icon):
    stop_screenshotting(icon)  # 停止截图功能
    icon.stop()  # 停止托盘图标
    root.quit()  # 退出Tkinter主循环

# 打开设置窗口，允许用户修改配置
def open_settings_window(icon):
    settings_window = tk.Toplevel()  # 创建一个新的顶级窗口作为设置窗口
    settings_window.title("FrameKeeper 设置")  # 设置窗口标题
    settings_window.geometry("600x300")  # 设置窗口大小
    settings_window.resizable(False, False)  # 禁止调整窗口大小
    main_frame = ttk.Frame(settings_window, padding="10")  # 创建主框架并添加内边距
    main_frame.pack(fill="both", expand=True)  # 填充整个窗口并允许扩展
    ttk.Label(main_frame, text="截图间隔 (秒):").grid(row=0, column=0, sticky="w", pady=5)  # 添加标签和输入框
    interval_var = tk.IntVar(value=config.interval)  # 创建一个整数变量用于存储截图间隔
    ttk.Entry(main_frame, textvariable=interval_var).grid(row=0, column=1, sticky="ew")  # 添加输入框
    ttk.Label(main_frame, text="保存路径:").grid(row=1, column=0, sticky="w", pady=5)  # 添加标签和输入框
    path_var = tk.StringVar(value=config.base_save_path)  # 创建一个字符串变量用于存储保存路径
    save_path_entry = tk.Entry(settings_window, width=40)
    save_path_entry.grid(row=0, column=1, padx=5, pady=5)
    save_path_entry.insert(0, config.base_save_path)  # 显示当前保存路径
    # 添加浏览按钮，允许用户选择保存路径
    def select_path():
        path = filedialog.askdirectory()  # 打开文件对话框选择目录
        if path:
            config.base_save_path = path
            save_path_entry.delete(0, tk.END)
            save_path_entry.insert(0, path)
            config.initialize_folder_counter()  # 重新初始化文件夹计数
    ttk.Button(main_frame, text="浏览...", command=select_path).grid(row=1, column=2, padx=5)  # 添加浏览按钮
    ttk.Label(main_frame, text="图片格式:").grid(row=2, column=0, sticky="w", pady=5)  # 添加标签和下拉菜单
    format_var = tk.StringVar(value=config.format)  # 创建一个字符串变量用于存储图片格式
    format_menu = ttk.Combobox(main_frame, textvariable=format_var, values=["PNG", "JPG"], state="readonly")  # 创建下拉菜单
    format_menu.grid(row=2, column=1, sticky="ew")  # 设置下拉菜单填充方式
    jpg_frame = ttk.Frame(main_frame)  # 创建一个框架用于JPG设置
    jpg_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=5)  # 设置框架位置和填充方式
    quality_label_text = ttk.Label(jpg_frame, text="JPG 压缩质量:")  # 添加JPG压缩质量标签
    quality_label_text.pack(side="left")  # 设置标签位置
    quality_var = tk.IntVar(value=config.jpg_quality)  # 创建一个整数变量用于存储JPG压缩质量
    quality_scale = ttk.Scale(jpg_frame, from_=1, to=100, orient="horizontal", variable=quality_var)  # 创建滑动条用于调整JPG压缩质量
    quality_scale.pack(side="left", expand=True, fill="x", padx=5)  # 设置滑动条填充方式
    quality_entry = ttk.Entry(jpg_frame, width=4, justify="center")  # 创建输入框用于显示JPG压缩质量
    quality_entry.pack(side="left")  # 设置输入框位置
    quality_entry.insert(0, str(config.jpg_quality))  # 初始化输入框内容为当前JPG压缩质量
    # 更新输入框内容为滑动条的值
    def update_entry_from_scale(val):
        quality_entry.delete(0, tk.END)  # 清空输入框
        quality_entry.insert(0, str(int(float(val))))  # 将滑动条值转换为整数并插入到输入框
    # 当输入框失去焦点或按下回车键时调用
    def update_scale_from_entry(event=None):
        try:  # 尝试将输入框内容转换为整数
            val = int(quality_entry.get())  # 获取输入框内容
            if 1 <= val <= 100:  # 如果值在有效范围内
                quality_var.set(val)  # 更新滑动条值
            else:  # 如果值不在有效范围内
                quality_entry.delete(0, tk.END)  # 清空输入框
                quality_entry.insert(0, str(quality_var.get()))  # 恢复为滑动条当前值
        except ValueError:  # 如果输入框内容无法转换为整数
            quality_entry.delete(0, tk.END)  # 清空输入框
            quality_entry.insert(0, str(quality_var.get()))  # 恢复为滑动条当前值
    quality_scale.config(command=update_entry_from_scale)  # 当滑动条值变化时调用
    quality_entry.bind("<Return>", update_scale_from_entry)  # 当按下回车键时调用
    quality_entry.bind("<FocusOut>", update_scale_from_entry)  # 当输入框失去焦点时调用
    # 定义JPG质量状态切换函数
    def toggle_jpg_quality_state(event=None):
        if format_var.get() == "PNG":  # 如果选择的格式为PNG
            quality_scale.state(["disabled"])  # 禁用滑动条
            quality_entry.state(["disabled"])  # 禁用输入框
            quality_label_text.config(foreground="gray")  # 设置标签颜色为灰色
        else:  # 如果选择的格式为JPG
            quality_scale.state(["!disabled"])  # 启用滑动条
            quality_entry.state(["!disabled"])  # 启用输入框
            quality_label_text.config(foreground="")  # 恢复标签颜色
    format_menu.bind("<<ComboboxSelected>>", toggle_jpg_quality_state)  # 当选择的格式变化时调用
    toggle_jpg_quality_state()  # 初始化时调用一次以设置状态
    auto_start_var = tk.BooleanVar(value=config.auto_start)  # 创建布尔变量用于存储开机自启状态
    # 定义开机自启状态切换函数
    def toggle_auto_start():
        if auto_start_var.get():  # 如果勾选了开机自启
            set_auto_start()  # 设置开机自启
        else:  # 如果取消勾选
            remove_auto_start()  # 取消开机自启
        check_auto_start()  # 检查当前开机自启状态
        auto_start_var.set(config.auto_start)  # 更新复选框状态
    ttk.Checkbutton(main_frame, text="开机自启", variable=auto_start_var, command=toggle_auto_start).grid(row=4, column=0, columnspan=2, sticky="w", pady=10)  # 添加复选框用于设置开机自启
    # 定义保存设置函数
    def save_settings():
        config.interval = interval_var.get()  # 获取截图间隔
        config.save_path = path_var.get()  # 获取保存路径
        config.format = format_var.get()  # 获取图片格式
        config.jpg_quality = quality_var.get()  # 获取JPG压缩质量
        config.save_config()  # 保存配置到文件
        messagebox.showinfo("成功", "设置已保存！")  # 显示保存成功消息
        settings_window.destroy()  # 关闭设置窗口
    ttk.Button(main_frame, text="保存并关闭", command=save_settings).grid(row=5, column=0, columnspan=3, pady=20)  # 添加保存按钮
    main_frame.columnconfigure(1, weight=1)  # 设置第二列可扩展

# 创建主Tkinter窗口
def run_in_main_thread(func, *args):
    root.after(0, func, *args)  # 在主线程中执行函数

# 导出图片到视频
def export_to_video(icon):
    # 创建临时顶级窗口
    temp_window = tk.Toplevel()
    temp_window.withdraw()  # 隐藏临时窗口
    # 打开文件夹选择对话框
    source_dir = filedialog.askdirectory(title="选择包含截图的文件夹", initialdir=config.save_path, parent=temp_window)
    if not source_dir:  # 用户取消选择
        temp_window.destroy()
        return
    # 获取目录中所有图片文件
    images = [img for img in os.listdir(source_dir) if img.lower().endswith((".png", ".jpg", ".jpeg"))]
    if not images:  # 没有找到图片
        messagebox.showwarning("无图片", "所选文件夹中没有找到图片文件。", parent=temp_window)
        temp_window.destroy()
        return
    images.sort()  # 按文件名排序，确保顺序正确
    # 打开保存视频文件对话框
    save_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 文件", "*.mp4")], title="保存视频文件", initialdir=config.save_path, parent=temp_window)
    if not save_path:  # 用户取消保存
        temp_window.destroy()
        return
    # 获取用户输入的帧率
    frame_rate = simpledialog.askinteger("帧率", "请输入视频帧率 (FPS):", initialvalue=30, minvalue=1, maxvalue=60, parent=temp_window)
    if not frame_rate:  # 用户取消输入
        temp_window.destroy()
        return
    # 读取第一张图片以获取尺寸
    first_image_path = os.path.join(source_dir, images[0])
    try:
        with open(first_image_path, "rb") as f:
            img_np = np.frombuffer(f.read(), np.uint8)
        frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
    except Exception:
        frame = None
    if frame is None:  # 无法读取第一帧
        messagebox.showerror("错误", f"无法读取第一帧图片: {first_image_path}", parent=temp_window)
        temp_window.destroy()
        return
    height, width, _ = frame.shape  # 获取图片尺寸

    # 设置进度窗口
    progress_window = tk.Toplevel(temp_window)
    progress_window.title("正在导出视频...")
    progress_window.geometry("400x180")
    progress_window.transient(temp_window)
    progress_window.grab_set()
    progress_window.resizable(False, False)
    progress_window.protocol("WM_DELETE_WINDOW", lambda: None)  # 禁止关闭窗口
    progress_frame = ttk.Frame(progress_window, padding=15)
    progress_frame.pack(fill=tk.BOTH, expand=True)
    ttk.Label(progress_frame, text="正在导出视频...", font=("Arial", 10, "bold")).pack(anchor="w")
    ttk.Separator(progress_frame).pack(fill=tk.X, pady=5)
    progress_var = tk.DoubleVar(value=0)
    progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=len(images), length=350, mode="determinate")
    progress_bar.pack(fill=tk.X, pady=(0, 10))
    status_frame = ttk.Frame(progress_frame)
    status_frame.pack(fill=tk.X, pady=(0, 15))
    left_status = ttk.Frame(status_frame)
    left_status.pack(side=tk.LEFT, fill=tk.X, expand=True)
    percent_var = tk.StringVar(value="0%")
    ttk.Label(left_status, textvariable=percent_var, font=("Arial", 10)).pack(anchor="w")
    files_var = tk.StringVar(value=f"0 / {len(images)} 文件已处理")
    ttk.Label(left_status, textvariable=files_var, font=("Arial", 9)).pack(anchor="w")
    size_info = ttk.Frame(status_frame)
    size_info.pack(side=tk.RIGHT, fill=tk.X)
    res_var = tk.StringVar(value=f"{width}x{height}")
    ttk.Label(size_info, textvariable=res_var, font=("Arial", 9)).pack(anchor="e")
    size_var = tk.StringVar(value="估计大小: ---")
    ttk.Label(size_info, textvariable=size_var, font=("Arial", 9)).pack(anchor="e")
    time_frame = ttk.Frame(progress_frame)
    time_frame.pack(fill=tk.X)
    time_var = tk.StringVar(value="估计剩余时间: --:--")
    ttk.Label(time_frame, textvariable=time_var, font=("Arial", 9)).pack(anchor="w")
    cancel_flag = threading.Event()  # 创建取消标志

    # 取消导出函数
    def cancel_export():
        cancel_flag.set()
        progress_window.destroy()
        temp_window.destroy()
        messagebox.showinfo("导出取消", "视频导出已被取消。")

    ttk.Button(progress_frame, text="取消导出", command=cancel_export, width=15).pack(pady=(10, 0))

    # 格式化时间函数
    def format_time(seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    update_queue = queue.Queue()
    def update_from_queue():
        if not progress_window.winfo_exists() or cancel_flag.is_set():
            return

        while not update_queue.empty():
            try:
                # 从队列中获取一个更新项目
                current, total, remaining_time, estimated_size = update_queue.get_nowait()
                percent = int(current * 100 / total)
                percent_var.set(f"{percent}%")
                files_var.set(f"{current} / {total} 文件已处理")
                time_var.set(f"估计剩余时间: {format_time(remaining_time) if remaining_time is not None else '--:--'}")
                size_var.set(f"估计大小: {estimated_size:.1f}MB" if estimated_size else "估计大小: ---")
                progress_var.set(current)
            except queue.Empty:
                break # 队列已空，退出循环

        # 每100毫秒后再次检查队列
        progress_window.after(100, update_from_queue)

    # 【新增】启动队列检查循环
    progress_window.after(100, update_from_queue)

    # 【修改】函数签名，接收一个队列参数
    def do_export(update_q):
        temp_output = None
        video = None
        try:
            # 创建临时文件
            temp_dir = tempfile.gettempdir()
            temp_file = f"temp_framekeeper_{os.getpid()}.mp4"
            temp_output = os.path.join(temp_dir, temp_file)
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            video = cv2.VideoWriter(temp_output, fourcc, frame_rate, (width, height))
            if not video.isOpened():
                raise Exception("无法初始化视频编码器。")
            try:
                video.set(cv2.VIDEOWRITER_PROP_QUALITY, 90)
            except:
                pass
            # 估算视频大小
            first_frame_size = os.path.getsize(first_image_path)
            estimated_size = len(images) * (first_frame_size / (frame_rate * 1.5)) / (1024 * 1024)
            start_time = time.time()

            for i, image in enumerate(images):
                if cancel_flag.is_set():
                    break

                image_path = os.path.join(source_dir, image)
                try:
                    with open(image_path, "rb") as f:
                        img_np = np.frombuffer(f.read(), np.uint8)
                    frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
                    if frame is None:
                        continue
                    video.write(frame)
                except Exception:
                    continue
                # 计算剩余时间
                elapsed = time.time() - start_time
                remaining = (elapsed / (i + 1)) * (len(images) - i - 1) if i > 0 else 0
                
                # 【修改】将更新请求放入队列，而不是直接调用GUI更新
                update_q.put((i + 1, len(images), remaining, estimated_size))

            if video:
                video.release()
                video = None

            if cancel_flag.is_set():
                return
            shutil.move(temp_output, save_path)
            final_size = os.path.getsize(save_path) / (1024 * 1024)
            duration = len(images) / frame_rate
            root.after(0, lambda: messagebox.showinfo("导出成功", f"视频已成功导出:\n路径: {save_path}\n尺寸: {width}x{height}\n时长: {duration:.1f}秒\n大小: {final_size:.1f}MB", parent=temp_window))
        except Exception as e:
            traceback.print_exc()
            # 【修改】在主线程中显示错误消息
            root.after(0, lambda: messagebox.showerror("导出错误", f"导出过程中发生错误:\n{str(e)}", parent=progress_window))
        finally:
            if video is not None:
                video.release()
            if temp_output and os.path.exists(temp_output):
                try:
                    os.remove(temp_output)
                except:
                    pass
            # 【修改】在主线程中销毁窗口
            root.after(0, lambda: (progress_window.destroy(), temp_window.destroy()))

    # 【修改】启动导出线程，并将队列作为参数传递
    threading.Thread(target=do_export, args=(update_queue,), daemon=True).start()

# 设置时间间隔
def set_interval(icon, interval):
    def inner():
        config.interval = interval
        if config.is_running:
            stop_screenshotting(icon)
            start_screenshotting(icon)
    return inner

# 更新托盘菜单
def update_menu(icon):
    status_text = "运行中" if config.is_running else "已停止"  # 根据截图功能状态设置状态文本
    start_stop_item = item("停止截图" if config.is_running else "开始截图", lambda: stop_screenshotting(icon) if config.is_running else start_screenshotting(icon))  # 创建开始/停止截图菜单项
    icon.menu = pystray.Menu(item(f"状态: {status_text}", None, enabled=False), pystray.Menu.SEPARATOR, start_stop_item, item("快速更改时间间隔", pystray.Menu(item("5 秒", set_interval(icon, 5)), item("10 秒", set_interval(icon, 10)), item("30 秒", set_interval(icon, 30)), item("60 秒", set_interval(icon, 60)))), item("导出为视频", lambda: run_in_main_thread(export_to_video, icon)), item("设置", lambda: open_settings_window(icon)), pystray.Menu.SEPARATOR, item("退出", lambda: on_quit(icon)))  # 更新托盘菜单项

# 检查进程是否在运行
def main():
    set_dpi_aware()  # 设置DPI感知
    global root  # 声明全局变量root
    root = tk.Tk()  # 创建主Tkinter窗口
    root.withdraw()  # 隐藏主窗口
    check_auto_start()  # 检查当前是否已设置开机自启
    icon_image = create_icon("off")  # 创建初始托盘图标
    icon = pystray.Icon("FrameKeeper", icon_image, "FrameKeeper")  # 创建托盘图标对象
    update_menu(icon)  # 更新托盘菜单
    def run_icon(icon):  # 定义托盘图标运行函数
        icon.run()  # 启动托盘图标
    pystray_thread = threading.Thread(target=run_icon, args=(icon,), daemon=True)  # 创建托盘图标线程
    pystray_thread.start()  # 启动托盘图标线程
    root.mainloop()  # 启动Tkinter主循环

# 确保脚本作为主程序运行
if __name__ == "__main__":
    try:
        temp_dir = os.environ.get("TEMP", os.path.expanduser("~"))  # 获取临时目录路径
        lock_file_path = os.path.join(temp_dir, "framekeeper.lock")  # 定义锁文件路径
        if os.path.exists(lock_file_path):  # 如果锁文件已存在
            with open(lock_file_path, "r") as f:  # 打开锁文件
                existing_pid = f.read().strip()  # 读取锁文件中的进程ID
            if existing_pid and is_pid_running(existing_pid):  # 如果锁文件中的进程ID存在且进程仍在运行
                ctypes.windll.user32.MessageBoxW(0, "FrameKeeper 已在运行中。", "错误", 0x10)  # 显示错误消息框
                sys.exit(1)  # 退出程序
            else:  # 如果锁文件中的进程ID不存在或进程已结束
                os.remove(lock_file_path)  # 删除锁文件
        with open(lock_file_path, "w") as f:  # 创建或覆盖锁文件
            f.write(str(os.getpid()))  # 写入当前进程ID到锁文件
        config_dir = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "FrameKeeper")  # 定义配置文件目录路径
        if not os.path.exists(config_dir):  # 如果配置目录不存在
            os.makedirs(config_dir)  # 创建配置目录
        config_file = os.path.join(config_dir, "config.ini")  # 定义配置文件路径
        config = Config(config_file)  # 创建配置对象
        main()  # 启动主程序
    finally:  # 确保在程序退出时删除锁文件
        if os.path.exists(lock_file_path):  # 如果锁文件仍然存在
            os.remove(lock_file_path)  # 删除锁文件
