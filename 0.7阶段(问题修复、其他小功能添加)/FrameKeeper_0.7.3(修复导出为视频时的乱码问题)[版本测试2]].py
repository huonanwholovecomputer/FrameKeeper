# 导入相关模块
import io  # 用于 BytesIO 操作
import re  # 正则表达式
import os  # 操作系统接口 - 文件和目录操作
import sys  # 系统相关功能 - 命令行参数、退出程序等
import cv2  # OpenCV 库 - 计算机视觉和图像处理
import time  # 时间相关功能 - 延时、计时等
import queue  # 队列 - 线程间通信
import psutil  # 内存监控
import ctypes  # C语言兼容库 - 调用 Windows API
import shutil  # 高级文件操作 - 复制、移动、删除等
import pystray  # 系统托盘图标创建和管理
import tempfile  # 临时文件和目录管理
import threading  # 多线程编程支持
import subprocess  # 子进程管理 - 运行外部程序
import numpy as np  # 数组和矩阵处理 - 数值计算
import configparser  # 配置文件解析器
import tkinter as tk  # GUI 工具包 - 创建图形界面
import winreg as reg  # Windows 注册表操作
from datetime import datetime  # 时间处理
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
        self.project_name = "默认项目"  # 默认项目名称
        self.project_path = os.path.join(self.base_save_path, self.project_name)  # 默认项目路径为保存路径下的默认项目文件夹
        self.format = "JPG"  # 默认图片格式为 JPG
        self.jpg_quality = 75  # 默认 JPG 压缩质量为 75
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
            self.base_save_path = self.config.get("DEFAULT", "base_save_path")  # 获取截图的储存位置
            self.project_name = self.config.get("DEFAULT", "last_porject_name")  # 获取上次使用的项目名称
            self.project_path = self.config.get("DEFAULT", "last_project_path")  # 获取上次使用的项目路径
            self.current_subfolder = self.config.get("DEFAULT", "current_subfolder")  # 获取截图时间间隔
            self.format = self.config.get("DEFAULT", "format")  # 获取图片格式
            self.jpg_quality = self.config.getint("DEFAULT", "jpg_quality")  # 获取JPG压缩质量
            self.auto_start = self.config.getboolean("DEFAULT", "auto_start")  # 获取是否开机自启
        else:  # 如果配置文件不存在，则使用默认值
            self.save_config()  # 调用函数save_config保存一个默认配置文件到配置文件目录

    # 定义函数：保存配置到文件
    def save_config(self):
        self.config["DEFAULT"] = {
            "interval": self.interval,
            "base_save_path": self.base_save_path,
            "last_porject_name": self.project_name,
            "last_project_path": self.project_path,
            "current_subfolder": self.current_subfolder,
            "format": self.format,
            "jpg_quality": self.jpg_quality,
            "auto_start": self.auto_start
        }
        with open(self.config_file, "w") as configfile:  # 打开配置文件进行写入
            self.config.write(configfile)  # 写入配置内容

    # 定义函数：获取当前保存路径
    def get_current_save_path(self):  # 定义获取当前路径方法
        return os.path.join(self.project_path, self.current_subfolder)  # 返回当前子文件夹完整路径

    # 定义函数：增加文件计数并检查是否需要创建新文件夹
    def increment_file_count(self):  # 定义文件计数增加方法
        current_path = self.get_current_save_path()  # 获取当前保存路径
        self.current_file_count = len([f for f in os.listdir(current_path) if os.path.isfile(os.path.join(current_path, f))])  # 重新计算实际文件数量
        if self.current_file_count >= 10000:  # 检查是否达到文件上限
            new_folder = str(int(self.current_subfolder) + 1)  # 计算新文件夹编号
            self.current_subfolder = new_folder  # 更新子文件夹名
            self.current_file_count = 0  # 重置文件计数器
            os.makedirs(self.get_current_save_path(), exist_ok=True)  # 创建新子文件夹
            self.save_config()  # 调用函数{save_config()}保存当前配置文件

    # 定义函数：初始化文件夹计数器
    def initialize_folder_counter(self):
        '''确保基础路径和项目路径存在'''
        if not os.path.exists(self.base_save_path):  # 如果基础保存路径不存在
            os.makedirs(self.base_save_path)  # 创建基础保存路径
        if not os.path.exists(self.project_path):  # 如果默认项目路径不存在
            os.makedirs(self.project_path)  # 创建默认项目路径

        subfolders = [f for f in os.listdir(self.project_path) if os.path.isdir(os.path.join(self.project_path, f)) and f.isdigit()]  # 列出所有数字命名的子文件夹

        '''如果没有子文件夹，初始化为第一个子文件夹'''
        if not subfolders:  # 如果不存在子文件夹
            self.current_subfolder = "1"  # 初始化第一个子文件夹名
            self.current_file_count = 0  # 初始化文件计数器
            os.makedirs(self.get_current_save_path(), exist_ok=True)  # 创建初始子文件夹
            return  # 结束函数  # 直接返回

        '''找到编号最大的子文件夹'''
        max_folder = max(subfolders, key=int)  # 找到编号最大的子文件夹
        current_path = os.path.join(self.project_path, max_folder)  # 构建最大子文件夹完整路径

        '''计算实际文件数量'''
        self.current_file_count = len([f for f in os.listdir(current_path) if os.path.isfile(os.path.join(current_path, f))])
        self.current_subfolder = max_folder

        '''如果文件数量达到上限，创建新文件夹'''
        if self.current_file_count >= 10000:  # 如果文件数达到上限
            new_folder = str(int(max_folder) + 1)  # 计算新文件夹编号
            self.current_subfolder = new_folder  # 更新当前子文件夹名
            self.current_file_count = 0  # 重置文件计数器
            os.makedirs(self.get_current_save_path(), exist_ok=True)  # 创建新子文件夹

        self.save_config()  # 保存配置

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
        if getattr(sys, 'frozen', False):  # 判断是否是打包后的EXE
            command = f'"{script_path}"'  # EXE模式：直接使用双引号包裹路径
        else:
            command = f'"{sys.executable}" "{script_path}"'  # 脚本模式：Python解释器 + 脚本路径(双引号包裹)
        reg.SetValueEx(key, "FrameKeeper", 0, reg.REG_SZ, command)  # 在注册表中创建/修改值，键名称设为"FrameKeeper"，值类型为 REG_SZ (字符串)，值数据是 command 变量
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

