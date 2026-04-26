"""
Prompt 工具函数 —— 加载参考资料、字段文档、grade 比较
"""

import os
from setting import (
    INITIAL_PROMPT_FILE,
    ALPHA_EXAMPLES_FILE, MAX_EXAMPLES_CHARS,
    PAPER_NOTES_FILE, MAX_PAPERS_CHARS,
    FIELDS_FILE, MAX_FIELDS_CHARS,
    MAX_IDEA_CHARS,
)


# ═══════════════════════════════════════════════════════════
#  Grade 比较
# ═══════════════════════════════════════════════════════════

_GRADE_ORDER = {
    "REJECT":  0,
    "FAIL":    0,
    "LOW":     1,
    "MEDIUM":  2,
    "MID":     2,
    "HIGH":    3,
    "GOOD":    4,
    "GREAT":   5,
    "SUPERIOR":6,
}


def grade_ge(a: str, b: str) -> bool:
    """a 的 grade 是否 >= b"""
    va = _GRADE_ORDER.get((a or "").upper().strip(), -1)
    vb = _GRADE_ORDER.get((b or "").upper().strip(), -1)
    return va >= vb


# ═══════════════════════════════════════════════════════════
#  加载策略思路
# ═══════════════════════════════════════════════════════════

def load_initial_idea() -> str:
    """从 strategy_prompt.txt 读取用户策略思路，截断到 MAX_IDEA_CHARS"""
    if not os.path.isfile(INITIAL_PROMPT_FILE):
        return ""
    with open(INITIAL_PROMPT_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
    if len(content) > MAX_IDEA_CHARS:
        content = content[:MAX_IDEA_CHARS] + "\n... (已截断)"
    return content


# ═══════════════════════════════════════════════════════════
#  加载 Alpha 示例
# ═══════════════════════════════════════════════════════════

def load_alpha_examples() -> str:
    """从 alpha_examples.txt 读取示例，截断到 MAX_EXAMPLES_CHARS"""
    if not os.path.isfile(ALPHA_EXAMPLES_FILE):
        return ""
    with open(ALPHA_EXAMPLES_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
    if not content:
        return ""
    if len(content) > MAX_EXAMPLES_CHARS:
        truncated = content[:MAX_EXAMPLES_CHARS]
        last_nl = truncated.rfind("\n")
        if last_nl > 0:
            truncated = truncated[:last_nl]
        return truncated + "\n... (已截断)"
    return content


# ═══════════════════════════════════════════════════════════
#  加载论文笔记
# ═══════════════════════════════════════════════════════════

def load_paper_notes() -> str:
    """从 paper_notes.txt 读取论文笔记，截断到 MAX_PAPERS_CHARS"""
    if not os.path.isfile(PAPER_NOTES_FILE):
        return ""
    with open(PAPER_NOTES_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
    if not content:
        return ""
    if len(content) > MAX_PAPERS_CHARS:
        truncated = content[:MAX_PAPERS_CHARS]
        last_nl = truncated.rfind("\n")
        if last_nl > 0:
            truncated = truncated[:last_nl]
        return truncated + "\n... (已截断)"
    return content


# ═══════════════════════════════════════════════════════════
#  加载字段文档
# ═══════════════════════════════════════════════════════════

def load_fields_doc() -> str:
    """
    加载 fields.md 字段参考文档。
    优先保留顶部摘要（前缀规则 + 简单别名），
    剩余空间尽量多放完整字段列表。
    """
    if not os.path.isfile(FIELDS_FILE):
        print("  ⚠️  fields.md 不存在，AI 将无字段约束")
        return ""

    with open(FIELDS_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
    if not content:
        return ""

    marker = "下面是所有的字段："
    if marker in content:
        summary, full_list = content.split(marker, 1)
        summary = summary.strip()
        full_list = full_list.strip()
        total_fields = len(full_list.splitlines())

        budget = MAX_FIELDS_CHARS - len(summary) - 200
        if budget > 0 and full_list:
            chunk = full_list[:budget]
            last_nl = chunk.rfind("\n")
            if last_nl > 0:
                chunk = chunk[:last_nl]
            return (
                f"{summary}\n\n{marker}\n{chunk}\n"
                f"... (完整字段列表共 {total_fields} 个，详见 fields.md)"
            )
        return summary

    if len(content) > MAX_FIELDS_CHARS:
        truncated = content[:MAX_FIELDS_CHARS]
        last_nl = truncated.rfind("\n")
        if last_nl > 0:
            truncated = truncated[:last_nl]
        return truncated + "\n... (已截断，完整列表见 fields.md)"

    return content