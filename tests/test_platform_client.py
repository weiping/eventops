import pytest

from scripts.platform_client import dry_run_enabled


@pytest.mark.parametrize("value,expected", [
    (None, True),      # 变量根本不存在
    ("", True),        # vars.DRY_RUN 未定义时 Actions 注入的空串
    ("   ", True),
    ("true", True),
    ("True", True),
    ("1", True),
    ("false", False),
    ("no", False),
])
def test_dry_run_defaults_to_rehearsal(monkeypatch, value, expected):
    monkeypatch.delenv("DRY_RUN", raising=False)
    if value is not None:
        monkeypatch.setenv("DRY_RUN", value)
    assert dry_run_enabled() is expected