# 定义函数：清理冗余截图
def clean_nonstandard_frame(root_directory):
    confirm = messagebox.askyesno("确认清理", f"即将清理【{config.project_name}】项目的冗余截图，参考截图时间间隔为 {config.interval} 秒\n删除后不可恢复，是否继续?", icon='warning')  # 弹出确认对话框，询问用户是否继续清理操作
    if not confirm:  # 如果用户点击"否"或关闭对话框
        return  # 直接退出函数，不执行后续操作

    pattern = re.compile(r'^capture_(\d{8}_\d{6})\.(jpg|png)$')  # 定义文件格式的正则表达式

    total_deleted = 0  # 初始化计数器，记录总共删除的文件数
    log_content = []  # 用于存储详细日志信息的列表

    '''使用os.walk遍历根目录及其所有子目录'''
    for dirpath, dirnames, filenames in os.walk(root_directory):  # 遍历根目录及其所有子目录
        file_times = []  # 存储当前目录提取到的文件时间和文件名
        
        '''收集当前目录下所有符合条件的文件'''
        for filename in filenames:
            match = pattern.match(filename)  # 使用正则表达式匹配文件名
            if match:
                time_str = match.group(1)  # 提取时间部分
                try:
                    time = datetime.strptime(time_str, "%Y%m%d_%H%M%S")  # 转换时间为 datetime 对象
                    file_times.append((time, filename))  # 存储(时间, 文件名)元组
                except ValueError:
                    continue  # 时间格式无效的文件跳过

        if not file_times:  # 如果没有符合条件的文件
            continue  # 跳过当前目录

        file_times.sort(key=lambda x: x[0])  # 按时间排序文件列表

        '''计算需要删除的文件'''
        delete_list = []
        last_kept_time = file_times[0][0]  # 保留的第一个文件时间

        '''遍历所有文件（从第二个开始）'''
        for time, filename in file_times[1:]:
            delta = (time - last_kept_time).total_seconds()  # 计算与上一个保留文件的时间差（秒）
            if delta < config.interval:  # 如果时间间隔小于配置中的间隔
                delete_list.append(filename)  #  加入删除列表
            else:
                last_kept_time = time  # 时间间隔大于等于 config.interval 秒，更新保留时间点

        if not delete_list:  # 如果没有要删除的文件
            continue  #  跳过当前目录

        '''记录当前目录信息到日志'''
        dir_log = f"\n处理目录: {dirpath}\n删除以下 {len(delete_list)} 个文件:"
        log_content.append(dir_log)

        '''处理删除操作'''
        dir_deleted = 0  # 初始化当前目录删除计数器
        for filename in delete_list:  # 遍历需要删除的文件列表
            filepath = os.path.join(dirpath, filename)  # 构建完整文件路径
            file_log = f" - {filename}"  # 记录文件名到日志
            log_content.append(file_log)  # 添加到日志内容
            try:
                os.remove(filepath)  # 删除文件
                dir_deleted += 1  # 删除计数器加 1
            except Exception as e:  # 捕获删除文件时的异常
                error_log = f"  删除失败 {filename}: {str(e)}"  # 记录错误信息到日志
                log_content.append(error_log)  # 添加到日志内容

        total_deleted += dir_deleted  # 更新总删除计数器

    '''将日志写入桌面文件'''
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")  # 获取用户桌面路径
    log_file = os.path.join(desktop_path, "详细信息.log")  # 构建日志文件路径

    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(log_content))  # 将日志内容写入文件
    except Exception as e:
        messagebox.showerror("错误", f"无法写入日志文件: {str(e)}")  # 如果写入日志文件失败，显示错误消息

    messagebox.showinfo("清理完成", f"已清理冗余截图 {total_deleted} 个\n详细信息请查看桌面上的[详细信息.log]文件")  # 显示完成对话框

'''设置窗口功能'''
# 定义函数：打开“设置”窗口
def open_settings_window(icon):
    '''窗口创建'''
    settings_window = tk.Toplevel()  # 创建设置窗口（顶级窗口）
    settings_window.title("FrameKeeper 设置")  # 设置窗口标题
    settings_window.geometry("500x300")  # 设置窗口大小(宽x高)
    settings_window.resizable(False, False)  # 禁止调整窗口大小

    '''创建主框架容器'''
    main_frame = ttk.Frame(settings_window, padding="10")  # 设置内边距为10像素
    main_frame.pack(fill="both", expand=True)  # 填充整个窗口并允许扩展

    '''控件布局'''
    ttk.Label(main_frame, text="截图间隔 (秒):").grid(row=0, column=0, sticky="w", pady=5)  # 添加截图间隔标签(第0行第0列)
    interval_var = tk.IntVar(value=config.interval)  # 创建并初始化截图间隔变量，绑定到输入框，从配置中读取初始值
    ttk.Entry(main_frame, textvariable=interval_var).grid(row=0, column=1, sticky="ew")  # 创建输入框并放置在网格布局中(第0行第1列)
    ttk.Label(main_frame, text="程序储存目录:").grid(row=1, column=0, sticky="w", pady=5)  # 程序储存目录标签(第1行第0列)
    path_var = tk.StringVar(value=config.base_save_path)  # 创建并初始化保存路径变量，绑定到输入框，从配置中读取初始路径
    save_path_entry = ttk.Entry(main_frame, textvariable=path_var)  # 创建路径输入框
    save_path_entry.grid(row=1, column=1, sticky="ew")  # 放置在网格布局中(第1行第1列)

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
        config.base_save_path = path_var.get()  # 获取保存路径
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

