import sys
import time
import threading
import pandas as pd
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from auth_client import create_authenticated_session
from build_alphas import build_probe_list
from simulate import submit_and_wait
from evaluate import get_probe_result
from logger import log_start, log_field_summary, log_end
from setting import (
    OUTPUT_DIR,
    MAX_WAIT_SEC,
    SESSION_REFRESH_INTERVAL,
    MAX_CONCURRENT,
    FIELDS_CSV,
)

_thread_local = threading.local()


def _get_session() -> object:
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


def _process_one(item: dict) -> dict:
    probe_type = item["probe_type"]
    expr       = item["expr"]
    payload    = item["payload"]

    sess = _get_session()

    alpha_id, err, _ = submit_and_wait(
        sess=sess,
        alpha_payload=payload,
        max_wait_sec=MAX_WAIT_SEC,
    )
    if err:
        return {
            "alpha_id":    None,
            "probe_type":  probe_type,
            "expr":        expr,
            "long_count":  None,
            "short_count": None,
            "error":       err,
        }

    result, err = get_probe_result(
        sess=sess,
        alpha_id=alpha_id,
        probe_type=probe_type,
        expr=expr,
    )
    if err:
        return {
            "alpha_id":    alpha_id,
            "probe_type":  probe_type,
            "expr":        expr,
            "long_count":  None,
            "short_count": None,
            "error":       err,
        }

    return result


def _save(all_results: list, datafield: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"{datafield}_probe_results.csv")
    df = pd.DataFrame(all_results)
    df.to_csv(output_path, index=False)
    return output_path


def _run_field(datafield: str) -> None:
    print(f"\n🔍 开始探测字段: {datafield}\n")

    probe_list   = build_probe_list(datafield)
    total        = len(probe_list)
    log_start(total, datafield)

    all_results  = []
    results_lock = threading.Lock()
    completed    = 0

    with ThreadPoolExecutor(
        max_workers=MAX_CONCURRENT,
        thread_name_prefix="probe"
    ) as executor:

        futures = {
            executor.submit(_process_one, item): item
            for item in probe_list
        }

        for future in as_completed(futures):
            result = future.result()
            with results_lock:
                all_results.append(result)
                completed += 1
                print(f"  ⏳ 进度: {completed:>2}/{total}  [{result['probe_type']}]")

    log_field_summary(datafield, all_results)
    path = _save(all_results, datafield)
    log_end(total, datafield, path)


def main():
    if not os.path.exists(FIELDS_CSV):
        print(f"❌ 找不到字段列表文件: {FIELDS_CSV}")
        sys.exit(1)

    df = pd.read_csv(FIELDS_CSV)
    if "id" not in df.columns:
        print(f"❌ CSV 文件中没有 'id' 列，请检查文件格式")
        sys.exit(1)

    fields = df["id"].tolist()
    print(f"📂 从 {FIELDS_CSV} 读取 {len(fields)} 个字段，开始批量探测...\n")

    total_fields = len(fields)
    for i, datafield in enumerate(fields, 1):
        print(f"\n{'─' * 60}")
        print(f"  [{i}/{total_fields}] 字段: {datafield}")
        print(f"{'─' * 60}")
        _run_field(datafield)

    print(f"\n✅ 全部完成，共探测 {total_fields} 个字段")
    print(f"   结果保存在: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()