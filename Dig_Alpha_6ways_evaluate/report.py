"""
report.py  —  读取探针 CSV，输出字段特征分析报告

用法:
    python report.py --field adv20
    python report.py --file
    python report.py --file ..\Fetch_Fields\fundamental6_fields_ids.csv
"""

import argparse
import os
import pandas as pd
from setting import (
    OUTPUT_DIR,
    FREQ_WINDOWS,
    BOUND_THRESHOLDS,
    MEDIAN_THRESHOLDS,
    DIST_BINS,
    BACKFILL_WINDOWS,
    FIELDS_CSV,
)

UNIVERSE_SIZE = 3000  # TOP3000


# ─────────────────────────────────────────────────────────────
# 数据加载 & 辅助函数
# ─────────────────────────────────────────────────────────────

def _load(datafield: str) -> pd.DataFrame:
    path = os.path.join(OUTPUT_DIR, f"{datafield}_probe_results.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"找不到结果文件: {path}\n"
            f"请先运行: python main.py --field {datafield}"
        )
    return pd.read_csv(path)


def _lc(df: pd.DataFrame, probe_type: str) -> int | None:
    rows = df[df["probe_type"] == probe_type]
    if rows.empty:
        return None
    row = rows.iloc[0]
    err = row.get("error", None)
    if pd.notna(err) and str(err).strip() not in ("None", "nan", ""):
        return None
    val = row["long_count"]
    return int(val) if pd.notna(val) else None


def _sc(df: pd.DataFrame, probe_type: str) -> int | None:
    rows = df[df["probe_type"] == probe_type]
    if rows.empty:
        return None
    row = rows.iloc[0]
    val = row["short_count"]
    return int(val) if pd.notna(val) else None


def _pct(n: int | None, base: int = UNIVERSE_SIZE) -> str:
    if n is None or base == 0:
        return "  N/A"
    return f"{n / base * 100:>5.1f}%"


# ─────────────────────────────────────────────────────────────
# 7 个维度的分析函数
# ─────────────────────────────────────────────────────────────

def _r1_coverage(df: pd.DataFrame) -> list[str]:
    """① 粗覆盖率"""
    lc    = _lc(df, "probe1_raw") or 0
    sc    = _sc(df, "probe1_raw") or 0
    total = lc + sc
    rate  = total / UNIVERSE_SIZE * 100

    if rate >= 90:
        tag = "🟢 极高"
    elif rate >= 60:
        tag = "🟡 良好"
    elif rate >= 30:
        tag = "🟠 中等"
    else:
        tag = "🔴 偏低"

    return [
        f"  Long: {lc}  Short: {sc}  合计: {total} / {UNIVERSE_SIZE}",
        f"  覆盖率: {rate:.1f}%  {tag}",
    ]


def _r2_exact(df: pd.DataFrame) -> list[str]:
    """② 精确覆盖率"""
    lc = _lc(df, "probe2_nonzero")
    if lc is None:
        return ["  ❌ 数据缺失"]
    rate = lc / UNIVERSE_SIZE * 100

    if rate >= 90:
        tag = "🟢 几乎无缺失"
    elif rate >= 60:
        tag = "🟡 少量缺失"
    elif rate >= 30:
        tag = "🟠 较多缺失"
    else:
        tag = "🔴 大量缺失，建议排查"

    return [
        f"  非零股票数: {lc} / {UNIVERSE_SIZE} ({rate:.1f}%)  {tag}",
    ]


def _r3_freq(df: pd.DataFrame) -> list[str]:
    """③ 更新频率"""
    labels = {5: "周", 22: "月", 66: "季", 252: "年"}
    counts = {n: _lc(df, f"probe3_freq_N{n}") for n in FREQ_WINDOWS}
    base   = _lc(df, "probe2_nonzero") or UNIVERSE_SIZE

    lines = []
    for n in FREQ_WINDOWS:
        c = counts[n]
        lines.append(
            f"  N={n:>3} ({labels.get(n, '?')}): {str(c if c is not None else 'ERR'):>6}  {_pct(c, base)}"
        )

    update_n = None
    for n in FREQ_WINDOWS:
        c = counts[n]
        if c is not None and base > 0 and c / base >= 0.9:
            update_n = n
            break

    if update_n == 5:
        conclusion = "→ 每日或每周更新（高频）"
    elif update_n == 22:
        conclusion = "→ 约每月更新（月频）"
    elif update_n == 66:
        conclusion = "→ 约每季度更新（季频）"
    elif update_n == 252:
        conclusion = "→ 约每年更新（年频）"
    else:
        conclusion = "→ 更新极稀疏（超年频），或数据基本不变"

    lines.append(f"  {conclusion}")
    return lines


