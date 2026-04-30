import os
import threading
from datetime import datetime
from setting import LOGS_DIR, LOG_BASE_NAME

_log_lock = threading.Lock()
_log_file_path = None


def _resolve_log_path() -> str:
    today = datetime.now().strftime("%Y%m%d")
    os.makedirs(LOGS_DIR, exist_ok=True)

    for filename in os.listdir(LOGS_DIR):
        if filename.startswith(LOG_BASE_NAME) and today in filename:
            print(f"  📄 找到今日日志，追加写入: {filename}")
            return os.path.join(LOGS_DIR, filename)

    filename = f"{LOG_BASE_NAME}.{today}.log"
    print(f"  📄 新建今日日志: {filename}")
    return os.path.join(LOGS_DIR, filename)


def _get_log_path() -> str:
    global _log_file_path
    if _log_file_path is None:
        _log_file_path = _resolve_log_path()
    return _log_file_path


def _write(msg: str):
    with _log_lock:
        print(msg)
        with open(_get_log_path(), "a", encoding="utf-8") as f:
            f.write(msg + "\n")


def log_start(total: int, datafield: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _write(f"\n{'=' * 60}")
    _write(f"  开始时间 : {ts}")
    _write(f"  探测字段 : {datafield}")
    _write(f"  共 {total} 条探针待回测")
    _write(f"{'=' * 60}\n")


def log_field_summary(datafield: str, results: list[dict]):
    """
    所有探针跑完后，按 7 个维度汇总输出一次。
    """
    by_type: dict[str, dict] = {r["probe_type"]: r for r in results}

    def lc(probe_type: str) -> str:
        r = by_type.get(probe_type)
        if r is None or r.get("error"):
            return "ERR"
        v = r.get("long_count")
        return str(v) if v is not None else "ERR"

    ts = datetime.now().strftime("%H:%M:%S")

    _write(f"\n┌{'─' * 58}┐")
    _write(f"│  📊 字段: {datafield:<44}[{ts}]  │")
    _write(f"├{'─' * 58}┤")

    # ── ① 粗覆盖率 ────────────────────────────────────────
    _write(f"│  ① 覆盖率      Long: {lc('probe1_raw'):<10}  Short: 0              │")

    # ── ② 精确覆盖率 ──────────────────────────────────────
    _write(f"│  ② 精确覆盖率  Long: {lc('probe2_nonzero'):<36}│")

    # ── ③ 更新频率  N = 5 / 22 / 66 / 252 ─────────────────
    freq_str = (
        f"N5:{lc('probe3_freq_N5')}  "
        f"N22:{lc('probe3_freq_N22')}  "
        f"N66:{lc('probe3_freq_N66')}  "
        f"N252:{lc('probe3_freq_N252')}"
    )
    _write(f"│  ③ 更新频率    {freq_str:<44}│")

    # ── ④ 数值范围 ────────────────────────────────────────
    bound_str = (
        f"X0.01:{lc('probe4_bound_X0.01')}  "
        f"X0.1:{lc('probe4_bound_X0.1')}  "
        f"X0.5:{lc('probe4_bound_X0.5')}  "
        f"X1:{lc('probe4_bound_X1')}  "
        f"X2:{lc('probe4_bound_X2')}  "
        f"X5:{lc('probe4_bound_X5')}  "
        f"X10:{lc('probe4_bound_X10')}"
    )
    _write(f"│  ④ 数值范围    {bound_str:<44}│")

    # ── ⑤ 中位数 ─────────────────────────────────────────
    med_str = (
        f"X0:{lc('probe5_median_X0')}  "
        f"X0.1:{lc('probe5_median_X0.1')}  "
        f"X0.5:{lc('probe5_median_X0.5')}  "
        f"X1:{lc('probe5_median_X1')}  "
        f"X2:{lc('probe5_median_X2')}  "
        f"X5:{lc('probe5_median_X5')}"
    )
    _write(f"│  ⑤ 中位数      {med_str:<44}│")

    # ── ⑥ 分布形态 ───────────────────────────────────────
    dist_str = (
        f"[0,0.2]:{lc('probe6_dist_0.0_0.2')}  "
        f"[0.2,0.4]:{lc('probe6_dist_0.2_0.4')}  "
        f"[0.4,0.6]:{lc('probe6_dist_0.4_0.6')}  "
        f"[0.6,0.8]:{lc('probe6_dist_0.6_0.8')}  "
        f"[0.8,1]:{lc('probe6_dist_0.8_1.0')}"
    )
    _write(f"│  ⑥ 分布形态    {dist_str:<44}│")

    # ── ⑦ 填充覆盖率  N = 5 / 22 / 66 / 252 ──────────────
    fill_str = (
        f"N5:{lc('probe7_backfill_N5')}  "
        f"N22:{lc('probe7_backfill_N22')}  "
        f"N66:{lc('probe7_backfill_N66')}  "
        f"N252:{lc('probe7_backfill_N252')}"
    )
    _write(f"│  ⑦ 填充覆盖率  {fill_str:<44}│")

    _write(f"└{'─' * 58}┘\n")


def log_end(total: int, datafield: str, output_path: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _write(f"\n{'=' * 60}")
    _write(f"  结束时间 : {ts}")
    _write(f"  探测字段 : {datafield}")
    _write(f"  共完成   : {total} 条探针")
    _write(f"  已保存至 : {output_path}")
    _write(f"{'=' * 60}\n")