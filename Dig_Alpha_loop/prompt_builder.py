"""
链式 Prompt 构建器
──────────────────
第 1 轮: SYSTEM_PROMPT + 知识库 + 策略思路 + SETTING_SPEC + OUTPUT_FORMAT
第 N 轮: (知识库) + 最优 alpha 详情 + 年度表格 + 差距分析
                  + 上轮失败表达式 + SETTING_SPEC + OUTPUT_FORMAT

不做逐轮历史累加。每轮只看「当前最优」和「上轮结果」。
"""

from knowledge_loader import load_knowledge
from prompt_utils import (
    SYSTEM_PROMPT, SETTING_SPEC, OUTPUT_FORMAT,
    grade_ge,
)
from setting import (
    TARGET_SHARPE, TARGET_FITNESS, TARGET_GRADE,
    SIMULATION_SETTINGS, ALPHAS_PER_ROUND,
    SETTING_CHANGE_THRESHOLD,
)

try:
    from setting import KNOWLEDGE_EVERY_ROUND
except ImportError:
    KNOWLEDGE_EVERY_ROUND = False


# ═══════════════════════════════════════════════════════════
#  内部工具
# ═══════════════════════════════════════════════════════════

def _default_settings_block() -> str:
    """把 SIMULATION_SETTINGS 格式化成 prompt 段落，告诉 AI 当前默认配置"""
    s = SIMULATION_SETTINGS
    return (
        "## 当前默认回测设置（AI 输出的 setting 会覆盖这些默认值）\n"
        f"- region: {s.get('region', 'USA')}\n"
        f"- universe: {s.get('universe', 'TOP3000')}\n"
        f"- delay: {s.get('delay', 1)}\n"
        f"- decay: {s.get('decay', 0)}\n"
        f"- neutralization: {s.get('neutralization', 'MARKET')}\n"
        f"- truncation: {s.get('truncation', 0.08)}\n"
        f"- pasteurization: {s.get('pasteurization', 'ON')}\n"
        f"- nanHandling: {s.get('nanHandling', 'OFF')}\n\n"
    )


def _yearly_table(yearly_stats: list[dict] | None) -> str:
    if not yearly_stats:
        return "（无年度数据）"
    rows = [
        "| 年份 | Sharpe | Returns | Drawdown | Turnover |",
        "|------|--------|---------|----------|----------|",
    ]
    for y in sorted(yearly_stats, key=lambda x: x.get("year", 0)):
        yr = y.get("year", "?")
        sh = y.get("sharpe", 0) or 0
        rt = y.get("returns", 0) or 0
        dd = y.get("drawdown", 0) or 0
        to = y.get("turnover", 0) or 0
        flag = " 🔴" if sh < 0 else (" 🟡" if sh < 0.5 else "")
        rows.append(
            f"| {yr} | {sh:.4f}{flag} | {rt * 100:.2f}% "
            f"| {dd * 100:.2f}% | {to:.4f} |"
        )
    return "\n".join(rows)


def _gap_analysis(best: dict) -> str:
    sh = best.get("sharpe", 0) or 0
    fi = best.get("fitness", 0) or 0
    to = best.get("turnover", 0) or 0

    lines = []

    if sh < TARGET_SHARPE:
        lines.append(
            f"- Sharpe 差距 {TARGET_SHARPE - sh:.4f}："
            f"尝试增强信号强度、降噪、或组合互补因子"
        )
    if fi < TARGET_FITNESS:
        lines.append(
            f"- Fitness 差距 {TARGET_FITNESS - fi:.4f}："
            f"fitness ≈ sharpe × √days × (1 - maxDD)，需综合改善"
        )
    if to > 0.7:
        lines.append(
            f"- Turnover = {to:.4f} 偏高："
            f"加大 decay、用更平滑的算子（ts_mean / ewma 等）"
        )
    elif 0 < to < 0.01:
        lines.append(
            f"- Turnover = {to:.4f} 偏低："
            f"因子过于静态，可加入短期动量/事件信号"
        )

    yearly = best.get("yearly_stats", [])
    neg = [y for y in yearly if (y.get("sharpe", 0) or 0) < 0]
    if neg:
        yrs = ", ".join(str(y.get("year", "?")) for y in neg)
        lines.append(
            f"- {len(neg)} 年 Sharpe 为负 ({yrs})："
            f"这些年份因子失效，考虑自适应机制或减少过拟合"
        )

    return "\n".join(lines) if lines else "- 各项指标已接近目标，做微调即可"