def _r4_bounds(df: pd.DataFrame) -> list[str]:
    """④ 数值范围"""
    counts = {x: _lc(df, f"probe4_bound_X{x}") for x in BOUND_THRESHOLDS}
    base   = _lc(df, "probe2_nonzero") or UNIVERSE_SIZE

    lines = []
    for x in BOUND_THRESHOLDS:
        c = counts[x]
        lines.append(
            f"  |x| > {str(x):>5}: {str(c if c is not None else 'ERR'):>6}  {_pct(c, base)}"
        )

    upper = None
    for x in BOUND_THRESHOLDS:
        c = counts[x]
        if c is not None and base > 0 and c / base < 0.1:
            upper = x
            break

    if upper is None:
        conclusion = "→ 绝对值可能超过 10，数据未归一化"
    elif upper <= 0.01:
        conclusion = "→ 绝对值极小，几乎全在 0.01 以内"
    elif upper <= 0.1:
        conclusion = "→ 数据已归一化，绝对值在 0.1 以内"
    elif upper <= 0.5:
        conclusion = "→ 绝对值上限约 0.5"
    elif upper <= 1:
        conclusion = "→ 归一化到 [-1, 1]"
    elif upper <= 2:
        conclusion = "→ 绝对值上限约 1 ~ 2"
    elif upper <= 5:
        conclusion = "→ 绝对值上限约 2 ~ 5"
    else:
        conclusion = "→ 绝对值上限约 5 ~ 10"

    lines.append(f"  {conclusion}")
    return lines


def _r5_median(df: pd.DataFrame) -> list[str]:
    """⑤ 中位数水平"""
    counts = {x: _lc(df, f"probe5_median_X{x}") for x in MEDIAN_THRESHOLDS}
    base   = _lc(df, "probe2_nonzero") or UNIVERSE_SIZE
    half   = base / 2

    lines = []
    for x in MEDIAN_THRESHOLDS:
        c = counts[x]
        lines.append(
            f"  中位数 > {str(x):>4}: {str(c if c is not None else 'ERR'):>6}  {_pct(c, base)}"
        )

    prev_x, prev_c = None, None
    median_range   = None
    for x in MEDIAN_THRESHOLDS:
        c = counts[x]
        if c is None:
            continue
        if prev_c is not None and prev_c >= half > c:
            median_range = (prev_x, x)
            break
        prev_x, prev_c = x, c

    if median_range:
        conclusion = f"→ 中位数约在 {median_range[0]} ~ {median_range[1]} 之间"
    elif counts.get(MEDIAN_THRESHOLDS[-1]) is not None and counts[MEDIAN_THRESHOLDS[-1]] >= half:
        conclusion = f"→ 中位数 > {MEDIAN_THRESHOLDS[-1]}，请扩展 X 上限"
    elif counts.get(MEDIAN_THRESHOLDS[0]) is not None and counts[MEDIAN_THRESHOLDS[0]] < half:
        conclusion = "→ 中位数 ≤ 0，数据含大量负值或零"
    else:
        conclusion = "→ 中位数推断失败，请检查数据"

    lines.append(f"  {conclusion}")
    return lines


def _r6_dist(df: pd.DataFrame) -> list[str]:
    """⑥ 分布形态"""
    counts = {(lo, hi): _lc(df, f"probe6_dist_{lo}_{hi}") for lo, hi in DIST_BINS}
    valid  = {k: v for k, v in counts.items() if v is not None}

    if not valid:
        return ["  ❌ 数据缺失"]

    total_in_bins = sum(valid.values()) or 1
    lines = []
    for (lo, hi), c in counts.items():
        bar_len = int((c or 0) / total_in_bins * 20)
        bar = "█" * bar_len
        lines.append(f"  [{lo:.1f}, {hi:.1f}]: {str(c if c is not None else 'ERR'):>6}  {bar}")

    lower = sum(v for (lo, hi), v in valid.items() if hi  <= 0.4)
    upper = sum(v for (lo, hi), v in valid.items() if lo  >= 0.6)
    mid   = valid.get((0.4, 0.6)) or 0

    if lower > upper * 1.5 and lower > mid:
        skew = "左偏 → 数据集中在低值区（scale_down 后）"
    elif upper > lower * 1.5 and upper > mid:
        skew = "右偏 → 数据集中在高值区（scale_down 后）"
    elif mid > lower and mid > upper:
        skew = "中心集中 → 近似正态或均匀分布"
    else:
        skew = "分布较均匀"

    lines.append(f"  → {skew}")
    return lines


