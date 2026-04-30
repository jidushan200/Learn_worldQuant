"""
Prompt 构造器 —— 将策略、历史、参考资料、字段约束组装成 system / user prompt
"""

from prompt_utils import (
    load_alpha_examples,
    load_paper_notes,
    load_fields_doc,
)
from knowledge_loader import (
    _load_knowledge
)
from setting import (
    BATCH_SIZE, TARGET_GRADE, TARGET_SHARPE, TARGET_FITNESS,MAX_IMPROVE_ATTEMPTS
)

# ═══════════════════════════════════════════════════════════
#  内部 helpers
# ═══════════════════════════════════════════════════════════

def _system_base() -> str:
    fields_doc = load_fields_doc()

    base = (
        "你是一位顶级量化研究员，专精 WorldQuant Brain 平台的 FAST Expression 语法。\n"
        "你的任务是根据用户的策略思路，生成可在 Brain 平台回测的 alpha 表达式。\n\n"
        "## 核心规则\n"
        "1. 每个 alpha 必须是一个完整的 FAST Expression，可以直接粘贴到平台运行。如果一个Alpha质量不好，不要钻牛角尖，及时变通，改变策略\n"
        "2. 只能使用下方「可用字段」中列出的字段名，严禁自行编造或猜测不存在的字段。\n"
        "3. 特别注意 必须严格参照字段文档中的归属。而且在制作Alpha时尽量先保证setting的固定，在固定setting的基础上变化Alpha\n"
        "4. 如果不确定某字段属于哪个前缀，优先使用无前缀的简单别名"
        "（如 sales, ebit, revenue, cashflow_op 等）。\n"
        "5. 只使用 FAST Expression 支持的函数和运算符（rank, ts_rank, ts_zscore, "
        "ts_regression, group_rank, ts_delta, ts_mean, ts_std_dev, "
        "ts_arg_max, ts_arg_min, ts_corr, ts_covariance, ts_decay_linear, "
        "ts_decay_exp_window, ts_min, ts_max, ts_sum, ts_product, "
        "ts_skewness, ts_kurtosis, signed_power, log, abs, divide, "
        "add, subtract, multiply, min, max, clamp, if_else, less, "
        "greater, equals, and_op, or_op, not_op, is_nan, purify, "
        "filter, trade_when 等）。\n\n"
        "## Checks 评估说明\n"
        "平台会对每个 alpha 执行一系列 checks，每项结果为 PASS / FAIL / WARNING / PENDING：\n"
        "- LOW_SHARPE: Sharpe 不得低于 limit（通常 1.25）\n"
        "- LOW_FITNESS: Fitness 不得低于 limit（通常 1.0）\n"
        "- LOW_TURNOVER / HIGH_TURNOVER: 换手率需在合理范围内\n"
        "- CONCENTRATED_WEIGHT: 持仓权重不能过于集中\n"
        "- LOW_SUB_UNIVERSE_SHARPE: 子宇宙 Sharpe 不得低于 limit\n"
        "- UNITS: 表达式中存在单位维度不兼容（通常是 group 操作后直接做除法导致）\n"
        "- SELF_CORRELATION: 与已提交 alpha 的相关性检测\n"
        "- MATCHES_COMPETITION: 是否符合比赛要求\n"
        "所有 checks 必须无 FAIL 才能提交。请根据 FAIL 项的 value 和 limit 差距针对性优化。\n\n"
        "## Yearly Performance 说明\n"
        "回测会返回每年的详细数据，包括 Sharpe、Turnover、Fitness、Returns、Drawdown、\n"
        "Margin、Long Count、Short Count。请特别关注表现差的年份（如 Sharpe 为负），\n"
        "思考因子在哪类市场环境中失效，并针对性改进。\n\n"
        "## 输出格式（严格遵守）\n"
        "输出必须是纯 JSON 数组，不要输出任何其他文字。\n"
        "每个元素包含三个字段：\n"
        '  - "name"：简短唯一的因子命名（英文+下划线+数字）\n'
        '  - "expr"：完整的 FAST Expression 字符串\n'
        '  - "setting"：回测参数对象，包含以下字段：\n'
        '      instrumentType, region, universe, delay, decay,\n'
        '      neutralization, truncation, pasteurization,\n'
        '      unitHandling, nanHandling, language, visualization\n'
        "示例：\n"
        '[{"name":"demo_alpha","expr":"rank(close)","setting":{'
        '"instrumentType":"EQUITY","region":"USA","universe":"TOP3000",'
        '"delay":1,"decay":0,"neutralization":"SUBINDUSTRY",'
        '"truncation":0.08,"pasteurization":"ON",'
        '"unitHandling":"VERIFY","nanHandling":"OFF",'
        '"language":"FASTEXPR","visualization":false}}]\n'
    )

    if fields_doc:
        base += (
            "\n## 可用字段（严格限制）\n"
            "以下是你唯一允许使用的数据字段。\n"
            "使用不存在的字段会导致回测直接报错，请务必逐字核对字段名。\n\n"
            f"{fields_doc}\n"
        )

    return base

