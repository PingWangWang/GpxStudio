"""
图标管理系统
统一管理Lucide风格的SVG图标，提供图标注册、加载和创建功能
"""

import os
from typing import Dict, Optional
from core.resource_path import resource_path
from ui.widgets.svg_animated_button import LucideSvgButton
from ui.widgets.slider_animated_button import SliderAnimatedButton
from ui.widgets.path_draw_animated_button import PathDrawAnimatedButton
from ui.widgets.transform_animated_button import TransformAnimatedButton
from ui.widgets.complex_animated_button import ComplexAnimatedButton


class IconManager:
    """图标管理器"""
    
    def __init__(self):
        self._icons: Dict[str, str] = {}  # 图标名称 -> SVG路径
        self._animation_types: Dict[str, str] = {}  # 图标名称 -> 动画类型
        self._register_default_icons()
    
    def _register_default_icons(self):
        """注册默认图标"""
        # 旋转动画图标 (SVG)
        self.register_icon('MapSetting', 'res/icons/MapSetting.svg', '地图设置', 'rotation')
        
        # 滑块动画图标 (Slider)
        self.register_icon('RouteSetting', 'res/icons/RouteSetting.svg', '路线设置', 'slider')
        
        # 路径绘制动画图标 (PathDraw)
        self.register_icon('Cancel', 'res/icons/Cancel.svg', '取消', 'path_draw')
        self.register_icon('Yes', 'res/icons/Yes.svg', '确认', 'path_draw')
        self.register_icon('Route', 'res/icons/Route.svg', '路线', 'path_draw')
        self.register_icon('Delete', 'res/icons/Delete.svg', '删除', 'path_draw')
        
        # 变换动画图标 (Transform)
        self.register_icon('Search', 'res/icons/Search.svg', '搜索', 'transform')
        self.register_icon('Location', 'res/icons/Location.svg', '位置', 'transform')
        self.register_icon('ZoomBig', 'res/icons/ZoomBig.svg', '放大', 'transform')
        self.register_icon('ZoomSmall', 'res/icons/ZoomSmall.svg', '缩小', 'transform')
        self.register_icon('Loading', 'res/icons/Loading.svg', '加载', 'transform')
        self.register_icon('Add', 'res/icons/Add.svg', '添加', 'transform')
        
        # 复杂动画图标 (Complex)
        self.register_icon('History', 'res/icons/History.svg', '历史', 'complex')
        
        # 简单SVG图标 (无特殊动画)
        self.register_icon('Download', 'res/icons/Download.svg', '下载', 'simple')
        self.register_icon('Eye', 'res/icons/Eye.svg', '显示', 'simple')
        self.register_icon('EyeOff', 'res/icons/EyeOff.svg', '隐藏', 'simple')
        self.register_icon('Log', 'res/icons/Log.svg', '日志', 'simple')
        self.register_icon('About', 'res/icons/About.svg', '关于', 'simple')
    
    def register_icon(self, name: str, svg_path: str, description: str = "", animation_type: str = "simple"):
        """
        注册图标
        
        Args:
            name: 图标名称
            svg_path: SVG文件路径（相对于项目根目录）
            description: 图标描述
            animation_type: 动画类型 ('rotation', 'slider', 'path_draw', 'transform', 'complex', 'simple')
        """
        full_path = resource_path(svg_path)
        if os.path.exists(full_path):
            self._icons[name] = full_path
            self._animation_types[name] = animation_type
            print(f"[图标管理器] 注册图标: {name} -> {svg_path} ({description}) [{animation_type}]")
        else:
            print(f"[图标管理器] 警告: 图标文件不存在: {svg_path}")
    
    def get_icon_path(self, name: str) -> Optional[str]:
        """获取图标路径"""
        return self._icons.get(name)
    
    def get_animation_type(self, name: str) -> str:
        """获取图标动画类型"""
        return self._animation_types.get(name, 'simple')
    
    def has_icon(self, name: str) -> bool:
        """检查图标是否存在"""
        return name in self._icons
    
    def list_icons(self) -> list:
        """列出所有已注册的图标"""
        return list(self._icons.keys())
    
    def create_button(self, icon_name: str, tooltip: str = None, parent=None):
        """
        创建图标按钮
        
        Args:
            icon_name: 图标名称
            tooltip: 工具提示
            parent: 父组件
        
        Returns:
            按钮实例（根据动画类型返回不同的按钮类）
        """
        if not self.has_icon(icon_name):
            print(f"[图标管理器] 警告: 图标不存在: {icon_name}")
            # 创建一个备用按钮
            button = LucideSvgButton('MapSetting', parent)
        else:
            animation_type = self.get_animation_type(icon_name)
            
            if animation_type == 'slider':
                button = SliderAnimatedButton(parent)
            elif animation_type == 'path_draw':
                button = PathDrawAnimatedButton(icon_name, parent)
            elif animation_type == 'transform':
                button = TransformAnimatedButton(icon_name, parent)
            elif animation_type == 'complex':
                button = ComplexAnimatedButton(icon_name, parent)
            else:  # 'rotation' or 'simple'
                button = LucideSvgButton(icon_name, parent)
        
        if tooltip:
            button.setToolTip(tooltip)
        
        return button
    
    def add_lucide_icons_batch(self, icons_info: list):
        """
        批量添加Lucide图标
        
        Args:
            icons_info: 图标信息列表，格式: [(name, svg_content, description, animation_type), ...]
        """
        for icon_info in icons_info:
            if len(icon_info) == 3:
                name, svg_content, description = icon_info
                animation_type = 'simple'
            else:
                name, svg_content, description, animation_type = icon_info
            
            svg_path = f'res/icons/{name}.svg'
            full_path = resource_path(svg_path)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # 写入SVG文件
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(svg_content)
                
                # 注册图标
                self.register_icon(name, svg_path, description, animation_type)
                
            except Exception as e:
                print(f"[图标管理器] 创建图标文件失败: {name} - {e}")


# 全局图标管理器实例
icon_manager = IconManager()


def create_icon_button(icon_name: str, tooltip: str = None, parent=None):
    """
    便捷函数：创建图标按钮
    
    Args:
        icon_name: 图标名称
        tooltip: 工具提示
        parent: 父组件
    
    Returns:
        按钮实例（根据动画类型自动选择）
    """
    return icon_manager.create_button(icon_name, tooltip, parent)


def register_icon(name: str, svg_path: str, description: str = "", animation_type: str = "simple"):
    """
    便捷函数：注册图标
    
    Args:
        name: 图标名称
        svg_path: SVG文件路径
        description: 图标描述
        animation_type: 动画类型
    """
    icon_manager.register_icon(name, svg_path, description, animation_type)


def add_lucide_icon_from_tsx(name: str, tsx_content: str, description: str = "", animation_type: str = "simple"):
    """
    从TSX内容中提取SVG并添加图标
    
    Args:
        name: 图标名称
        tsx_content: TSX文件内容
        description: 图标描述
        animation_type: 动画类型
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
        icon_manager.add_lucide_icons_batch([(name, svg_content, description, animation_type)])
        
        print(f"[图标管理器] 从TSX提取并添加图标: {name}")
        return True
    else:
        print(f"[图标管理器] 无法从TSX中提取SVG路径: {name}")
        return False