def _r7_backfill(df: pd.DataFrame) -> list[str]:
    """⑦ 填充覆盖率"""
    counts = {n: _lc(df, f"probe7_backfill_N{n}") for n in BACKFILL_WINDOWS}
    exact  = _lc(df, "probe2_nonzero") or 0

    lines = []
    for n in BACKFILL_WINDOWS:
        c    = counts[n]
        gain = (c - exact) if (c is not None and exact) else None
        gain_str = f"  (+{gain})" if gain and gain > 0 else ""
        lines.append(
            f"  N={n:>3}: {str(c if c is not None else 'ERR'):>6}{gain_str}"
        )

    max_fill = max((c for c in counts.values() if c is not None), default=None)

    if max_fill is None or exact == 0:
        lines.append("  → 无法对比（精确覆盖率为 0）")
        return lines

    gain     = max_fill - exact
    gain_pct = gain / UNIVERSE_SIZE * 100

    if gain_pct < 2:
        conclusion = "→ 填充提升微小，数据连续性良好"
    elif gain_pct < 10:
        conclusion = f"→ 填充后提升 {gain} 只（+{gain_pct:.1f}%），存在少量日内缺失"
    else:
        conclusion = f"→ 填充后提升 {gain} 只（+{gain_pct:.1f}%），字段更新稀疏，建议使用 ts_backfill"

    lines.append(f"  {conclusion}")
    return lines


# ─────────────────────────────────────────────────────────────
# 汇总输出
# ─────────────────────────────────────────────────────────────

def generate_report(datafield: str) -> None:
    df  = _load(datafield)
    sep = "=" * 60

    print(f"\n{sep}")
    print(f"  📋 字段分析报告: {datafield}")
    print(f"{sep}\n")

    sections = [
        ("① 粗覆盖率",   _r1_coverage(df)),
        ("② 精确覆盖率", _r2_exact(df)),
        ("③ 更新频率",   _r3_freq(df)),
        ("④ 数值范围",   _r4_bounds(df)),
        ("⑤ 中位数",     _r5_median(df)),
        ("⑥ 分布形态",   _r6_dist(df)),
        ("⑦ 填充覆盖率", _r7_backfill(df)),
    ]

    for title, lines in sections:
        print(f"  【{title}】")
        for line in lines:
            print(line)
        print()

    print(sep)


# ─────────────────────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Dig_Alpha: 输出字段特征分析报告")
    group  = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--field", type=str, help="单个字段，例如: --field adv20")
    group.add_argument(
        "--file",
        type=str,
        nargs="?",
        const=FIELDS_CSV,
        default=None,
        help=f"字段列表 CSV，默认: {FIELDS_CSV}"
    )
    args = parser.parse_args()

    if args.field:
        fields = [args.field]
    else:
        path = args.file or FIELDS_CSV
        if not os.path.exists(path):
            parser.error(f"找不到字段列表文件: {path}")
        df = pd.read_csv(path)
        if "id" not in df.columns:
            parser.error(f"CSV 文件 {path} 中没有 'id' 列，请检查文件格式")
        fields = df["id"].tolist()
        print(f"📂 从 {path} 读取 {len(fields)} 个字段\n")

    missing = []
    for datafield in fields:
        try:
            generate_report(datafield)
        except FileNotFoundError as e:
            print(f"  ⚠️  跳过 {datafield}: {e}\n")
            missing.append(datafield)

    if missing:
        print(f"\n⚠️  以下 {len(missing)} 个字段缺少结果文件，请先跑 main.py：")
        for f in missing:
            print(f"    python main.py --field {f}")


if __name__ == "__main__":
    main()