def _fmt_checks(checks: list[dict]) -> str:
    """将 checks 数组格式化为紧凑可读的文本"""
    if not checks:
        return "  checks: 无数据\n"

    lines = []
    seen_warnings = {}

    for c in checks:
        name = c.get("name", "?")
        result = c.get("result", "?")
        value = c.get("value")
        limit = c.get("limit")
        message = c.get("message")
        competitions = c.get("competitions")

        if result == "WARNING":
            # 合并重复的 WARNING
            key = name
            seen_warnings[key] = seen_warnings.get(key, 0) + 1
            if seen_warnings[key] > 1:
                continue
            # 第一次出现时先占位，后面补数量
            line = f"    ⚠️  {name}: WARNING"
            if message:
                # 截取关键信息
                msg_short = message if len(message) <= 80 else message[:77] + "..."
                line += f" - {msg_short}"
            lines.append((key, line))
        elif result == "FAIL":
            line = f"    ❌ {name}: FAIL (value={value}, limit={limit})"
            lines.append((None, line))
        elif result == "PASS":
            line = f"    ✅ {name}: PASS"
            if value is not None and limit is not None:
                line += f" (value={value}, limit={limit})"
            if competitions:
                comp_names = [comp.get("name", comp.get("id", "?")) for comp in competitions]
                line += f" → 匹配比赛: {', '.join(comp_names)}"
            lines.append((None, line))
        elif result == "PENDING":
            line = f"    ⏳ {name}: PENDING"
            lines.append((None, line))
        else:
            line = f"    {name}: {result}"
            lines.append((None, line))

    # 回填 WARNING 数量
    formatted = []
    for key, line in lines:
        if key and seen_warnings.get(key, 0) > 1:
            line += f" (共 {seen_warnings[key]} 次)"
        formatted.append(line)

    return "  checks:\n" + "\n".join(formatted) + "\n"

