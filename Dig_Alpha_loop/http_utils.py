"""
公共 HTTP 请求工具 —— 统一处理重试、限流、网络异常
"""

import requests
from time import sleep
from requests.exceptions import ConnectionError, ProxyError, Timeout
from setting import MAX_RETRY

_RETRYABLE = (ConnectionError, ProxyError, Timeout)

_DEFAULT_HEADERS = {
    "accept": "application/json;version=2.0",
}


def _merge_headers(kwargs: dict) -> dict:
    """将默认 headers 与调用方传入的 headers 合并（调用方优先）"""
    headers = dict(_DEFAULT_HEADERS)
    if "headers" in kwargs:
        headers.update(kwargs["headers"])
    kwargs["headers"] = headers
    return kwargs


def request_once(
    sess: requests.Session,
    method: str,
    url: str,
    label: str = "",
    **kwargs
) -> requests.Response | None:
    """
    单次 HTTP 请求，仅捕获网络异常返回 None，不重试。
    """
    kwargs.setdefault("timeout", 30)
    kwargs = _merge_headers(kwargs)
    try:
        return sess.request(method, url, **kwargs)
    except _RETRYABLE as e:
        print(f"  ⚠️  {label} 网络异常: {e}")
        return None


def request_with_retry(
    sess: requests.Session,
    method: str,
    url: str,
    label: str = "",
    **kwargs
) -> requests.Response | None:
    """
    带重试的 HTTP 请求（处理网络异常 + 429 限流）
    """
    kwargs.setdefault("timeout", 30)
    kwargs = _merge_headers(kwargs)
    r = None

    for attempt in range(1, MAX_RETRY + 1):
        try:
            r = sess.request(method, url, **kwargs)
        except _RETRYABLE as e:
            wait = 15 * attempt
            print(f"  ⚠️  {label} 网络异常 (attempt {attempt}/{MAX_RETRY})，{wait}s 后重试: {e}")
            sleep(wait)
            continue

        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 10))
            print(f"  ⚠️  {label} 限流 (attempt {attempt}/{MAX_RETRY})，等待 {wait} 秒...")
            sleep(wait)
            continue

        return r

    return r