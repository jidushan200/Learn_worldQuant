"""
回测结果查询模块
"""

from time import sleep
from setting import MAX_RETRY, API_ALPHA_URL, API_YEARLY_STATS_URL
from http_utils import request_with_retry, request_once


def _fetch_yearly_stats(sess, alpha_id: str) -> list[dict] | None:
    """外层循环统一控制重试，总计最多 MAX_RETRY 次请求。"""
    url = API_YEARLY_STATS_URL.format(alpha_id=alpha_id)
    sleep(3)

    for attempt in range(1, MAX_RETRY + 1):
        resp = request_once(sess, "GET", url, label="yearly-stats")

        if resp is None:
            if attempt < MAX_RETRY:
                wait = 5 * attempt
                print(f"  ⚠️  yearly-stats 网络异常 (attempt {attempt}/{MAX_RETRY})，{wait}s 后重试")
                sleep(wait)
                continue
            else:
                print(f"  ❌ yearly-stats 最终失败: 网络异常, alpha_id={alpha_id}")
                return None

        if resp.status_code >= 400:
            if attempt < MAX_RETRY:
                wait = 5 * attempt
                print(f"  ⚠️  yearly-stats HTTP {resp.status_code} (attempt {attempt}/{MAX_RETRY})，{wait}s 后重试")
                sleep(wait)
                continue
            else:
                print(f"  ❌ yearly-stats 最终失败: HTTP {resp.status_code}, alpha_id={alpha_id}")
                return None

        try:
            data = resp.json()
            props = [p['name'] for p in data['schema']['properties']]
            records = [dict(zip(props, row)) for row in data['records']]

            if records:
                print(f"  📊 yearly-stats 获取成功: {len(records)} 年数据, alpha_id={alpha_id}")
                return records
            else:
                if attempt < MAX_RETRY:
                    wait = 5 * attempt
                    print(f"  ⚠️  yearly-stats 返回空 (attempt {attempt}/{MAX_RETRY})，{wait}s 后重试")
                    sleep(wait)
                    continue
                else:
                    print(f"  ⚠️  yearly-stats 最终返回空, alpha_id={alpha_id}")
                    return None

        except Exception as e:
            if attempt < MAX_RETRY:
                wait = 5 * attempt
                print(f"  ⚠️  yearly-stats 解析失败 (attempt {attempt}/{MAX_RETRY})，{wait}s 后重试: {e}")
                sleep(wait)
                continue
            else:
                print(f"  ❌ yearly-stats 解析最终失败: {e}, alpha_id={alpha_id}")
                return None

    print(f"  ❌ yearly-stats 重试耗尽, alpha_id={alpha_id}")
    return None


def get_alpha_result(sess, alpha_id: str) -> tuple:
    url = API_ALPHA_URL.format(alpha_id=alpha_id)

    resp = request_with_retry(sess, "GET", url, label="evaluate")

    if resp is None:
        return None, "查询失败：重试耗尽仍无响应"
    if resp.status_code >= 400:
        return None, f"查询失败: {resp.status_code} {resp.text}"

    data = resp.json()

    is_data = data.get("is")
    if not is_data:
        return None, "返回数据中缺少 is 字段"

    regular_data = data.get("regular") or {}
    expr = regular_data.get("code", "")

    sharpe   = is_data.get("sharpe")
    fitness  = is_data.get("fitness")
    turnover = is_data.get("turnover")
    returns  = is_data.get("returns")
    drawdown = is_data.get("drawdown")
    margin   = is_data.get("margin")

    grade  = data.get("grade")
    stage  = data.get("stage")
    status = data.get("status")

    # ---------- checks：完整保留原始数组 ----------
    checks = is_data.get("checks", [])

    # 便捷布尔值：是否全部通过（忽略 PENDING 和 WARNING）
    checks_pass = all(
        c.get("result") in ("PASS", "PENDING", "WARNING")
        for c in checks
    )

    # 统计各状态数量，方便日志输出
    fail_checks = [c for c in checks if c.get("result") == "FAIL"]
    warn_checks = [c for c in checks if c.get("result") == "WARNING"]
    pending_checks = [c for c in checks if c.get("result") == "PENDING"]

    # 提取匹配的比赛信息
    matched_competitions = []
    for c in checks:
        if c.get("name") == "MATCHES_COMPETITION" and c.get("result") == "PASS":
            matched_competitions = c.get("competitions", [])
            break

    yearly_stats = _fetch_yearly_stats(sess, alpha_id)

    result = {
        "alpha_id":             alpha_id,
        "expr":                 expr,
        "grade":                grade,
        "stage":                stage,
        "status":               status,
        "sharpe":               sharpe,
        "fitness":              fitness,
        "turnover":             turnover,
        "returns":              returns,
        "drawdown":             drawdown,
        "margin":               margin,
        "checks_pass":          checks_pass,
        "checks":               checks,          # 完整原始 checks 数组
        "fail_checks":          fail_checks,      # FAIL 项列表
        "warn_checks":          warn_checks,      # WARNING 项列表
        "pending_checks":       pending_checks,   # PENDING 项列表
        "matched_competitions": matched_competitions,
        "yearly_stats":         yearly_stats,
        "error":                None,
    }

    return result, None