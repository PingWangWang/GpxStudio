#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关于界面配置管理
提供关于对话框中展示的各种信息的配置功能
"""

from typing import Dict, Any, Optional


class AboutConfig:
    """关于界面配置类"""

    def __init__(self):
        self._config_data = self._load_default_config()

    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        return {
            "app_info": {
                "name": "GPX Studio",
                "version": "1.1.1",
                "platform": "Windows",
                "description": "路线规划工具，支持多种交通方式，可导出GPX格式文件"
            },
            "open_source_info": {
                "license": "MIT 许可证",
                "license_text": "开源软件 - 本软件采用 MIT 许可证开源"
            },
            "developer_info": {
                "team": "GPX Studio 团队",
                "email": "1341783770@qq.com"
            },
            "copyright_info": {
                "year": "2024-2025",
                "holder": "GPX Studio 团队",
                "map_api_copyright": "使用高德地图API，© 2025 AutoNavi"
            },
            "contact_info": {
                "project_url": "https://github.com/PingWangWang/gpx-studio",
                "email": "1341783770@qq.com"
            }
        }

    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """获取配置项"""
        keys = key.split('.')
        value = self._config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value

    def get_app_name(self) -> str:
        """获取应用名称"""
        return self.get("app_info.name", "GPX Studio")

    def get_app_version(self) -> str:
        """获取应用版本"""
        return self.get("app_info.version", "1.0.0")

    def get_app_platform(self) -> str:
        """获取应用平台"""
        return self.get("app_info.platform", "Windows")

    def get_app_description(self) -> str:
        """获取应用描述"""
        return self.get("app_info.description", "路线规划工具")

    def get_license_text(self) -> str:
        """获取许可证文本"""
        return self.get("open_source_info.license_text", "开源软件")

    def get_developer_team(self) -> str:
        """获取开发者团队"""
        return self.get("developer_info.team", "GPX Studio 团队")

    def get_developer_email(self) -> str:
        """获取开发者邮箱"""
        return self.get("developer_info.email", "contact@gpxstudio.com")

    def get_copyright_text(self) -> str:
        """获取版权文本"""
        year = self.get("copyright_info.year", "2024-2025")
        holder = self.get("copyright_info.holder", "GPX Studio 团队")
        return f"© {year} {holder}"

    def get_map_api_copyright(self) -> str:
        """获取地图API版权"""
        return self.get("copyright_info.map_api_copyright", "使用高德地图API")

    def get_project_url(self) -> str:
        """获取项目URL"""
        return self.get("contact_info.project_url", "")

    def get_contact_email(self) -> str:
        """获取联系邮箱"""
        return self.get("contact_info.email", "")


# 创建全局配置实例
about_config = AboutConfig()
