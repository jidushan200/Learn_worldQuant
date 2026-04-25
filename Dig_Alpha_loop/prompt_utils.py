"""
Prompt 构建所需的常量、Grade 工具、格式化辅助函数、策略文件加载。
"""

import os
from setting import INITIAL_PROMPT_FILE

# ═══════════════════════════════════════════════════════════
#  常量模板
# ═══════════════════════════════════════════════════════════

SYSTEM_PROMPT = (
    "你是 WorldQuant Brain 平台的量化 alpha 表达式专家。\n"
    "你精通 FASTEXPR 语法，熟悉平台支持的所有数据字段和函数。\n"
    "你的目标：生成能通过平台全部 checks、grade 达到 GOOD 或以上的 alpha。\n"
    "你还需要为每个 alpha 选择最合适的回测参数（setting），而不是千篇一律。\n\n"
    "重要规则：\n"
    "1. 只使用参考资料中列出的字段和函数，不要编造不存在的字段/函数\n"
    "2. 仔细参考成功范例的结构和风格\n"
    "3. 结合论文思路设计有经济学逻辑的因子\n"
    "4. 关注自相关、换手率、覆盖率等 checks 指标\n"
    "5. region 必须固定为 \"USA\"，不要使用其他区域（其他区域暂未开放）"
)

SETTING_SPEC = (
    "## 回测参数说明（setting 字段）\n"
    "每个 alpha 必须包含 setting 字段，可选值如下：\n\n"
    "| 参数 | 可选值 | 说明 |\n"
    "|------|--------|------|\n"
    '| instrumentType | "EQUITY" | 固定 |\n'
    '| region | "USA" | 固定为USA（其他区域暂不可用） |\n'
    '| universe | "TOP200", "TOP500", "TOP1000", "TOP2000", "TOP3000" | 股票池 |\n'
    "| delay | 0, 1 | 信号延迟天数 |\n"
    "| decay | 0~20 整数 | 线性衰减天数 |\n"
    '| neutralization | "NONE", "MARKET", "SECTOR", "INDUSTRY", "SUBINDUSTRY" | 中性化 |\n'
    "| truncation | 0.01~0.10 | 截断比例 |\n"
    '| pasteurization | "ON", "OFF" | 巴氏灭菌 |\n'
    '| unitHandling | "VERIFY", "NONE" | 单位处理 |\n'
    '| nanHandling | "ON", "OFF" | NaN处理 |\n'
    '| language | "FASTEXPR" | 固定 |\n\n'
    "⚠️ **region 必须为 \"USA\"，当前不支持 CHN/EUR/ASI/GLB 等其他区域。**\n\n"
    "选择建议：\n"
    "- 动量/反转类：decay 偏高(6-12)，neutralization 用 SUBINDUSTRY\n"
    "- 基本面质量类：decay 偏低(2-6)，neutralization 用 MARKET 或 INDUSTRY\n"
    "- 高换手因子：truncation 调低(0.05)，decay 调高\n"
    "- 低频因子：delay=1，decay 可较低\n"
)

OUTPUT_FORMAT = (
    "## 输出格式\n"
    "先用 2-3 句话简述设计思路，然后 **严格** 输出如下 JSON 数组：\n\n"
    "```json\n"
    "[\n"
    "  {\n"
    '    "name": "alpha_001_xxx",\n'
    '    "expr": "rank(ts_zscore(return_equity, 252)) ...",\n'
    '    "setting": {\n'
    '      "instrumentType": "EQUITY",\n'
    '      "region": "USA",\n'
    '      "universe": "TOP3000",\n'
    '      "delay": 1,\n'
    '      "decay": 4,\n'
    '      "neutralization": "MARKET",\n'
    '      "truncation": 0.08,\n'
    '      "pasteurization": "ON",\n'
    '      "unitHandling": "VERIFY",\n'
    '      "nanHandling": "OFF",\n'
    '      "language": "FASTEXPR"\n'
    "    }\n"
    "  }\n"
    "]\n"
    "```\n\n"
    "**注意：region 必须固定为 \"USA\"。**\n"
)

# ═══════════════════════════════════════════════════════════
#  Grade 等级工具
# ═══════════════════════════════════════════════════════════

GRADE_ORDER = ["INFERIOR", "AVERAGE", "GOOD", "STRONG", "EXCELLENT", "SPECTACULAR"]


def grade_ge(actual: str, target: str) -> bool:
    actual_upper = (actual or "").strip().upper()
    target_upper = (target or "").strip().upper()
    if actual_upper not in GRADE_ORDER or target_upper not in GRADE_ORDER:
        return False
    return GRADE_ORDER.index(actual_upper) >= GRADE_ORDER.index(target_upper)


def best_grade(grades: list[str]) -> str:
    best_idx = -1
    best_val = ""
    for g in grades:
        g_upper = (g or "").strip().upper()
        if g_upper in GRADE_ORDER:
            idx = GRADE_ORDER.index(g_upper)
            if idx > best_idx:
                best_idx = idx
                best_val = g_upper
    return best_val


# ═══════════════════════════════════════════════════════════
#  数值格式化
# ═══════════════════════════════════════════════════════════

