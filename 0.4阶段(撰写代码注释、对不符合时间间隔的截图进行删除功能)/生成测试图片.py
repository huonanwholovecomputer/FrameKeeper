import os
import random
from datetime import datetime, timedelta

def generate_test_images(root_dir, num_days=3, images_per_day=20):
    """
    生成不符合时间间隔的测试图片
    :param root_dir: 生成图片的根目录
    :param num_days: 生成多少天的测试数据（默认3天）
    :param images_per_day: 每天生成多少图片（默认20张）
    """
    # 确保目录存在
    os.makedirs(root_dir, exist_ok=True)
    
    # 创建一些子目录
    sub_dirs = ["1", "2", "3", "4"]
    for sub_dir in sub_dirs:
        os.makedirs(os.path.join(root_dir, sub_dir), exist_ok=True)
    
    # 生成测试图片
    total_generated = 0
    
    # 生成不同日期的图片
    for day in range(num_days):
        base_date = datetime.now() - timedelta(days=num_days - day - 1)
        
        # 在每个子目录中生成图片
        for sub_dir in sub_dirs:
            # 随机决定是否在这个子目录生成图片
            if random.random() > 0.7:  # 70%几率跳过
                continue
                
            current_time = base_date.replace(hour=9, minute=0, second=0)  # 从早上9点开始
            
            # 生成当天的图片序列
            for i in range(images_per_day):
                # 随机决定时间间隔：40%几率小于10秒，60%几率大于等于10秒
                if random.random() < 0.4:
                    delta = random.randint(1, 9)  # 1-9秒
                else:
                    delta = random.randint(10, 60)  # 10-60秒
                
                current_time += timedelta(seconds=delta)
                
                # 随机选择jpg或png格式
                ext = random.choice(['jpg', 'png'])
                
                # 生成文件名
                filename = f"capture_{current_time.strftime('%Y%m%d_%H%M%S')}.{ext}"
                filepath = os.path.join(root_dir, sub_dir, filename)
                
                # 创建空文件（在实际应用中可以是真实图片）
                with open(filepath, 'wb') as f:
                    f.write(b'')  # 写入空内容
                
                total_generated += 1
    
    print(f"成功生成 {total_generated} 个测试图片在目录 {root_dir} 及其子目录中")

if __name__ == "__main__":
    target_directory = r"C:\Users\DELL\Desktop\test - 副本"
    generate_test_images(target_directory)
