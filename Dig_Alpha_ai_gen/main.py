import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from auth_client import create_authenticated_session
from simulate import submit_and_wait
from evaluate import get_alpha_result
from logger import log_start, log_result, log_end
from generate_web import generate_web
from setting import (
    ALPHAS_FILE, SIMULATION_SETTINGS,
    MAX_WAIT_SEC, SESSION_REFRESH_INTERVAL, MAX_CONCURRENT
)

_thread_local = threading.local()


def _load_alpha_list() -> list[dict]:
    with open(ALPHAS_FILE, "r", encoding="utf-8") as f:
        alphas = json.load(f)
    print(f"读取到 {len(alphas)} 个 AI 生成 alpha\n")

    alpha_list = []
    for item in alphas:
        name     = item["name"]
        expr     = item["expr"]
        custom   = item.get("setting", {})
        settings = {**SIMULATION_SETTINGS, **custom}

        payload = {
            "type":     "REGULAR",
            "settings": settings,
            "regular":  expr,
        }

        alpha_list.append({
            "field_id": name,
            "payload":  payload,
        })

    return alpha_list


def _get_session(max_retries: int = 3, retry_delay: float = 5.0) -> object:
    need_new = (
        not hasattr(_thread_local, "sess")
        or _thread_local.sess is None
        or time.time() - _thread_local.session_start > SESSION_REFRESH_INTERVAL
    )
    if need_new:
        last_err = None
        for attempt in range(1, max_retries + 1):
            try:
                sess, status = create_authenticated_session()
                _thread_local.sess          = sess
                _thread_local.session_start = time.time()
                print(f"  🔑 [线程 {threading.current_thread().name}] 认证成功: {status}")
                last_err = None
                break
            except Exception as e:
                last_err = e
                print(f"  ⚠️  [线程 {threading.current_thread().name}] 认证失败 (第 {attempt}/{max_retries} 次): {e}")
                if attempt < max_retries:
                    time.sleep(retry_delay)
        if last_err:
            raise last_err

    return _thread_local.sess


def _process_one(item: dict, index: int, total: int) -> dict:
    field_id = item["field_id"]
    payload  = item["payload"]
    expr     = payload["regular"]
    settings = payload["settings"]

    try:
        sess = _get_session()
    except Exception as e:
        err = f"认证失败: {e}"
        log_result(index, total, None, field_id, expr, settings, None, err)
        return {"alpha_id": None, "field_id": field_id, "expr": expr, "error": err}

    alpha_id, err, _ = submit_and_wait(
        sess=sess,
        alpha_payload=payload,
        max_wait_sec=MAX_WAIT_SEC
    )
    if err:
        log_result(index, total, None, field_id, expr, settings, None, err)
        return {"alpha_id": None, "field_id": field_id, "expr": expr, "error": err}

    result, err = get_alpha_result(sess=sess, alpha_id=alpha_id)
    if err:
        log_result(index, total, alpha_id, field_id, expr, settings, None, err)
        return {"alpha_id": alpha_id, "field_id": field_id, "expr": expr, "error": err}

    log_result(index, total, alpha_id, field_id, expr, settings, result, None)
    result["field_id"] = field_id
    result["expr"]     = expr
    return result


def main():
    alpha_list = _load_alpha_list()
    total      = len(alpha_list)
    log_start(total)

    all_results  = []
    results_lock = threading.Lock()

    with ThreadPoolExecutor(
        max_workers=MAX_CONCURRENT,
        thread_name_prefix="sim"
    ) as executor:

        futures = {
            executor.submit(_process_one, item, i, total): i
            for i, item in enumerate(alpha_list, 1)
        }

        for future in as_completed(futures):
            result = future.result()
            with results_lock:
                all_results.append(result)

    succeeded = sum(1 for r in all_results if r.get("alpha_id"))
    log_end(total, succeeded)
    generate_web()


if __name__ == "__main__":
    main()