# 定义函数：剩余时间估计
def format_time(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

# 全局变量，用于在多线程中传递异常
exception_queue = queue.Queue()

# 定义函数：获取 ffmpeg.exe 路径(兼容打包和未打包情况)
def get_ffmpeg_path():
    if getattr(sys, 'frozen', False):  # 判断是否打包成 EXE
        base_dir = os.path.dirname(sys.executable)  # EXE 所在目录
    else:
        base_dir = os.path.dirname(__file__)  # 脚本所在目录
    return os.path.join(base_dir, "_internal", "ffmpeg.exe")

# 定义函数：创建 FFmpeg 写入器
def create_ffmpeg_writer(output_path, width, height, fps, bitrate):
    ffmpeg_path = get_ffmpeg_path()
    if not os.path.exists(ffmpeg_path):
        messagebox.showerror("错误", "找不到 FFmpeg。请确保主程序所在目录下的_internal/ffmpeg.exe存在。")
        raise FileNotFoundError("ffmpeg.exe 未找到")

    '''构建 FFmpeg 命令'''
    # -ffmpeg_path: 使用绝对路径调用 ffmpeg
    # -y: 覆盖输出文件
    # -f rawvideo: 输入格式为原始视频数据
    # -vcodec rawvideo: 输入编解码器
    # -s: 视频尺寸 (widthxheight)
    # -pix_fmt bgr24: 输入像素格式 (OpenCV 默认使用 BGR)
    # -r: 输入帧率
    # -i -: 从标准输入 (stdin) 读取数据
    # -c:v libx264: 使用 H.264 编码器
    # -b:v: 视频目标比特率 (例如 '2000k')
    # -pix_fmt yuv420p: 输出像素格式，确保在大多数播放器上兼容
    # -preset: 编码速度与压缩率的权衡 (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)
    # 'veryfast' 是一个很好的平衡点
    command = [
        ffmpeg_path,
        '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', f'{int(width)}x{int(height)}',
        '-pix_fmt', 'bgr24',
        '-r', str(fps),
        '-i', '-',
        '-c:v', 'libx264',
        '-b:v', f'{bitrate // 1000}k',
        '-pix_fmt', 'yuv420p',
        '-preset', 'veryfast',
        output_path
    ]

    '''添加 creationflags 参数来隐藏控制台窗口'''
    if os.name == 'nt':  # 仅适用于 Windows 系统
        startupinfo = subprocess.STARTUPINFO()  # 创建 STARTUPINFO 对象
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # 设置标志以使用窗口显示选项
        startupinfo.wShowWindow = subprocess.SW_HIDE  # 隐藏窗口
    else:
        startupinfo = None  # 对于非 Windows 系统，不需要设置 startupinfo

    '''启动子进程'''
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,  # 允许向 FFmpeg 写入数据
        stdout=subprocess.DEVNULL,  # 隐藏 FFmpeg 的控制台输出，避免刷屏
        stderr=subprocess.DEVNULL,  # 隐藏 FFmpeg 的控制台输出，避免刷屏
        startupinfo=startupinfo  # 传入 startupinfo 以判断是否隐藏控制台窗口
    )
    return process  # 返回 FFmpeg 子进程对象

# 定义函数：根据分辨率动态计算推荐的比特率
def calculate_bitrate(width, height, fps):
    '''确保有效的分辨率'''
    if width <= 0 or height <= 0:
        return 2_000_000  # 默认比特率

    pixels = width * height  # 计算像素总数

    '''根据分辨率范围设置比特率'''
    if pixels <= 640 * 480:      # SD (480p)
        base_bitrate = 2_500_000
    elif pixels <= 1280 * 720:     # HD (720p)
        base_bitrate = 4_500_000
    elif pixels <= 1920 * 1080:    # Full HD (1080p)
        base_bitrate = 6_500_000
    elif pixels <= 3840 * 2160:    # 4K
        base_bitrate = 10_500_000
    else:                          # 更高分辨率
        base_bitrate = 15_500_000

    '''根据帧率调整比特率'''
    fps_factor = max(0.5, min(2.0, fps / 30.0))  # 限制帧率因子在 0.5 到 2.0 之间
    adjusted_bitrate = int(base_bitrate * fps_factor)  # 调整比特率
    
    '''确保最小比特率'''
    min_bitrate = 500_000  # 设置最小比特率为 500 kbps
    return max(adjusted_bitrate, min_bitrate)  # 返回计算后的比特率，确保不低于最小比特率

