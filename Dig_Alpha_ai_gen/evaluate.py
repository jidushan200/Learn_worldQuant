import requests


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

    resp = sess.get(
        url=f"https://api.worldquantbrain.com/alphas/{alpha_id}",
        timeout=30
    )
    if resp.status_code >= 400:
        return None, f"查询失败: {resp.status_code} {resp.text}"

    data = resp.json()

    is_data = data.get("is")
    if not is_data:
        return None, "返回数据中缺少 is 字段"

    sharpe   = is_data.get("sharpe")
    fitness  = is_data.get("fitness")
    turnover = is_data.get("turnover")
    returns  = is_data.get("returns")

    checks = data.get("checks", [])
    checks_pass   = all(c.get("result") == "PASS" for c in checks)
    checks_detail = [
        {"name": c.get("name"), "result": c.get("result"), "value": c.get("value")}
        for c in checks
    ]

    # ── 可选指标：按 check 名称模糊匹配提取 ──────────────────
    # ⚠️ check 名称以实际 API 返回为准，若对不上可在此调整关键词
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
        elif "SELF" in name and "CORR" in name:
            self_corr = val

    result = {
        "alpha_id":        alpha_id,
        "expr":            data.get("regular", ""),
        "sharpe":          sharpe,
        "fitness":         fitness,
        "turnover":        turnover,
        "returns":         returns,
        "checks_pass":     checks_pass,
        "checks_detail":   checks_detail,
        "weight_max":      weight_max,
        "sub_univ_sharpe": sub_univ_sharpe,
        "self_corr":       self_corr,
        "error":           None,
    }

    return result, None