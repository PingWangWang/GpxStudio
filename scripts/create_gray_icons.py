"""
创建灰色版本的图标
将导出按钮的图标转换为灰色，用于禁用状态显示
"""

from PIL import Image
import os

def create_gray_icon(input_path, output_path, gray_value=128):
    """
    将图标转换为灰色版本

    Args:
        input_path: 输入图标路径
        output_path: 输出图标路径
        gray_value: 灰色值 (0-255)，默认128为中等灰色
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

                # 如果像素不是完全透明的，将其转换为灰色，保持透明度
                if a > 0:
                    pixels[x, y] = (gray_value, gray_value, gray_value, a)

        # 保存图像
        img.save(output_path)
        print(f"✓ 已创建灰色图标: {output_path}")

    except Exception as e:
        print(f"✗ 创建灰色图标失败 {input_path}: {e}")

def main():
    """主函数"""
    # 获取项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    res_dir = os.path.join(project_root, 'res')

    # 需要转换的图标列表
    icons_to_convert = [
        ('Downloading.png', 'Downloading_gray.png'),
    ]

    print("开始创建灰色图标...")
    print("=" * 60)

    for input_name, output_name in icons_to_convert:
        input_path = os.path.join(res_dir, input_name)
        output_path = os.path.join(res_dir, output_name)

        if os.path.exists(input_path):
            create_gray_icon(input_path, output_path, gray_value=128)  # 使用中等灰色
        else:
            print(f"✗ 找不到图标文件: {input_path}")

    print("=" * 60)
    print("灰色图标创建完成！")

if __name__ == '__main__':
    main()