# 定义函数：生产者线程
def read_and_decode_worker(path_queue, frame_queue, cancel_flag, memory_threshold=95):
    consecutive_high_memory = 0  # 初始化高内存连续计数
    while True:
        if cancel_flag.is_set():  # 检查是否收到取消信号
            break

        '''内存检查：连续3次检测到高内存才暂停'''
        mem_percent = psutil.virtual_memory().percent  # 获取当前内存使用百分比
        if mem_percent > memory_threshold:  # 检查内存是否超过阈值
            consecutive_high_memory += 1  # 增加高内存连续计数
            if consecutive_high_memory >= 3:  # 如果连续3次超过阈值
                sleep_time = min(0.1 * (2 ** (consecutive_high_memory - 3)), 2.0)  # 逐渐增加等待时间：100ms, 200ms, 400ms...
                time.sleep(sleep_time)  # 暂停线程以释放内存压力
                continue  # 跳过当前循环
        else:
            consecutive_high_memory = 0  # 重置高内存连续计数

        '''动态调整队列获取速度'''
        try:
            '如果队列较满，降低处理速度'
            if frame_queue.qsize() > frame_queue.maxsize * 0.8:  # 检查帧队列是否接近满
                time.sleep(0.05)  # 稍微延迟以减缓处理速度
            image_path = path_queue.get(timeout=0.5)  # 从路径队列获取图像路径，最多等待0.5秒
        except queue.Empty:  # 如果队列为空
            continue  # 继续下一次循环
        if image_path is None:  # 如果获取到None（结束信号）
            break  # 退出循环
        try:
            image_path_unicode = image_path if isinstance(image_path, str) else image_path.decode('utf-8')  # 处理中文路径 - 使用unicode字符串
            frame = cv2.imdecode(np.fromfile(image_path_unicode, dtype=np.uint8), cv2.IMREAD_COLOR)  # 读取彩色图像
            if frame is None:  # 如果图像读取失败
                messagebox.showerror("错误", f"无法读取图片: {image_path_unicode}")  # 抛出IO错误
            while not cancel_flag.is_set():  # 在未收到取消信号时循环
                try:
                    if frame_queue.full():  # 检查帧队列是否已满
                        time.sleep(0.01)  # 短暂等待
                        continue  # 继续尝试
                    frame_queue.put(frame, block=False)  # 将帧放入队列（非阻塞方式）
                    break  # 成功放入后退出循环
                except queue.Full:  # 如果队列已满
                    time.sleep(0.01)  # 短暂等待后重试
        except Exception as e:  # 捕获所有其他异常
            messagebox.showerror("错误", f"警告：无法处理文件 {os.path.basename(image_path)}: {e}")  # 显示错误消息
        finally:
            path_queue.task_done()  # 标记路径队列中的任务已完成
    frame_queue.put(None)  # 向帧队列发送结束信号

