import time
import requests


def submit_and_wait(
    sess: requests.Session,
    alpha_payload: dict,
    max_wait_sec: int = 1800
):
    """提交 simulation 并轮询直到结束，返回 (alpha_id, err, raw_json)。"""

    # 1) 提交仿真任务
    r = sess.post(
        "https://api.worldquantbrain.com/simulations",
        json=alpha_payload,
        timeout=30
    )
    if r.status_code >= 400:
        return None, f"提交失败: {r.status_code} {r.text}", None

    # 2) 从响应头拿进度查询地址
    progress_url = r.headers.get("Location")
    if not progress_url:
        return None, "响应缺少 Location", None

    t0 = time.time()

    # 3) 按 Retry-After 轮询，直到完成或超时
    while True:
        p = sess.get(progress_url, timeout=30)
        if p.status_code >= 400:
            return None, f"轮询失败: {p.status_code} {p.text}", None

        retry_after = float(p.headers.get("Retry-After", 0))

        # Retry-After=0 代表计算完成
        if retry_after == 0:
            raw = p.json()
            alpha_id = raw.get("alpha")
            if not alpha_id:
                return None, "完成但 alpha 为空", raw
            return alpha_id, None, raw

        if time.time() - t0 > max_wait_sec:
            return None, "轮询超时", None

        time.sleep(retry_after)