import os
import re
from datetime import datetime

def clean_nonstandard_frame(root_directory):
    """
    删除指定目录及其子目录中间隔时间小于10秒的冗余图片文件
    :param root_directory: 目标根目录路径
    """
    # 定义文件格式的正则表达式
    pattern = re.compile(r'^capture_(\d{8}_\d{6})\.(jpg|png)$')
    
    total_deleted = 0
    
    # 遍历根目录及其所有子目录
    for dirpath, dirnames, filenames in os.walk(root_directory):
        # 存储当前目录提取到的文件时间和文件名
        file_times = []
        
        # 收集当前目录下所有符合条件的文件
        for filename in filenames:
            match = pattern.match(filename)
            if match:
                time_str = match.group(1)
                try:
                    # 转换时间为datetime对象
                    time = datetime.strptime(time_str, "%Y%m%d_%H%M%S")
                    # 存储(时间, 文件名)元组
                    file_times.append((time, filename))
                except ValueError:
                    # 时间格式无效的文件跳过
                    continue
        
        # 如果没有符合条件的文件，跳过当前目录
        if not file_times:
            continue
        
        # 按时间排序
        file_times.sort(key=lambda x: x[0])
        
        # 计算需要删除的文件
        delete_list = []
        last_kept_time = file_times[0][0]  # 保留的第一个文件时间
        
        # 遍历所有文件（从第二个开始）
        for time, filename in file_times[1:]:
            # 计算与上一个保留文件的时间差（秒）
            delta = (time - last_kept_time).total_seconds()
            
            if delta < 10:
                # 时间间隔小于10秒，加入删除列表
                delete_list.append(filename)
            else:
                # 时间间隔大于等于10秒，更新保留时间点
                last_kept_time = time
        
        # 如果没有要删除的文件，跳过当前目录
        if not delete_list:
            continue
        
        # 打印当前目录信息
        print(f"\n处理目录: {dirpath}")
        print(f"删除以下 {len(delete_list)} 个文件:")
        
        # 处理删除操作
        dir_deleted = 0
        for filename in delete_list:
            filepath = os.path.join(dirpath, filename)
            print(f" - {filename}")
            try:
                os.remove(filepath)
                dir_deleted += 1
            except Exception as e:
                print(f"  删除失败 {filename}: {str(e)}")
        
        print(f"当前目录已删除 {dir_deleted} 个文件")
        total_deleted += dir_deleted
    
    print(f"\n总计已删除 {total_deleted} 个文件")

if __name__ == "__main__":
    target_directory = r"C:\Users\DELL\Desktop\test - 副本"
    clean_nonstandard_frame(target_directory)