# 定义函数：消费者线程
def encode_worker(frame_queue, ffmpeg_stdin, total_frames, update_q, cancel_flag, start_time, num_producers):
    producers_finished = 0  # 记录已完成的生产者线程数量
    processed_count = 0  # 已处理的帧数计数器
    last_update_time = time.time()  # 记录上次更新进度的时间
    try:
        '''主循环：当还有生产者线程在工作且未收到取消信号时继续'''
        while producers_finished < num_producers and not cancel_flag.is_set():
            try:
                frame = frame_queue.get(timeout=2)  # 从帧队列获取帧，最多等待2秒
                if frame is None:  # 如果收到结束信号（None）
                    producers_finished += 1  # 增加已完成的生产者计数
                    continue  # 继续处理下一帧
                ffmpeg_stdin.write(frame.tobytes())  # 将 NumPy 数组帧转换为原始字节并写入 FFmpeg 的 stdin
                processed_count += 1  # 增加已处理帧数计数
                current_time = time.time()  # 获取当前时间
                if (processed_count % max(1, total_frames // 100) == 0 or current_time - last_update_time > 0.5):  # 更新进度条件
                    elapsed = current_time - start_time  # 计算已用时间
                    remaining = (elapsed / processed_count) * (total_frames - processed_count) if processed_count > 0 else 0  # 计算剩余时间
                    update_q.put((processed_count, total_frames, remaining, None))  # 发送进度更新
                    last_update_time = current_time  # 更新最后更新时间
            except queue.Empty:  # 如果帧队列为空
                time.sleep(0.05)  # 短暂等待后重试

    except Exception as e:  # 捕获所有其他异常
        exception_queue.put(e)  # 将异常放入异常队列

def resolution_check_worker(path_queue, result_queue, progress_queue, cancel_flag):
    """
    生产者线程工作函数：读取一个图片文件，获取其分辨率，然后将结果放入队列。
    该函数在独立线程中运行。
    """
    while not cancel_flag.is_set():
        try:
            # 从队列中获取一个路径，使用超时以便能检查cancel_flag
            img_path = path_queue.get(timeout=0.1)
            
            try:
                with Image.open(img_path) as img:
                    width, height = img.size
                    # 将结果（路径、宽度、高度）放入结果队列
                    result_queue.put((img_path, width, height))
            except Exception:
                # 如果图片损坏或无法读取，则将其路径与None尺寸一起放入结果
                result_queue.put((img_path, None, None))
            finally:
                # 发出此任务已完成的信号，并发送一个进度更新
                path_queue.task_done()
                progress_queue.put(1) # 表示一个文件已被处理

        except queue.Empty:
            # 如果队列为空，则该线程的工作已完成
            break
        except Exception:
            # 捕获线程中任何其他意外错误
            continue

def check_image_resolutions_threaded(images, parent_window):
    """
    管理带进度条的多线程分辨率检查过程。
    """
    # 创建进度窗口
    progress_window = tk.Toplevel(parent_window)
    progress_window.title("检查图片分辨率")
    progress_window.geometry("400x180")
    progress_window.resizable(False, False)
    progress_window.transient(parent_window)
    progress_window.grab_set()

    progress_frame = ttk.Frame(progress_window, padding=15)
    progress_frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(progress_frame, text="正在全面检查图片分辨率...", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))

    total_files = len(images)
    progress_var = tk.DoubleVar(value=0)
    progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=total_files, mode="determinate")
    progress_bar.pack(fill=tk.X, pady=10)

    files_var = tk.StringVar(value=f"0 / {total_files} 张图片已检查")
    ttk.Label(progress_frame, textvariable=files_var).pack(anchor="w")

    cancel_flag = threading.Event()
    
    def cancel_check():
        if messagebox.askyesno("确认取消", "确定要取消分辨率检查吗？", parent=progress_window):
            cancel_flag.set()
            progress_window.destroy()
    
    cancel_button = ttk.Button(progress_frame, text="取消", command=cancel_check)
    cancel_button.pack(pady=15)

    # 创建队列
    path_queue = queue.Queue()
    result_queue = queue.Queue()
    progress_queue = queue.Queue()

    # 填充任务队列
    for img_path in images:
        path_queue.put(img_path)

    # 线程安全计数器
    processed_count = 0
    all_results = []
    incompatible_images = []

    # 进度更新函数
    def update_progress_ui():
        nonlocal processed_count
        
        # 从队列中获取更新
        while not progress_queue.empty():
            processed_count += progress_queue.get_nowait()
        
        # 更新UI
        progress_var.set(processed_count)
        files_var.set(f"{processed_count} / {total_files} 张图片已检查")
        
        # 检查是否完成
        if processed_count >= total_files or cancel_flag.is_set():
            progress_window.destroy()
        else:
            # 继续调度更新
            progress_window.after(100, update_progress_ui)

    # 创建工作线程
    num_threads = min(os.cpu_count() or 4, 8)  # 最多使用8个线程
    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(
            target=resolution_check_worker,
            args=(path_queue, result_queue, progress_queue, cancel_flag),
            daemon=True
        )
        thread.start()
        threads.append(thread)

    # 启动UI更新循环
    progress_window.after(100, update_progress_ui)
    parent_window.wait_window(progress_window)  # 等待进度窗口关闭

    # 如果用户取消了操作
    if cancel_flag.is_set():
        return None

    # 收集所有结果
    while not result_queue.empty():
        all_results.append(result_queue.get_nowait())
    
    # 分析结果
    resolutions = {}
    for path, width, height in all_results:
        if width is None:  # 无法读取的文件
            incompatible_images.append(path)
            continue
        
        aspect_ratio = round(width / height, 4) if height != 0 else 0
        res_key = f"{width}x{height}"
        if res_key not in resolutions:
            resolutions[res_key] = {"count": 0, "aspect": aspect_ratio}
        resolutions[res_key]["count"] += 1

    # 如果没有不一致的分辨率
    if len(resolutions) <= 1:
        return incompatible_images

    # 查找主要宽高比
    main_res_key = max(resolutions, key=lambda k: resolutions[k]["count"])
    main_aspect = resolutions[main_res_key]["aspect"]
    
    # 识别不匹配的图片
    paths_by_res = {}
    for path, width, height in all_results:
        if width is None:
            continue
        res_key = f"{width}x{height}"
        if res_key not in paths_by_res:
            paths_by_res[res_key] = []
        paths_by_res[res_key].append(path)

    for res_key, res_data in resolutions.items():
        if abs(res_data["aspect"] - main_aspect) > 0.01:  # 1%容差
            incompatible_images.extend(paths_by_res[res_key])
    
    # 处理不一致的图片
    if incompatible_images:
        response = messagebox.askyesno(
            "发现分辨率不一致的图片",
            f"检测到 {len(incompatible_images)} 张图片的分辨率与主流分辨率不一致。\n"
            "是否将这些图片移动到新建文件夹？",
            parent=parent_window
        )
        
        if response:
            base_dir = os.path.dirname(incompatible_images[0])
            new_folder = os.path.join(base_dir, "分辨率不一致的图片")
            
            if not os.path.exists(new_folder):
                os.makedirs(new_folder)
            
            moved_count = 0
            for img_path in incompatible_images:
                try:
                    if os.path.isfile(img_path):
                        filename = os.path.basename(img_path)
                        dest_path = os.path.join(new_folder, filename)
                        
                        # 处理文件名冲突
                        counter = 1
                        while os.path.exists(dest_path):
                            name, ext = os.path.splitext(filename)
                            dest_path = os.path.join(new_folder, f"{name}_{counter}{ext}")
                            counter += 1
                        
                        shutil.move(img_path, dest_path)
                        moved_count += 1
                except Exception as e:
                    print(f"移动图片失败: {img_path}, 错误: {str(e)}")
            
            # 更新原始图片列表
            images[:] = [img for img in images if img not in incompatible_images]
            
            messagebox.showinfo(
                "移动完成",
                f"已将 {moved_count} 张图片移动到:\n{new_folder}",
                parent=parent_window
            )
    
    return incompatible_images

