# 此文件用于重新导出 update_popup.py 中的 CustomMessageDialog
# 以便其他模块可以方便地导入

try:
    from ui.popups.update_popup import CustomMessageDialog
except ImportError:
    # 避免循环导入问题，如果 update_popup 尚未加载，可能需要其他方式
    pass
