"""
ExportCoordinator 单元测试

覆盖：
- export() 正常导出：服务返回 True → 调用 on_success
- export() 服务返回 False → 调用 on_error
- export() 服务抛出异常 → 调用 on_error，不传播
- generate_filename() 城市名提取逻辑
- _extract_city_name() 分号/逗号分隔规则
- get_last_export_path() 读取持久化配置
- 导出成功后保存 last_export_path
"""
import pytest
import json
import os
import tempfile
from unittest.mock import MagicMock, patch, mock_open

from domain.coordinators.export_coordinator import ExportCoordinator


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_coordinator(gpx_service, config_dir=None):
    success_calls = []
    error_calls = []
    coordinator = ExportCoordinator(
        gpx_service=gpx_service,
        config_dir=config_dir or tempfile.mkdtemp(),
        on_success=success_calls.append,
        on_error=error_calls.append,
    )
    return coordinator, success_calls, error_calls


def _mock_gpx_service(return_value=True):
    svc = MagicMock()
    svc.export_to_gpx.return_value = return_value
    return svc


MOCK_ROUTE_POINTS = [(39.9, 116.4), (39.95, 116.45), (40.0, 116.5)]
MOCK_DATETIME = MagicMock()
MOCK_DATETIME.toString.return_value = '20240101_0800'


# ──────────────────────────────────────────────────────────────────────────────
# Tests: export()
# ──────────────────────────────────────────────────────────────────────────────

class TestExportCoordinatorExport:
    def test_success_calls_on_success(self, tmp_path):
        svc = _mock_gpx_service(True)
        coordinator, successes, errors = _make_coordinator(svc, str(tmp_path))
        file_path = str(tmp_path / 'route.gpx')
        coordinator.export(MOCK_ROUTE_POINTS, MOCK_DATETIME, file_path)
        assert len(successes) == 1
        assert successes[0] == file_path
        assert not errors

    def test_success_calls_gpx_service_export(self, tmp_path):
        svc = _mock_gpx_service(True)
        coordinator, successes, errors = _make_coordinator(svc, str(tmp_path))
        file_path = str(tmp_path / 'route.gpx')
        coordinator.export(MOCK_ROUTE_POINTS, MOCK_DATETIME, file_path,
                          start_name='北京市朝阳区', end_name='上海市浦东新区')
        svc.export_to_gpx.assert_called_once()
        call_kwargs = svc.export_to_gpx.call_args[1]
        # 城市名应被提取（截取分号/逗号前的部分）
        assert call_kwargs['start_name'] == '北京市朝阳区'  # 无分隔符不截取
        assert call_kwargs['end_name'] == '上海市浦东新区'

    def test_service_returns_false_calls_on_error(self, tmp_path):
        svc = _mock_gpx_service(False)
        coordinator, successes, errors = _make_coordinator(svc, str(tmp_path))
        file_path = str(tmp_path / 'route.gpx')
        coordinator.export(MOCK_ROUTE_POINTS, MOCK_DATETIME, file_path)
        assert not successes
        assert len(errors) == 1

    def test_service_exception_calls_on_error(self, tmp_path):
        svc = MagicMock()
        svc.export_to_gpx.side_effect = RuntimeError('写入失败')
        coordinator, successes, errors = _make_coordinator(svc, str(tmp_path))
        coordinator.export(MOCK_ROUTE_POINTS, MOCK_DATETIME, str(tmp_path / 'route.gpx'))
        assert not successes
        assert len(errors) == 1
        assert '写入失败' in errors[0]

    def test_service_exception_does_not_propagate(self, tmp_path):
        svc = MagicMock()
        svc.export_to_gpx.side_effect = Exception('致命错误')
        coordinator, successes, errors = _make_coordinator(svc, str(tmp_path))
        # 不应抛出
        coordinator.export(MOCK_ROUTE_POINTS, MOCK_DATETIME, str(tmp_path / 'route.gpx'))
        assert errors

    def test_export_saves_last_export_path(self, tmp_path):
        svc = _mock_gpx_service(True)
        coordinator, successes, errors = _make_coordinator(svc, str(tmp_path))
        file_path = str(tmp_path / 'sub' / 'route.gpx')
        os.makedirs(str(tmp_path / 'sub'), exist_ok=True)
        coordinator.export(MOCK_ROUTE_POINTS, MOCK_DATETIME, file_path)
        saved_path = coordinator.get_last_export_path()
        assert saved_path == str(tmp_path / 'sub')


# ──────────────────────────────────────────────────────────────────────────────
# Tests: city name extraction
# ──────────────────────────────────────────────────────────────────────────────

class TestExtractCityName:
    """_extract_city_name() 私有方法通过 generate_filename() 间接测试。"""

    def _extract(self, full_name):
        svc = _mock_gpx_service()
        coordinator, _, _ = _make_coordinator(svc)
        return coordinator._extract_city_name(full_name)

    def test_no_separator_returns_full_name(self):
        assert self._extract('北京') == '北京'

    def test_semicolon_splits_at_first(self):
        assert self._extract('北京市;朝阳区') == '北京市'

    def test_comma_splits_at_first(self):
        assert self._extract('上海市,浦东新区') == '上海市'

    def test_semicolon_takes_priority(self):
        # 分号在前，逗号在后
        assert self._extract('城市;区,街道') == '城市'

    def test_strips_whitespace(self):
        assert self._extract('  北京市  ;朝阳区') == '北京市'

    def test_empty_string_returns_empty(self):
        assert self._extract('') == ''


# ──────────────────────────────────────────────────────────────────────────────
# Tests: generate_filename()
# ──────────────────────────────────────────────────────────────────────────────

class TestGenerateFilename:
    def test_basic_filename(self):
        svc = _mock_gpx_service()
        coordinator, _, _ = _make_coordinator(svc)
        name = coordinator.generate_filename('北京', '上海', MOCK_DATETIME)
        assert name == '北京_上海_20240101_0800.gpx'

    def test_extracts_city_from_full_name(self):
        svc = _mock_gpx_service()
        coordinator, _, _ = _make_coordinator(svc)
        name = coordinator.generate_filename('北京市;朝阳区', '上海市,浦东新区', MOCK_DATETIME)
        assert name == '北京市_上海市_20240101_0800.gpx'

    def test_empty_names_use_defaults(self):
        svc = _mock_gpx_service()
        coordinator, _, _ = _make_coordinator(svc)
        name = coordinator.generate_filename('', '', MOCK_DATETIME)
        assert name == '起点_终点_20240101_0800.gpx'


# ──────────────────────────────────────────────────────────────────────────────
# Tests: get_last_export_path()
# ──────────────────────────────────────────────────────────────────────────────

class TestGetLastExportPath:
    def test_returns_none_when_no_config(self, tmp_path):
        svc = _mock_gpx_service()
        coordinator, _, _ = _make_coordinator(svc, str(tmp_path))
        assert coordinator.get_last_export_path() is None

    def test_returns_saved_path(self, tmp_path):
        config_path = tmp_path / 'export_config.json'
        config_path.write_text(
            json.dumps({'last_export_path': '/saved/path'}),
            encoding='utf-8'
        )
        svc = _mock_gpx_service()
        coordinator, _, _ = _make_coordinator(svc, str(tmp_path))
        assert coordinator.get_last_export_path() == '/saved/path'
