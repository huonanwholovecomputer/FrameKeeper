import os
import sys
import cv2
import time
import ctypes
import shutil
import pystray
import tempfile
import threading
import subprocess
import numpy as np
import tkinter as tk
import winreg as reg
from pystray import MenuItem as item
from PIL import Image, ImageGrab, ImageDraw, ImageFilter
from tkinter import ttk, filedialog, messagebox, simpledialog
import configparser

class Config:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.interval = 5
        self.save_path = os.path.join(os.path.expanduser("~"), "FrameKeeper_Captures")
        self.format = "JPG"
        self.jpg_quality = 95
        self.is_running = False
        self.auto_start = False
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
            self.interval = self.config.getint('DEFAULT', 'interval', fallback=5)
            self.save_path = self.config.get('DEFAULT', 'save_path', fallback=os.path.join(os.path.expanduser("~"), "FrameKeeper_Captures"))
            self.format = self.config.get('DEFAULT', 'format', fallback="JPG")
            self.jpg_quality = self.config.getint('DEFAULT', 'jpg_quality', fallback=95)
            self.auto_start = self.config.getboolean('DEFAULT', 'auto_start', fallback=False)
        else:
            self.save_config()

    def save_config(self):
        self.config['DEFAULT'] = {
            'interval': self.interval,
            'save_path': self.save_path,
            'format': self.format,
            'jpg_quality': self.jpg_quality,
            'auto_start': self.auto_start
        }
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

def is_pid_running(pid):
    try:
        output = subprocess.check_output(f'tasklist /FI "PID eq {pid}"', shell=True, encoding='oem')
        return str(pid) in output
    except subprocess.CalledProcessError:
        return False

def set_dpi_aware():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except AttributeError:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception as e:
        pass

def take_screenshot():
    if not os.path.exists(config.save_path):
        os.makedirs(config.save_path)
    screenshot = ImageGrab.grab()
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"capture_{timestamp}.{config.format.lower()}"
    filepath = os.path.join(config.save_path, filename)
    if config.format == "JPG":
        screenshot.save(filepath, "JPEG", quality=config.jpg_quality)
    else:
        screenshot.save(filepath, "PNG", compress_level=0)

def screenshot_loop():
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

def stop_screenshotting(icon):
    if config.is_running:
        config.is_running = False
        icon.icon = create_icon("off")
        update_menu(icon)

def get_startup_key():
    return reg.HKEY_CURRENT_USER

def get_startup_path():
    return r"Software\Microsoft\Windows\CurrentVersion\Run"

def set_auto_start():
    try:
        key = reg.OpenKey(get_startup_key(), get_startup_path(), 0, reg.KEY_ALL_ACCESS)
        script_path = os.path.abspath(sys.argv[0])
        reg.SetValueEx(key, "FrameKeeper", 0, reg.REG_SZ, f'"{sys.executable}" "{script_path}"')
        reg.CloseKey(key)
        config.auto_start = True
        config.save_config()
        messagebox.showinfo("成功", "已成功设置开机自启！")
    except Exception as e:
        messagebox.showerror("错误", f"设置开机自启失败: {e}")

def remove_auto_start():
    try:
        key = reg.OpenKey(get_startup_key(), get_startup_path(), 0, reg.KEY_ALL_ACCESS)
        reg.DeleteValue(key, "FrameKeeper")
        reg.CloseKey(key)
        config.auto_start = False
        config.save_config()
        messagebox.showinfo("成功", "已成功取消开机自启！")
    except FileNotFoundError:
        messagebox.showinfo("提示", "程序未被设置为开机自启。")
        config.auto_start = False
        config.save_config()
    except Exception as e:
        messagebox.showerror("错误", f"取消开机自启失败: {e}")

def check_auto_start():
    try:
        key = reg.OpenKey(get_startup_key(), get_startup_path(), 0, reg.KEY_READ)
        reg.QueryValueEx(key, "FrameKeeper")
        reg.CloseKey(key)
        config.auto_start = True
    except FileNotFoundError:
        config.auto_start = False

def get_dpi_scale(root):
    try:
        root.update()
        dpi = root.winfo_fpixels('1i')
        scale = dpi / 96.0
        return scale
    except Exception as e:
        return 1.0