def fmt(v, d=2):
    return f"{v:.{d}f}" if isinstance(v, (int, float)) else "N/A"


def pct(v, d=1):
    return f"{v * 100:.{d}f}%" if isinstance(v, (int, float)) else "N/A"


# ═══════════════════════════════════════════════════════════
#  加载用户策略思路
# ═══════════════════════════════════════════════════════════

def load_initial_idea() -> str:
    if not os.path.exists(INITIAL_PROMPT_FILE):
        return ""
    with open(INITIAL_PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()


# ═══════════════════════════════════════════════════════════
#  年度数据格式化
# ═══════════════════════════════════════════════════════════

def format_yearly_for_prompt(yearly_stats: list[dict] | None) -> str:
    if not yearly_stats:
        return (
            "\n## 最优 Alpha 年度表现（IS）\n"
            "⚠️ 年度数据未获取到（API 可能尚未聚合完成），"
            "请基于整体 Sharpe/Fitness 优化，关注跨年稳定性。\n"
        )

    lines = [
        "\n## 最优 Alpha 年度表现（IS）",
        f"{'Year':<6}{'Sharpe':>8}{'Fitness':>9}{'Turnover':>10}{'Returns':>10}{'Drawdown':>10}{'Margin':>10}",
        "-" * 63,
    ]

    for y in yearly_stats:
        yr = y.get('year', '?')
        sh = y.get('sharpe', 0) or 0
        fi = y.get('fitness', 0) or 0
        to = (y.get('turnover', 0) or 0) * 100
        rt = (y.get('returns', 0) or 0) * 100
        dd = (y.get('drawdown', 0) or 0) * 100
        mg = (y.get('margin', 0) or 0) * 10000
        lines.append(
            f"{yr:<6}{sh:>8.2f}{fi:>9.2f}{to:>9.2f}%{rt:>9.2f}%{dd:>9.2f}%{mg:>9.2f}‱"
        )

    weak = [y for y in yearly_stats if (y.get('sharpe', 0) or 0) < 0.5]
    negative = [y for y in yearly_stats if (y.get('sharpe', 0) or 0) < 0]

    if negative:
        lines.append(
            f"\n🔴 负 Sharpe 年份: {', '.join(str(y.get('year', '?')) for y in negative)}"
        )
        lines.append("这些年份因子方向完全错误，是最需要修复的薄弱环节。")
    if weak and len(weak) > len(negative):
        only_weak = [y for y in weak if (y.get('sharpe', 0) or 0) >= 0]
        if only_weak:
            lines.append(
                f"🟡 弱年份（0 ≤ Sharpe < 0.5）: {', '.join(str(y.get('year', '?')) for y in only_weak)}"
            )

    if not weak:
        lines.append("✅ 所有年份 Sharpe ≥ 0.5，年度稳定性良好。")

    sharpes = [y.get('sharpe', 0) or 0 for y in yearly_stats]
    if len(sharpes) >= 2:
        mean = sum(sharpes) / len(sharpes)
        var  = sum((s - mean) ** 2 for s in sharpes) / (len(sharpes) - 1)
        std  = var ** 0.5
        lines.append(f"\n📈 年度 Sharpe 统计: 均值={mean:.2f}, 标准差={std:.2f}（越小越稳定）")
        if std > 1.0:
            lines.append("⚠️ 年度波动较大，优化时需重点关注一致性。")

    return "\n".join(lines) + "\n"


# ═══════════════════════════════════════════════════════════
#  历史记录格式化（备用）
# ═══════════════════════════════════════════════════════════

def format_history(history: list[dict]) -> str:
    lines = []
    for h in history:
        it = h["iteration"]
        results = h["results"]
        lines.append(f"\n### 第 {it} 轮")

        ok = [r for r in results if r.get("sharpe") is not None and not r.get("error")]
        fail = [r for r in results if r.get("error")]

        if ok:
            ok.sort(key=lambda x: x.get("sharpe", 0), reverse=True)
            lines.append("✅ 成功：")
            for r in ok:
                name = r.get("field_id", "?")
                sh   = fmt(r.get("sharpe"), 4)
                fi   = fmt(r.get("fitness"), 4)
                to   = pct(r.get("turnover"))
                ret  = pct(r.get("returns"), 2)
                dd   = pct(r.get("drawdown"), 2)
                gr   = r.get("grade", "N/A")
                chk  = r.get("checks_pass", "N/A")
                expr = r.get("expr", "?")
                stg  = r.get("settings_used", {})
                dec  = stg.get("decay", "?")
                neu  = stg.get("neutralization", "?")
                uni  = stg.get("universe", "?")
                lines.append(
                    f"  {name}  Grade={gr} Sharpe={sh} Fitness={fi} "
                    f"Turnover={to} Returns={ret} Drawdown={dd} "
                    f"Checks={chk} "
                    f"[decay={dec}, neut={neu}, univ={uni}]"
                )
                lines.append(f"    expr: {expr}")

        if fail:
            lines.append("❌ 失败：")
            for r in fail:
                name = r.get("field_id", "?")
                lines.append(f"  {name}: {r.get('error', '?')}")
                lines.append(f"    expr: {r.get('expr', '?')}")

    return "\n".join(lines)