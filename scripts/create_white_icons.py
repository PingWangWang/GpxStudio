"""
创建白色版本的图标
将交通方式和切换按钮的图标转换为白色，以便在蓝色背景上显示更清晰
"""

from PIL import Image
import os

def create_white_icon(input_path, output_path):
    """
    将图标转换为白色版本

    Args:
        input_path: 输入图标路径
        output_path: 输出图标路径
    """
    try:
        # 打开图像
        img = Image.open(input_path).convert('RGBA')

        # 获取像素数据
        pixels = img.load()
        width, height = img.size

        # 遍历所有像素
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]

                # 如果像素不是完全透明的，将其转换为白色，保持透明度
                if a > 0:
                    pixels[x, y] = (255, 255, 255, a)

        # 保存图像
        img.save(output_path)
        print(f"✓ 已创建白色图标: {output_path}")

    except Exception as e:
        print(f"✗ 创建白色图标失败 {input_path}: {e}")

def main():
    """主函数"""
    # 获取项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    res_dir = os.path.join(project_root, 'res')

    # 需要转换的图标列表
    icons_to_convert = [
        ('Driving.png', 'Driving_white.png'),
        ('Cycling.png', 'Cycling_white.png'),
        ('Waking.png', 'Waking_white.png'),
        ('Switch.png', 'Switch_white.png'),
        ('Cancel.png', 'Cancel_white.png'),
        ('History.png', 'History_white.png'),
    ]

    print("开始创建白色图标...")
    print("=" * 60)

    for input_name, output_name in icons_to_convert:
        input_path = os.path.join(res_dir, input_name)
        output_path = os.path.join(res_dir, output_name)

        if os.path.exists(input_path):
            create_white_icon(input_path, output_path)
        else:
            print(f"✗ 找不到图标文件: {input_path}")

    print("=" * 60)
    print("白色图标创建完成！")

if __name__ == '__main__':
    main()