def _failed_exprs(last_results: list[dict] | None) -> str:
    if not last_results:
        return ""

    items = []
    for r in last_results:
        expr = r.get("expr", "?")
        if r.get("error"):
            items.append(f"  ❌ `{expr}` → 错误: {r['error']}")
        elif r.get("alpha_id") and not grade_ge(r.get("grade", ""), TARGET_GRADE):
            gr = r.get("grade", "?")
            sh = r.get("sharpe", 0) or 0
            items.append(f"  ⚠️ `{expr}` → Grade={gr}, Sharpe={sh:.4f}")

    if not items:
        return ""

    return (
        "## 上轮未达标的表达式（请避免相似方向）\n"
        + "\n".join(items)
    )


# ═══════════════════════════════════════════════════════════
#  首轮 Prompt
# ═══════════════════════════════════════════════════════════

def build_initial_prompt(idea: str) -> tuple[str, str]:
    knowledge = load_knowledge()

    system = SYSTEM_PROMPT

    user = f"## 用户策略思路\n{idea}\n\n"

    if knowledge:
        user += knowledge

    user += _default_settings_block()

    user += (
        "## 任务\n"
        f"请根据以上思路和参考资料，生成 {ALPHAS_PER_ROUND} 个多样化的 alpha 表达式。\n\n"
        "## 要求\n"
        "1. 使用 FASTEXPR 语法，**只使用参考资料中列出的字段和函数**\n"
        "2. 每个 alpha 之间应有显著差异（不同因子、不同窗口期、不同组合方式）\n"
        f"3. **核心目标：grade 达到 {TARGET_GRADE} 或以上**\n"
        f"   （参考指标：Sharpe >= {TARGET_SHARPE}，Fitness >= {TARGET_FITNESS}）\n"
        "4. name 字段用简短英文标识因子含义\n"
        "5. 考虑因子的经济学逻辑和衰减特性\n"
        "6. **请先根据策略特性选定一组最合适的 setting（universe / delay / decay / neutralization 等），所有 alpha 使用相同的 setting**\n"
        "   （后续迭代会锁定该 setting 专注优化表达式，只有长期无提升时才调参）\n"
        "7. 重视通过平台全部 checks（低自相关、足够覆盖率、合理换手等）\n"
        "8. 参考成功范例的结构，但不要照抄\n"
        '9. **region 必须为 "USA"，不要使用其他区域**\n\n'
        f"{SETTING_SPEC}\n\n"
        f"{OUTPUT_FORMAT}\n\n"
        "**注意：所有 alpha 请使用同一组 setting，只在表达式上做差异化。**\n"
    )

    return system, user


# ═══════════════════════════════════════════════════════════
#  迭代 Prompt（链式：只看当前最优 + 上轮结果）
# ═══════════════════════════════════════════════════════════

