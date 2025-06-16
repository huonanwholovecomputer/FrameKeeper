# 导入相关模块

import os  # 操作系统接口 - 文件和目录操作
import sys  # 系统相关功能 - 命令行参数、退出程序等
import cv2  # OpenCV 库 - 计算机视觉和图像处理
import time  # 时间相关功能 - 延时、计时等
import queue  # 队列 - 线程间通信
import ctypes  # C语言兼容库 - 调用 Windows API
import shutil  # 高级文件操作 - 复制、移动、删除等
import pystray  # 系统托盘图标创建和管理
import tempfile  # 临时文件和目录管理
import traceback  # 错误追踪 - 获取异常信息
import threading  # 多线程编程支持
import subprocess  # 子进程管理 - 运行外部程序
import numpy as np  # 数值计算库 - 数组操作等
import configparser  # 配置文件解析器
import tkinter as tk  # GUI 工具包 - 创建图形界面
import winreg as reg  # Windows 注册表操作
from pystray import MenuItem as item  # 系统托盘菜单项
from PIL import Image, ImageGrab, ImageDraw, ImageFilter  # Python 图像处理库 - 图像捕获、编辑等
from tkinter import ttk, filedialog, messagebox, simpledialog  # Tkinter 扩展组件 - 文件对话框、消息框等

# 新建一个配置类，用于管理应用程序的配置
class Config:
    # 初始化配置类
    def __init__(self, config_file):
        self.config_file = config_file  # 配置文件路径
        self.config = configparser.ConfigParser()  # 创建配置解析器
        self.interval = 10  # 默认截图间隔为 10 秒
        self.base_save_path = os.path.join(os.path.expanduser("~"), "FrameKeeper_Captures")  # 默认保存路径为用户目录下的 FrameKeeper_Captures 文件夹
        self.format = "JPG"  # 默认图片格式为 JPG
        self.jpg_quality = 65  # 默认 JPG 压缩质量为 65
        self.current_subfolder = "1"  # 当前子文件夹名称
        self.current_file_count = 0   # 当前子文件夹中的文件计数
        self.is_running = False  # 截图运行状态默认为不运行
        self.auto_start = False  # 程序默认不开机自启
        self.load_config()  # 调用函数 load_config 加载配置文件
        self.initialize_folder_counter()  # 初始化文件夹计数器

    # 定义函数：加载配置文件
    def load_config(self):
        if os.path.exists(self.config_file):  # 检查配置文件是否存在
            self.config.read(self.config_file)  # 读取配置文件
            self.interval = self.config.getint("DEFAULT", "interval")  # 获取截图间隔
            self.base_save_path = self.config.get("DEFAULT", "save_path")  # 获取截图的储存位置
            self.current_subfolder = self.config.get("DEFAULT", "current_subfolder")  # 获取截图时间间隔
            self.format = self.config.get("DEFAULT", "format")  # 获取图片格式
            self.jpg_quality = self.config.getint("DEFAULT", "jpg_quality")  # 获取JPG压缩质量
            self.auto_start = self.config.getboolean("DEFAULT", "auto_start")  # 获取是否开机自启
        else:  # 如果配置文件不存在，则使用默认值
            self.save_config()  # 调用函数save_config保存一个默认配置文件到配置文件目录

    # 定义函数：保存配置到文件
    def save_config(self):
        self.config["DEFAULT"] = {"interval": self.interval, "save_path": self.base_save_path, "current_subfolder": self.current_subfolder, "format": self.format, "jpg_quality": self.jpg_quality, "auto_start": self.auto_start}  # 设置默认配置
        with open(self.config_file, "w") as configfile:  # 打开配置文件进行写入
            self.config.write(configfile)  # 写入配置内容
    # 定义函数：获取当前保存路径
    def get_current_save_path(self):  # 定义获取当前路径方法
        return os.path.join(self.base_save_path, self.current_subfolder)  # 返回当前子文件夹完整路径

    # 定义函数：增加文件计数并检查是否需要创建新文件夹
    def increment_file_count(self):  # 定义文件计数增加方法
        self.current_file_count += 1  # 文件计数加1
        if self.current_file_count >= 10000:  # 检查是否达到文件上限
            new_folder = str(int(self.current_subfolder) + 1)  # 计算新文件夹编号
            self.current_subfolder = new_folder  # 更新子文件夹名
            self.current_file_count = 0  # 重置文件计数器
            os.makedirs(self.get_current_save_path(), exist_ok=True)  # 创建新子文件夹
            self.save_config()  # 调用函数{save_config()}保存当前配置文件

    # 定义函数：初始化文件夹计数器
    def initialize_folder_counter(self):
        self.increment_file_count()
        if not os.path.exists(self.base_save_path):  # 如果基础保存路径不存在
            os.makedirs(self.base_save_path)  # 创建基础保存路径
        subfolders = [f for f in os.listdir(self.base_save_path) if os.path.isdir(os.path.join(self.base_save_path, f)) and f.isdigit()]  # 列出所有数字命名的子文件夹
        if not subfolders:  # 如果不存在子文件夹
            self.current_subfolder = "1"  # 初始化第一个子文件夹名
            self.current_file_count = 0  # 初始化文件计数器
            os.makedirs(self.get_current_save_path(), exist_ok=True)  # 创建初始子文件夹
            return  # 结束函数  # 直接返回
        max_folder = max(subfolders, key=int)  # 找到编号最大的子文件夹
        current_path = os.path.join(self.base_save_path, max_folder)  # 构建最大子文件夹完整路径
        self.current_file_count = len([f for f in os.listdir(current_path) if os.path.isfile(os.path.join(current_path, f))])  # 统计文件夹内文件数量
        if self.current_file_count >= 10000:  # 检查文件数是否达到上限
            new_folder = str(int(max_folder) + 1)  # 计算新文件夹编号
            self.current_subfolder = new_folder  # 更新当前子文件夹名
            self.current_file_count = 0  # 重置文件计数器
            os.makedirs(self.get_current_save_path(), exist_ok=True)  # 创建新子文件夹
        else:  # 文件数未达上限
            self.current_subfolder = max_folder  # 使用最大编号文件夹

