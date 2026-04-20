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
    OUTPUT_ALL, OUTPUT_PASSED,
    MAX_WAIT_SEC, SESSION_REFRESH_INTERVAL, MAX_CONCURRENT,
    BRAIN_URL_PREFIX
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
        settings = item.get("settings", SIMULATION_SETTINGS)

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


def _get_session() -> object:
    need_new = (
        not hasattr(_thread_local, "sess")
        or _thread_local.sess is None
        or time.time() - _thread_local.session_start > SESSION_REFRESH_INTERVAL
    )
    if need_new:
        sess, status = create_authenticated_session()
        _thread_local.sess       = sess
        _thread_local.session_start = time.time()
        print(f"  🔑 [线程 {threading.current_thread().name}] 认证成功: {status}")

    return _thread_local.sess


def _process_one(item: dict, index: int, total: int) -> dict:
    field_id = item["field_id"]
    payload  = item["payload"]
    expr     = payload["regular"]
    settings = payload["settings"]

    sess = _get_session()

    # ── 提交回测 ─────────────────────────────────────────────
    alpha_id, err, _ = submit_and_wait(
        sess=sess,
        alpha_payload=payload,
        max_wait_sec=MAX_WAIT_SEC
    )
    if err:
        log_result(index, total, None, field_id, expr, settings, None, err)
        return {"alpha_id": None, "field_id": field_id, "expr": expr, "error": err}

    # ── 查询指标 ─────────────────────────────────────────────
    result, err = get_alpha_result(sess=sess, alpha_id=alpha_id)
    if err:
        log_result(index, total, alpha_id, field_id, expr, settings, None, err)
        return {"alpha_id": alpha_id, "field_id": field_id, "expr": expr, "error": err}

    log_result(index, total, alpha_id, field_id, expr, settings, result, None)
    result["field_id"] = field_id
    result["expr"]     = expr
    return result


def _save(all_results: list, output_all: str, output_passed: str):
    # ── 写入全部结果 ──────────────────────────────────────────
    with open(output_all, "w", encoding="utf-8") as f:
        for r in all_results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ── 写入成功拿到 alpha_id 的结果 ─────────────────────────
    with open(output_passed, "w", encoding="utf-8") as f:
        for r in all_results:
            if r.get("alpha_id"):
                r["url"] = BRAIN_URL_PREFIX + str(r["alpha_id"])
                f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    alpha_list = _load_alpha_list()
    total      = len(alpha_list)
    log_start(total)

    all_results    = []
    results_lock   = threading.Lock()
    completed_count = 0

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
                completed_count += 1

                if completed_count % 10 == 0:
                    _save(all_results, OUTPUT_ALL, OUTPUT_PASSED)
                    print(f"  💾 已保存进度 ({completed_count}/{total})\n")

    _save(all_results, OUTPUT_ALL, OUTPUT_PASSED)
    succeeded = sum(1 for r in all_results if r.get("alpha_id"))
    log_end(total, succeeded)
    generate_web()


if __name__ == "__main__":
    main()