# 定义函数：导出
def do_export_optimized(images, save_path, frame_rate, width, height, update_q, cancel_flag):
    temp_output = None  # 初始化临时输出文件路径为 None
    ffmpeg_process = None # 初始化FFmpeg 进程对象为 None
    try:
        '''动态调整线程数和队列大小'''
        num_cores = os.cpu_count() or 4  # 获取CPU核心数，默认为4
        num_reader_threads = max(1, min(num_cores - 1, 4))  # 限制最大线程数

        '''基于图片数量动态设置队列大小'''
        if len(images) < 100:
            max_queue_size = 10  # 如果图片少于100张，设置较小的队列大小
        elif len(images) < 500:
            max_queue_size = 20  # 如果图片少于500张，设置中等队列大小
        else:
            max_queue_size = 30  # 如果图片多于500张，设置较大的队列大小

        '''创建队列'''
        path_queue = queue.Queue()  # 用于存储图片路径的队列
        frame_queue = queue.Queue(maxsize=max_queue_size)  # 用于存储解码后的帧的队列，设置最大大小以控制内存使用
        for img_path in images:
            path_queue.put(img_path)  # 将所有图片路径放入路径队列

        '''确保临时目录存在'''
        temp_dir = tempfile.gettempdir()  # 获取系统临时目录
        if not os.path.exists(temp_dir):  
            os.makedirs(temp_dir)  # 如果临时目录不存在，则创建它

        temp_output = os.path.join(temp_dir, f"temp_export_{os.getpid()}_{time.time()}.mp4")  # 创建唯一的临时文件名

        '''初始化 FFmpeg 编码器'''
        bitrate = calculate_bitrate(width, height, frame_rate)  # 根据分辨率和帧率计算推荐的比特率
        ffmpeg_process = create_ffmpeg_writer(temp_output, width, height, frame_rate, bitrate)  # 创建 FFmpeg 编码器子进程
        
        '''创建并启动线程'''
        start_time = time.time()  # 记录开始时间
        threads = []  # 初始化线程列表

        '''消费者线程'''
        # 将 ffmpeg_process.stdin 传递给编码器
        encoder_thread = threading.Thread(
            target=encode_worker,  # 编码器线程
            args=(frame_queue, ffmpeg_process.stdin, len(images), update_q, cancel_flag, start_time, num_reader_threads),  # 传递必要的参数
            daemon=True  # 设置为守护线程，确保主程序退出时它也会退出
        )
        encoder_thread.start()  # 启动编码器线程
        threads.append(encoder_thread)  # 将编码器线程添加到线程列表

        '''生产者线程'''
        for _ in range(num_reader_threads):
            reader_thread = threading.Thread(target=read_and_decode_worker, args=(path_queue, frame_queue, cancel_flag, 95), daemon=True)  # 创建生产者线程
            reader_thread.start()  # 启动生产者线程
            threads.append(reader_thread)  # 将生产者线程添加到线程列表

        path_queue.join()  # 等待路径队列中的所有任务完成
        
        '''发送结束信号'''
        for _ in range(num_reader_threads):
            path_queue.put(None)  # 向每个生产者线程发送结束信号（None）
            
        '''等待线程结束'''
        for t in threads:
            t.join(timeout=10.0) # 增加超时时间以防万一
        if cancel_flag.is_set():  # 如果取消标志被设置
            root.after(0, lambda: messagebox.showinfo("导出取消", "视频导出已被取消。", parent=root))  # 在主线程中显示取消信息
            return  # 直接返回

        '''完成导出'''
        ffmpeg_process.stdin.close()  # 关闭 FFmpeg 的标准输入流，通知 FFmpeg 没有更多数据
        ffmpeg_process.wait()  # 等待 FFmpeg 进程完成

        '''检查 FFmpeg 是否成功执行'''
        if ffmpeg_process.returncode != 0:
            messagebox.showerror("错误", f"FFmpeg 编码失败，返回码: {ffmpeg_process.returncode}。请检查控制台输出。")

        shutil.move(temp_output, save_path)
        final_size = os.path.getsize(save_path) / (1024 * 1024)
        duration = len(images) / frame_rate
        root.after(0, lambda: messagebox.showinfo("视频导出成功",
            f"视频已成功导出:\n视频路径: {save_path}\n视频尺寸: {width}x{height}\n"
            f"使用图片: {len(images)}张\n"
            f"视频时长: {duration:.1f}秒\n视频大小: {final_size:.1f}MB",
            parent=root))

    except Exception as e:
        cancel_flag.set()  # 设置取消标志以停止所有线程
        run_in_main_thread(messagebox.showerror, "导出错误", f"导出过程中发生严重错误:\n{str(e)}")

    finally:
        '''清理资源'''
        if ffmpeg_process:
            if ffmpeg_process.poll() is None:  # 如果进程仍在运行
                ffmpeg_process.terminate()  # 尝试终止进程
                ffmpeg_process.wait()  # 等待进程结束
        if temp_output and os.path.exists(temp_output):  # 如果临时输出文件存在
            try:
                os.remove(temp_output)  # 删除临时输出文件
            except OSError:
                pass  # 忽略删除失败的错误

