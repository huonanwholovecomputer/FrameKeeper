import os
import sys
import cv2
import time
import ctypes
import pystray
import threading
import subprocess
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
    temp_window = tk.Toplevel()
    temp_window.withdraw()
    source_dir = filedialog.askdirectory(
        title="选择包含截图的文件夹",
        initialdir=config.save_path,
        parent=temp_window
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