'''截图功能'''
# 定义函数：捕获屏幕并保存为图片
def take_screenshot():
    current_save_path = config.get_current_save_path()  # 获取当前保存路径
    if not os.path.exists(current_save_path):  # 如果当前保存路径不存在
        os.makedirs(current_save_path)  # 创建当前保存路径
    screenshot = ImageGrab.grab()  # 使用 ImageGrab 库捕获屏幕截图
    timestamp = time.strftime("%Y%m%d_%H%M%S")  # 获取当前时间戳
    filename = f"capture_{timestamp}.{config.format.lower()}"  # 构建文件名，包含时间戳和格式
    filepath = os.path.join(current_save_path, filename)  # 构建完整文件路径
    if config.format == "JPG":  # 如果配置的格式为 JPG
        screenshot.save(filepath, "JPEG", quality=config.jpg_quality)  # 保存为 JPG 格式，使用指定的压缩质量
    else:  # 如果配置的格式为 PNG
        screenshot.save(filepath, "PNG", compress_level=0)  # 保存为 PNG 格式，压缩级别为 0 （无压缩）
    config.increment_file_count()  # 调用函数 increment_file_count 增加文件计数

# 定义函数：不断捕获屏幕截图
def screenshot_loop():
    while config.is_running:  # 如果截图功能正在运行
        take_screenshot()  # 调用截图函数
        time.sleep(config.interval)  # 等待指定的间隔时间

# 定义函数：启动截图功能
def start_screenshotting(icon):
    if not config.is_running:  # 如果截图功能未运行
        config.is_running = True  # 设置为运行状态
        icon.icon = create_icon("on")  # 更新托盘图标为“开启”状态
        update_menu(icon)  # 更新托盘菜单
        thread = threading.Thread(target=screenshot_loop, daemon=True)  # 创建一个后台线程执行截图循环
        thread.start()  # 启动线程

# 定义函数：停止截图功能
def stop_screenshotting(icon):
    if config.is_running:  # 如果截图功能正在运行
        config.is_running = False  # 设置为未运行状态
        icon.icon = create_icon("off")  # 更新托盘图标为“关闭”状态
        update_menu(icon)  # 更新托盘菜单

'''检查程序是否已经在运行功能'''
# 定义函数：检查指定的进程ID是否正在运行
def is_pid_running(pid):
    try:
        output = subprocess.check_output(f'tasklist /FI "PID eq {pid}"', shell=True, encoding="oem")  # 使用 tasklist 命令检查进程
        return str(pid) in output  # 如果输出中包含 PID ，则进程正在运行
    except subprocess.CalledProcessError:  # 如果命令执行失败，说明进程不存在
        return False

# 定义函数：设置进程为DPI感知，以支持高分辨率显示
def set_dpi_aware():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # 设置为系统级DPI感知
    except AttributeError:  # 如果系统不支持 SetProcessDpiAwareness ，使用 SetProcessDPIAware 作为备选方案
        ctypes.windll.user32.SetProcessDPIAware()  # 设置为应用程序级DPI感知
    except Exception as e:  # 捕获其他异常
        pass  # 忽略异常，继续执行

