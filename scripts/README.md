# Scripts 目录

项目维护和测试脚本。

## 脚本说明

### clean.py - 项目清理
删除临时文件、构建目录、缓存等。

```bash
python scripts/clean.py --all      # 清理所有
python scripts/clean.py --build    # 只清理构建文件
python scripts/clean.py --test     # 只清理测试文件
python scripts/clean.py --cache    # 只清理缓存
python scripts/clean.py --help     # 查看所有选项
```

### run_gpx_tests.py - 运行GPX测试
运行所有GPX相关的单元测试。

```bash
python scripts/run_gpx_tests.py
```

### run_error_fallback_tests.py - 运行错误回退测试
专门测试错误处理逻辑。

```bash
python scripts/run_error_fallback_tests.py
```

## 注意事项

- 所有脚本都应该从项目根目录运行
- 脚本会自动处理路径问题，无需手动设置PYTHONPATH
