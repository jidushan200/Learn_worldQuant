"""
日志模块 —— 负责回测过程的终端打印 + JSONL 文件持久化
每天一个日志文件，格式为 {LOG_BASE_NAME}.{YYYYMMDD}.jsonl
支持多线程安全写入（使用 threading.Lock）
"""

import os
import json
import threading
from datetime import datetime
from setting import LOGS_DIR, LOG_BASE_NAME, BRAIN_URL_PREFIX

# ── 线程锁 & 全局日志路径缓存 ──────────────────────────────
_log_lock      = threading.Lock()        # 保证多线程写日志不冲突
_log_file_path = None                    # 缓存当天日志文件路径，避免重复解析


def _resolve_log_path() -> str:
    """
    确定今天的日志文件路径：
    - 如果 LOGS_DIR 下已有今天的文件 → 追加写入
    - 否则 → 新建一个
    """
    today = datetime.now().strftime("%Y%m%d")
    os.makedirs(LOGS_DIR, exist_ok=True)

    # 遍历目录，查找是否已有今天的日志文件
    for filename in os.listdir(LOGS_DIR):
        if filename.startswith(LOG_BASE_NAME) and today in filename:
            print(f"  📄 找到今日日志，追加写入: {filename}")
            return os.path.join(LOGS_DIR, filename)

    # 没有找到 → 新建
    filename = f"{LOG_BASE_NAME}.{today}.jsonl"
    print(f"  📄 新建今日日志: {filename}")
    return os.path.join(LOGS_DIR, filename)


def _get_log_path() -> str:
    """惰性获取日志路径（第一次调用时解析，之后直接返回缓存值）"""
    global _log_file_path
    if _log_file_path is None:
        _log_file_path = _resolve_log_path()
    return _log_file_path


def _fmt_ts() -> str:
    """返回带中文括号的时间戳，用于终端打印"""
    return f"【{datetime.now().strftime('%Y_%m_%d %H:%M:%S')}】"


def _format_grade(grade: str | None) -> str | None:
    """
    格式化 grade 字符串：
    "GOOD" → "Good"，"SUB_INDUSTRY" → "Sub Industry"
    空值 / 非字符串 → None
    """
    if not isinstance(grade, str) or not grade.strip():
        return None
    return grade.replace("_", " ").title()


# ═══════════════════════════════════════════════════════════
#  核心写入：先打印到终端，再追加到 JSONL 文件
# ═══════════════════════════════════════════════════════════

