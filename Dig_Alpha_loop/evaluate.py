"""
回测结果查询模块 —— 从 WorldQuant Brain API 获取 alpha 回测结果
包含两个核心功能：
1. get_alpha_result()  : 查询单个 alpha 的整体回测指标
2. _fetch_yearly_stats(): 拉取按年度拆分的 IS 统计数据
"""

import requests
from time import sleep
from requests.exceptions import ConnectionError, ProxyError, Timeout
from setting import MAX_RETRY

# 可重试的网络异常类型（连接失败 / 代理错误 / 超时）
_RETRYABLE = (ConnectionError, ProxyError, Timeout)
_MAX_RETRY = MAX_RETRY


# ═══════════════════════════════════════════════════════════
#  拉取年度统计数据
# ═══════════════════════════════════════════════════════════

def _fetch_yearly_stats(sess: requests.Session, alpha_id: str) -> list[dict] | None:
    """
    调用 /alphas/{id}/recordsets/yearly-stats 接口
    返回每年的 sharpe / fitness / turnover / returns / drawdown / margin
    格式: [{"year":"2019","sharpe":-0.56,"fitness":-0.17,...}, ...]
    失败时返回 None

    注意：回测刚完成时年度聚合可能还没ready，所以首次失败会延迟重试
    """
    url = f"https://api.worldquantbrain.com/alphas/{alpha_id}/recordsets/yearly-stats"

    # ── 首次调用前等待几秒，让平台完成年度聚合 ──
    sleep(3)

    resp = None
    for attempt in range(1, _MAX_RETRY + 1):
        try:
            resp = sess.get(url, timeout=30)
        except _RETRYABLE as e:
            wait = 15 * attempt
            print(f"  ⚠️  yearly-stats 网络异常 (attempt {attempt}/{_MAX_RETRY})，{wait}s 后重试: {e}")
            sleep(wait)
            continue

        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", 10))
            print(f"  ⚠️  yearly-stats 限流 (attempt {attempt}/{_MAX_RETRY})，等待 {wait} 秒...")
            sleep(wait)
            continue

        if resp.status_code >= 400:
            # 非限流的错误（如 404），可能是数据还没ready，等几秒重试
            if attempt < _MAX_RETRY:
                wait = 5 * attempt
                print(f"  ⚠️  yearly-stats HTTP {resp.status_code} (attempt {attempt}/{_MAX_RETRY})，{wait}s 后重试")
                sleep(wait)
                continue
            else:
                print(f"  ❌ yearly-stats 最终失败: HTTP {resp.status_code}, alpha_id={alpha_id}")
                return None

        # ── 请求成功，尝试解析 ──
        try:
            data = resp.json()
            props = [p['name'] for p in data['schema']['properties']]
            records = [dict(zip(props, row)) for row in data['records']]

            if records:
                print(f"  📊 yearly-stats 获取成功: {len(records)} 年数据, alpha_id={alpha_id}")
                return records
            else:
                # records 为空，可能数据还没聚合完
                if attempt < _MAX_RETRY:
                    wait = 5 * attempt
                    print(f"  ⚠️  yearly-stats 返回空 (attempt {attempt}/{_MAX_RETRY})，{wait}s 后重试")
                    sleep(wait)
                    continue
                else:
                    print(f"  ⚠️  yearly-stats 最终返回空, alpha_id={alpha_id}")
                    return None

        except Exception as e:
            if attempt < _MAX_RETRY:
                wait = 5 * attempt
                print(f"  ⚠️  yearly-stats 解析失败 (attempt {attempt}/{_MAX_RETRY})，{wait}s 后重试: {e}")
                sleep(wait)
                continue
            else:
                print(f"  ❌ yearly-stats 解析最终失败: {e}, alpha_id={alpha_id}")
                return None

    # 超出重试次数
    print(f"  ❌ yearly-stats 重试耗尽, alpha_id={alpha_id}")
    return None


# ═══════════════════════════════════════════════════════════
#  查询 alpha 回测结果（主接口）
# ═══════════════════════════════════════════════════════════

