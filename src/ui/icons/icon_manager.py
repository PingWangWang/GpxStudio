"""
图标管理系统
统一管理Lucide风格的SVG图标，提供图标注册、加载和创建功能
"""

import os
from typing import Dict, Optional
from core.resource_path import resource_path
from ui.widgets.svg_animated_button import LucideSvgButton


class IconManager:
    """图标管理器"""
    
    def __init__(self):
        self._icons: Dict[str, str] = {}  # 图标名称 -> SVG路径
        self._register_default_icons()
    
    def _register_default_icons(self):
        """注册默认图标"""
        # 基础图标
        self.register_icon('MapSetting', 'res/icons/MapSetting.svg', '地图设置')
        self.register_icon('RouteSetting', 'res/icons/RouteSetting.svg', '路线设置')
        
        # 可以继续添加更多图标
        # self.register_icon('user', 'res/icons/user.svg', '用户')
        # self.register_icon('search', 'res/icons/search.svg', '搜索')
        # self.register_icon('menu', 'res/icons/menu.svg', '菜单')
    
    def register_icon(self, name: str, svg_path: str, description: str = ""):
        """
        注册图标
        
        Args:
            name: 图标名称
            svg_path: SVG文件路径（相对于项目根目录）
            description: 图标描述
        """
        full_path = resource_path(svg_path)
        if os.path.exists(full_path):
            self._icons[name] = full_path
            print(f"[图标管理器] 注册图标: {name} -> {svg_path} ({description})")
        else:
            print(f"[图标管理器] 警告: 图标文件不存在: {svg_path}")
    
    def get_icon_path(self, name: str) -> Optional[str]:
        """获取图标路径"""
        return self._icons.get(name)
    
    def has_icon(self, name: str) -> bool:
        """检查图标是否存在"""
        return name in self._icons
    
    def list_icons(self) -> list:
        """列出所有已注册的图标"""
        return list(self._icons.keys())
    
    def create_button(self, icon_name: str, tooltip: str = None, parent=None) -> LucideSvgButton:
        """
        创建图标按钮
        
        Args:
            icon_name: 图标名称
            tooltip: 工具提示
            parent: 父组件
        
        Returns:
            LucideSvgButton: 按钮实例
        """
        if not self.has_icon(icon_name):
            print(f"[图标管理器] 警告: 图标不存在: {icon_name}")
            # 创建一个备用按钮
            button = LucideSvgButton('MapSetting', parent)  # 使用MapSetting作为备用
        else:
            button = LucideSvgButton(icon_name, parent)
        
        if tooltip:
            button.setToolTip(tooltip)
        
        return button
    
    def add_lucide_icons_batch(self, icons_info: list):
        """
        批量添加Lucide图标
        
        Args:
            icons_info: 图标信息列表，格式: [(name, svg_content, description), ...]
        """
        for name, svg_content, description in icons_info:
            svg_path = f'res/icons/{name}.svg'
            full_path = resource_path(svg_path)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # 写入SVG文件
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(svg_content)
                
                # 注册图标
                self.register_icon(name, svg_path, description)
                
            except Exception as e:
                print(f"[图标管理器] 创建图标文件失败: {name} - {e}")


# 全局图标管理器实例
icon_manager = IconManager()


def create_icon_button(icon_name: str, tooltip: str = None, parent=None) -> LucideSvgButton:
    """
    便捷函数：创建图标按钮
    
    Args:
        icon_name: 图标名称
        tooltip: 工具提示
        parent: 父组件
    
    Returns:
        LucideSvgButton: 按钮实例
    """
    return icon_manager.create_button(icon_name, tooltip, parent)


def register_icon(name: str, svg_path: str, description: str = ""):
    """
    便捷函数：注册图标
    
    Args:
        name: 图标名称
        svg_path: SVG文件路径
        description: 图标描述
    """
    icon_manager.register_icon(name, svg_path, description)


def add_lucide_icon_from_tsx(name: str, tsx_content: str, description: str = ""):
    """
    从TSX内容中提取SVG并添加图标
    
    Args:
        name: 图标名称
        tsx_content: TSX文件内容
        description: 图标描述
    """
    import re
    
    # 从TSX中提取SVG路径
    svg_paths = []
    
    # 匹配 <path d="..." /> 模式
    path_pattern = r'<path\s+d="([^"]+)"\s*/>'
    paths = re.findall(path_pattern, tsx_content)
    
    if paths:
        # 构建完整的SVG内容
        svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
'''
        
        for path in paths:
            svg_content += f'  <path d="{path}" />\n'
        
        svg_content += '</svg>'
        
        # 添加到图标管理器
        icon_manager.add_lucide_icons_batch([(name, svg_content, description)])
        
        print(f"[图标管理器] 从TSX提取并添加图标: {name}")
        return True
    else:
        print(f"[图标管理器] 无法从TSX中提取SVG路径: {name}")
        return False