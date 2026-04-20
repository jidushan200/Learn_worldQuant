from setting import (
    FREQ_WINDOWS,
    BOUND_THRESHOLDS,
    MEDIAN_THRESHOLDS,
    DIST_BINS,
    BACKFILL_WINDOWS,
)


def _make_payload(expr: str) -> dict:
    """
    统一设置：None 中性化 + Decay 0
    """
    return {
        "type":        "REGULAR",
        "settings": {
            "instrumentType": "EQUITY",
            "region":         "USA",
            "universe":       "TOP3000",
            "delay":          1,
            "decay":          0,
            "neutralization": "NONE",
            "truncation":     0.08,
            "pasteurization": "ON",
            "unitHandling":   "VERIFY",
            "nanHandling":    "OFF",
            "language":       "FASTEXPR",
            "visualization":  False,
        },
        "regular": expr,
    }


def build_probe_list(datafield: str) -> list[dict]:
    """
    为一个 datafield 构造全部 7 类探针，返回 list[dict]
    每条 dict 包含：probe_type / expr / payload
    """
    probes = []

    def add(probe_type: str, expr: str):
        probes.append({
            "probe_type": probe_type,
            "expr":       expr,
            "payload":    _make_payload(expr),
        })

    # ── ① 粗覆盖率 ────────────────────────────────────────
    add("probe1_raw", datafield)

    # ── ② 精确覆盖率 ──────────────────────────────────────
    add("probe2_nonzero", f"{datafield} != 0 ? 1 : 0")

    # ── ③ 更新频率  N = 5 / 22 / 66 / 252 ─────────────────
    for n in FREQ_WINDOWS:
        add(
            f"probe3_freq_N{n}",
            f"ts_std_dev({datafield}, {n}) != 0 ? 1 : 0",
        )

    # ── ④ 数值范围  X = 0.01 / 0.1 / … / 10 ──────────────
    for x in BOUND_THRESHOLDS:
        label = str(x)
        add(
            f"probe4_bound_X{label}",
            f"abs({datafield}) > {x}",
        )

    # ── ⑤ 中位数   X = 0 / 0.1 / … / 5 ───────────────────
    for x in MEDIAN_THRESHOLDS:
        label = str(x)
        add(
            f"probe5_median_X{label}",
            f"ts_median({datafield}, 1000) > {x}",
        )

    # ── ⑥ 分布形态  区间滑动 ──────────────────────────────
    for lo, hi in DIST_BINS:
        add(
            f"probe6_dist_{lo}_{hi}",
            f"{lo} < scale_down({datafield}) && scale_down({datafield}) < {hi}",
        )

    # ── ⑦ 填充覆盖率  N = 5 / 22 / 66 / 252 ──────────────
    for n in BACKFILL_WINDOWS:
        add(
            f"probe7_backfill_N{n}",
            f"ts_backfill({datafield}, {n}) != 0 ? 1 : 0",
        )

    return probes