def _fmt_history(
    best_alpha: dict | None,
    last_results: list[dict] | None,
) -> str:
    parts: list[str] = []
    if best_alpha:
        ba = best_alpha
        parts.append(
            f"\n## 当前全局最佳 Alpha\n"
            f"- expr: {ba.get('expr', '?')}\n"
            f"- sharpe: {ba.get('sharpe', 0):.4f}\n"
            f"- fitness: {ba.get('fitness', 0):.4f}\n"
            f"- turnover: {ba.get('turnover', 0):.4f}\n"
            f"- returns: {ba.get('returns', 0):.4f}\n"
            f"- drawdown: {ba.get('drawdown', 0):.4f}\n"
            f"- margin: {ba.get('margin', 0):.6f}\n"
            f"- checks_pass: {ba.get('checks_pass', False)}\n"
        )
        if ba.get("checks"):
            parts.append(_fmt_checks(ba["checks"]))
        if ba.get("yearly_stats"):
            parts.append(_fmt_yearly(ba["yearly_stats"]))

    if last_results:
        parts.append("\n## 上一轮回测结果\n")
        for i, r in enumerate(last_results, 1):
            aid = r.get("alpha_id") or "失败"
            expr = r.get("expr", "?")
            err = r.get("error")

            if err:
                parts.append(f"### Alpha {i}: [{aid}]\n")
                parts.append(f"  expr: {expr}\n")
                parts.append(f"  ❌ 错误: {err}\n\n")
            else:
                sh = r.get("sharpe", 0) or 0
                fi = r.get("fitness", 0) or 0
                tn = r.get("turnover", 0) or 0
                rt = r.get("returns", 0) or 0
                dd = r.get("drawdown", 0) or 0
                mg = r.get("margin", 0) or 0
                cp = r.get("checks_pass", False)

                parts.append(f"### Alpha {i}: [{aid}]\n")
                parts.append(f"  expr: {expr}\n")
                parts.append(
                    f"  sharpe={sh:.4f}, fitness={fi:.4f}, "
                    f"turnover={tn:.4f}, returns={rt:.4f}, "
                    f"drawdown={dd:.4f}, margin={mg:.6f}, "
                    f"checks_pass={cp}\n"
                )
                if r.get("checks"):
                    parts.append(_fmt_checks(r["checks"]))
                if r.get("yearly_stats"):
                    parts.append(_fmt_yearly(r["yearly_stats"]))
                parts.append("")

    return "".join(parts)

def _fmt_yearly(yearly_stats: list[dict]) -> str:
    """把 yearly_stats 格式化成跟测试脚本一致的表格"""
    if not yearly_stats:
        return ""

    lines = ["  yearly performance:\n"]
    lines.append(
        f"    {'Year':>4} | {'Sharpe':>7} | {'Turnover':>9} | {'Fitness':>7} | "
        f"{'Returns':>8} | {'Drawdown':>9} | {'Margin':>9} | {'Long':>5} | {'Short':>5}\n"
    )
    for rec in yearly_stats:
        y  = rec.get("year", "?")
        sh = rec.get("sharpe", 0) or 0
        tn = rec.get("turnover", 0) or 0
        fi = rec.get("fitness", 0) or 0
        rt = rec.get("returns", 0) or 0
        dd = rec.get("drawdown", 0) or 0
        mg = rec.get("margin", 0) or 0
        lc = rec.get("longCount", 0) or 0
        sc = rec.get("shortCount", 0) or 0
        lines.append(
            f"    {y:>4} | {sh:>7.2f} | {tn*100:>8.2f}% | {fi:>7.2f} | "
            f"{rt*100:>7.2f}% | {dd*100:>8.2f}% | {mg*10000:>8.2f}‱ | {lc:>5} | {sc:>5}\n"
        )
    return "".join(lines)

def build_system_prompt() -> str:
    parts = [_system_base()]

    examples = load_alpha_examples()
    if examples:
        parts.append(f"\n## 优秀 Alpha 示例（仅供参考风格）\n{examples}\n")

    papers = load_paper_notes()
    if papers:
        parts.append(f"\n## 论文笔记（因子灵感来源）\n{papers}\n")

    return "\n".join(parts)


def _fmt_examples() -> str:
    examples = load_alpha_examples()
    if not examples:
        return ""
    return f"\n## 参考 Alpha 示例\n{examples}\n"


def _fmt_papers() -> str:
    papers = load_paper_notes()
    if not papers:
        return ""
    return f"\n## 论文笔记参考\n{papers}\n"


# ═══════════════════════════════════════════════════════════
#  User prompt
# ═══════════════════════════════════════════════════════════

def build_user_prompt(idea: str, history_block: str = "") -> str:
    parts = [
        f"策略思路：\n{idea}\n",
        f"请生成 {BATCH_SIZE} 个不同的 alpha 表达式。",
        f"目标：Sharpe >= {TARGET_SHARPE}，Fitness >= {TARGET_FITNESS}，"
        f"等级 >= {TARGET_GRADE}。"
        f"请注意，结果不良的Alpha最多修改{MAX_IMPROVE_ATTEMPTS}次",
        "每个 alpha 的思路、因子组合、参数应有明显差异。",
    ]
    if history_block:
        parts.append(f"\n## 历史回测结果（避免重复，从中学习）\n{history_block}")
    parts.append("\n请直接输出 JSON 数组，不要输出任何解释。")
    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════
