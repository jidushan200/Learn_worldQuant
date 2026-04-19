import threading
from datetime import datetime
from setting import OUTPUT_LOG

# 多线程下防止日志交叉乱序
_log_lock = threading.Lock()


def _write(msg: str):
    """将消息同时输出到控制台和日志文件（线程安全）"""
    with _log_lock:
        print(msg)
        with open(OUTPUT_LOG, "a", encoding="utf-8") as f:
            f.write(msg + "\n")


def log_start(total: int):
    """程序启动时写入日志头"""
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
    """
    每个 alpha 回测完成后，格式化输出结果并写入日志

    输出格式示例：
        [  3/120] alpha_id: abc123xyz
                  字段: fn_sales_growth → group_rank(fn_sales_growth, subindustry)
                  sharpe=1.45 | fitness=1.12 | turnover=0.25 | returns=8.3% | checks=✅ | 结果=✅ PASS

    Args:
        index:    当前序号（从1开始）
        total:    总数
        alpha_id: 回测返回的 alpha id，失败时为 None
        field_id: 本次使用的字段 id
        expr:     本次使用的表达式
        result:   evaluate.py 返回的结果字典，失败时为 None
        err:      错误信息，成功时为 None
    """
    ts = datetime.now().strftime("%H:%M:%S")

    # ── 第一行：序号 + alpha_id ──────────────────────────────
    id_str = alpha_id if alpha_id else "FAILED"
    line1 = f"[{index:>4}/{total}] [{ts}] alpha_id: {id_str}"

    # ── 第二行：字段来源 ─────────────────────────────────────
    line2 = f"           字段: {field_id} → {expr}"

    # ── 第三行：指标结果 或 错误信息 ─────────────────────────
    if err:
        line3 = f"           ❌ 错误: {err}"
    else:
        sharpe   = result.get("sharpe")
        fitness  = result.get("fitness")
        turnover = result.get("turnover")
        returns  = result.get("returns")
        checks   = "✅" if result.get("checks_pass") else "❌"
        overall  = "✅ PASS" if result.get("overall_pass") else "❌ FAIL"

        # returns 转为百分比显示，更直观
        ret_str = f"{returns * 100:.2f}%" if returns is not None else "N/A"

        line3 = (
            f"           sharpe={sharpe} | fitness={fitness} | "
            f"turnover={turnover} | returns={ret_str} | "
            f"checks={checks} | 结果={overall}"
        )

    _write(line1)
    _write(line2)
    _write(line3)
    _write("")  # 空行分隔，提高可读性


def log_end(total: int, passed: int):
    """程序结束时写入汇总"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _write(f"\n{'=' * 60}")
    _write(f"  结束时间: {ts}")
    _write(f"  总计: {total}  ✅ 通过: {passed}  ❌ 未通过: {total - passed}")
    _write(f"{'=' * 60}\n")