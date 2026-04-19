import time
import threading
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from auth_client import create_authenticated_session
from build_alphas import build_alpha_list
from simulate import submit_and_wait
from evaluate import get_alpha_result
from logger import log_start, log_result, log_end
from setting import (
    OUTPUT_ALL, OUTPUT_PASSED,
    MAX_WAIT_SEC, SESSION_REFRESH_INTERVAL, MAX_CONCURRENT
)

# 每个线程独立维护自己的 Session，互不干扰
_thread_local = threading.local()


def _get_session() -> object:
    """
    获取当前线程的 Session，不存在则新建，过期则刷新。
    每个线程独立认证，避免多线程共用同一 Session 的线程安全问题。
    """
    need_new = (
        not hasattr(_thread_local, "sess")
        or _thread_local.sess is None
        or time.time() - _thread_local.session_start > SESSION_REFRESH_INTERVAL
    )
    if need_new:
        sess, status = create_authenticated_session()
        _thread_local.sess = sess
        _thread_local.session_start = time.time()
        print(f"  🔑 [线程 {threading.current_thread().name}] 认证成功: {status}")

    return _thread_local.sess


def _process_one(item: dict, index: int, total: int) -> dict:
    """
    单个 alpha 的完整处理流程（在独立线程中运行）：
    获取 Session → 提交回测 → 等待结果 → 查询指标 → 记录日志

    Args:
        item:  包含 field_id 和 payload 的 dict
        index: 当前序号（从1开始），仅用于日志显示
        total: 总数，仅用于日志显示

    Returns:
        dict: 包含所有指标或错误信息的结果字典
    """
    field_id = item["field_id"]
    payload  = item["payload"]
    expr     = payload["regular"]

    sess = _get_session()

    # ── 提交回测，等待结果 ────────────────────────────────────
    alpha_id, err, _ = submit_and_wait(
        sess=sess,
        alpha_payload=payload,
        max_wait_sec=MAX_WAIT_SEC
    )
    if err:
        log_result(index, total, None, field_id, expr, None, err)
        return {
            "alpha_id":     None,
            "field_id":     field_id,
            "expr":         expr,
            "error":        err,
            "overall_pass": False,
        }

    # ── 查询回测指标 ──────────────────────────────────────────
    result, err = get_alpha_result(sess=sess, alpha_id=alpha_id)
    if err:
        log_result(index, total, alpha_id, field_id, expr, None, err)
        return {
            "alpha_id":     alpha_id,
            "field_id":     field_id,
            "expr":         expr,
            "error":        err,
            "overall_pass": False,
        }

    # ── 格式化输出 + 写入日志 ─────────────────────────────────
    log_result(index, total, alpha_id, field_id, expr, result, None)
    result["field_id"] = field_id
    return result


def _save(all_results: list, output_all: str, output_passed: str):
    """
    将结果列表保存为两个 CSV：
    - output_all:    全部 alpha（含失败）
    - output_passed: 仅 overall_pass == True 的 alpha
    """
    df_all = pd.DataFrame(all_results)
    df_all.to_csv(output_all, index=False)

    # 筛选通过的 alpha 单独保存
    df_passed = df_all[df_all["overall_pass"] == True]
    df_passed.to_csv(output_passed, index=False)


def main():

    # ── 构造 alpha 列表 ────────────────────────────────────────
    alpha_list = build_alpha_list()
    total = len(alpha_list)
    log_start(total)

    all_results = []
    results_lock = threading.Lock()   # 保护 all_results 列表的写入
    completed_count = 0

    # ── 并发跑，MAX_CONCURRENT 个线程同时 simulate ─────────────
    with ThreadPoolExecutor(
        max_workers=MAX_CONCURRENT,
        thread_name_prefix="sim"      # 线程名前缀，方便日志里区分
    ) as executor:

        # 把所有任务提交给线程池，future → index 方便追踪
        futures = {
            executor.submit(_process_one, item, i, total): i
            for i, item in enumerate(alpha_list, 1)
        }

        # 哪个先完成就先处理哪个
        for future in as_completed(futures):
            result = future.result()

            with results_lock:
                all_results.append(result)
                completed_count += 1

                # 每完成 10 个保存一次，防止崩溃丢数据
                if completed_count % 10 == 0:
                    _save(all_results, OUTPUT_ALL, OUTPUT_PASSED)
                    print(f"  💾 已保存进度 ({completed_count}/{total})\n")

    # ── 全部完成，最终保存 + 写日志尾 ─────────────────────────
    _save(all_results, OUTPUT_ALL, OUTPUT_PASSED)
    passed = sum(1 for r in all_results if r.get("overall_pass"))
    log_end(total, passed)


if __name__ == "__main__":
    main()