def build_iteration_prompt(
    idea: str,
    iteration: int,
    best_alpha: dict | None,
    last_results: list[dict] | None,
    no_improve_count: int = 0,
) -> tuple[str, str]:

    # ── best_alpha 为 None（历史全部失败），回退首轮 + 失败提示 ──
    if best_alpha is None:
        system, user = build_initial_prompt(idea)

        failed = _failed_exprs(last_results)
        if failed:
            user += (
                "\n## ⚠️ 重要提示：上轮所有 alpha 全部失败！\n"
                "最常见原因是**使用了平台不存在的字段名**。\n"
                "请 **严格只使用** 参考资料「Fields」中列出的字段 id，不要编造字段。\n"
                "例如：`return_equity` 是真实字段，但 `roe`、`roa`、`gpoa`、`fcf_to_assets` 不是。\n\n"
                f"{failed}\n"
            )

        return system, user

    # ── 正常迭代：有 best_alpha ──
    knowledge = load_knowledge() if KNOWLEDGE_EVERY_ROUND else ""

    expr = best_alpha.get("expr", "?")
    stg = best_alpha.get("settings_used", {})
    sh = best_alpha.get("sharpe", 0) or 0
    fi = best_alpha.get("fitness", 0) or 0
    to = best_alpha.get("turnover", 0) or 0
    rt = best_alpha.get("returns", 0) or 0
    dd = best_alpha.get("drawdown", 0) or 0
    gr = best_alpha.get("grade", "N/A")
    yearly = _yearly_table(best_alpha.get("yearly_stats"))
    gap = _gap_analysis(best_alpha)
    failed = _failed_exprs(last_results)

    # ── system ──
    system = (
        f"{SYSTEM_PROMPT}\n\n"
        "你正在进行链式迭代优化。\n"
        "每轮你会收到「当前全局最优 alpha」的完整评估，你的任务是在此基础上改进。\n"
        "\n"
        f"目标: Grade >= {TARGET_GRADE}, Sharpe >= {TARGET_SHARPE}, "
        f"Fitness >= {TARGET_FITNESS}\n"
    )
    if knowledge:
        system += f"\n{knowledge}\n"

    # ── user ──
    grade_status = "✅" if grade_ge(gr, TARGET_GRADE) else "❌"
    sharpe_status = "✅" if sh >= TARGET_SHARPE else f"❌ 差 {TARGET_SHARPE - sh:.4f}"
    fitness_status = "✅" if fi >= TARGET_FITNESS else f"❌ 差 {TARGET_FITNESS - fi:.4f}"
    turnover_status = "⚠️ 偏高" if to > 0.7 else ("⚠️ 偏低" if 0 < to < 0.01 else "正常")

    user = (
        f"## 第 {iteration} 轮优化\n\n"
        "## 策略方向（供参考）\n"
        f"{idea}\n\n"
        "## 当前全局最优 Alpha\n"
        f"- 表达式: `{expr}`\n"
        f"- Settings: decay={stg.get('decay', '?')}, "
        f"neutralization={stg.get('neutralization', '?')}, "
        f"universe={stg.get('universe', '?')}\n\n"
        "### 评估结果\n"
        "| 指标 | 当前值 | 目标 | 状态 |\n"
        "|------|--------|------|------|\n"
        f"| Grade | {gr} | >= {TARGET_GRADE} | {grade_status} |\n"
        f"| Sharpe | {sh:.4f} | >= {TARGET_SHARPE} | {sharpe_status} |\n"
        f"| Fitness | {fi:.4f} | >= {TARGET_FITNESS} | {fitness_status} |\n"
        f"| Turnover | {to:.4f} | — | {turnover_status} |\n"
        f"| Returns | {rt * 100:.2f}% | — | — |\n"
        f"| Drawdown | {dd * 100:.2f}% | — | — |\n\n"
        "### 年度表现\n"
        f"{yearly}\n\n"
        "## 差距分析与改进建议\n"
        f"{gap}\n"
    )

    # ── 连续无提升 → 提示 AI 换 setting ──
    if no_improve_count >= SETTING_CHANGE_THRESHOLD:
        user += (
            f"\n## ⚠️ 已连续 {no_improve_count} 轮无提升！\n"
            "当前 setting 可能已到瓶颈，**请大胆调整回测参数**：\n"
            "- 换 neutralization（如 MARKET → SUBINDUSTRY 或反之）\n"
            "- 换 decay（如 4 → 8 或 2）\n"
            "- 换 universe（如 TOP3000 → TOP1000）\n"
            "- 同时尝试完全不同的因子逻辑方向\n\n"
        )

    if failed:
        user += f"\n{failed}\n"

    user += (
        "\n## 要求\n"
        "请在当前最优 alpha 的基础上改进。你可以：\n"
        "1. 调整表达式结构（加入新算子、组合因子、改变窗口期）\n"
        "2. 调整 settings（decay、neutralization 等）\n"
        "3. 保留有效的核心逻辑，针对性改进薄弱环节\n"
        "4. **只使用参考资料中列出的字段和函数，不要编造不存在的字段**\n\n"
        f"请生成 {ALPHAS_PER_ROUND} 个改进方案。\n\n"
        f"{SETTING_SPEC}\n\n"
        f"{OUTPUT_FORMAT}\n"
    )

    return system, user