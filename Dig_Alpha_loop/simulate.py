import time
from time import sleep
import requests
from requests.exceptions import ConnectionError, ProxyError, Timeout
from setting import MAX_WAIT_SEC, MAX_RETRY

# 需要重试的网络层异常
_RETRYABLE = (ConnectionError, ProxyError, Timeout)


def _get_with_retry(sess: requests.Session, url: str) -> requests.Response:
    """
    带 429 + 网络异常重试的 GET 请求，复用于轮询阶段
    """
    r = None
    for attempt in range(1, MAX_RETRY + 1):
        try:
            r = sess.get(url, timeout=30)
        except _RETRYABLE as e:
            wait = 15 * attempt          # 网络抖动，逐步拉长等待
            print(f"  ⚠️  网络异常 (attempt {attempt}/{MAX_RETRY})，{wait}s 后重试: {e}")
            sleep(wait)
            continue

        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 10))
            print(f"  ⚠️  轮询限流 (attempt {attempt}/{MAX_RETRY})，等待 {wait} 秒...")
            sleep(wait)
            continue

        return r

    return r   # 超出重试次数，返回最后一次响应（可能为 None）


def submit_and_wait(
    sess: requests.Session,
    alpha_payload: dict,
    max_wait_sec: int = MAX_WAIT_SEC
) -> tuple:
    """
    提交 alpha 回测任务，并轮询直到结果返回
    """

    # ── 1) 提交回测任务 ───────────────────────────────────────
    r = None
    for attempt in range(1, MAX_RETRY + 1):
        try:
            r = sess.post(
                url="https://api.worldquantbrain.com/simulations",
                json=alpha_payload,
                timeout=30
            )
        except _RETRYABLE as e:
            wait = 15 * attempt
            print(f"  ⚠️  提交网络异常 (attempt {attempt}/{MAX_RETRY})，{wait}s 后重试: {e}")
            sleep(wait)
            continue

        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 10))
            print(f"  ⚠️  提交限流 (attempt {attempt}/{MAX_RETRY})，等待 {wait} 秒...")
            sleep(wait)
            continue

        break   # 非限流、非异常，跳出

    if r is None:
        return None, "提交失败：重试耗尽仍未响应", None
    if r.status_code >= 400:
        return None, f"提交失败: {r.status_code} {r.text}", None

    # ── 2) 获取进度查询地址 ───────────────────────────────────
    progress_url = r.headers.get("Location")
    if not progress_url:
        return None, "响应缺少 Location", None

    # ── 3) 轮询直到完成或超时 ─────────────────────────────────
    elapsed = 0
    while elapsed < max_wait_sec:

        p = _get_with_retry(sess, progress_url)

        if p is None:
            return None, "轮询失败：重试耗尽仍无响应", None
        if p.status_code >= 400:
            return None, f"轮询失败: {p.status_code} {p.text}", None

        retry_after = float(p.headers.get("Retry-After", 0))

        if retry_after == 0:
            raw = p.json()
            alpha_id = raw.get("alpha")
            if not alpha_id:
                return None, "完成但 alpha 为空", raw
            return alpha_id, None, raw

        start = time.time()
        sleep(retry_after)
        elapsed += time.time() - start

    return None, f"超时：超过 {max_wait_sec} 秒", None