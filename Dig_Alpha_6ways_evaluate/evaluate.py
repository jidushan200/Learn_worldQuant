import requests


def get_probe_result(
    sess: requests.Session,
    alpha_id: str,
    probe_type: str,
    expr: str,
) -> tuple:
    """
    查询探针回测结果，只提取 Long Count / Short Count

    Args:
        sess:       已认证的 requests.Session
        alpha_id:   由 simulate.py 返回的 alpha id
        probe_type: 探针类型标识（如 probe1_raw / probe3_freq_N22）
        expr:       探针表达式原文（用于日志）

    Returns:
        tuple: (result_dict, err)
               成功时 result_dict 包含 long_count / short_count，err 为 None
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
    is_data = data.get("is")
    if not is_data:
        return None, "返回数据中缺少 is 字段"

    # ── 3) 提取 Long Count / Short Count ─────────────────────
    long_count  = is_data.get("longCount")
    short_count = is_data.get("shortCount")

    if long_count is None and short_count is None:
        return None, "is 字段中缺少 longCount / shortCount"

    # ── 4) 整理返回结果 ───────────────────────────────────────
    result = {
        "alpha_id":    alpha_id,
        "probe_type":  probe_type,
        "expr":        expr,
        "long_count":  long_count,
        "short_count": short_count,
        "error":       None,
    }

    return result, None