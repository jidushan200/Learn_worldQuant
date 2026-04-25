import requests
from time import sleep
from requests.exceptions import ConnectionError, ProxyError, Timeout

_RETRYABLE = (ConnectionError, ProxyError, Timeout)
_MAX_RETRY = 5


def get_alpha_result(
    sess: requests.Session,
    alpha_id: str
) -> tuple:
    """
    查询 alpha 回测结果，提取平台返回的全部指标，不做本地审批

    Args:
        sess:     已认证的 requests.Session
        alpha_id: 由 simulate.py 返回的 alpha id

    Returns:
        tuple: (result_dict, err)
    """

    url = f"https://api.worldquantbrain.com/alphas/{alpha_id}"
    resp = None

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

    checks = is_data.get("checks", [])
    checks_pass = all(c.get("result") == "PASS" for c in checks if c.get("result") != "PENDING")
    checks_detail = [
        {
            "name": c.get("name"),
            "result": c.get("result"),
            "value": c.get("value"),
            "limit": c.get("limit"),
            "message": c.get("message"),
        }
        for c in checks
    ]

    # ── 可选指标：按 check 名称提取 ──────────────────────────
    weight_max      = None
    sub_univ_sharpe = None
    self_corr       = None

    for c in checks:
        name   = (c.get("name") or "").upper()
        result = c.get("result")
        val    = c.get("value")

        if "WEIGHT" in name:
            weight_max = val
        elif "SUB_UNIVERSE" in name or "SUBUNIVERSE" in name:
            sub_univ_sharpe = val
        elif "SELF" in name and "CORRELATION" in name:
            self_corr = val

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
        "error":           None,
    }

    return result, None