"""
Brain 平台回测：提交 alpha 并轮询等待结果
"""

import time
from time import sleep
from setting import MAX_WAIT_SEC, API_SIMULATION_URL, DEFAULT_SETTING
from http_utils import request_with_retry


def build_sim_payload(alpha: dict) -> dict:
    """
    将 {name, expr, setting} 格式的 alpha 转成提交给 Brain API 的 payload
    """
    expr = alpha["expr"]
    setting = alpha.get("setting", DEFAULT_SETTING)

    return {
        "type": "REGULAR",
        "settings": setting,
        "regular": expr,
    }


def submit_and_wait(sess, alpha: dict, max_wait_sec: int = MAX_WAIT_SEC) -> tuple:
    """
    提交 alpha 回测任务，并轮询直到结果返回。

    参数：
        sess:  已认证的 requests.Session
        alpha: {"name": str, "expr": str, "setting": dict}
              也兼容旧格式（直接传 payload dict 含 "regular" 键）

    返回：
        (alpha_id, error_msg, raw_json)
    """

    # ── 兼容新旧格式 ──
    if "regular" in alpha:
        payload = alpha
        label = alpha.get("regular", "")[:40]
    else:
        payload = build_sim_payload(alpha)
        label = alpha.get("name", alpha["expr"][:40])

    # ── 1) 提交回测任务 ──
    r = request_with_retry(sess, "POST", API_SIMULATION_URL, label=f"提交[{label}]", json=payload)

    if r is None:
        return None, "提交失败：重试耗尽仍未响应", None
    if r.status_code >= 400:
        return None, f"提交失败: {r.status_code} {r.text[:200]}", None

    # ── 2) 获取进度查询地址 ──
    progress_url = r.headers.get("Location")
    if not progress_url:
        return None, "响应缺少 Location", None

    # ── 3) 轮询直到完成或超时 ──
    elapsed = 0
    while elapsed < max_wait_sec:

        p = request_with_retry(sess, "GET", progress_url, label=f"轮询[{label}]")

        if p is None:
            return None, "轮询失败：重试耗尽仍无响应", None
        if p.status_code >= 400:
            return None, f"轮询失败: {p.status_code} {p.text[:200]}", None

        retry_after = float(p.headers.get("Retry-After", 0))

        if retry_after == 0:
            raw = p.json()
            alpha_id = raw.get("alpha")
            if not alpha_id:
                return None, "完成但 alpha 为空", raw
            print(f"  ✅ [{label}] 回测完成 → alpha_id={alpha_id}")
            return alpha_id, None, raw

        start = time.time()
        sleep(retry_after)
        elapsed += time.time() - start

    return None, f"超时：超过 {max_wait_sec} 秒", None