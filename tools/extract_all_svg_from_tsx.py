#!/usr/bin/env python3
"""
从所有TSX文件中提取SVG内容并创建对应的SVG文件
"""

import os
import re
import sys

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.resource_path import resource_path


def extract_svg_from_tsx(tsx_file_path):
    """从TSX文件中提取SVG路径"""
    try:
        with open(tsx_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取SVG路径
        paths = []
        circles = []
        lines = []
        
        # 匹配 <path d="..." />
        path_pattern = r'<(?:motion\.)?path[^>]*d="([^"]+)"[^>]*/?>'
        path_matches = re.findall(path_pattern, content)
        paths.extend(path_matches)
        
        # 匹配 <circle cx="..." cy="..." r="..." />
        circle_pattern = r'<(?:motion\.)?circle[^>]*cx="([^"]+)"[^>]*cy="([^"]+)"[^>]*r="([^"]+)"[^>]*/?>'
        circle_matches = re.findall(circle_pattern, content)
        circles.extend(circle_matches)
        
        # 匹配 <line x1="..." y1="..." x2="..." y2="..." />
        line_pattern = r'<(?:motion\.)?line[^>]*x1="([^"]+)"[^>]*y1="([^"]+)"[^>]*x2="([^"]+)"[^>]*y2="([^"]+)"[^>]*/?>'
        line_matches = re.findall(line_pattern, content)
        lines.extend(line_matches)
        
        print(f"  提取结果: 路径={len(paths)}, 圆形={len(circles)}, 线条={len(lines)}")
        
        return paths, circles, lines
        
    except Exception as e:
        print(f"读取TSX文件失败: {tsx_file_path} - {e}")
        return [], [], []


def create_svg_content(paths, circles, lines):
    """创建SVG内容"""
    svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
'''
    
    # 添加路径
    for path in paths:
        svg_content += f'  <path d="{path}" />\n'
    
    # 添加圆形
    for cx, cy, r in circles:
        svg_content += f'  <circle cx="{cx}" cy="{cy}" r="{r}" />\n'
    
    # 添加线条
    for x1, y1, x2, y2 in lines:
        svg_content += f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" />\n'
    
    svg_content += '</svg>'
    
    return svg_content


def process_all_tsx_files():
    """处理所有TSX文件"""
    icons_dir = resource_path('res/icons')
    
    if not os.path.exists(icons_dir):
        print(f"图标目录不存在: {icons_dir}")
        return
    
    # 获取所有TSX文件
    tsx_files = [f for f in os.listdir(icons_dir) if f.endswith('.tsx')]
    
    print(f"找到 {len(tsx_files)} 个TSX文件")
    
    for tsx_file in tsx_files:
        tsx_path = os.path.join(icons_dir, tsx_file)
        svg_file = tsx_file.replace('.tsx', '.svg')
        svg_path = os.path.join(icons_dir, svg_file)
        
        print(f"处理: {tsx_file} -> {svg_file}")
        
        # 提取SVG内容
        paths, circles, lines = extract_svg_from_tsx(tsx_path)
        
        if not paths and not circles and not lines:
            print(f"  警告: 未找到SVG元素")
            continue
        
        # 创建SVG内容
        svg_content = create_svg_content(paths, circles, lines)
        
        # 写入SVG文件
        try:
            with open(svg_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            print(f"  成功创建: {svg_file}")
            print(f"    路径: {len(paths)}, 圆形: {len(circles)}, 线条: {len(lines)}")
        except Exception as e:
            print(f"  创建SVG文件失败: {e}")


if __name__ == "__main__":
    process_all_tsx_files()