import requests


def get_alpha_result(
    sess: requests.Session,
    alpha_id: str
) -> tuple:
    """
    查询 alpha 回测结果，提取核心指标，并判断是否通过筛选条件

    Args:
        sess:     已认证的 requests.Session
        alpha_id: 由 simulate.py 返回的 alpha id

    Returns:
        tuple: (result_dict, err)
               成功时 result_dict 包含所有指标，err 为 None
               失败时 result_dict 为 None，err 为错误信息
    """

    # ── 1) 请求 alpha 详情 ────────────────────────────────────
    resp = sess.get(
        url=f"https://api.worldquantbrain.com/alphas/{alpha_id}",
        timeout=30
    )
    if resp.status_code >= 400:
        return None, f"查询失败: {resp.status_code} {resp.text}"

    data = resp.json()

    # ── 2) 检查 is 字段是否存在 ───────────────────────────────
    # is 字段包含 sharpe / fitness / turnover 等核心指标
    is_data = data.get("is")
    if not is_data:
        return None, "返回数据中缺少 is 字段"

    # ── 3) 提取核心指标 ───────────────────────────────────────
    sharpe   = is_data.get("sharpe")    # 夏普率
    fitness  = is_data.get("fitness")   # 适应度
    turnover = is_data.get("turnover")  # 换手率
    returns  = is_data.get("returns")   # 年化收益

    # ── 4) checks 全部通过才算合规 ───────────────────────────
    # checks 是平台自动执行的一系列合规检查，结果为 PASS / FAIL
    # 使用 checks 统一判断，避免与 criteria_pass 重复
    checks = data.get("checks", [])
    checks_pass = all(c.get("result") == "PASS" for c in checks)

    # ── 5) 综合判断是否通过 ───────────────────────────────────
    overall_pass = (
        checks_pass                             and  # 平台合规检查全通过
        sharpe   is not None and sharpe   > 1.25 and  # 夏普率 > 1.25
        fitness  is not None and fitness  > 1.0  and  # 适应度 > 1.0
        turnover is not None and 0.01 <= turnover <= 0.7  # 换手率在合理范围
    )

    # ── 6) 整理返回结果 ───────────────────────────────────────
    result = {
        "alpha_id":     alpha_id,
        "expr":         data.get("regular", ""),  # alpha 表达式
        "sharpe":       sharpe,
        "fitness":      fitness,
        "turnover":     turnover,
        "returns":      returns,
        "checks_pass":  checks_pass,
        "overall_pass": overall_pass,
        "error":        None,
    }

    return result, None