def get_alpha_result(
    sess: requests.Session,
    alpha_id: str
) -> tuple:
    """
    查询单个 alpha 的回测结果，返回 (result_dict, error_str)
    - 成功: (result_dict, None)
    - 失败: (None, "错误描述")

    result_dict 包含:
    - 核心指标: sharpe, fitness, turnover, returns, drawdown, margin
    - 状态信息: grade, stage, status
    - Checks 汇总: checks_pass(bool), checks_detail(list)
    - Checks 细项: weight_max, sub_univ_sharpe, self_corr
    - 年度统计: yearly_stats
    """

    url = f"https://api.worldquantbrain.com/alphas/{alpha_id}"
    resp = None

    # ── 带重试的 HTTP 请求 ──
    for attempt in range(1, _MAX_RETRY + 1):
        try:
            resp = sess.get(url=url, timeout=30)
        except _RETRYABLE as e:
            wait = 15 * attempt
            print(f"  ⚠️  evaluate 网络异常 (attempt {attempt}/{_MAX_RETRY})，{wait}s 后重试: {e}")
            sleep(wait)
            continue

        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", 10))
            print(f"  ⚠️  evaluate 限流 (attempt {attempt}/{_MAX_RETRY})，等待 {wait} 秒...")
            sleep(wait)
            continue

        break

    # ── 请求失败兜底 ──
    if resp is None:
        return None, "查询失败：重试耗尽仍无响应"
    if resp.status_code >= 400:
        return None, f"查询失败: {resp.status_code} {resp.text}"

    data = resp.json()

    # ── 提取 IS（in-sample）指标 ──
    is_data = data.get("is")
    if not is_data:
        return None, "返回数据中缺少 is 字段"

    # 表达式原文存在 data["regular"]["code"] 中
    regular_data = data.get("regular") or {}
    expr = regular_data.get("code", "")

    # 核心数值指标
    sharpe   = is_data.get("sharpe")
    fitness  = is_data.get("fitness")
    turnover = is_data.get("turnover")
    returns  = is_data.get("returns")
    drawdown = is_data.get("drawdown")
    margin   = is_data.get("margin")

    # alpha 状态信息
    grade  = data.get("grade")
    stage  = data.get("stage")
    status = data.get("status")

    # ── 解析 Checks（平台合规检查项） ──
    checks = is_data.get("checks", [])

    checks_pass = all(c.get("result") == "PASS" for c in checks if c.get("result") != "PENDING")

    checks_detail = [
        {
            "name":    c.get("name"),
            "result":  c.get("result"),
            "value":   c.get("value"),
            "limit":   c.get("limit"),
            "message": c.get("message"),
        }
        for c in checks
    ]

    # ── 从 Checks 中提取特定指标 ──
    weight_max      = None
    sub_univ_sharpe = None
    self_corr       = None

    for c in checks:
        name = (c.get("name") or "").upper()
        val  = c.get("value")

        if "WEIGHT" in name:
            weight_max = val
        elif "SUB_UNIVERSE" in name or "SUBUNIVERSE" in name:
            sub_univ_sharpe = val
        elif "SELF" in name and "CORRELATION" in name:
            self_corr = val

    # ── 拉取年度统计（补充维度，用于分析跨年稳定性） ──
    yearly_stats = _fetch_yearly_stats(sess, alpha_id)

    # ── 组装结果字典 ──
    result = {
        "alpha_id":        alpha_id,
        "expr":            expr,
        "grade":           grade,
        "stage":           stage,
        "status":          status,
        "sharpe":          sharpe,
        "fitness":         fitness,
        "turnover":        turnover,
        "returns":         returns,
        "drawdown":        drawdown,
        "margin":          margin,
        "checks_pass":     checks_pass,
        "checks_detail":   checks_detail,
        "weight_max":      weight_max,
        "sub_univ_sharpe": sub_univ_sharpe,
        "self_corr":       self_corr,
        "yearly_stats":    yearly_stats,
        "error":           None,
    }

    return result, None