# 定义函数：导出为视频
def export_to_video(icon=None):
    dialog_parent = tk.Toplevel(root)  # 创建顶层对话框窗口
    dialog_parent.withdraw()  # 隐藏对话框

    '''选择需要导出为视频的项目'''
    source_dir = filedialog.askdirectory(title="请选择需要导出为视频的项目：", initialdir=config.base_save_path, parent=dialog_parent)  # 打开目录选择对话框
    if not source_dir:  # 如果用户取消选择
        dialog_parent.destroy()  # 销毁对话框
        return  # 直接返回

    '''遍历子文件夹收集图片文件'''
    images = []  # 存储找到的图片路径
    for root_dir, dirs, files in os.walk(source_dir):  # 遍历目录树
        if root_dir == source_dir:  # 跳过根目录本身
            continue
        for file in files:  # 检查每个文件
            if file.lower().endswith((".png", ".jpg", ".jpeg")):  # 检查图片扩展名
                images.append(os.path.join(root_dir, file))  # 添加完整路径

    '''检查是否找到图片'''
    if not images:  # 如果没有找到图片
        messagebox.showwarning("无图片", "所选文件夹的子文件夹中没有找到图片文件", parent=dialog_parent)
        dialog_parent.destroy()  # 关闭对话框
        return  # 结束函数

    images.sort(key=lambda x: os.path.basename(x))  # 按文件名排序

    '''选择视频保存路径'''
    save_path = filedialog.asksaveasfilename(
        defaultextension=".mp4",  # 默认扩展名
        filetypes=[("MP4 文件", "*.mp4")],  # 文件类型过滤器
        title="保存视频文件",  # 对话框标题
        initialdir=os.path.join(os.path.expanduser("~"), "Desktop"),  # 默认目录
        parent=dialog_parent
    )
    if not save_path:  # 如果用户取消保存
        dialog_parent.destroy()  # 关闭对话框
        return  # 结束函数

    '''获取用户设置的帧率'''
    frame_rate = simpledialog.askinteger(
        "帧率",
        "请输入视频帧率 (FPS):",
        initialvalue=30,  # 默认值 30
        minvalue=1,  # 最小值 1
        maxvalue=60,  # 最大值 60
        parent=dialog_parent  # 对话框为父窗口
    )
    dialog_parent.destroy()  # 关闭对话框
    if not frame_rate:  # 如果用户取消输入
        return  # 结束函数

    # 执行分辨率检查
    incompatible_images = check_image_resolutions_threaded(images, root)
    
    # 如果用户取消了检查
    if incompatible_images is None:
        messagebox.showinfo("导出中止", "分辨率检查被取消，已中止导出操作。")
        return
    
    # 如果发现不一致分辨率
    if incompatible_images:
        # 显示不一致图片的数量
        answer = messagebox.askyesno(
            "分辨率不一致",
            f"发现 {len(incompatible_images)} 张图片的分辨率与主流分辨率不一致。\n是否继续导出？\n不一致的图片将被跳过。",
            icon='warning',
            parent=root
        )
        
        if not answer:  # 用户选择不继续
            return
        
        # 用户选择继续，从未通过检查的图片中移除不一致的图片
        images = [img for img in images if img not in incompatible_images]
        
        # 检查移除后是否还有图片
        if not images:
            messagebox.showwarning("无有效图片", "跳过不一致图片后，没有可导出的图片。")
            return
    
    # 读取第一帧图片获取视频尺寸（使用过滤后的列表）
    try:
        first_image = Image.open(images[0])
        width, height = first_image.size
        first_image.close()
    except Exception as e:
        messagebox.showerror("错误", f"无法读取第一张图片: {str(e)}")
        return

    '''读取第一帧图片获取视频尺寸'''
    try:
        with open(images[0], 'rb') as f:  # 以二进制模式打开第一张图片
            img_np = np.frombuffer(f.read(), np.uint8)  # 将文件内容读取为 NumPy 数组
            first_image = cv2.imdecode(img_np, cv2.IMREAD_COLOR)  # 解码为彩色图像
        if first_image is None:  # 如果读取失败
            messagebox.showerror("错误", f"无法读取第一帧图片: {images[0]}")  # 显示错误消息
        height, width, _ = first_image.shape  # 获取图片尺寸
    except Exception as e:  # 捕获所有异常
        messagebox.showerror("错误", f"读取首帧图片失败: {e}", parent=root)  # 显示错误消息
        return  # 结束函数

    '''进度窗口'''
    progress_window = tk.Toplevel(root)  # 创建进度窗口作为根窗口的子窗口
    progress_window.title("正在导出视频...")  # 设置窗口标题
    progress_window.geometry("400x300")  # 设置固定窗口大小
    progress_window.resizable(False, False)  # 禁止调整窗口大小
    progress_window.protocol("WM_DELETE_WINDOW", lambda: None)  # 禁用窗口关闭按钮

    '''主框架容器'''
    progress_frame = ttk.Frame(progress_window, padding=15)  # 带内边距的框架
    progress_frame.pack(fill=tk.BOTH, expand=True)  # 填充整个窗口

    '''标题标签'''
    ttk.Label(progress_frame, text="正在导出视频...", font=("Arial", 10, "bold")).pack(anchor="w")  # 左对齐的粗体标题
    ttk.Separator(progress_frame).pack(fill=tk.X, pady=5)  # 分隔线

    '''进度条组件'''
    progress_var = tk.DoubleVar(value=0)  # 进度值变量(0 - 100)
    progress_bar = ttk.Progressbar(
        progress_frame, 
        variable=progress_var,  # 绑定变量
        maximum=len(images),  # 最大值设为图片总数
        length=350,  # 进度条长度
        mode="determinate"  # 确定模式(有明确终点)
    )
    progress_bar.pack(fill=tk.X, pady=(0, 10))  # 填充水平空间

    '''状态信息区域'''
    status_frame = ttk.Frame(progress_frame)  # 状态信息容器
    status_frame.pack(fill=tk.X, pady=(0, 15))  # 填充水平空间

    '''左侧状态信息(百分比和文件数)'''
    left_status = ttk.Frame(status_frame)  # 左侧容器
    left_status.pack(side=tk.LEFT, fill=tk.X, expand=True)  # 左对齐
    percent_var = tk.StringVar(value="0%")  # 百分比显示变量
    ttk.Label(left_status, textvariable=percent_var, font=("Arial", 10)).pack(anchor="w")  # 百分比标签
    files_var = tk.StringVar(value=f"0 / {len(images)} 文件已处理")  # 文件计数变量
    ttk.Label(left_status, textvariable=files_var, font=("Arial", 9)).pack(anchor="w")  # 文件计数标签

    '''右侧状态信息(分辨率)'''
    size_info = ttk.Frame(status_frame)  # 右侧容器
    size_info.pack(side=tk.RIGHT, fill=tk.X)  # 右对齐
    res_var = tk.StringVar(value=f"{width}x{height}")  # 分辨率变量
    ttk.Label(size_info, textvariable=res_var, font=("Arial", 9)).pack(anchor="e")  # 分辨率标签

    '''剩余时间显示'''
    time_frame = ttk.Frame(progress_frame)  # 时间信息容器
    time_frame.pack(fill=tk.X)  # 填充水平空间
    time_var = tk.StringVar(value="估计剩余时间: --:--")  # 剩余时间变量
    ttk.Label(time_frame, textvariable=time_var, font=("Arial", 9)).pack(anchor="w")  # 剩余时间标签

    cancel_flag = threading.Event()  # 创建线程事件对象，用于控制导出线程的取消

    # 定义函数：取消导出
    def cancel_export():
        if messagebox.askyesno("确认取消", "你确定要取消视频导出吗？", parent=progress_window):  # 设置 parent 参数为父窗口以确保对话框居中
            cancel_flag.set()  # 设置取消标志，通知所有工作线程停止

    '''创建取消按钮区域'''
    button_frame = ttk.Frame(progress_frame)  # 按钮容器框架
    button_frame.pack(fill=tk.X, pady=(10, 0))  # 填充水平空间，上方留白 10 px

    '''创建取消按钮'''
    cancel_button = ttk.Button(
        button_frame, 
        text="取消导出",  # 按钮文本
        command=cancel_export,  # 绑定点击事件处理函数
        width=15  # 固定按钮宽度
    )
    cancel_button.pack(pady=5)  # 添加按钮，垂直方向留白 5 px

    '''更新UI并设置窗口焦点'''
    root.update_idletasks()  # 强制刷新UI，确保所有组件正确渲染
    progress_window.grab_set()  # 设置模态窗口，阻止与其他窗口交互

    update_queue = queue.Queue()  # 创建进度更新队列，用于工作线程向主线程传递进度更新

    # 定义函数：UI更新循环
    def update_from_queue():
        if not progress_window.winfo_exists():  # 检查进度窗口是否仍然存在
            return  # 如果窗口已关闭则停止更新
        try:
            while not update_queue.empty():
                current, total, remaining_time, _ = update_queue.get_nowait()  # 从队列获取进度数据(当前进度,总数,剩余时间,错误信息)
                percent = int(current * 100 / total)  # 计算并更新百分比显示
                percent_var.set(f"{percent}%")  # 更新百分比文本
                files_var.set(f"{current} / {total} 文件已处理")  # 更新已处理文件计数
                time_var.set(f"估计剩余时间: {format_time(remaining_time) if remaining_time is not None else '--:--'}")  # 更新剩余时间显示
                progress_var.set(current)  # 更新进度条值
        except queue.Empty:  # 捕获队列为空的异常
            pass  # 忽略空队列异常
        finally:
            if not (cancel_flag.is_set() or progress_var.get() >= len(images)):  # 检查是否应该继续更新(未取消且未完成)
                progress_window.after(100, update_from_queue)  # 100ms后再次调用自身实现持续更新

    # 定义函数：启动导出任务
    def start_export():
        # 定义函数：导出任务包装器
        def export_task_wrapper():
            try:
                do_export_optimized(images, save_path, frame_rate, width, height, update_queue, cancel_flag)  # 调用核心导出函数
            finally:
                if progress_window.winfo_exists():  # 确保完成后关闭进度窗口
                    root.after(100, progress_window.destroy)  # 使用after确保在主线程执行UI操作
        threading.Thread(target=export_task_wrapper, daemon=True).start()  # 创建并启动导出线程(守护线程)
    progress_window.after(100, update_from_queue)  # 启动UI更新循环(100ms 后开始)
    start_export()  # 启动导出任务

