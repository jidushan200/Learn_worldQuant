"""
构建发给 AI 的 prompt —— 初始轮 / 迭代轮
支持从 knowledge/ 目录加载字段、函数、范例、论文等参考资料
"""

import os
import glob
from setting import (
    TARGET_SHARPE, TARGET_FITNESS, TARGET_GRADE,
    ALPHAS_PER_ROUND, INITIAL_PROMPT_FILE, KNOWLEDGE_DIR,
    KNOWLEDGE_EVERY_ROUND,
)


# ═══════════════════════════════════════════════════════════
#  知识库加载
# ═══════════════════════════════════════════════════════════

_KNOWLEDGE_FILES = {
    "fields.md":    "## 平台数据字段参考",
    "functions.md": "## 平台函数参考",
    "examples.md":  "## 成功 Alpha 表达式范例",
    "papers.md":    "## 论文 / 因子研究参考",
    "tips.md":      "## 调参技巧与经验",
}


def _load_knowledge() -> str:
    """加载 knowledge/ 目录下的所有参考资料，拼成 prompt 段落"""
    if not os.path.isdir(KNOWLEDGE_DIR):
        return ""

    sections = []

    # 1. 先加载预定义的文件（按固定顺序）
    loaded_files = set()
    for filename, title in _KNOWLEDGE_FILES.items():
        path = os.path.join(KNOWLEDGE_DIR, filename)
        if os.path.exists(path):
            content = _read_file(path)
            if content:
                sections.append(f"{title}\n{content}")
                loaded_files.add(filename)

    # 2. 再加载目录下其他 .md / .txt 文件
    for path in sorted(glob.glob(os.path.join(KNOWLEDGE_DIR, "*"))):
        fname = os.path.basename(path)
        if fname in loaded_files:
            continue
        if not fname.endswith((".md", ".txt")):
            continue
        content = _read_file(path)
        if content:
            nice_name = os.path.splitext(fname)[0].replace("_", " ").title()
            sections.append(f"## 参考资料: {nice_name}\n{content}")

    if not sections:
        return ""

    return (
        "\n\n---\n"
        "# 📚 参考知识库（请充分利用以下信息来设计 alpha）\n\n"
        + "\n\n".join(sections)
        + "\n\n---\n\n"
    )


