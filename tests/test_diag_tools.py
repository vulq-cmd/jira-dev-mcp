"""devflow_diag: báo code đang chạy + cờ cấu hình, KHÔNG lộ secret."""
import os

from tools import diag_tools


def test_diag_shape_and_no_secret():
    out = diag_tools.devflow_diag()
    # cấu trúc cốt lõi
    for k in ("pid", "loaded_fingerprint", "disk_fingerprint", "stale", "services", "transport"):
        assert k in out
    assert isinstance(out["stale"], bool)
    assert isinstance(out["services"]["figma"], bool)
    # tuyệt đối không có token nào trong output
    s = str(out)
    for secret_env in ("JIRA_PAT", "GITLAB_TOKEN", "NOTION_TOKEN", "FIGMA_TOKEN"):
        assert os.environ[secret_env] not in s
    assert "Bearer" not in s and "PRIVATE-TOKEN" not in s


def test_diag_not_stale_when_disk_unchanged():
    # Không sửa file trong lúc test → bản nạp == bản đĩa → stale phải False.
    out = diag_tools.devflow_diag()
    assert out["loaded_fingerprint"] == out["disk_fingerprint"]
    assert out["stale"] is False