'''开机自启功能 '''
# 定义函数：返回 Windows 注册表的 HKEY_CURRENT_USER 根键，表示操作将在当前用户的注册表分支下进行
def get_startup_key():
    return reg.HKEY_CURRENT_USER  # 返回Windows注册表的 HKEY_CURRENT_USER 根键

# 定义函数：返回注册表路径 Software\Microsoft\Windows\CurrentVersion\Run ，这是 Windows 系统用于存储开机自启动程序的标准路径
def get_startup_path():
    return r"Software\Microsoft\Windows\CurrentVersion\Run" # 返回 Windows 系统用于存储开机自启动程序的标准路径

# 定义函数：设置开机自启
def set_auto_start():
    try:
        key = reg.OpenKey(get_startup_key(), get_startup_path(), 0, reg.KEY_ALL_ACCESS)  # 调用函数 get_startup_key 获取根键、调用函数 get_startup_path 获取子路径，授予 KEY_ALL_ACCESS 完全控制权限，传递 0 作为子键索引
        script_path = os.path.abspath(sys.argv[0])  # 获取当前执行脚本的绝对路径
        reg.SetValueEx(key, "FrameKeeper", 0, reg.REG_SZ, f"'{sys.executable}' '{script_path}'")  # 在注册表中创建/修改值，键名称设为"FrameKeeper"，值类型为REG_SZ（字符串），值数据是Python解释器路径和脚本路径的组合（f"'{sys.executable}' '{script_path}'"）
        reg.CloseKey(key)  # 关闭注册表键
        config.auto_start = True  # 更新配置为开机自启状态
        config.save_config()  # 保存配置到文件
        messagebox.showinfo("成功", "已成功设置开机自启！")  # 显示成功消息
    except Exception as e:  # 捕获异常
        messagebox.showerror("错误", f"设置开机自启失败: {e}")  # 显示错误消息

# 定义函数：取消开机自启
def remove_auto_start():
    try:
        key = reg.OpenKey(get_startup_key(), get_startup_path(), 0, reg.KEY_ALL_ACCESS)  # 与函数 set_auto_start 相同
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

# 定义函数：检查当前是否已设置开机自启
def check_auto_start():
    try:
        key = reg.OpenKey(get_startup_key(), get_startup_path(), 0, reg.KEY_READ)  # 与函数 set_auto_start 基本相同，KEY_READ 权限表示只读访问
        reg.QueryValueEx(key, "FrameKeeper")  # 查询开机自启的注册表值
        reg.CloseKey(key)  # 关闭注册表键
        config.auto_start = True  # 更新配置为开机自启状态
    except FileNotFoundError:  # 如果注册表值不存在
        config.auto_start = False  # 更新配置为未开机自启状态

'''自适应DPI缩放功能'''
# 定义函数：获取DPI缩放比例
def get_dpi_scale():
    root = tk.Tk()   # 创建一个 Tkinter 窗口
    root.withdraw()  # 隐藏窗口
    root.update()  # 确保窗口初始化完成
    try:
        dpi = root.winfo_fpixels("1i")  # 获取每英寸像素数
        scale = dpi / 96.0  # 计算缩放比例（ 96 DPI 为标准）
    except Exception as e:
        scale = 1.0  # 失败时返回默认值
    finally:
        root.destroy()  # 销毁窗口
    return scale  # 返回缩放比例

# 定义函数：创建托盘图标
def create_icon(state="off", base_size=64):
    scale = get_dpi_scale()  # 调用函数 get_dpi_scale 获取 DPI 缩放比例
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
    if "radius" not in locals():  # 如果没有定义 radius 变量
        radius = center - padding  # 计算外圆半径
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))  # 创建一个透明背景的阴影图像
    shadow_draw = ImageDraw.Draw(shadow)  # 创建绘图对象
    shadow_draw.ellipse([center-radius+2, center-radius+2, center+radius-2, center+radius-2], fill=(0, 0, 0, 30))  # 绘制阴影外圆
    shadow = shadow.filter(ImageFilter.GaussianBlur(2))  # 应用高斯模糊以创建阴影效果
    image = Image.alpha_composite(shadow, image)  # 将阴影与图像合成
    return image  # 返回最终的图标图像

