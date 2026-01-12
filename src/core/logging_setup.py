"""
日志配置模块
提供应用程序日志记录功能，支持文件轮转和大小监控
"""

import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from typing import Optional

from services.config.map_config import map_config

class LoggingSetup:
    """日志配置类"""
    
    @staticmethod
    def get_log_directory():
        """
        获取日志存储目录
        与配置文件存储在同一目录
        """
        config_path = map_config._get_config_path()
        log_dir = os.path.dirname(config_path)
        return log_dir
    
    @staticmethod
    def get_log_path():
        """
        获取日志文件路径
        """
        log_dir = LoggingSetup.get_log_directory()
        return os.path.join(log_dir, "GPXStudioRun.log")
    
    @staticmethod
    def setup_logging():
        """
        设置日志配置
        配置文件轮转，单个文件最大100MB，最多保留5个备份
        """
        log_path = LoggingSetup.get_log_path()
        log_dir = os.path.dirname(log_path)
        
        # 确保日志目录存在
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 创建日志记录器
        logger = logging.getLogger()
        
        # 从配置中获取日志级别
        log_level = LoggingSetup.get_log_level()
        logger.setLevel(log_level)
        
        # 清除已有的处理器
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 创建文件处理器，配置轮转
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=100 * 1024 * 1024,  # 100MB
            backupCount=5,  # 最多保留5个备份
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # 添加处理器
        logger.addHandler(file_handler)
        
        # 添加控制台处理器（可选）
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    @staticmethod
    def mark_first_run_completed():
        """
        标记首次启动完成
        将 is_first_run 设置为 False，并将日志级别设置为 WARNING（如果用户没有手动修改）
        """
        from services.config.map_config import map_config
        
        # 检查是否是首次启动
        is_first_run = map_config.get('is_first_run', True)
        
        if is_first_run:
            # 检查用户是否手动修改了日志级别
            has_custom_log_level = map_config.get('log_level') is not None
            
            if not has_custom_log_level:
                # 用户没有手动修改，设置为 WARNING
                map_config.set('log_level', 'WARNING')
            
            # 标记首次启动完成
            map_config.set('is_first_run', False)
            
            # 重新初始化日志配置
            LoggingSetup.setup_logging()
    
    @staticmethod
    def get_log_level():
        """
        获取日志级别
        从配置中读取，默认为WARNING
        首次启动时使用DEBUG级别（如果用户没有手动设置）
        """
        from services.config.map_config import map_config
        
        # 首先检查用户是否手动设置了日志级别
        log_level_str = map_config.get('log_level')
        
        # 如果用户手动设置了日志级别，直接使用
        if log_level_str is not None:
            # 转换为logging模块的级别常量
            log_level_map = {
                'DEBUG': logging.DEBUG,
                'INFO': logging.INFO,
                'WARNING': logging.WARNING,
                'ERROR': logging.ERROR,
                'CRITICAL': logging.CRITICAL
            }
            return log_level_map.get(log_level_str, logging.WARNING)
        
        # 检查是否是首次启动
        is_first_run = map_config.get('is_first_run', True)
        
        # 首次启动时使用DEBUG级别
        if is_first_run:
            return logging.DEBUG
        
        # 非首次启动且用户没有手动设置，使用WARNING级别
        return logging.WARNING
    
    @staticmethod
    def set_log_level(level):
        """
        设置日志级别
        """
        from services.config.map_config import map_config
        # 保存到配置
        success = map_config.set('log_level', level)
        if not success:
            raise Exception("保存日志级别失败")
        
        # 重新初始化日志配置
        LoggingSetup.setup_logging()
    
    @staticmethod
    def get_log_size():
        """
        获取日志文件大小（MB）
        """
        log_path = LoggingSetup.get_log_path()
        if os.path.exists(log_path):
            return os.path.getsize(log_path) / (1024 * 1024)
        return 0.0
    
    @staticmethod
    def clean_logs():
        """
        清理所有日志文件
        """
        log_dir = LoggingSetup.get_log_directory()
        log_path = LoggingSetup.get_log_path()
        
        # 先移除所有日志处理器
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()
        
        success = True
        
        # 尝试删除主日志文件
        try:
            if os.path.exists(log_path):
                os.remove(log_path)
        except Exception as e:
            print(f"清理日志文件 {log_path} 失败: {e}")
            success = False
        
        # 尝试删除所有备份日志文件
        try:
            log_files = [f for f in os.listdir(log_dir) if f.startswith('GPXStudioRun.log.')]
            for log_file in log_files:
                backup_log_path = os.path.join(log_dir, log_file)
                if os.path.exists(backup_log_path):
                    os.remove(backup_log_path)
        except Exception as e:
            print(f"清理备份日志文件失败: {e}")
            success = False
        
        # 重新初始化日志配置
        LoggingSetup.setup_logging()
        
        return success
    
    @staticmethod
    def open_log_directory():
        """
        打开日志存储目录
        """
        log_dir = LoggingSetup.get_log_directory()
        if os.path.exists(log_dir):
            if sys.platform == 'win32':
                os.startfile(log_dir)
            elif sys.platform == 'darwin':
                os.system(f'open "{log_dir}"')
            else:
                os.system(f'xdg-open "{log_dir}"')
            return True
        return False

# 重定向print函数到日志系统
class PrintLogger:
    def __init__(self):
        # 保存原始的print函数
        import builtins
        self.old_print = builtins.print
        # 保存builtins模块的引用，以便在需要时获取最新的print函数
        self.builtins = builtins
    
    def __call__(self, *args, **kwargs):
        try:
            # 调用原始的print函数
            self.old_print(*args, **kwargs)
            # 将输出记录到日志
            message = ' '.join(map(str, args))
            # 每次调用时都获取最新的根日志记录器，确保使用最新的配置
            import logging
            logger = logging.getLogger()
            logger.info(message)
        except Exception as e:
            # 如果出现异常，使用原始的print函数输出异常信息
            self.old_print(f"PrintLogger错误: {e}")

# 初始化日志配置
logger = LoggingSetup.setup_logging()

# 重定向print函数
import builtins
builtins.print = PrintLogger()

# 导出常用方法
get_log_directory = LoggingSetup.get_log_directory
get_log_path = LoggingSetup.get_log_path
get_log_size = LoggingSetup.get_log_size
clean_logs = LoggingSetup.clean_logs
open_log_directory = LoggingSetup.open_log_directory
get_log_level = LoggingSetup.get_log_level
set_log_level = LoggingSetup.set_log_level
mark_first_run_completed = LoggingSetup.mark_first_run_completed
