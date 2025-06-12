from PIL import Image, ImageDraw, ImageFilter
import tkinter as tk

def get_dpi_scale(root):
    return root.winfo_fpixels('1i') / 72.0

def create_large_icon(state="off", base_size=256):  # 修改基础尺寸为256
    """创建256x256像素的专业风格录制工具图标"""
    # 获取 DPI 缩放比例
    root = tk.Tk()
    scale = get_dpi_scale(root)
    root.destroy()
    
    size = int(base_size * scale)
    padding = int(16 * scale)  # 按比例放大padding
    center = size // 2
    
    # 创建透明背景的图像
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    if state == "on":
        # 录制状态 - 红色脉冲效果
        radius = center - padding
        inner_radius = int(radius * 0.5)
        
        # 外圈红色渐变（增加渐变层数使效果更平滑）
        for i in range(radius, radius - int(20*scale), -1):  # 增加渐变范围
            alpha = int(200 * (i / radius))
            draw.ellipse(
                [center-i, center-i, center+i, center+i],
                fill=(255, 50, 50, alpha),
                outline=(255, 255, 255, 30)
            )
        
        # 中心实心红圈
        draw.ellipse(
            [center-inner_radius, center-inner_radius, 
             center+inner_radius, center+inner_radius],
            fill=(230, 0, 0),
            outline=(255, 255, 255)
        )
        
        # 中心白色圆点
        dot_radius = int(inner_radius * 0.3)
        draw.ellipse(
            [center-dot_radius, center-dot_radius, 
             center+dot_radius, center+dot_radius],
            fill=(255, 255, 255),
            outline=(200, 200, 200)
        )
        
    else:
        # 非录制状态 - 灰色简约设计
        radius = center - padding
        border_width = int(8 * scale)  # 按比例放大边框宽度
        
        # 外圈金属质感
        draw.ellipse(
            [center-radius, center-radius, center+radius, center+radius],
            fill=(100, 100, 100),
            outline=(180, 180, 180),
            width=border_width
        )
        
        # 内圈
        inner_radius = int(radius * 0.7)
        draw.ellipse(
            [center-inner_radius, center-inner_radius, 
             center+inner_radius, center+inner_radius],
            fill=(60, 60, 60),
            outline=(120, 120, 120),
            width=border_width//2
        )
        
        # 中心红点提示
        dot_radius = int(inner_radius * 0.3)
        draw.ellipse(
            [center-dot_radius, center-dot_radius, 
             center+dot_radius, center+dot_radius],
            fill=(150, 0, 0),
            outline=(100, 0, 0)
        )
    
    # 确保radius变量已定义
    if 'radius' not in locals():
        radius = center - padding
        
    # 添加更精细的阴影效果
    shadow = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.ellipse(
        [center-radius+8, center-radius+8,  # 按比例放大阴影偏移
         center+radius-8, center+radius-8],
        fill=(0, 0, 0, 30)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(8))  # 增加模糊半径
    image = Image.alpha_composite(shadow, image)
    
    return image

# 生成并保存两种状态的256x256图标
icon_on = create_large_icon(state="on")
icon_off = create_large_icon(state="off")

# 保存为PNG文件
icon_on.save("recording_icon_on_256.png")
icon_off.save("recording_icon_off_256.png")

print("已生成256x256大小的图标: recording_icon_on_256.png 和 recording_icon_off_256.png")