'''设置窗口功能'''
# 定义函数：打开“设置”窗口
def open_settings_window(icon):
    settings_window = tk.Toplevel()
    settings_window.title("FrameKeeper 设置")
    settings_window.geometry("500x300")
    settings_window.resizable(False, False)
    main_frame = ttk.Frame(settings_window, padding="10")
    main_frame.pack(fill="both", expand=True)
    ttk.Label(main_frame, text="截图间隔 (秒):").grid(row=0, column=0, sticky="w", pady=5)
    interval_var = tk.IntVar(value=config.interval)
    ttk.Entry(main_frame, textvariable=interval_var).grid(row=0, column=1, sticky="ew")
    ttk.Label(main_frame, text="保存路径:").grid(row=1, column=0, sticky="w", pady=5)
    path_var = tk.StringVar(value=config.base_save_path)
    save_path_entry = ttk.Entry(main_frame, textvariable=path_var)
    save_path_entry.grid(row=1, column=1, sticky="ew")

    # 定义函数：选择保存路径
    def select_path():
        path = filedialog.askdirectory()  # 打开文件对话框选择目录
        if path:  # 如果用户选择了路径(未点击取消)
            config.base_save_path = path  # 更新配置文件中的保存路径
            '清空并更新路径输入框的内容'
            save_path_entry.delete(0, tk.END)  # 删除现有内容
            save_path_entry.insert(0, path)  # 插入新路径
            config.initialize_folder_counter()  # 重新初始化文件夹计数器
 
    '''图片格式下拉菜单'''
    ttk.Button(main_frame, text="浏览...", command=select_path).grid(row=1, column=2, padx=5)  # 创建浏览按钮，点击时调用 select_path 函数，放在第 1 行第 2 列(路径输入框旁边)，左右添加 5 像素间距
    ttk.Label(main_frame, text="图片格式:").grid(row=2, column=0, sticky="w", pady=5)  # 创建标签，放在第 2 行第 0 列，左对齐(w)，上下添加 5 像素间距
    format_var = tk.StringVar(value=config.format)  # 绑定到配置中的当前格式
    format_menu = ttk.Combobox(main_frame, textvariable=format_var, values=["PNG", "JPG"], state="readonly")  # 创建一个下拉菜单，readonly 表示禁止直接编辑，只能选择
    format_menu.grid(row=2, column=1, sticky="ew")  # 放置在第 2 行第 1 列，水平拉伸

    '''JPG质量设置框架'''
    jpg_frame = ttk.Frame(main_frame)  # 创建框架
    jpg_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=5)  # 跨 3 列，水平拉伸，上下边距为 5 像素

    '''JPG质量调节组件'''
    '标签'
    quality_label_text = ttk.Label(jpg_frame, text="JPG 压缩质量:")  # 添加JPG压缩质量标签
    quality_label_text.pack(side="left")  # 标签靠左放置
    '滑动条'
    quality_var = tk.IntVar(value=config.jpg_quality)  # 绑定到配置中的当前质量值
    quality_scale = ttk.Scale(jpg_frame, from_=1, to=100, orient="horizontal", variable=quality_var)  # 取值范围 1-100 ，水平方向，绑定到变量
    quality_scale.pack(side="left", expand=True, fill="x", padx=5)  # 设置滑动条填充方式
    quality_entry = ttk.Entry(jpg_frame, width=4, justify="center")  # 创建输入框用于显示JPG压缩质量
    '数值输入框'
    quality_entry.pack(side="left")  # 设置输入框位置
    quality_entry.insert(0, str(config.jpg_quality))  # 初始化输入框内容为当前JPG压缩质量

    # 定义函数：更新输入框内容为滑动条的值
    def update_entry_from_scale(val):
        quality_entry.delete(0, tk.END)  # 清空输入框
        quality_entry.insert(0, str(int(float(val))))  # 将滑动条值转换为整数并插入到输入框

    # 定义函数：尝试将输入框内容转换为整数
    def update_scale_from_entry(event=None):
        try:
            val = int(quality_entry.get())  # 获取输入框内容
            if 1 <= val <= 100:  # 如果值在有效范围内
                quality_var.set(val)  # 更新滑动条值
            else:  # 如果值不在有效范围内
                quality_entry.delete(0, tk.END)  # 清空输入框
                quality_entry.insert(0, str(quality_var.get()))  # 恢复为滑动条当前值
        except ValueError:  # 如果输入框内容无法转换为整数
            quality_entry.delete(0, tk.END)  # 清空输入框
            quality_entry.insert(0, str(quality_var.get()))  # 恢复为滑动条当前值

    quality_scale.config(command=update_entry_from_scale)  # 当滑动条值变化时调用函数 update_entry_from_scale 以更新输入框内容为滑动条的值
    quality_entry.bind("<Return>", update_scale_from_entry)  # 当按下回车键时调用函数 update_scale_from_entry 以尝试将输入框内容转换为整数
    quality_entry.bind("<FocusOut>", update_scale_from_entry)  # 当输入框失去焦点时调用函数 update_scale_from_entry 以尝试将输入框内容转换为整数

    # 定义函数：“JPG 压缩质量：”文字、滑动条和输入框的状态切换
    def toggle_jpg_quality_state(event=None):
        if format_var.get() == "PNG":  # 如果选择的格式为PNG
            quality_scale.state(["disabled"])  # 禁用滑动条
            quality_entry.state(["disabled"])  # 禁用输入框
            quality_label_text.config(foreground="gray")  # 设置标签颜色为灰色
        else:  # 如果选择的格式为JPG
            quality_scale.state(["!disabled"])  # 启用滑动条
            quality_entry.state(["!disabled"])  # 启用输入框
            quality_label_text.config(foreground="")  # 恢复标签颜色
    format_menu.bind("<<ComboboxSelected>>", toggle_jpg_quality_state)  # 当选择的格式变化时调用 toggle_jpg_quality_state 以实现文字“JPG 压缩质量：”、滑动条和输入框的状态切换
    toggle_jpg_quality_state()  # 程序初始化时调用一次函数 toggle_jpg_quality_state 以设置文字“JPG 压缩质量：”、滑动条和输入框的状态

    '''开机自启动功能'''
    auto_start_var = tk.BooleanVar(value=config.auto_start)  # 创建布尔变量用于存储开机自启状态

    # 定义函数：开机自启动状态切换
    def toggle_auto_start():
        if auto_start_var.get():  # 如果勾选了开机自启
            set_auto_start()  # 调用函数 set_auto_start 设置开机自启
        else:  # 如果取消勾选
            remove_auto_start()  # 调用函数 remove_auto_start 取消开机自启
        check_auto_start()  # 调用函数 check_auto_start 检查当前开机自启状态
        auto_start_var.set(config.auto_start)  # 更新复选框状态
    ttk.Checkbutton(main_frame, text="开机自启", variable=auto_start_var, command=toggle_auto_start).grid(row=4, column=0, columnspan=2, sticky="w", pady=10)  # 创建开机自启复选框，绑定状态变量和回调函数，放在第 4 行，跨 2 列左对齐，带 10 像素边距

    # 定义函数：保存设置
    def save_settings():
        config.interval = interval_var.get()  # 获取截图间隔
        config.save_path = path_var.get()  # 获取保存路径
        config.format = format_var.get()  # 获取图片格式
        config.jpg_quality = quality_var.get()  # 获取JPG压缩质量
        config.save_config()  # 保存配置到文件
        messagebox.showinfo("成功", "设置已保存！")  # 显示保存成功消息
        settings_window.destroy()  # 关闭设置窗口
    ttk.Button(main_frame, text="保存并关闭", command=save_settings).grid(row=5, column=0, columnspan=3, pady=20)  # 创建保存按钮，放在第 5 行，跨 3 列，上下边距 20 像素
    main_frame.columnconfigure(1, weight=1)  # 第2列可扩展，让界面元素能自适应宽度