def create_icon(state="off", base_size=64):
    root = tk.Tk()
    scale = get_dpi_scale(root)
    root.destroy()
    size = int(base_size * scale)
    padding = int(4 * scale)
    center = size // 2
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    if state == "on":
        radius = center - padding
        inner_radius = int(radius * 0.5)
        for i in range(radius, radius - int(5*scale), -1):
            alpha = int(200 * (i / radius))
            draw.ellipse(
                [center-i, center-i, center+i, center+i],
                fill=(255, 50, 50, alpha),
                outline=(255, 255, 255, 30)
            )
        draw.ellipse(
            [center-inner_radius, center-inner_radius, 
             center+inner_radius, center+inner_radius],
            fill=(230, 0, 0),
            outline=(255, 255, 255)
        )
        dot_radius = int(inner_radius * 0.3)
        draw.ellipse(
            [center-dot_radius, center-dot_radius, 
             center+dot_radius, center+dot_radius],
            fill=(255, 255, 255),
            outline=(200, 200, 200)
        )
    else:
        radius = center - padding
        border_width = int(2 * scale)
        draw.ellipse(
            [center-radius, center-radius, center+radius, center+radius],
            fill=(100, 100, 100),
            outline=(180, 180, 180),
            width=border_width
        )
        inner_radius = int(radius * 0.7)
        draw.ellipse(
            [center-inner_radius, center-inner_radius, 
             center+inner_radius, center+inner_radius],
            fill=(60, 60, 60),
            outline=(120, 120, 120),
            width=border_width//2
        )
        dot_radius = int(inner_radius * 0.3)
        draw.ellipse(
            [center-dot_radius, center-dot_radius, 
             center+dot_radius, center+dot_radius],
            fill=(150, 0, 0),
            outline=(100, 0, 0)
        )
    if 'radius' not in locals():
        radius = center - padding
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

def on_quit(icon):
    stop_screenshotting(icon)
    icon.stop()
    root.quit()

def open_settings_window(icon):
    settings_window = tk.Toplevel()
    settings_window.title("FrameKeeper 设置")
    settings_window.geometry("400x350")
    settings_window.resizable(False, False)
    main_frame = ttk.Frame(settings_window, padding="10")
    main_frame.pack(fill="both", expand=True)
    ttk.Label(main_frame, text="截图间隔 (秒):").grid(row=0, column=0, sticky="w", pady=5)
    interval_var = tk.IntVar(value=config.interval)
    ttk.Entry(main_frame, textvariable=interval_var).grid(row=0, column=1, sticky="ew")
    ttk.Label(main_frame, text="保存路径:").grid(row=1, column=0, sticky="w", pady=5)
    path_var = tk.StringVar(value=config.save_path)
    path_entry = ttk.Entry(main_frame, textvariable=path_var)
    path_entry.grid(row=1, column=1, sticky="ew")
    def select_path():
        path = filedialog.askdirectory()
        if path:
            path_var.set(path)
    ttk.Button(main_frame, text="浏览...", command=select_path).grid(row=1, column=2, padx=5)
    ttk.Label(main_frame, text="图片格式:").grid(row=2, column=0, sticky="w", pady=5)
    format_var = tk.StringVar(value=config.format)
    format_menu = ttk.Combobox(
        main_frame, textvariable=format_var,
        values=["PNG", "JPG"], state="readonly"
    )
    format_menu.grid(row=2, column=1, sticky="ew")
    jpg_frame = ttk.Frame(main_frame)
    jpg_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=5)
    quality_label_text = ttk.Label(jpg_frame, text="JPG 压缩质量:")
    quality_label_text.pack(side="left")
    quality_var = tk.IntVar(value=config.jpg_quality)
    quality_scale = ttk.Scale(
        jpg_frame, from_=1, to=100, orient="horizontal",
        variable=quality_var
    )
    quality_scale.pack(side="left", expand=True, fill="x", padx=5)
    quality_entry = ttk.Entry(jpg_frame, width=4, justify="center")
    quality_entry.pack(side="left")
    quality_entry.insert(0, str(config.jpg_quality))
    def update_entry_from_scale(val):
        quality_entry.delete(0, tk.END)
        quality_entry.insert(0, str(int(float(val))))
    def update_scale_from_entry(event=None):
        try:
            val = int(quality_entry.get())
            if 1 <= val <= 100:
                quality_var.set(val)
            else:
                quality_entry.delete(0, tk.END)
                quality_entry.insert(0, str(quality_var.get()))
        except ValueError:
            quality_entry.delete(0, tk.END)
            quality_entry.insert(0, str(quality_var.get()))
    quality_scale.config(command=update_entry_from_scale)
    quality_entry.bind("<Return>", update_scale_from_entry)
    quality_entry.bind("<FocusOut>", update_scale_from_entry)
    def toggle_jpg_quality_state(event=None):
        if format_var.get() == "PNG":
            quality_scale.state(["disabled"])
            quality_entry.state(["disabled"])
            quality_label_text.config(foreground="gray")
        else:
            quality_scale.state(["!disabled"])
            quality_entry.state(["!disabled"])
            quality_label_text.config(foreground="")
    format_menu.bind("<<ComboboxSelected>>", toggle_jpg_quality_state)
    toggle_jpg_quality_state()
    auto_start_var = tk.BooleanVar(value=config.auto_start)
    def toggle_auto_start():
        if auto_start_var.get():
            set_auto_start()
        else:
            remove_auto_start()
        check_auto_start()
        auto_start_var.set(config.auto_start)
    ttk.Checkbutton(main_frame, text="开机自启", variable=auto_start_var, command=toggle_auto_start).grid(row=4, column=0, columnspan=2, sticky="w", pady=10)
    def save_settings():
        config.interval = interval_var.get()
        config.save_path = path_var.get()
        config.format = format_var.get()
        config.jpg_quality = quality_var.get()
        config.save_config()
        messagebox.showinfo("成功", "设置已保存！")
        settings_window.destroy()
    ttk.Button(main_frame, text="保存并关闭", command=save_settings).grid(row=5, column=0, columnspan=3, pady=20)
    main_frame.columnconfigure(1, weight=1)