def _log_entry(obj: dict):
    """线程安全地写入一条日志：先终端打印，再写文件"""
    with _log_lock:
        _print_entry(obj)                  # 终端可视化
        with open(_get_log_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")   # 一行一条 JSON


def _print_entry(obj: dict):
    """
    根据日志类型（start / result / end）在终端打印格式化信息
    这里不写文件，只负责好看的输出
    """
    t   = obj.get("type")
    pad = " " * 12               # 统一缩进，让次级信息对齐

    # ── 回测开始 ──
    if t == "start":
        print(f"\n{'=' * 60}")
        print(f"  开始时间 : {obj['timestamp']}")
        print(f"  共 {obj['total']} 个 alpha 待回测")
        print(f"{'=' * 60}\n")

    # ── 单个 alpha 的回测结果 ──
    elif t == "result":
        index    = obj.get("index", 0)       # 当前第几个
        total    = obj.get("total", 0)        # 总共几个
        alpha_id = obj.get("alpha_id") or "—"
        expr     = obj.get("expr", "")
        error    = obj.get("error")

        # 第一行：序号 + alpha_id
        print(f"[{index:4d}/{total:4d}]  {alpha_id}  【Alpha_id】")
        print(f"{pad}expr      : {expr}")

        if error:
            # 回测失败，只打印错误
            print(f"{pad}error     : {error}")
        else:
            # ── 核心指标：Sharpe / Fitness / Turnover ──
            sharpe   = obj.get("sharpe")
            fitness  = obj.get("fitness")
            turnover = obj.get("turnover")
            returns  = obj.get("returns")
            drawdown = obj.get("drawdown")
            margin   = obj.get("margin")

            if None not in (sharpe, fitness, turnover):
                # turnover 如果 <=1 说明是小数形式，转成百分比
                to_pct = turnover * 100 if isinstance(turnover, (int, float)) and turnover <= 1 else turnover
                print(f"{pad}sharpe    : {sharpe:.2f}    fitness  : {fitness:.2f}    turnover : {to_pct:.1f}%")

            # ── 收益 / 回撤 / margin ──
            if returns is not None or drawdown is not None or margin is not None:
                ret_str = f"{returns * 100:.2f}%" if isinstance(returns, (int, float)) else "N/A"
                dd_str  = f"{drawdown * 100:.2f}%" if isinstance(drawdown, (int, float)) else "N/A"
                mg_str  = f"{margin:.6f}" if isinstance(margin, (int, float)) else "N/A"
                print(f"{pad}returns   : {ret_str}    drawdown : {dd_str}    margin   : {mg_str}")

            # ── Grade / Stage / Status ──
            grade  = _format_grade(obj.get("grade"))
            stage  = obj.get("stage")
            status = obj.get("status")
            if grade is not None or stage is not None or status is not None:
                print(f"{pad}grade     : {grade or 'N/A'}    stage    : {stage or 'N/A'}    status   : {status or 'N/A'}")

            # ── Checks 细项：权重上限 / 子宇宙 Sharpe / 自相关 ──
            weight_max      = obj.get("weight_max")
            sub_univ_sharpe = obj.get("sub_univ_sharpe")
            self_corr       = obj.get("self_corr")

            if weight_max      is not None:
                print(f"{pad}weight    : max={weight_max:.4f}")
            if sub_univ_sharpe is not None:
                print(f"{pad}sub-univ  : sharpe={sub_univ_sharpe:.2f}")
            if self_corr       is not None:
                print(f"{pad}self-corr : {self_corr:.2f}")

            # ── 年度表现表格 ──
            yearly = obj.get("yearly_stats")
            if yearly:
                print(f"{pad}┌─ 年度表现 {'─' * 58}")
                print(f"{pad}│ {'Year':<6}{'Sharpe':>8}{'Fitness':>9}{'Turnover':>10}{'Returns':>10}{'Drawdown':>10}{'Margin':>10}")
                print(f"{pad}│ {'─' * 62}")
                for y in yearly:
                    yr = y.get('year', '?')
                    sh = y.get('sharpe', 0) or 0
                    fi = y.get('fitness', 0) or 0
                    to = (y.get('turnover', 0) or 0) * 100          # 转百分比
                    rt = (y.get('returns', 0) or 0) * 100
                    dd = (y.get('drawdown', 0) or 0) * 100
                    mg = (y.get('margin', 0) or 0) * 10000          # 转万分比
                    print(f"{pad}│ {yr:<6}{sh:>8.2f}{fi:>9.2f}{to:>9.2f}%{rt:>9.2f}%{dd:>9.2f}%{mg:>9.2f}‱")
                print(f"{pad}└{'─' * 69}")

        # 每条结果末尾打印时间戳
        print(f"{pad}{_fmt_ts()}")
        print()

    # ── 回测结束汇总 ──
    elif t == "end":
        print(f"\n{'=' * 60}")
        print(f"  结束时间 : {obj['timestamp']}")
        print(f"  总计: {obj['total']}  ✅ 成功: {obj['succeeded']}  ❌ 失败: {obj['failed']}")
        print(f"{'=' * 60}\n")


# ═══════════════════════════════════════════════════════════
#  公开接口 —— 供 main.py 等模块调用
# ═══════════════════════════════════════════════════════════

def log_start(total: int):
    """记录一批回测的开始（打印 + 写文件）"""
    _log_entry({
        "type":      "start",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total":     total,
    })


def log_result(
    index:    int,                  # 当前序号（第几个）
    total:    int,                  # 这批总共几个
    alpha_id: str | None,          # 平台返回的 alpha ID
    field_id: str,                 # 用户自定义的因子标识名
    expr:     str,                 # alpha 表达式原文
    settings: dict | None,         # 回测参数（universe / delay / decay 等）
    result:   dict | None,         # 回测结果字典（sharpe / fitness / ...）
    err:      str | None,          # 如果出错，错误信息
):
    """记录单个 alpha 的回测结果"""
    # 拼接 Brain 平台的在线查看链接
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

    # 回测成功时，把所有指标塞进 entry
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
            "yearly_stats":    result.get("yearly_stats"),
        })

    _log_entry(entry)


def log_end(total: int, succeeded: int):
    """记录一批回测的结束汇总"""
    _log_entry({
        "type":      "end",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total":     total,
        "succeeded": succeeded,
        "failed":    total - succeeded,
    })