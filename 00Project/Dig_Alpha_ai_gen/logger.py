import os
import json
import threading
from datetime import datetime
from setting import LOGS_DIR, LOG_BASE_NAME, BRAIN_URL_PREFIX

_log_lock      = threading.Lock()
_log_file_path = None


def _resolve_log_path() -> str:
    today = datetime.now().strftime("%Y%m%d")
    os.makedirs(LOGS_DIR, exist_ok=True)

    for filename in os.listdir(LOGS_DIR):
        if filename.startswith(LOG_BASE_NAME) and today in filename:
            print(f"  📄 找到今日日志，追加写入: {filename}")
            return os.path.join(LOGS_DIR, filename)

    filename = f"{LOG_BASE_NAME}.{today}.jsonl"
    print(f"  📄 新建今日日志: {filename}")
    return os.path.join(LOGS_DIR, filename)


def _get_log_path() -> str:
    global _log_file_path
    if _log_file_path is None:
        _log_file_path = _resolve_log_path()
    return _log_file_path


def _fmt_ts() -> str:
    return f"【{datetime.now().strftime('%Y_%m_%d %H:%M:%S')}】"


def _format_grade(grade: str | None) -> str | None:
    if not isinstance(grade, str) or not grade.strip():
        return None
    return grade.replace("_", " ").title()


def _log_entry(obj: dict):
    """写入文件并打印到控制台（线程安全）"""
    with _log_lock:
        _print_entry(obj)
        with open(_get_log_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _print_entry(obj: dict):
    t   = obj.get("type")
    pad = " " * 12

    if t == "start":
        print(f"\n{'=' * 60}")
        print(f"  开始时间 : {obj['timestamp']}")
        print(f"  共 {obj['total']} 个 alpha 待回测")
        print(f"{'=' * 60}\n")

    elif t == "result":
        index    = obj.get("index", 0)
        total    = obj.get("total", 0)
        alpha_id = obj.get("alpha_id") or "—"
        expr     = obj.get("expr", "")
        error    = obj.get("error")

        print(f"[{index:4d}/{total:4d}]  {alpha_id}  【Alpha_id】")
        print(f"{pad}expr      : {expr}")

        if error:
            print(f"{pad}error     : {error}")
        else:
            sharpe   = obj.get("sharpe")
            fitness  = obj.get("fitness")
            turnover = obj.get("turnover")
            returns  = obj.get("returns")
            drawdown = obj.get("drawdown")
            margin   = obj.get("margin")

            if None not in (sharpe, fitness, turnover):
                to_pct = turnover * 100 if isinstance(turnover, (int, float)) and turnover <= 1 else turnover
                print(f"{pad}sharpe    : {sharpe:.2f}    fitness  : {fitness:.2f}    turnover : {to_pct:.1f}%")

            if returns is not None or drawdown is not None or margin is not None:
                ret_str = f"{returns * 100:.2f}%" if isinstance(returns, (int, float)) else "N/A"
                dd_str  = f"{drawdown * 100:.2f}%" if isinstance(drawdown, (int, float)) else "N/A"
                mg_str  = f"{margin:.6f}" if isinstance(margin, (int, float)) else "N/A"
                print(f"{pad}returns   : {ret_str}    drawdown : {dd_str}    margin   : {mg_str}")

            grade  = _format_grade(obj.get("grade"))
            stage  = obj.get("stage")
            status = obj.get("status")
            if grade is not None or stage is not None or status is not None:
                print(f"{pad}grade     : {grade or 'N/A'}    stage    : {stage or 'N/A'}    status   : {status or 'N/A'}")

            weight_max      = obj.get("weight_max")
            sub_univ_sharpe = obj.get("sub_univ_sharpe")
            self_corr       = obj.get("self_corr")

            if weight_max      is not None:
                print(f"{pad}weight    : max={weight_max:.4f}")
            if sub_univ_sharpe is not None:
                print(f"{pad}sub-univ  : sharpe={sub_univ_sharpe:.2f}")
            if self_corr       is not None:
                print(f"{pad}self-corr : {self_corr:.2f}")

        print(f"{pad}{_fmt_ts()}")
        print()

    elif t == "end":
        print(f"\n{'=' * 60}")
        print(f"  结束时间 : {obj['timestamp']}")
        print(f"  总计: {obj['total']}  ✅ 成功: {obj['succeeded']}  ❌ 失败: {obj['failed']}")
        print(f"{'=' * 60}\n")


# ── 公开接口 ──────────────────────────────────────────────────

def log_start(total: int):
    _log_entry({
        "type":      "start",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total":     total,
    })


def log_result(
    index:    int,
    total:    int,
    alpha_id: str | None,
    field_id: str,
    expr:     str,
    settings: dict | None,
    result:   dict | None,
    err:      str | None,
):
    url = (BRAIN_URL_PREFIX + alpha_id) if alpha_id else None

    entry = {
        "type":      "result",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "index":     index,
        "total":     total,
        "alpha_id":  alpha_id,
        "url":       url,
        "field_id":  field_id,
        "expr":      expr,
        "settings":  settings,
        "error":     err,
    }

    if result and not err:
        entry.update({
            "grade":           result.get("grade"),
            "stage":           result.get("stage"),
            "status":          result.get("status"),
            "sharpe":          result.get("sharpe"),
            "fitness":         result.get("fitness"),
            "turnover":        result.get("turnover"),
            "returns":         result.get("returns"),
            "drawdown":        result.get("drawdown"),
            "margin":          result.get("margin"),
            "checks_pass":     result.get("checks_pass"),
            "checks_detail":   result.get("checks_detail"),
            "weight_max":      result.get("weight_max"),
            "sub_univ_sharpe": result.get("sub_univ_sharpe"),
            "self_corr":       result.get("self_corr"),
        })

    _log_entry(entry)


def log_end(total: int, succeeded: int):
    _log_entry({
        "type":      "end",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total":     total,
        "succeeded": succeeded,
        "failed":    total - succeeded,
    })