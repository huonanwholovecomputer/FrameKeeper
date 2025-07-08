import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
import os
import cv2
import threading
import queue
import time
import psutil
import tempfile
import shutil
import subprocess

# 定义函数：创建主Tkinter窗口
# 假设 root 窗口在程序的其他地方已经创建和配置
# root = tk.Tk()
# root.withdraw() # 通常主窗口会隐藏

def run_in_main_thread(func, *args):
    # 假设 root 是一个全局可访问的 Tkinter 根窗口实例
    root.after(0, func, *args)  # 在主线程中执行函数

# 定义函数：剩余时间估计
def format_time(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

# 全局变量，用于在多线程中传递异常
exception_queue = queue.Queue()

# --- 代码修改开始 ---

def create_ffmpeg_writer(output_path, width, height, fps, bitrate):
    """
    创建一个 FFmpeg 子进程用于视频编码。
    这将取代原来的 cv2.VideoWriter，以实现更精细的参数控制。
    """
    # 确保 ffmpeg 可执行文件存在
    if not shutil.which('ffmpeg'):
        raise FileNotFoundError("错误：找不到 FFmpeg。请确保 FFmpeg 已安装并已添加到系统 PATH 环境变量中。")

    # 构建 FFmpeg 命令
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
    #          'veryfast' 是一个很好的平衡点
    command = [
        'ffmpeg',
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
    
    print(f"执行 FFmpeg 命令: {' '.join(command)}")

    # 启动子进程
    # stdin=subprocess.PIPE: 允许我们向 FFmpeg 写入数据
    # stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL: 隐藏 FFmpeg 的控制台输出，避免刷屏
    # 如果需要调试 FFmpeg，可以移除 stdout 和 stderr 参数
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return process

# --- 原来的 create_video_writer 函数已被移除 ---

def calculate_bitrate(width, height, fps):
    """根据分辨率动态计算推荐的比特率"""
    # 确保有效的分辨率
    if width <= 0 or height <= 0:
        return 2_000_000  # 默认比特率
    
    # 计算像素总数
    pixels = width * height
    
    # 根据分辨率范围设置比特率
    if pixels <= 640 * 480:      # SD (480p)
        base_bitrate = 1000_000 # 提高基础码率以获得更好质量
    elif pixels <= 1280 * 720:     # HD (720p)
        base_bitrate = 2000_000
    elif pixels <= 1920 * 1080:    # Full HD (1080p)
        base_bitrate = 4000_000
    elif pixels <= 3840 * 2160:    # 4K
        base_bitrate = 8000_000
    else:                          # 更高分辨率
        base_bitrate = 10_000_000
    
    # 根据帧率调整比特率
    fps_factor = max(0.5, min(2.0, fps / 30.0))
    adjusted_bitrate = int(base_bitrate * fps_factor)
    
    # 确保最小比特率
    min_bitrate = 500_000
    return max(adjusted_bitrate, min_bitrate)

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
            frame = cv2.imread(image_path, cv2.IMREAD_COLOR)  # 读取彩色图像
            if frame is None:  # 如果图像读取失败
                raise IOError(f"无法读取图片: {image_path}")  # 抛出IO错误
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

# 定义函数：消费者线程（已修改）
def encode_worker(frame_queue, ffmpeg_stdin, total_frames, update_q, cancel_flag, start_time, num_producers):
    """
    这个工作线程现在将帧写入 FFmpeg 进程的 stdin。
    """
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
                
                # --- 修改核心 ---
                # 将 NumPy 数组帧转换为原始字节并写入 FFmpeg 的 stdin
                ffmpeg_stdin.write(frame.tobytes())
                # --- 修改核心 ---

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

# 定义函数：导出（已修改）
def do_export_optimized(images, save_path, frame_rate, width, height, update_q, cancel_flag):
    temp_output = None  # 临时输出文件路径
    ffmpeg_process = None # FFmpeg 进程对象
    threads = []  # 线程列表
    try:
        '''动态调整线程数和队列大小'''
        num_cores = os.cpu_count() or 4  # 获取CPU核心数，默认为4
        num_reader_threads = max(1, min(num_cores - 1, 4))  # 限制最大线程数

        '''基于图片数量动态设置队列大小'''
        if len(images) < 100:
            max_queue_size = 10
        elif len(images) < 500:
            max_queue_size = 20
        else:
            max_queue_size = 30

        '''创建队列'''
        path_queue = queue.Queue()
        frame_queue = queue.Queue(maxsize=max_queue_size)
        for img_path in images:
            path_queue.put(img_path)

        '''确保临时目录存在'''
        temp_dir = tempfile.gettempdir()
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        '''创建唯一的临时文件名'''
        temp_output = os.path.join(temp_dir, f"temp_export_{os.getpid()}_{time.time()}.mp4")
        print(f"临时文件路径: {temp_output}")

        '''初始化 FFmpeg 编码器'''
        bitrate = calculate_bitrate(width, height, frame_rate)
        ffmpeg_process = create_ffmpeg_writer(temp_output, width, height, frame_rate, bitrate)
        
        '''创建并启动线程'''
        start_time = time.time()
        threads = []

        '''消费者线程'''
        # 将 ffmpeg_process.stdin 传递给编码器
        encoder_thread = threading.Thread(
            target=encode_worker,
            args=(frame_queue, ffmpeg_process.stdin, len(images), update_q, cancel_flag, start_time, num_reader_threads),
            daemon=True
        )
        encoder_thread.start()
        threads.append(encoder_thread)

        '''生产者线程'''
        for _ in range(num_reader_threads):
            reader_thread = threading.Thread(target=read_and_decode_worker, args=(path_queue, frame_queue, cancel_flag, 95), daemon=True)
            reader_thread.start()
            threads.append(reader_thread)

        path_queue.join()
        
        '''发送结束信号'''
        for _ in range(num_reader_threads):
            path_queue.put(None)
            
        '''等待线程结束'''
        for t in threads:
            t.join(timeout=10.0) # 增加超时时间以防万一
        if not exception_queue.empty():
            raise exception_queue.get()
        if cancel_flag.is_set():
            root.after(0, lambda: messagebox.showinfo("导出取消", "视频导出已被取消。", parent=root))
            return

        '''完成导出'''
        # 关闭 stdin，等待 FFmpeg 完成编码
        ffmpeg_process.stdin.close()
        ffmpeg_process.wait()

        # 检查 FFmpeg 是否成功执行
        if ffmpeg_process.returncode != 0:
            raise RuntimeError(f"FFmpeg 编码失败，返回码: {ffmpeg_process.returncode}。请检查控制台输出。")

        shutil.move(temp_output, save_path)
        final_size = os.path.getsize(save_path) / (1024 * 1024)
        duration = len(images) / frame_rate
        root.after(0, lambda: messagebox.showinfo("视频导出成功",
            f"视频已成功导出:\n视频路径: {save_path}\n视频尺寸: {width}x{height}\n"
            f"视频时长: {duration:.1f}秒\n视频大小: {final_size:.1f}MB",
            parent=root))

    except Exception as e:
        cancel_flag.set()
        # 在主线程中显示错误信息
        run_in_main_thread(messagebox.showerror, "导出错误", f"发生严重错误: {e}")
        print(e)
    finally:
        # 清理资源
        if ffmpeg_process:
            # 如果进程仍在运行，尝试终止它
            if ffmpeg_process.poll() is None:
                ffmpeg_process.terminate()
                ffmpeg_process.wait()
        if temp_output and os.path.exists(temp_output):
            try:
                os.remove(temp_output)
            except OSError:
                pass

# --- 代码修改结束 ---

# 定义函数：导出为视频
def export_to_video(icon=None):
    # 检查 FFmpeg 是否可用
    if not shutil.which('ffmpeg'):
        messagebox.showerror("依赖缺失", "未找到 FFmpeg。请先安装 FFmpeg 并将其添加到系统 PATH 中。")
        return

    dialog_parent = tk.Toplevel(root)
    dialog_parent.withdraw()

    source_dir = filedialog.askdirectory(
        title="选择包含截图的文件夹",
        # initialdir=config.base_save_path, # 假设 config 存在
        parent=dialog_parent
    )
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

    save_path = filedialog.asksaveasfilename(
        defaultextension=".mp4",
        filetypes=[("MP4 文件", "*.mp4")],
        title="保存视频文件",
        # initialdir=config.base_save_path, # 假设 config 存在
        parent=dialog_parent
    )
    if not save_path:
        dialog_parent.destroy()
        return

    frame_rate = simpledialog.askinteger(
        "帧率",
        "请输入视频帧率 (FPS):",
        initialvalue=30,
        minvalue=1,
        maxvalue=60,
        parent=dialog_parent
    )
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
    progress_bar = ttk.Progressbar(
        progress_frame, 
        variable=progress_var,
        maximum=len(images),
        length=350,
        mode="determinate"
    )
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
        if messagebox.askyesno(
            "确认取消", 
            "你确定要取消视频导出吗？", 
            parent=progress_window
        ):
            cancel_flag.set()
    
    button_frame = ttk.Frame(progress_frame)
    button_frame.pack(fill=tk.X, pady=(10, 0))
    
    cancel_button = ttk.Button(
        button_frame, 
        text="取消导出",
        command=cancel_export,
        width=15
    )
    cancel_button.pack(pady=5)

    root.update_idletasks()
    progress_window.grab_set()

    update_queue = queue.Queue()

    def update_from_queue():
        if not progress_window.winfo_exists():
            return
        
        try:
            while not update_queue.empty():
                current, total, remaining_time, _ = update_queue.get_nowait()
                
                percent = int(current * 100 / total)
                percent_var.set(f"{percent}%")
                
                files_var.set(f"{current} / {total} 文件已处理")
                
                time_var.set(
                    f"估计剩余时间: {format_time(remaining_time) if remaining_time is not None else '--:--'}"
                )
                
                progress_var.set(current)
                
        except queue.Empty:
            pass
        finally:
            if not (cancel_flag.is_set() or progress_var.get() >= len(images)):
                progress_window.after(100, update_from_queue)

    def start_export():
        def export_task_wrapper():
            try:
                do_export_optimized(images, save_path, frame_rate, width, height, update_queue, cancel_flag)
            finally:
                if progress_window.winfo_exists():
                    root.after(100, progress_window.destroy)
        threading.Thread(target=export_task_wrapper, daemon=True).start()
    progress_window.after(100, update_from_queue)
    start_export()

# --- 用于测试的桩代码 ---
if __name__ == '__main__':
    root = tk.Tk()
    root.title("视频导出器")

    # 创建一个按钮来启动导出过程
    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    export_button = ttk.Button(main_frame, text="导出为视频...", command=export_to_video)
    export_button.pack(pady=20)

    # 模拟一个 config 对象
    class Config:
        base_save_path = os.path.expanduser("~")
    
    config = Config()

    # 确保在关闭主窗口时程序能正确退出
    def on_closing():
        if messagebox.askokcancel("退出", "你确定要退出吗?"):
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