def _read_file(path: str, max_chars: int = 15000) -> str:
    """读取文件，超长则截断"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n\n... (截断，原文共 {len(content)} 字符)"
        return content
    except Exception as e:
        print(f"  ⚠️  读取 {path} 失败: {e}")
        return ""


# ═══════════════════════════════════════════════════════════
#  系统 Prompt
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
    "4. 关注自相关、换手率、覆盖率等 checks 指标"
)


# ═══════════════════════════════════════════════════════════
#  Setting 说明 & 输出格式
# ═══════════════════════════════════════════════════════════

SETTING_SPEC = (
    "## 回测参数说明（setting 字段）\n"
    "每个 alpha 必须包含 setting 字段，可选值如下：\n\n"
    "| 参数 | 可选值 | 说明 |\n"
    "|------|--------|------|\n"
    '| instrumentType | "EQUITY" | 固定 |\n'
    '| region | "USA", "CHN", "EUR", "ASI", "GLB" | 市场区域 |\n'
    '| universe | "TOP200", "TOP500", "TOP1000", "TOP2000", "TOP3000" | 股票池 |\n'
    "| delay | 0, 1 | 信号延迟天数 |\n"
    "| decay | 0~20 整数 | 线性衰减天数 |\n"
    '| neutralization | "NONE", "MARKET", "SECTOR", "INDUSTRY", "SUBINDUSTRY" | 中性化 |\n'
    "| truncation | 0.01~0.10 | 截断比例 |\n"
    '| pasteurization | "ON", "OFF" | 巴氏灭菌 |\n'
    '| unitHandling | "VERIFY", "NONE" | 单位处理 |\n'
    '| nanHandling | "ON", "OFF" | NaN处理 |\n'
    '| language | "FASTEXPR" | 固定 |\n\n'
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
    "**注意：每个 alpha 的 setting 应根据因子特性单独调参，不要所有 alpha 用同样的 setting。**\n"
)


# ═══════════════════════════════════════════════════════════
#  Grade 工具
# ═══════════════════════════════════════════════════════════

GRADE_ORDER = ["INFERIOR", "WEAK", "NORMAL", "GOOD", "STRONG", "EXCELLENT"]


def grade_ge(actual: str, target: str) -> bool:
    """判断 actual grade 是否 >= target grade"""
    actual_upper = (actual or "").strip().upper()
    target_upper = (target or "").strip().upper()
    if actual_upper not in GRADE_ORDER or target_upper not in GRADE_ORDER:
        return False
    return GRADE_ORDER.index(actual_upper) >= GRADE_ORDER.index(target_upper)


# ═══════════════════════════════════════════════════════════
#  加载用户策略思路
# ═══════════════════════════════════════════════════════════

def load_initial_idea() -> str:
    if not os.path.exists(INITIAL_PROMPT_FILE):
        return ""
    with open(INITIAL_PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()


# ═══════════════════════════════════════════════════════════
#  第 1 轮 Prompt（始终带知识库）
# ═══════════════════════════════════════════════════════════

def build_initial_prompt(idea: str) -> tuple[str, str]:
    knowledge = _load_knowledge()

    user = (
        f"## 用户策略思路\n{idea}\n\n"
        f"{knowledge}"
        f"## 任务\n"
        f"请根据以上思路和参考资料，生成 {ALPHAS_PER_ROUND} 个多样化的 alpha 表达式。\n\n"
        f"## 要求\n"
        f"1. 使用 FASTEXPR 语法，**只使用参考资料中列出的字段和函数**\n"
        f"2. 每个 alpha 之间应有显著差异（不同因子、不同窗口期、不同组合方式）\n"
        f"3. **核心目标：grade 达到 {TARGET_GRADE} 或以上**\n"
        f"   （参考指标：Sharpe >= {TARGET_SHARPE}，Fitness >= {TARGET_FITNESS}）\n"
        f"4. name 字段用简短英文标识因子含义\n"
        f"5. 考虑因子的经济学逻辑和衰减特性\n"
        f"6. 每个 alpha 必须包含独立的 setting，根据因子特性单独调参\n"
        f"7. 重视通过平台全部 checks（低自相关、足够覆盖率、合理换手等）\n"
        f"8. 参考成功范例的结构，但不要照抄\n\n"
        f"{SETTING_SPEC}\n"
        f"{OUTPUT_FORMAT}\n"
    )
    return SYSTEM_PROMPT, user


# ═══════════════════════════════════════════════════════════
#  第 N 轮 Prompt（根据开关决定是否带知识库）
# ═══════════════════════════════════════════════════════════

def build_iteration_prompt(
    idea: str,
    iteration: int,
    history: list[dict],
) -> tuple[str, str]:

    if KNOWLEDGE_EVERY_ROUND:
        knowledge = _load_knowledge()
        knowledge_hint = ""
    else:
        knowledge = ""
        knowledge_hint = "（参考资料已在第1轮提供，请继续基于那些字段和函数设计）\n\n"

    hist_text = _format_history(history)

    all_ok = [
        r for h in history for r in h["results"]
        if isinstance(r.get("sharpe"), (int, float)) and not r.get("error")
    ]
    best_sh = max((r["sharpe"] for r in all_ok), default=0)
    best_fi = max((r.get("fitness", 0) for r in all_ok), default=0)
    best_gr = _best_grade([r.get("grade", "") for r in all_ok])

    user = (
        f"## 用户策略思路\n{idea}\n\n"
        f"{knowledge}"
        f"{knowledge_hint}"
        f"## 目标\n"
        f"- **核心目标：grade 达到 {TARGET_GRADE} 或以上**\n"
        f"- 参考指标：Sharpe >= {TARGET_SHARPE}，Fitness >= {TARGET_FITNESS}\n\n"
        f"## 当前进度\n"
        f"- 已完成 {len(history)} 轮，即将开始第 {iteration} 轮\n"
        f"- 历史最佳 Sharpe = {best_sh:.4f}，Fitness = {best_fi:.4f}，"
        f"最佳 Grade = {best_gr or 'N/A'}\n\n"
        f"## 历史回测结果\n{hist_text}\n\n"
        f"## 第 {iteration} 轮任务\n"
        f"请仔细分析以上所有历史结果和参考资料，然后：\n"
        f"1. 总结哪些因子方向/结构有效，哪些无效或报错\n"
        f"2. 重点关注 **grade** 和 **checks 通过情况**，找出制约 grade 的瓶颈\n"
        f"3. 对效果好的 alpha 做深入变体（调窗口、调权重、换组合方式、加入新因子）\n"
        f"4. **同时优化 setting 参数**（对比不同 decay/neutralization/universe 的效果）\n"
        f"5. 引入 1-2 个全新思路（可参考论文），避免局部最优\n"
        f"6. 生成 {ALPHAS_PER_ROUND} 个 **全新的、未测试过的** alpha 表达式\n"
        f"7. **只使用参考资料中列出的字段和函数**，绝不编造\n"
        f"8. 绝不重复之前已测试的表达式\n\n"
        f"{SETTING_SPEC}\n"
        f"{OUTPUT_FORMAT}\n"
    )
    return SYSTEM_PROMPT, user


# ═══════════════════════════════════════════════════════════
#  格式化历史记录
# ═══════════════════════════════════════════════════════════

def _format_history(history: list[dict]) -> str:
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
                sh   = _f(r.get("sharpe"), 4)
                fi   = _f(r.get("fitness"), 4)
                to   = _pct(r.get("turnover"))
                ret  = _pct(r.get("returns"), 2)
                dd   = _pct(r.get("drawdown"), 2)
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


def _best_grade(grades: list[str]) -> str:
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


def _f(v, d=2):
    return f"{v:.{d}f}" if isinstance(v, (int, float)) else "N/A"

def _pct(v, d=1):
    return f"{v * 100:.{d}f}%" if isinstance(v, (int, float)) else "N/A"