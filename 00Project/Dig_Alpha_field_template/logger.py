import os
import threading
from datetime import datetime
from setting import LOGS_DIR, LOG_BASE_NAME

_log_lock = threading.Lock()
_log_file_path = None  # 缓存当前运行的日志路径


def _resolve_log_path() -> str:
    """
    启动时扫描 logs/ 目录：
    - 找到含今日日期的文件 → 返回该路径（追加）
    - 找不到 → 新建今日文件（新建）
    """
    today = datetime.now().strftime("%Y%m%d")

    # 确保 logs/ 目录存在
    os.makedirs(LOGS_DIR, exist_ok=True)

    # 遍历目录，查找今天的日志文件
    for filename in os.listdir(LOGS_DIR):
        if filename.startswith(LOG_BASE_NAME) and today in filename:
            print(f"  📄 找到今日日志，追加写入: {filename}")
            return os.path.join(LOGS_DIR, filename)

    # 没找到，新建
    filename = f"{LOG_BASE_NAME}.{today}.log"
    print(f"  📄 新建今日日志: {filename}")
    return os.path.join(LOGS_DIR, filename)


def _get_log_path() -> str:
    """获取日志路径，只在第一次调用时解析，之后复用缓存"""
    global _log_file_path
    if _log_file_path is None:
        _log_file_path = _resolve_log_path()
    return _log_file_path


def _write(msg: str):
    """将消息同时输出到控制台和日志文件（线程安全）"""
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
    result:   dict | None,
    err:      str | None,
):
    ts = datetime.now().strftime("%H:%M:%S")

    id_str = alpha_id if alpha_id else "FAILED"
    line1 = f"[{index:>4}/{total}] [{ts}] alpha_id: {id_str}"
    line2 = f"           字段: {field_id} → {expr}"

    if err:
        line3 = f"           ❌ 错误: {err}"
    else:
        sharpe   = result.get("sharpe")
        fitness  = result.get("fitness")
        turnover = result.get("turnover")
        returns  = result.get("returns")
        checks   = "✅" if result.get("checks_pass") else "❌"
        overall  = "✅ PASS" if result.get("overall_pass") else "❌ FAIL"
        ret_str  = f"{returns * 100:.2f}%" if returns is not None else "N/A"

        line3 = (
            f"           sharpe={sharpe} | fitness={fitness} | "
            f"turnover={turnover} | returns={ret_str} | "
            f"checks={checks} | 结果={overall}"
        )

    _write(line1)
    _write(line2)
    _write(line3)
    _write("")


def log_end(total: int, passed: int):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _write(f"\n{'=' * 60}")
    _write(f"  结束时间: {ts}")
    _write(f"  总计: {total}  ✅ 通过: {passed}  ❌ 未通过: {total - passed}")
    _write(f"{'=' * 60}\n")