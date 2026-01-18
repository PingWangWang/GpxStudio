#!/usr/bin/env python3
"""
替换代码中的PNG图标使用为动画SVG按钮
"""

import os
import re
import sys

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.resource_path import resource_path


# PNG图标到SVG图标的映射
PNG_TO_SVG_MAPPING = {
    'Cancel.png': 'Cancel',
    'Search.png': 'Search', 
    'Location.png': 'Location',
    'ZoomBig.png': 'ZoomBig',
    'Route.png': 'Route',
    'Yes.png': 'Yes',
    'History.png': 'History',
    'Loading.png': 'Loading',
    'Cancel_white.png': 'Cancel',
    'History_white.png': 'History',
    'Driving.png': 'Route',  # 使用Route图标代替
    'Cycling.png': 'Route',  # 使用Route图标代替
    'Waking.png': 'Route',   # 使用Route图标代替
    'Driving_white.png': 'Route',
    'Cycling_white.png': 'Route', 
    'Waking_white.png': 'Route',
    'Switch.png': 'Route',   # 使用Route图标代替
    'Switch_white.png': 'Route',
    'Add.png': 'ZoomBig',    # 使用ZoomBig图标代替
    'Delete.png': 'Cancel',  # 使用Cancel图标代替
}


def find_png_usage_in_file(file_path):
    """在文件中查找PNG图标使用"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找PNG文件引用
        png_pattern = r"['\"]([^'\"]*\.png)['\"]"
        matches = re.findall(png_pattern, content)
        
        # 过滤出图标相关的PNG
        icon_matches = []
        for match in matches:
            filename = os.path.basename(match)
            if filename in PNG_TO_SVG_MAPPING:
                icon_matches.append((match, filename))
        
        return content, icon_matches
        
    except Exception as e:
        print(f"读取文件失败: {file_path} - {e}")
        return None, []


def replace_png_with_svg_button(file_path, content, png_matches):
    """替换PNG使用为SVG按钮"""
    if not png_matches:
        return content, False
    
    modified_content = content
    changes_made = False
    
    print(f"\n处理文件: {file_path}")
    
    for full_match, filename in png_matches:
        svg_icon_name = PNG_TO_SVG_MAPPING[filename]
        print(f"  发现PNG使用: {filename} -> {svg_icon_name}")
        
        # 检查是否是按钮创建的上下文
        if 'setIcon' in content and full_match in content:
            # 这是传统的QIcon使用，需要替换为create_icon_button
            print(f"    需要替换为动画按钮: {filename}")
            
            # 查找包含此PNG的代码块
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if full_match in line and 'setIcon' in line:
                    # 找到按钮变量名
                    button_var_pattern = r'(\w+)\.setIcon'
                    button_match = re.search(button_var_pattern, line)
                    if button_match:
                        button_var = button_match.group(1)
                        print(f"      按钮变量: {button_var}")
                        
                        # 添加导入语句（如果不存在）
                        if 'from ui.icons.icon_manager import create_icon_button' not in content:
                            # 查找合适的位置插入导入
                            import_lines = []
                            for j, import_line in enumerate(lines):
                                if import_line.strip().startswith('from ') or import_line.strip().startswith('import '):
                                    import_lines.append(j)
                            
                            if import_lines:
                                insert_pos = max(import_lines) + 1
                                lines.insert(insert_pos, 'from ui.icons.icon_manager import create_icon_button')
                                print(f"      添加导入语句在第{insert_pos+1}行")
                        
                        # 替换按钮创建代码
                        # 查找按钮创建的行
                        for k in range(max(0, i-10), min(len(lines), i+5)):
                            if f'{button_var} = ' in lines[k] and 'QPushButton' in lines[k]:
                                # 替换按钮创建
                                tooltip_match = re.search(r'setToolTip\(["\']([^"\']+)["\']\)', content)
                                tooltip = tooltip_match.group(1) if tooltip_match else None
                                
                                replacement = f'        {button_var} = create_icon_button("{svg_icon_name}"'
                                if tooltip:
                                    replacement += f', "{tooltip}"'
                                replacement += ', self)'
                                
                                lines[k] = replacement
                                print(f"      替换按钮创建: 第{k+1}行")
                                break
                        
                        # 删除或注释掉setIcon相关的代码
                        lines[i] = f'        # {line.strip()}  # 已替换为动画按钮'
                        print(f"      注释掉setIcon: 第{i+1}行")
                        
                        changes_made = True
    
    if changes_made:
        modified_content = '\n'.join(lines)
    
    return modified_content, changes_made


def process_python_files():
    """处理所有Python文件"""
    src_dir = resource_path('src')
    
    # 需要处理的文件列表
    files_to_process = []
    
    # 遍历src目录查找Python文件
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                files_to_process.append(os.path.join(root, file))
    
    print(f"找到 {len(files_to_process)} 个Python文件")
    
    total_changes = 0
    
    for file_path in files_to_process:
        content, png_matches = find_png_usage_in_file(file_path)
        
        if content and png_matches:
            modified_content, changes_made = replace_png_with_svg_button(file_path, content, png_matches)
            
            if changes_made:
                try:
                    # 备份原文件
                    backup_path = file_path + '.backup'
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    # 写入修改后的内容
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(modified_content)
                    
                    print(f"  ✓ 已更新文件: {os.path.relpath(file_path, src_dir)}")
                    total_changes += 1
                    
                except Exception as e:
                    print(f"  ✗ 更新文件失败: {file_path} - {e}")
    
    print(f"\n总共更新了 {total_changes} 个文件")


def show_mapping_info():
    """显示PNG到SVG的映射信息"""
    print("PNG图标到SVG动画按钮的映射:")
    print("=" * 50)
    
    for png_name, svg_name in PNG_TO_SVG_MAPPING.items():
        print(f"{png_name:20} -> {svg_name}")
    
    print("\n动画类型说明:")
    print("- Cancel, Yes, Route: 路径绘制动画")
    print("- Search, Location, ZoomBig, Loading: 变换动画")  
    print("- History: 复杂动画")
    print("- 其他: 简单SVG动画")


if __name__ == "__main__":
    show_mapping_info()
    print("\n开始处理文件...")
    process_python_files()