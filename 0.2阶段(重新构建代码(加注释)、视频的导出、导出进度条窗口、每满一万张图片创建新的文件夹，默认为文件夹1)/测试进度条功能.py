import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import random
import queue

def start_export():
    # 创建主窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 设置进度窗口 - 增加高度到200px
    progress_window = tk.Toplevel(root)
    progress_window.title("正在导出视频...")
    progress_window.geometry("400x230")  # 增加高度到200px
    progress_window.resizable(False, False)
    progress_window.protocol("WM_DELETE_WINDOW", lambda: None)  # 禁止关闭窗口
    
    # 进度窗口内容
    progress_frame = ttk.Frame(progress_window, padding=15)
    progress_frame.pack(fill=tk.BOTH, expand=True)
    
    # 标题标签
    ttk.Label(progress_frame, text="正在导出视频...", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
    
    # 分隔线
    ttk.Separator(progress_frame).pack(fill=tk.X, pady=5)
    
    # 进度条变量
    total_images = 100
    progress_var = tk.DoubleVar(value=0)
    
    # 进度条
    progress_bar = ttk.Progressbar(
        progress_frame, 
        variable=progress_var, 
        maximum=total_images,
        length=350,
        mode="determinate"
    )
    progress_bar.pack(fill=tk.X, pady=(0, 10))
    
    # 状态信息
    status_frame = ttk.Frame(progress_frame)
    status_frame.pack(fill=tk.X, pady=(0, 10))  # 减少下方间距
    
    # 左侧状态
    left_status = ttk.Frame(status_frame)
    left_status.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    percent_var = tk.StringVar(value="0%")
    ttk.Label(left_status, textvariable=percent_var, font=("Arial", 10)).pack(anchor="w")
    
    files_var = tk.StringVar(value=f"0 / {total_images} 文件已处理")
    ttk.Label(left_status, textvariable=files_var, font=("Arial", 9)).pack(anchor="w", pady=(2, 0))  # 减少间距
    
    # 右侧状态
    size_info = ttk.Frame(status_frame)
    size_info.pack(side=tk.RIGHT, fill=tk.X)
    
    res_var = tk.StringVar(value="1920x1080")
    ttk.Label(size_info, textvariable=res_var, font=("Arial", 9)).pack(anchor="e")
    
    size_var = tk.StringVar(value="估计大小: ---")
    ttk.Label(size_info, textvariable=size_var, font=("Arial", 9)).pack(anchor="e", pady=(2, 0))  # 减少间距
    
    # 时间信息
    time_frame = ttk.Frame(progress_frame)
    time_frame.pack(fill=tk.X, pady=(0, 10))  # 减少下方间距
    
    time_var = tk.StringVar(value="估计剩余时间: --:--")
    ttk.Label(time_frame, textvariable=time_var, font=("Arial", 9)).pack(anchor="w")
    
    # 取消标志
    cancel_flag = threading.Event()
    
    # 取消导出函数
    def cancel_export():
        cancel_flag.set()
        progress_window.destroy()
        root.destroy()
        messagebox.showinfo("导出取消", "视频导出已被取消。")
    
    # 创建按钮容器框架 - 确保按钮有足够空间
    button_frame = ttk.Frame(progress_frame)
    button_frame.pack(fill=tk.X, pady=(10, 0))  # 上方留出空间
    
    # 将按钮放在容器中并居中
    cancel_button = ttk.Button(button_frame, text="取消导出", command=cancel_export, width=15)
    cancel_button.pack(pady=5)  # 在按钮周围添加内边距
    
    # 格式化时间函数
    def format_time(seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    # 创建队列用于线程间通信
    update_queue = queue.Queue()
    
    # 更新进度函数 - 从队列获取更新
    def update_from_queue():
        while not update_queue.empty():
            current, total, remaining_time, estimated_size = update_queue.get()
            percent = int(current * 100 / total)
            percent_var.set(f"{percent}%")
            files_var.set(f"{current} / {total} 文件已处理")
            time_var.set(f"估计剩余时间: {format_time(remaining_time) if remaining_time is not None else '--:--'}")
            size_var.set(f"估计大小: {estimated_size:.1f}MB" if estimated_size else "估计大小: ---")
            progress_var.set(current)
        
        # 继续检查队列
        if not cancel_flag.is_set():
            progress_window.after(100, update_from_queue)
    
    # 启动队列检查
    progress_window.after(100, update_from_queue)
    
    # 模拟导出任务
    def export_task():
        start_time = time.time()
        total = total_images
        
        for i in range(1, total + 1):
            if cancel_flag.is_set():
                return
                
            # 模拟处理时间 (0.05-0.2秒)
            time.sleep(random.uniform(0.05, 0.2))
            
            # 计算剩余时间
            elapsed = time.time() - start_time
            remaining = (elapsed / i) * (total - i) if i > 0 else 0
            
            # 模拟估计大小 (10-20MB)
            estimated_size = random.uniform(10, 20)
            
            # 将更新请求放入队列
            update_queue.put((i, total, remaining, estimated_size))
        
        # 导出完成
        if not cancel_flag.is_set():
            # 在主线程中显示完成消息
            progress_window.after(0, lambda: messagebox.showinfo("导出完成", "视频导出成功！"))
            progress_window.after(0, progress_window.destroy)
            progress_window.after(0, root.destroy)
    
    # 启动导出线程
    threading.Thread(target=export_task, daemon=True).start()
    
    # 启动主循环
    progress_window.mainloop()

# 启动测试
if __name__ == "__main__":
    start_export()