# 定义函数：创建主Tkinter窗口
def run_in_main_thread(func, *args):
    root.after(0, func, *args)  # 在主线程中执行函数

# 定义函数：导出截图为视频
def export_to_video(icon):
    dialog_parent = tk.Toplevel(root)  # 创建一个新的顶级窗口作为对话框的父窗口
    dialog_parent.withdraw()  # 隐藏窗口，避免在askdirectory前显示空白窗口

    source_dir = filedialog.askdirectory(title="选择包含截图的文件夹", initialdir=config.base_save_path, parent=dialog_parent)  # 让用户选择包含截图的文件夹，初始目录为配置中的基本保存路径
    if not source_dir:  # 如果用户取消了选择
        dialog_parent.destroy()  # 销毁对话框父窗口
        return  # 直接返回

    '''获取所有子文件夹中的图片文件'''
    images = []
    for root_dir, dirs, files in os.walk(source_dir):
        '''跳过顶级目录（source_dir本身）'''
        if root_dir == source_dir:
            continue
        '''遍历当前子目录中的所有文件'''
        for file in files:
            if file.lower().endswith((".png", ".jpg", ".jpeg")):
                images.append(os.path.join(root_dir, file))  # 存储文件的完整路径

    if not images:  # 如果没有找到图片文件
        messagebox.showwarning("无图片", "所选文件夹的子文件夹中没有找到图片文件", parent=dialog_parent)  # 显示警告对话框
        dialog_parent.destroy()  # 销毁对话框父窗口
        return  # 直接返回

    images.sort(key=lambda x: os.path.basename(x))  # 对图片文件名进行排序
    save_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 文件", "*.mp4")], title="保存视频文件", initialdir=config.base_save_path, parent=dialog_parent)  # 让用户选择视频保存路径，默认扩展名为.mp4

    if not save_path:  # 如果用户取消了保存
        dialog_parent.destroy()  # 销毁对话框父窗口
        return  # 直接返回

    frame_rate = simpledialog.askinteger("帧率", "请输入视频帧率 (FPS):", initialvalue=30, minvalue=1, maxvalue=60, parent=dialog_parent)  # 让用户输入视频帧率，默认值30，范围1-60
    dialog_parent.destroy()  # 销毁对话框父窗口

    if not frame_rate:  # 如果用户没有输入帧率
        return  # 直接返回

    first_image_path = images[0]  # 获取第一张图片的完整路径
    try:
        with open(first_image_path, "rb") as f:  # 读取第一张图片
            img_np = np.frombuffer(f.read(), np.uint8)  # 将图片数据读取为numpy数组
        frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)  # 解码图片
    except Exception:  # 如果读取失败
        frame = None  # 设置为None
        
    if frame is None:  # 如果无法读取第一帧
        messagebox.showerror("错误", f"无法读取第一帧图片: {first_image_path}", parent=root)  # 显示错误对话框
        return  # 直接返回
        
    height, width, _ = frame.shape  # 获取图片的高度、宽度（忽略通道数）

    '''进度窗口'''
    progress_window = tk.Toplevel(root)  # 创建一个顶层窗口作为进度显示窗口，root 是主窗口
    progress_window.title("正在导出视频...")  # 设置进度窗口的标题为"正在导出视频..."
    progress_window.geometry("400x230")  # 设置窗口大小为宽度 400 像素，高度 230 像素
    progress_window.resizable(False, False)  # 禁止用户调整窗口大小（宽度和高度都不可调整）
    progress_window.protocol("WM_DELETE_WINDOW", lambda: None)  # 禁用窗口的关闭按钮（X按钮），lambda: None 表示点击关闭按钮时不执行任何操作
    progress_frame = ttk.Frame(progress_window, padding=15)  # 创建一个框架容器，用于放置进度相关的控件，padding=15 表示内边距为 15 像素
    progress_frame.pack(fill=tk.BOTH, expand=True)  # 让框架填充整个窗口，并在两个方向上都扩展（fill=tk.BOTH 表示水平和垂直都填充）
    ttk.Label(progress_frame, text="正在导出视频...", font=("Arial", 10, "bold")).pack(anchor="w")  # 创建一个标签显示"正在导出视频..."，字体为 Arial ，大小 10 ，加粗；anchor="w" 表示文本左对齐（west）
    ttk.Separator(progress_frame).pack(fill=tk.X, pady=5)  # 添加一条水平分隔线，fill=tk.X 表示填充X方向（水平），pady=5 表示垂直方向外边距为 5 像素

    '''创建进度条'''
    progress_var = tk.DoubleVar(value=0)  # 创建一个 DoubleVar 变量来存储进度值，初始值为 0
    progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=len(images), length=350, mode="determinate")  # 创建一个进度条，绑定到 progress_var 变量，maximum=len(images) 表示最大值为图片数量（总进度），length=350 表示进度条长度为 350 像素，mode="determinate" 表示确定模式（有明确进度）
    progress_bar.pack(fill=tk.X, pady=(0, 10))  # 填充 X 方向（水平），pady=(0, 10)表示上边距为 0 ，下边距为 10 像素

    '''创建状态显示框架'''
    status_frame = ttk.Frame(progress_frame)  # 创建一个框架用于放置状态信息
    status_frame.pack(fill=tk.X, pady=(0, 15))    # 填充X方向，pady=(0, 15)表示上边距为 0 ，下边距为 15 像素

    '''左侧状态信息'''
    left_status = ttk.Frame(status_frame)  # 创建左侧状态信息框架
    left_status.pack(side=tk.LEFT, fill=tk.X, expand=True)  # side=tk.LEFT 表示靠左放置，fill=tk.X 表示水平填充，expand=True 表示可扩展
    percent_var = tk.StringVar(value="0%")  # 创建一个字符串变量存储百分比，初始值为"0%"
    ttk.Label(left_status, textvariable=percent_var, font=("Arial", 10)).pack(anchor="w")  # 创建一个标签显示百分比，字体为 Arial，大小 10 ，anchor="w"表示左对齐
    files_var = tk.StringVar(value=f"0 / {len(images)} 文件已处理")  # 创建一个字符串变量存储文件处理进度，初始值为"0 / 总图片数 文件已处理"
    ttk.Label(left_status, textvariable=files_var, font=("Arial", 9)).pack(anchor="w")  # 创建一个标签显示文件处理进度，字体为 Arial，大小 9 ，左对齐

    '''右侧尺寸信息'''
    
    size_info = ttk.Frame(status_frame)  # 创建右侧尺寸信息框架
    size_info.pack(side=tk.RIGHT, fill=tk.X)  # side=tk.RIGHT 表示靠右放置，fill=tk.X 表示水平填充
    res_var = tk.StringVar(value=f"{width}x{height}")  # 创建一个字符串变量存储分辨率，初始值为"宽度x高度"
    ttk.Label(size_info, textvariable=res_var, font=("Arial", 9)).pack(anchor="e")  # 创建一个标签显示分辨率，字体为 Arial ，大小 9 ，anchor="e"表示右对齐（east）
    size_var = tk.StringVar(value="估计大小: ---")  # 创建一个字符串变量存储估计大小，初始值为"估计大小: ---"
    ttk.Label(size_info, textvariable=size_var, font=("Arial", 9)).pack(anchor="e")  # 创建一个标签显示估计大小，字体为 Arial ，大小 9 ，右对齐

    '''剩余时间显示'''
    time_frame = ttk.Frame(progress_frame)  # 创建剩余时间框架
    time_frame.pack(fill=tk.X)  # 创建剩余时间框架
    time_var = tk.StringVar(value="估计剩余时间: --:--")  # 时间变量
    ttk.Label(time_frame, textvariable=time_var, font=("Arial", 9)).pack(anchor="w")  # 添加剩余时间标签
    cancel_flag = threading.Event()  # 创建取消标志事件

    # 定义函数：取消导出操作
    def cancel_export():
        if messagebox.askyesno("确认取消", "你确定要取消视频导出吗？", parent=progress_window):  # 取消导出确认对话框
            cancel_flag.set()  # 设置取消标志

    '''创建取消按钮'''
    button_frame = ttk.Frame(progress_frame)  # 创建按钮框架
    button_frame.pack(fill=tk.X, pady=(10, 0))  # 填充X方向，上边距为10像素
    cancel_button = ttk.Button(button_frame, text="取消导出", command=cancel_export, width=15)  # 创建取消按钮，点击时调用 cancel_export 函数
    cancel_button.pack(pady=5)  # 添加按钮的上下边距为5像素

    root.update_idletasks()  # 更新UI
    progress_window.grab_set()  # 使进度窗口获取焦点
    update_queue = queue.Queue()  # 创建更新队列

    # 定义函数：格式化时间为MM:SS
    def format_time(seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    # 定义函数：从队列中获取更新并更新UI
    def update_from_queue():
        if not progress_window.winfo_exists():  # 如果窗口已不存在
            return
        try:
            while not update_queue.empty():  # 处理队列中的所有消息
                current, total, remaining_time, estimated_size = update_queue.get_nowait()  # 获取当前进度、总数、剩余时间和估计大小
                percent = int(current * 100 / total)  # 计算百分比
                percent_var.set(f"{percent}%")  # 更新百分比显示
                files_var.set(f"{current} / {total} 文件已处理")  # 更新文件计数
                time_var.set(f"估计剩余时间: {format_time(remaining_time) if remaining_time is not None else '--:--'}")  # 更新剩余时间显示，并调用 format_time 函数格式化时间
                size_var.set(f"估计大小: {estimated_size:.1f}MB" if estimated_size else "估计大小: ---")  # 更新大小估计
                progress_var.set(current)  # 更新进度条
        except queue.Empty:  # 队列为空时忽略
            pass
        finally:
            if not cancel_flag.is_set():  # 如果没有取消
                # 100ms后再次检查更新
                progress_window.after(100, update_from_queue)  # 每 100 毫秒调用一次 update_from_queue 函数以进行进度条数据更新

    # 定义函数：视频导出，并接收一个队列用于更新进度
    def do_export(update_q):
        temp_output = None  # 初始化临时输出文件路径
        video = None  # 初始化视频编码器对象
        try:
            '''创建临时文件路径'''
            temp_dir = tempfile.gettempdir()  # 获取系统临时目录
            temp_file = f"temp_framekeeper_{os.getpid()}.mp4"  # 使用进程ID创建唯一临时文件名
            temp_output = os.path.join(temp_dir, temp_file)  # 拼接完整临时文件路径

            '''初始化视频编码器'''
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # 使用MP4V编解码器
            
            video = cv2.VideoWriter(temp_output, fourcc, frame_rate, (width, height))  # 创建视频写入器：参数依次为输出路径、编解码器、帧率(来自外部变量)、分辨率(宽x高)
            if not video.isOpened():  # 检查编码器是否初始化成功
                raise Exception("无法初始化视频编码器。")
            
            '''估算总文件大小（基于第一帧大小）'''
            first_frame_size = os.path.getsize(first_image_path)  # 获取第一张图片的文件大小(字节)
            
            estimated_total_size_mb = len(images) * first_frame_size * 0.5 / (1024 * 1024)  # 估算总大小：图片数量 × 第一帧大小 × 压缩系数0.5 ÷ (1024×1024转换为MB)
            start_time = time.time()  # 记录开始时间戳，用于计算处理时间

            '''处理每一张图片'''
            for i, image_path in enumerate(images):  # 遍历所有图片
                if cancel_flag.is_set():  # 检查是否设置了取消标志
                    break
                try:
                    '''读取并解码图片'''
                    with open(image_path, "rb") as f:  # 以二进制模式读取图片
                        img_np = np.frombuffer(f.read(), np.uint8)  # 将二进制数据转为 numpy 数组
                    frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)  # 解码为彩色图像
                    if frame is None:  # 如果解码失败
                        continue
                    video.write(frame)  # 将帧写入视频文件
                except Exception:  # 忽略处理中的错误
                    continue

                '''计算剩余时间'''
                elapsed = time.time() - start_time  # 已用时间(秒)
                remaining = (elapsed / (i + 1)) * (len(images) - (i + 1)) if i < len(images) - 1 else 0  # 剩余时间估算：(已用时间/已处理帧数) × 剩余帧数
                update_q.put((i + 1, len(images), remaining, estimated_total_size_mb))  # 将进度信息放入队列：(当前进度, 总数, 剩余时间, 估计大小)

            if video:  # 确保释放视频资源
                video.release()
                video = None

            if cancel_flag.is_set():  # 如果已取消  
                root.after(0, lambda: messagebox.showinfo("导出取消", "视频导出已被取消。", parent=root))  # 在主线程显示取消信息
                return

            shutil.move(temp_output, save_path)  # 将临时文件移动到最终保存路径

            '''计算最终文件大小和视频时长'''
            final_size = os.path.getsize(save_path) / (1024 * 1024)  # 最终文件大小(MB)
            duration = len(images) / frame_rate  # 视频时长(秒) = 总帧数/帧率

            '''在主线程显示成功信息'''
            root.after(0, lambda: messagebox.showinfo("视频导出成功", 
                f"视频已成功导出:\n视频路径: {save_path}\n视频尺寸: {width}x{height}\n"
                f"视频时长: {duration:.1f}秒\n视频大小: {final_size:.1f}MB", 
                parent=root))

        except Exception as e:  # 捕获所有异常
            traceback.print_exc()  # 打印异常堆栈
            root.after(0, lambda: messagebox.showerror("导出错误", f"导出过程中发生错误:\n{str(e)}", parent=progress_window))  # 在主线程显示错误信息
        finally:
            if video is not None:  # 确保释放视频资源
                video.release()
            if temp_output and os.path.exists(temp_output):  # 清理临时文件
                try: os.remove(temp_output)
                except OSError: pass
            if progress_window.winfo_exists():  # 如果进度窗口还存在
                root.after(0, progress_window.destroy)  # 在主线程销毁进度窗口

    progress_window.after(100, update_from_queue)  # 启动UI更新循环
    threading.Thread(target=do_export, args=(update_queue,), daemon=True).start()  # 调用 do_export 函数，启动导出线程

# 定义函数：退出程序时的处理函数
def on_quit(icon):
    stop_screenshotting(icon)  # 停止截图功能
    icon.stop()  # 停止托盘图标
    root.quit()  # 退出 Tkinter 主循环 5

# 定义函数：设置时间间隔
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
    icon.menu = pystray.Menu(item(f"状态: {status_text}", None, enabled=False), pystray.Menu.SEPARATOR, start_stop_item, item("快速更改时间间隔", pystray.Menu(item("5 秒", set_interval(icon, 5)), item("10 秒", set_interval(icon, 10)), item("30 秒", set_interval(icon, 30)), item("60 秒", set_interval(icon, 60)))), item("导出为视频", lambda: run_in_main_thread(export_to_video, icon)), item("设置", lambda: open_settings_window(icon)), pystray.Menu.SEPARATOR, item("退出", lambda: on_quit(icon)))  # 托盘菜单

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
