import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import cv2
import numpy as np
import threading
import queue
import time
import tempfile
import shutil
import traceback
import sys
from PIL import Image, ImageTk

# 模拟主窗口和基本保存路径
root = tk.Tk()
root.withdraw()  # 隐藏主窗口，因为我们只需要对话框
base_save_path = os.path.join(os.path.expanduser("~"), "Desktop")  # 默认保存路径设为桌面

# 图标处理函数
def set_icon(window, icon_path=None):
    try:
        if icon_path and os.path.exists(icon_path):
            img = Image.open(icon_path)
            photo = ImageTk.PhotoImage(img)
            window.tk.call('wm', 'iconphoto', window._w, photo)
        else:
            # 创建默认图标（16x16 和 32x32）
            default_icon = """
            # 这里可以添加你的默认图标数据，或者保持为空
            """
            if default_icon.strip():
                import base64
                import zlib
                icon_data = zlib.decompress(base64.b64decode(default_icon))
                window.iconbitmap(bitmap=icon_data)
    except Exception as e:
        print(f"设置图标失败: {e}", file=sys.stderr)

''' export_to_video 函数，导出为视频'''
def export_to_video(icon=None):
    dialog_parent = tk.Toplevel(root)  # 创建一个新的顶级窗口作为对话框的父窗口
    dialog_parent.withdraw()  # 隐藏窗口，避免在askdirectory前显示空白窗口

    source_dir = filedialog.askdirectory(title="选择包含截图的文件夹", initialdir=base_save_path, parent=dialog_parent)  # 让用户选择包含截图的文件夹，初始目录为配置中的基本保存路径
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
    save_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 文件", "*.mp4")], title="保存视频文件", initialdir=base_save_path, parent=dialog_parent)  # 让用户选择视频保存路径，默认扩展名为.mp4

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

# 测试调用
if __name__ == "__main__":
    
    # 调用函数进行测试
    export_to_video()
    
    # 启动事件循环
    root.mainloop()
    
    # 清理测试文件（可选）
    shutil.rmtree(test_dir, ignore_errors=True)