# 定义函数：退出程序时的处理函数
def on_quit(icon):
    stop_screenshotting(icon)  # 停止截图功能
    icon.stop()  # 停止托盘图标
    root.quit()  # 退出 Tkinter 主循环

# 定义函数：切换项目
def switch_project(project_name):
    new_project_path = os.path.join(config.base_save_path, project_name)  # 构建新的项目路径
    if not os.path.exists(new_project_path):
        return  # 如果新项目路径不存在，则不进行切换
    
    '''更新当前项目配置'''
    config.project_path = new_project_path
    config.project_name = project_name
    
    '''更新配置文件'''
    if hasattr(config, 'save_config'):
        config.save_config()
    
    messagebox.showinfo("切换成功", f"已切换到项目: {project_name}")  # 显示切换成功消息

# 定义函数：生成项目菜单项
def project_menu_items():
    project_names = []  # 初始化项目名称列表
    if os.path.exists(config.base_save_path):
        '''遍历基础路径下的所有目录'''
        for project_name in os.listdir(config.base_save_path):
            project_names.append(project_name)  # 将目录名称添加到项目名称列表
    # 定义函数：生成单个项目菜单项
    def make_project_item(project_name):
        return item(project_name, lambda: switch_project(project_name), checked=lambda item: config.project_name == project_name)  # 创建项目菜单项，点击时切换项目，选中状态取决于当前项目名称是否匹配
    project_menu_items = [make_project_item(name) for name in project_names]  # 生成项目菜单项列表
    return pystray.Menu(*project_menu_items)  # 定义项目菜单项的函数，返回一个 pystray.Menu 对象

# 定义函数：更新托盘菜单
def update_menu(icon):
    status_text = "运行中" if config.is_running else "已停止"  # 获取当前状态文本
    start_stop_text = "停止截图" if config.is_running else "开始截图"  # 获取开始/停止按钮文本
    start_stop_action = lambda: stop_screenshotting(icon) if config.is_running else start_screenshotting(icon)  # 定义开始/停止按钮的操作

    if not project_menu_items:
        project_menu_items.append(item("(无项目)", None, enabled=False))  # 如果没有项目则添加提示项

    '''创建包含所有项目的主菜单'''
    icon.menu = pystray.Menu(
        item(f"状态: {status_text}", None, enabled=False),
        pystray.Menu.SEPARATOR,
        item(start_stop_text, start_stop_action),
        item("切换项目", project_menu_items()),
        item("清理冗余截图", lambda: clean_nonstandard_frame(config.project_path)),
        item("导出为视频", lambda: run_in_main_thread(export_to_video, icon)),
        item("设置", lambda: open_settings_window(icon)),
        pystray.Menu.SEPARATOR,
        item("退出", lambda: on_quit(icon))
    )

# 定义函数：检查进程是否在运行
def main():
    set_dpi_aware()  # 设置DPI感知
    global root  # 声明全局变量root
    global incompatible_images  # 声明全局变量 incompatible_images
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

'''确保脚本作为主程序运行'''
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