def run_in_main_thread(func, *args):
    root.after(0, func, *args)

def export_to_video(icon):
    # 创建临时窗口用于文件对话框
    temp_window = tk.Toplevel()
    temp_window.withdraw()
    
    # 选择源文件夹
    source_dir = filedialog.askdirectory(
        title="选择包含截图的文件夹",
        initialdir=config.save_path,
        parent=temp_window
    )
    if not source_dir:
        temp_window.destroy()
        return
        
    # 获取图片文件
    images = [img for img in os.listdir(source_dir) 
              if img.lower().endswith((".png", ".jpg", ".jpeg"))]
    if not images:
        messagebox.showwarning("无图片", "所选文件夹中没有找到图片文件。", parent=temp_window)
        temp_window.destroy()
        return
        
    # 按文件名排序
    images.sort()
    
    # 获取保存路径
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
        
    # 获取帧率
    frame_rate = simpledialog.askinteger(
        "帧率", "请输入视频帧率 (FPS):", 
        initialvalue=30, minvalue=1, maxvalue=60, 
        parent=temp_window
    )
    if not frame_rate:
        temp_window.destroy()
        return
        
    # 获取第一帧确定尺寸
    first_image_path = os.path.join(source_dir, images[0])
    try:
        with open(first_image_path, 'rb') as f:
            img_np = np.frombuffer(f.read(), np.uint8)
        frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
    except Exception as e:
        frame = None # 如果读取失败，frame为None

    if frame is None:
        messagebox.showerror("错误", f"无法读取第一帧图片: {first_image_path}", parent=temp_window)
        temp_window.destroy()
        return
        if frame is None:
            messagebox.showerror("错误", f"无法读取第一帧图片: {first_image_path}", parent=temp_window)
            temp_window.destroy()
            return
    
    height, width, _ = frame.shape
    
    # 创建进度窗口
    progress_window = tk.Toplevel(temp_window)
    progress_window.title("正在导出视频...")
    progress_window.geometry("400x180")  # 扩大窗口以容纳更多信息
    progress_window.transient(temp_window)
    progress_window.grab_set()
    progress_window.resizable(False, False)
    progress_window.protocol("WM_DELETE_WINDOW", lambda: None)  # 禁用关闭按钮
    
    # 等待进度窗口渲染并显示
    progress_window.update()

    # 确保窗口可见并在主线程中更新
    progress_window.deiconify()
    progress_window.lift()
    progress_window.attributes('-topmost', True)
    progress_window.update()
    progress_window.attributes('-topmost', False)
    
    progress_frame = ttk.Frame(progress_window, padding=15)
    progress_frame.pack(fill=tk.BOTH, expand=True)
    
    # 顶部标题
    ttk.Label(progress_frame, text="正在导出视频...", font=("Arial", 10, "bold")).pack(anchor="w")
    
    # 分隔线
    ttk.Separator(progress_frame).pack(fill=tk.X, pady=5)
    
    # 进度条
    progress_var = tk.DoubleVar(value=0)
    progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, 
                                  maximum=len(images), length=350, 
                                  mode='determinate')
    progress_bar.pack(fill=tk.X, pady=(0, 10))
    
    # 详细进度信息
    status_frame = ttk.Frame(progress_frame)
    status_frame.pack(fill=tk.X, pady=(0, 15))
    
    left_status = ttk.Frame(status_frame)
    left_status.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    # 百分比和文件状态
    percent_var = tk.StringVar(value="0%")
    ttk.Label(left_status, textvariable=percent_var, font=("Arial", 10)).pack(anchor="w")
    
    files_var = tk.StringVar(value=f"0 / {len(images)} 文件已处理")
    ttk.Label(left_status, textvariable=files_var, font=("Arial", 9)).pack(anchor="w")
    
    # 尺寸和大小信息
    size_info = ttk.Frame(status_frame)
    size_info.pack(side=tk.RIGHT, fill=tk.X)
    
    res_var = tk.StringVar(value=f"{width}x{height}")
    ttk.Label(size_info, textvariable=res_var, font=("Arial", 9)).pack(anchor="e")
    
    size_var = tk.StringVar(value="估计大小: ---")
    ttk.Label(size_info, textvariable=size_var, font=("Arial", 9)).pack(anchor="e")
    
    # 剩余时间
    time_frame = ttk.Frame(progress_frame)
    time_frame.pack(fill=tk.X)
    
    time_var = tk.StringVar(value="估计剩余时间: --:--")
    ttk.Label(time_frame, textvariable=time_var, font=("Arial", 9)).pack(anchor="w")
    
    # 取消按钮
    cancel_flag = threading.Event()
    
    def cancel_export():
        cancel_flag.set()
        progress_window.destroy()
        temp_window.destroy()
        messagebox.showinfo("导出取消", "视频导出已被取消")
    
    ttk.Button(progress_frame, text="取消导出", command=cancel_export, width=15).pack(pady=(10, 0))
    
    # 格式化时间函数
    def format_time(seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    # 进度更新函数
    def update_progress(current, total, remaining_time=None, estimated_size=None):
        if not progress_window.winfo_exists():
            return
        percent = int(current * 100 / total)
        percent_var.set(f"{percent}%")
        files_var.set(f"{current} / {total} 文件已处理")

        if remaining_time is not None:
            time_var.set(f"估计剩余时间: {format_time(remaining_time)}")
        else:
            time_var.set("估计剩余时间: --:--")

        if estimated_size:
            size_var.set(f"估计大小: {estimated_size:.1f}MB")
        else:
            size_var.set("估计大小: 计算中...")

        progress_var.set(current)
        progress_window.update_idletasks()  # 使用 `update_idletasks()` 确保进度条被更新
    
    # 启动导出线程
    def do_export():
        # 更新初始状态
        root.after(0, lambda: update_progress(0, len(images)))
        
        try:
            # 使用临时文件防止导出中断时留下部分文件
            temp_dir = tempfile.gettempdir()
            temp_file = f"temp_framekeeper_{os.getpid()}.mp4"
            temp_output = os.path.join(temp_dir, temp_file)
            
            # 选择FourCC编码器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 优先使用mp4v保证兼容性
            
            # 初始化VideoWriter
            video = cv2.VideoWriter(temp_output, fourcc, frame_rate, (width, height))
            
            if not video.isOpened():
                root.after(0, lambda: messagebox.showerror(
                    "错误", "无法初始化视频编码器", parent=progress_window
                ))
                return
            
            # 设置比特率控制文件大小
            try:
                video.set(cv2.VIDEOWRITER_PROP_QUALITY, 90)  # 90%质量
            except:
                pass  # 忽略无法设置的情况
            
            # 获取第一帧大小用于估算
            first_frame_size = os.path.getsize(first_image_path)
            estimated_size = len(images) * (first_frame_size / (frame_rate * 1.5)) / (1024 * 1024)
            
            start_time = time.time()
            processed_images = 0
            
            # 主导出循环
            for i, image in enumerate(images):
                if cancel_flag.is_set():
                    break
                
                image_path = os.path.join(source_dir, image)
                try:
                    with open(image_path, 'rb') as f:
                        img_np = np.frombuffer(f.read(), np.uint8)
                    frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
                except Exception:
                    frame = None # 读取或解码失败

                if frame is None:
                    print(f"警告: 跳过无法读取的图片 {image_path}") # 可以在控制台输出提示
                    continue # 跳过无法读取的图片

                video.write(frame)
                
                if frame is None:
                    continue  # 跳过无法读取的图片
                
                video.write(frame)
                processed_images += 1
                
                # 计算进度信息
                current_time = time.time()
                elapsed = current_time - start_time
                
                if elapsed > 1:  # 运行1秒后开始估算
                    # 估计剩余时间
                    time_per_frame = elapsed / (i + 1)
                    remaining = time_per_frame * (len(images) - i - 1)
                    
                    # 更新进度UI
                    root.after(0, lambda: update_progress(
                        i + 1,
                        len(images),
                        remaining,
                        estimated_size
                    ))
                
                # 每10帧更新一次UI
                if i % 10 == 0:
                    progress_window.update()
            
            # 完成处理
            video.release()
            
            if cancel_flag.is_set():
                try:
                    os.remove(temp_output)
                except:
                    pass
                return
            
            # 移动临时文件到目标位置
            shutil.move(temp_output, save_path)
            
            # 获取最终文件信息
            final_size = os.path.getsize(save_path) / (1024 * 1024)  # MB
            duration = len(images) / frame_rate
            
            # 显示成功信息
            root.after(0, lambda: messagebox.showinfo(
                "导出成功",
                f"视频已成功导出:\n"
                f"路径: {save_path}\n"
                f"尺寸: {width}x{height}\n"
                f"时长: {duration:.1f}秒\n"
                f"大小: {final_size:.1f}MB",
                parent=temp_window
            ))
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            root.after(0, lambda: messagebox.showerror(
                "导出错误",
                f"导出过程中发生错误:\n{str(e)}",
                parent=progress_window
            ))
            
        finally:
            # 清理临时文件（如果存在）
            try:
                if os.path.exists(temp_output):
                    os.remove(temp_output)
            except:
                pass
            
            # 关闭窗口
            root.after(0, progress_window.destroy)
            root.after(0, temp_window.destroy)
    
    # 在后台线程启动导出
    # ... 此前是创建 progress_window 和其内部控件的代码 ...

    # ------------------- 新增代码块 [核心修复] -------------------
    # 1. 强制Tkinter处理所有待处理的事件，特别是窗口的布局和几何计算
    progress_window.update_idletasks() 

    # 2. 强制窗口重绘自身，确保它被显示出来
    progress_window.update() 

    # 3. (可选但推荐) 将窗口的父级从临时的temp_window改为root，或直接设为None
    #    这可以避免父窗口（被隐藏）对子窗口状态的潜在影响
    #    修改 progress_window 的创建代码:
    #    旧: progress_window = tk.Toplevel(temp_window)
    progress_window = tk.Toplevel(root)

    # 4. (可选但推荐) 确保进度窗口获得焦点
    progress_window.grab_set()
    # -----------------------------------------------------------

    # 启动导出线程
def start_export_thread():
    threading.Thread(target=do_export, daemon=True).start()

def set_interval(icon, interval):
    def inner():
        config.interval = interval
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
    set_dpi_aware()
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
            with open(lock_file_path, "r") as f:
                existing_pid = f.read().strip()
            if existing_pid and is_pid_running(existing_pid):
                ctypes.windll.user32.MessageBoxW(0, "FrameKeeper 已在运行中。", "错误", 0x10)
                sys.exit(1)
            else:
                os.remove(lock_file_path)
        with open(lock_file_path, "w") as f:
            f.write(str(os.getpid()))
        config_dir = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "FrameKeeper")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        config_file = os.path.join(config_dir, "config.ini")
        config = Config(config_file)
        main()
    finally:
        if os.path.exists(lock_file_path):
            os.remove(lock_file_path)