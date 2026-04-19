import os
import threading
from datetime import datetime
from setting import LOGS_DIR, LOG_BASE_NAME

_log_lock = threading.Lock()
_log_file_path = None


def _resolve_log_path() -> str:
    today = datetime.now().strftime("%Y%m%d")
    os.makedirs(LOGS_DIR, exist_ok=True)

    for filename in os.listdir(LOGS_DIR):
        if filename.startswith(LOG_BASE_NAME) and today in filename:
            print(f"  📄 找到今日日志，追加写入: {filename}")
            return os.path.join(LOGS_DIR, filename)

    filename = f"{LOG_BASE_NAME}.{today}.log"
    print(f"  📄 新建今日日志: {filename}")
    return os.path.join(LOGS_DIR, filename)


def _get_log_path() -> str:
    global _log_file_path
    if _log_file_path is None:
        _log_file_path = _resolve_log_path()
    return _log_file_path


def _write(msg: str):
    with _log_lock:
        print(msg)
        with open(_get_log_path(), "a", encoding="utf-8") as f:
            f.write(msg + "\n")


def log_start(total: int):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _write(f"\n{'=' * 60}")
    _write(f"  开始时间: {ts}")
    _write(f"  共 {total} 个 alpha 待回测")
    _write(f"{'=' * 60}\n")


def log_result(
    index:    int,
    total:    int,
    alpha_id: str,
    field_id: str,
    expr:     str,
    settings: dict | None,
    result:   dict | None,
    err:      str | None,
):
    ts     = datetime.now().strftime("%Y_%m_%d %H:%M:%S")
    id_str = alpha_id if alpha_id else "FAILED"

    line1 = f"[{index:>4}/{total}] [{ts}]"
    line2 = f"           alpha_id: {id_str}"
    line3 = f"           字段: {field_id}"
    line4 = f"           Alpha_expr: {expr}"

    # ── settings 展示 ──────────────────────────────────────────
    if settings:
        line5 = (
            f"           settings: "
            f"region={settings.get('region')} | "
            f"universe={settings.get('universe')} | "
            f"neutralization={settings.get('neutralization')} | "
            f"delay={settings.get('delay')} | "
            f"decay={settings.get('decay')} | "
            f"truncation={settings.get('truncation')} | "
            f"pasteurization={settings.get('pasteurization')} | "
            f"language={settings.get('language')}"
        )
    else:
        line5 = f"           settings: N/A"

    # ── 回测结果 ───────────────────────────────────────────────
    if err:
        line6 = f"           ❌ 错误: {err}"
    else:
        sharpe   = result.get("sharpe")
        fitness  = result.get("fitness")
        turnover = result.get("turnover")
        returns  = result.get("returns")
        ret_str = f"{returns * 100:.2f}%" if returns is not None else "N/A"

        # 只展示核心指标，不判断是否通过
        line6 = (
            f"           sharpe={sharpe} | fitness={fitness} | "
            f"turnover={turnover} | returns={ret_str}"
        )

    _write(line1)
    _write(line2)
    _write(line3)
    _write(line4)
    _write(line5)
    _write(line6)
    _write("")


def log_end(total: int, passed: int):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _write(f"\n{'=' * 60}")
    _write(f"  结束时间: {ts}")
    _write(f"  总计: {total}  ✅ 通过: {passed}  ❌ 未通过: {total - passed}")
    _write(f"{'=' * 60}\n")