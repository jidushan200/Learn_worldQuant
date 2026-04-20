import os
import json
import threading
from datetime import datetime
from setting import LOGS_DIR, LOG_BASE_NAME, BRAIN_URL_PREFIX

_log_lock = threading.Lock()
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
    """返回带括号的时间戳，如 【2026_04_20 14:24:29】"""
    return f"【{datetime.now().strftime('%Y_%m_%d %H:%M:%S')}】"


def _build_result_line(obj: dict) -> str:
    """
    构建非标准 JSONL 行：首字段为 alpha_id 裸值（无 key）
    例：{"6f3a2e91","expr":"rank(...)","sharpe":1.52,"fitness":1.23,"turnover":0.2840}
    """
    alpha_id = obj.get("alpha_id") or "—"
    expr     = (obj.get("expr") or "").replace('"', '\\"')
    error    = obj.get("error")

    if error:
        return f'{{"{alpha_id}","expr":"{expr}","error":"{error.replace(chr(34), chr(92)+chr(34))}"}}'

    parts = [f'"{alpha_id}"', f'"expr":"{expr}"']

    sharpe   = obj.get("sharpe")
    fitness  = obj.get("fitness")
    turnover = obj.get("turnover")

    if sharpe   is not None: parts.append(f'"sharpe":{sharpe}')
    if fitness  is not None: parts.append(f'"fitness":{fitness}')
    if turnover is not None: parts.append(f'"turnover":{round(turnover, 4)}')

    weight_max      = obj.get("weight_max")
    sub_univ_sharpe = obj.get("sub_univ_sharpe")
    self_corr       = obj.get("self_corr")

    if weight_max      is not None: parts.append(f'"weight_max":{round(weight_max, 4)}')
    if sub_univ_sharpe is not None: parts.append(f'"sub_univ_sharpe":{round(sub_univ_sharpe, 4)}')
    if self_corr       is not None: parts.append(f'"self_corr":{round(self_corr, 4)}')

    return "{" + ",".join(parts) + "}"


def _log_entry(obj: dict):
    """将日志写入文件并打印到控制台（线程安全）"""
    with _log_lock:
        _print_entry(obj)
        with open(_get_log_path(), "a", encoding="utf-8") as f:
            if obj.get("type") == "result":
                f.write(_build_result_line(obj) + "\n")
                f.write(_fmt_ts() + "\n")
            else:
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _print_entry(obj: dict):
    """按 type 格式化打印到控制台"""
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

            if None not in (sharpe, fitness, turnover):
                # turnover API 返回小数（如 0.284），乘 100 转成百分比显示
                to_pct = turnover * 100 if isinstance(turnover, (int, float)) and turnover <= 1 else turnover
                print(f"{pad}sharpe    : {sharpe:.2f}    fitness  : {fitness:.2f}    turnover : {to_pct:.1f}%")

            # 可选指标：有值才打印，没有整行跳过
            weight_max      = obj.get("weight_max")
            sub_univ_sharpe = obj.get("sub_univ_sharpe")
            self_corr       = obj.get("self_corr")

            if weight_max      is not None: print(f"{pad}weight    : max={weight_max:.4f}")
            if sub_univ_sharpe is not None: print(f"{pad}sub-univ  : sharpe={sub_univ_sharpe:.2f}")
            if self_corr       is not None: print(f"{pad}self-corr : {self_corr:.2f}")

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
            "sharpe":          result.get("sharpe"),
            "fitness":         result.get("fitness"),
            "turnover":        result.get("turnover"),
            "returns":         result.get("returns"),
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