#  公开接口
# ═══════════════════════════════════════════════════════════

def build_initial_prompt(idea: str) -> tuple[str, str]:
    """第一轮：基于策略思路生成初始 alpha"""
    sys_msg = _system_base()
    sys_msg += _fmt_examples()
    sys_msg += _fmt_papers()

    user_msg = (
        f"## 我的策略思路\n{idea}\n\n"
        f"请根据以上思路，生成 {BATCH_SIZE} 个不同的 alpha 表达式。\n"
        f"目标: Grade >= {TARGET_GRADE}, Sharpe >= {TARGET_SHARPE}, "
        f"Fitness >= {TARGET_FITNESS}\n\n"
        "⚠️ 提醒：所有字段必须来自上方「可用字段」列表，不得使用任何未列出的字段。\n\n"
        "输出格式（纯 JSON 数组，无其他文字）：\n"
        "```json\n"
        "[\n"
        '  {"name": "alpha_001_xxx", "expr": "...", "setting": {}},\n'
        '  {"name": "alpha_002_xxx", "expr": "...", "setting": {}}\n'
        "]\n"
        "```\n"
    )

    return sys_msg, user_msg


def build_iteration_prompt(
    idea: str,
    iteration: int,
    best_alpha: dict | None,
    last_results: list[dict] | None,
    *,
    no_improve_count: int = 0,
    need_redirect: bool = False,
) -> tuple[str, str]:
    """后续轮次：基于历史反馈迭代改进"""
    sys_msg = _system_base()
    sys_msg += _fmt_examples()
    sys_msg += _fmt_papers()

    # ★ 重定向时注入 knowledge
    if need_redirect:
        knowledge = _load_knowledge()
        if knowledge:
            sys_msg += (
                "\n## 参考知识库（请从中寻找新灵感）\n"
                f"{knowledge}\n"
            )

    sys_msg += _fmt_history(best_alpha, last_results)

    direction = ""
    if need_redirect:
        # ★ 重定向：强制换方向
        direction = (
            "\n🚨 上一轮超过 3 个 Alpha 回测失败（返回空结果），说明当前方向的表达式大量无效。\n"
            "请 **彻底更换因子构建方向**，不要在上一轮的表达式基础上修补。\n"
            "从上方「参考知识库」中选取一个全新的金融假设或因子组合思路重新出发。\n"
            "优先考虑：换用不同的数据字段、不同的时间窗口、不同的截面处理逻辑。\n"
        )
    elif no_improve_count >= 2:
        direction = (
            "\n⚠️ 已连续多轮没有改进，请大胆尝试全新的因子逻辑，"
            "不要在旧表达式上微调。考虑换一个完全不同的金融假设。\n"
        )

    user_msg = (
        f"## 第 {iteration} 轮迭代\n"
        f"策略思路: {idea}\n\n"
        f"请基于上一轮的反馈，生成 {BATCH_SIZE} 个改进后的 alpha 表达式。\n"
        f"目标: Grade >= {TARGET_GRADE}, Sharpe >= {TARGET_SHARPE}, "
        f"Fitness >= {TARGET_FITNESS}\n"
        f"{direction}\n"
        "⚠️ 提醒：所有字段必须来自上方「可用字段」列表，不得使用任何未列出的字段。\n\n"
        "输出格式（纯 JSON 数组，无其他文字）：\n"
        "```json\n"
        "[\n"
        '  {"name": "alpha_001_xxx", "expr": "...", "setting": {}},\n'
        '  {"name": "alpha_002_xxx", "expr": "...", "setting": {}}\n'
        "]\n"
        "```\n"
    )

    return sys_msg, user_msg

