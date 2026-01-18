#!/usr/bin/env python3
"""
添加Lucide图标的便捷脚本
支持从TSX文件或直接SVG内容添加图标
"""

import sys
import os
import re

# 添加src目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # 上一级目录（项目根目录）
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, src_dir)

def extract_svg_from_tsx(tsx_content):
    """从TSX内容中提取SVG路径"""
    # 匹配 <path d="..." /> 模式
    path_pattern = r'<path\s+d="([^"]+)"\s*/>'
    paths = re.findall(path_pattern, tsx_content)
    
    if not paths:
        return None
    
    # 构建完整的SVG内容
    svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
'''
    
    for path in paths:
        svg_content += f'  <path d="{path}" />\n'
    
    svg_content += '</svg>'
    
    return svg_content

def add_icon_from_tsx(tsx_file_path, icon_name, description=""):
    """从TSX文件添加图标"""
    if not os.path.exists(tsx_file_path):
        print(f"❌ TSX文件不存在: {tsx_file_path}")
        return False
    
    try:
        with open(tsx_file_path, 'r', encoding='utf-8') as f:
            tsx_content = f.read()
        
        svg_content = extract_svg_from_tsx(tsx_content)
        
        if not svg_content:
            print(f"❌ 无法从TSX文件中提取SVG内容: {tsx_file_path}")
            return False
        
        return add_icon_from_svg(svg_content, icon_name, description)
        
    except Exception as e:
        print(f"❌ 处理TSX文件失败: {e}")
        return False

def add_icon_from_svg(svg_content, icon_name, description=""):
    """从SVG内容添加图标"""
    # 使用项目根目录的路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    svg_file_path = os.path.join(project_root, f'res/icons/{icon_name}.svg')
    
    # 确保目录存在
    os.makedirs(os.path.dirname(svg_file_path), exist_ok=True)
    
    try:
        # 保存SVG文件
        with open(svg_file_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        print(f"✅ SVG图标已保存: {svg_file_path}")
        
        # 注册到图标管理器
        from ui.icons import register_icon
        register_icon(icon_name, svg_file_path, description)
        
        print(f"✅ 图标已注册: {icon_name} - {description}")
        return True
        
    except Exception as e:
        print(f"❌ 保存SVG文件失败: {e}")
        return False

def list_available_icons():
    """列出已注册的图标"""
    try:
        from ui.icons import icon_manager
        icons = icon_manager.list_icons()
        
        print("📋 已注册的图标:")
        for icon in icons:
            path = icon_manager.get_icon_path(icon)
            print(f"  - {icon}: {path}")
        
        return icons
        
    except Exception as e:
        print(f"❌ 获取图标列表失败: {e}")
        return []

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python add_lucide_icon.py list                           # 列出已注册的图标")
        print("  python add_lucide_icon.py tsx <tsx_file> <icon_name> [description]  # 从TSX文件添加图标")
        print("  python add_lucide_icon.py svg <svg_file> <icon_name> [description]  # 从SVG文件添加图标")
        print("")
        print("示例:")
        print("  python add_lucide_icon.py tsx res/icons/user.tsx user '用户图标'")
        print("  python add_lucide_icon.py svg res/icons/search.svg search '搜索图标'")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        list_available_icons()
        
    elif command == 'tsx':
        if len(sys.argv) < 4:
            print("❌ 参数不足，需要: tsx <tsx_file> <icon_name> [description]")
            return
        
        tsx_file = sys.argv[2]
        icon_name = sys.argv[3]
        description = sys.argv[4] if len(sys.argv) > 4 else ""
        
        print(f"正在从TSX文件添加图标: {icon_name}")
        if add_icon_from_tsx(tsx_file, icon_name, description):
            print(f"✅ 图标 '{icon_name}' 添加成功！")
        else:
            print(f"❌ 图标 '{icon_name}' 添加失败！")
    
    elif command == 'svg':
        if len(sys.argv) < 4:
            print("❌ 参数不足，需要: svg <svg_file> <icon_name> [description]")
            return
        
        svg_file = sys.argv[2]
        icon_name = sys.argv[3]
        description = sys.argv[4] if len(sys.argv) > 4 else ""
        
        if not os.path.exists(svg_file):
            print(f"❌ SVG文件不存在: {svg_file}")
            return
        
        try:
            with open(svg_file, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            print(f"正在从SVG文件添加图标: {icon_name}")
            if add_icon_from_svg(svg_content, icon_name, description):
                print(f"✅ 图标 '{icon_name}' 添加成功！")
            else:
                print(f"❌ 图标 '{icon_name}' 添加失败！")
                
        except Exception as e:
            print(f"❌ 读取SVG文件失败: {e}")
    
    else:
        print(f"❌ 未知命令: {command}")
        print("支持的命令: list, tsx, svg")

if __name__ == "__main__":
    main()