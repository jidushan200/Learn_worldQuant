import time
from time import sleep
import requests
from setting import MAX_WAIT_SEC, MAX_RETRY


def _get_with_retry(sess: requests.Session, url: str) -> requests.Response:
    """
    带 429 重试的 GET 请求，复用于轮询阶段
    遇到限流时自动等待 Retry-After 秒后重试，最多重试 MAX_RETRY 次

    Args:
        sess: 已认证的 requests.Session
        url:  请求地址

    Returns:
        requests.Response: 最后一次请求的响应
    """
    r = None
    for _ in range(MAX_RETRY):
        r = sess.get(url, timeout=30)

        if r.status_code == 429:
            # 服务端限流，按 Retry-After 等待，默认 10 秒
            wait = int(r.headers.get("Retry-After", 10))
            print(f"  ⚠️  轮询限流，等待 {wait} 秒...")
            sleep(wait)
            continue  # 重试

        # 非限流，直接返回
        return r

    # 超出重试次数，返回最后一次响应，由上层判断
    return r


def submit_and_wait(
    sess: requests.Session,
    alpha_payload: dict,
    max_wait_sec: int = MAX_WAIT_SEC
) -> tuple:
    """
    提交 alpha 回测任务，并轮询直到结果返回

    Args:
        sess:          已认证的 requests.Session
        alpha_payload: 要提交的 alpha payload（来自 build_alphas.py）
        max_wait_sec:  最长等待秒数，超时则放弃

    Returns:
        tuple: (alpha_id, err, raw)
               成功时 alpha_id 有值，err 为 None
               失败时 alpha_id 为 None，err 为错误信息
    """

    # ── 1) 提交回测任务，遇到 429 限流则重试 ──────────────────────
    r = None
    for attempt in range(1, MAX_RETRY + 1):
        r = sess.post(
            url="https://api.worldquantbrain.com/simulations",
            json=alpha_payload,
            timeout=30
        )

        if r.status_code == 429:
            # 服务端限流，按 Retry-After 等待后重试
            wait = int(r.headers.get("Retry-After", 10))
            print(f"  ⚠️  提交限流 (attempt {attempt}/{MAX_RETRY})，等待 {wait} 秒...")
            sleep(wait)
            continue

        # 非限流，跳出重试循环
        break

    # 拆开判断，避免 r 为 None 时直接调用 .status_code 引发 AttributeError
    if r is None:
        return None, "提交失败：重试耗尽仍未响应", None
    if r.status_code >= 400:
        return None, f"提交失败: {r.status_code} {r.text}", None

    # ── 2) 从响应头获取进度查询地址 ──────────────────────────────
    progress_url = r.headers.get("Location")
    if not progress_url:
        return None, "响应缺少 Location", None

    # ── 3) 轮询进度，直到完成或超时 ──────────────────────────────
    elapsed = 0
    while elapsed < max_wait_sec:

        # 使用带重试的 GET，防止轮询阶段也触发限流
        p = _get_with_retry(sess, progress_url)

        if p is None or p.status_code >= 400:
            return None, f"轮询失败: {p.status_code} {p.text}", None

        retry_after = float(p.headers.get("Retry-After", 0))

        # Retry-After == 0 表示计算已完成
        if retry_after == 0:
            raw = p.json()
            alpha_id = raw.get("alpha")
            if not alpha_id:
                return None, "完成但 alpha 为空", raw
            return alpha_id, None, raw

        # 用实际耗时更新 elapsed，比直接加 retry_after 更准确
        start = time.time()
        sleep(retry_after)
        elapsed += time.time() - start

    return None, f"超时：超过 {max_wait_sec} 秒", None