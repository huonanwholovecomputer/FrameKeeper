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
import psutil  # 导入psutil库用于内存监控

# 模拟主窗口和基本保存路径
root = tk.Tk()
root.withdraw()  # 隐藏主窗口，因为我们只需要对话框
base_save_path = os.path.join(os.path.expanduser("~"), "Desktop")  # 默认保存路径设为桌面

# --- GUI 和辅助函数 (未做核心修改) ---
def set_icon(window, icon_path=None):
    try:
        if icon_path and os.path.exists(icon_path):
            img = Image.open(icon_path)
            photo = ImageTk.PhotoImage(img)
            window.tk.call('wm', 'iconphoto', window._w, photo)
        else:
            default_icon = ""
            if default_icon.strip():
                import base64
                import zlib
                icon_data = zlib.decompress(base64.b64decode(default_icon))
                window.iconbitmap(bitmap=icon_data)
    except Exception as e:
        print(f"设置图标失败: {e}", file=sys.stderr)

def format_time(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

# --- 优化后的核心逻辑 ---

# 全局变量，用于在多线程中传递异常
exception_queue = queue.Queue()

def read_and_decode_worker(path_queue, frame_queue, cancel_flag, memory_threshold=95):
    """
    优化后的生产者线程：更智能的内存管理和队列控制
    """
    consecutive_high_memory = 0
    
    while True:
        if cancel_flag.is_set():
            break

        # 更智能的内存检查：连续3次检测到高内存才暂停
        mem_percent = psutil.virtual_memory().percent
        if mem_percent > memory_threshold:
            consecutive_high_memory += 1
            if consecutive_high_memory >= 3:
                # 逐渐增加等待时间：100ms, 200ms, 400ms...
                sleep_time = min(0.1 * (2 ** (consecutive_high_memory - 3)), 2.0)
                time.sleep(sleep_time)
                continue
        else:
            consecutive_high_memory = 0

        # 动态调整队列获取速度
        try:
            # 如果队列较满，降低处理速度
            if frame_queue.qsize() > frame_queue.maxsize * 0.8:
                time.sleep(0.05)
                
            image_path = path_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        if image_path is None:
            break
            
        try:
            # 使用更高效的图片读取方式
            frame = cv2.imread(image_path, cv2.IMREAD_COLOR)
            if frame is None:
                raise IOError(f"无法读取图片: {image_path}")
                
            # 非阻塞方式放入队列
            while not cancel_flag.is_set():
                try:
                    if frame_queue.full():
                        # 队列满时短暂等待而不是阻塞
                        time.sleep(0.01)
                        continue
                        
                    frame_queue.put(frame, block=False)
                    break
                except queue.Full:
                    time.sleep(0.01)
        except Exception as e:
            print(f"警告：无法处理文件 {os.path.basename(image_path)}: {e}")
        finally:
            path_queue.task_done()
    
    frame_queue.put(None)

def encode_worker(frame_queue, video_writer, total_frames, update_q, cancel_flag, start_time, num_producers):
    """
    优化后的消费者线程：更好的队列处理和进度更新
    """
    producers_finished = 0
    processed_count = 0
    last_update_time = time.time()
    
    try:
        while producers_finished < num_producers and not cancel_flag.is_set():
            try:
                # 增加超时时间，减少空转
                frame = frame_queue.get(timeout=2)
                
                if frame is None:
                    producers_finished += 1
                    continue
                    
                video_writer.write(frame)
                processed_count += 1
                
                # 优化进度更新：每处理1%或至少0.5秒更新一次
                current_time = time.time()
                if (processed_count % max(1, total_frames // 100) == 0 or 
                    current_time - last_update_time > 0.5):
                    
                    elapsed = current_time - start_time
                    remaining = (elapsed / processed_count) * (total_frames - processed_count) if processed_count > 0 else 0
                    update_q.put((processed_count, total_frames, remaining, None))
                    last_update_time = current_time
                    
            except queue.Empty:
                # 队列空时短暂等待
                time.sleep(0.05)
    except Exception as e:
        exception_queue.put(e)

def do_export_optimized(images, save_path, frame_rate, width, height, update_q, cancel_flag):
    """
    重构后的导出函数，优化线程和队列管理
    """
    temp_output = None
    video = None
    threads = []
    
    try:
        # 1. 动态调整线程数和队列大小
        num_cores = os.cpu_count() or 4
        num_reader_threads = max(1, min(num_cores - 1, 4))  # 限制最大线程数
        
        # 基于图片数量动态设置队列大小
        if len(images) < 100:
            max_queue_size = 10
        elif len(images) < 500:
            max_queue_size = 20
        else:
            max_queue_size = 30
            
        print(f"系统CPU核心数: {num_cores}, 使用 {num_reader_threads} 解码线程")
        print(f"帧队列大小: {max_queue_size}")

        # 2. 创建队列
        path_queue = queue.Queue()
        frame_queue = queue.Queue(maxsize=max_queue_size)

        for img_path in images:
            path_queue.put(img_path)

        # 3. 初始化视频编码器
        temp_output = os.path.join(tempfile.gettempdir(), f"temp_export_{os.getpid()}.mp4")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        video = cv2.VideoWriter(temp_output, fourcc, frame_rate, (width, height))
        
        if not video.isOpened():
            raise IOError("无法初始化视频编码器。")

        # 4. 创建并启动线程
        start_time = time.time()
        threads = []

        # 消费者线程
        encoder_thread = threading.Thread(
            target=encode_worker,
            args=(frame_queue, video, len(images), update_q, cancel_flag, start_time, num_reader_threads),
            daemon=True
        )
        encoder_thread.start()
        threads.append(encoder_thread)

        # 生产者线程
        for _ in range(num_reader_threads):
            reader_thread = threading.Thread(
                target=read_and_decode_worker,
                args=(path_queue, frame_queue, cancel_flag, 95),  # 使用95%的内存阈值
                daemon=True
            )
            reader_thread.start()
            threads.append(reader_thread)

        # 5. 等待任务完成
        path_queue.join()
        
        # 发送结束信号
        for _ in range(num_reader_threads):
            path_queue.put(None)
            
        # 等待线程结束
        for t in threads:
            t.join(timeout=5.0)
            
        if not exception_queue.empty():
            raise exception_queue.get()

        if cancel_flag.is_set():
            root.after(0, lambda: messagebox.showinfo("导出取消", "视频导出已被取消。", parent=root))
            return

        # 6. 完成导出
        video.release()
        shutil.move(temp_output, save_path)
        
        final_size = os.path.getsize(save_path) / (1024 * 1024)
        duration = len(images) / frame_rate
        root.after(0, lambda: messagebox.showinfo("视频导出成功",
            f"视频已成功导出:\n视频路径: {save_path}\n视频尺寸: {width}x{height}\n"
            f"视频时长: {duration:.1f}秒\n视频大小: {final_size:.1f}MB",
            parent=root))

    except Exception as e:
        # 错误处理保持不变
        traceback.print_exc()
        cancel_flag.set()
        root.after(0, lambda: messagebox.showerror("导出错误", f"导出过程中发生错误:\n{str(e)}", parent=root))
    finally:
        if video is not None:
            video.release()
        if temp_output and os.path.exists(temp_output):
            try:
                os.remove(temp_output)
            except OSError:
                pass

def export_to_video(icon=None):
    dialog_parent = tk.Toplevel(root)
    dialog_parent.withdraw()

    source_dir = filedialog.askdirectory(title="选择包含截图的文件夹", initialdir=base_save_path, parent=dialog_parent)
    if not source_dir:
        dialog_parent.destroy()
        return

    images = []
    for root_dir, dirs, files in os.walk(source_dir):
        if root_dir == source_dir:
            continue
        for file in files:
            if file.lower().endswith((".png", ".jpg", ".jpeg")):
                images.append(os.path.join(root_dir, file))

    if not images:
        messagebox.showwarning("无图片", "所选文件夹的子文件夹中没有找到图片文件", parent=dialog_parent)
        dialog_parent.destroy()
        return

    images.sort(key=lambda x: os.path.basename(x))
    save_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 文件", "*.mp4")], title="保存视频文件", initialdir=base_save_path, parent=dialog_parent)
    if not save_path:
        dialog_parent.destroy()
        return

    frame_rate = simpledialog.askinteger("帧率", "请输入视频帧率 (FPS):", initialvalue=30, minvalue=1, maxvalue=60, parent=dialog_parent)
    dialog_parent.destroy()
    if not frame_rate:
        return

    try:
        first_image = cv2.imread(images[0])
        if first_image is None:
            raise IOError(f"无法读取第一帧图片: {images[0]}")
        height, width, _ = first_image.shape
    except Exception as e:
        messagebox.showerror("错误", f"读取首帧图片失败: {e}", parent=root)
        return

    # --- 进度窗口UI (未做核心修改) ---
    progress_window = tk.Toplevel(root)
    progress_window.title("正在导出视频...")
    progress_window.geometry("400x230")
    progress_window.resizable(False, False)
    progress_window.protocol("WM_DELETE_WINDOW", lambda: None)
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
    time_frame = ttk.Frame(progress_frame)
    time_frame.pack(fill=tk.X)
    time_var = tk.StringVar(value="估计剩余时间: --:--")
    ttk.Label(time_frame, textvariable=time_var, font=("Arial", 9)).pack(anchor="w")

    cancel_flag = threading.Event()

    def cancel_export():
        if messagebox.askyesno("确认取消", "你确定要取消视频导出吗？", parent=progress_window):
            cancel_flag.set()

    button_frame = ttk.Frame(progress_frame)
    button_frame.pack(fill=tk.X, pady=(10, 0))
    cancel_button = ttk.Button(button_frame, text="取消导出", command=cancel_export, width=15)
    cancel_button.pack(pady=5)

    root.update_idletasks()
    progress_window.grab_set()
    update_queue = queue.Queue()

    # --- UI 更新循环 (未做核心修改) ---
    def update_from_queue():
        if not progress_window.winfo_exists():
            return
        try:
            while not update_queue.empty():
                current, total, remaining_time, _ = update_queue.get_nowait()
                percent = int(current * 100 / total)
                percent_var.set(f"{percent}%")
                files_var.set(f"{current} / {total} 文件已处理")
                time_var.set(f"估计剩余时间: {format_time(remaining_time) if remaining_time is not None else '--:--'}")
                progress_var.set(current)
        except queue.Empty:
            pass
        finally:
            if not (cancel_flag.is_set() or progress_var.get() >= len(images)):
                progress_window.after(100, update_from_queue)

    def start_export():
        # 创建一个包装器函数，以便在 finally 块中销毁窗口
        def export_task_wrapper():
            try:
                do_export_optimized(images, save_path, frame_rate, width, height, update_queue, cancel_flag)
            finally:
                if progress_window.winfo_exists():
                    # 确保在所有操作完成后（包括显示消息框）再关闭进度窗口
                    root.after(100, progress_window.destroy)
        
        # 启动核心导出任务
        threading.Thread(target=export_task_wrapper, daemon=True).start()

    progress_window.after(100, update_from_queue)
    start_export()

if __name__ == "__main__":
    try:
        export_to_video()
        root.mainloop()
    except Exception as e:
        # 兜底的异常捕获
        messagebox.showerror("致命错误", f"程序遇到无法恢复的错误:\n{e}")
        traceback.print_exc()
