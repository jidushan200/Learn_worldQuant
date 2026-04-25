"""
知识库加载 —— 从 knowledge/ 目录读取字段、函数、范例、论文等参考资料
独立于 prompt 业务逻辑，纯 I/O 模块
"""

import os
import glob
from setting import KNOWLEDGE_DIR


# ── 预定义的知识库文件及其标题（按此顺序优先加载） ──
_KNOWLEDGE_FILES = {
    "fields.md":    "## 平台数据字段参考",
    "functions.md": "## 平台函数参考",
    "examples.md":  "## 成功 Alpha 表达式范例",
    "papers.md":    "## 论文 / 因子研究参考",
    "tips.md":      "## 调参技巧与经验",
}


def _read_file(path: str, max_chars: int = 50000) -> str:
    """读取单个文件，超长时截断"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n\n... (截断，原文共 {len(content)} 字符)"
        return content
    except Exception as e:
        print(f"  ⚠️  读取 {path} 失败: {e}")
        return ""


def load_knowledge() -> str:
    """
    加载 KNOWLEDGE_DIR 下的所有参考资料，拼接成一段 Markdown 文本。
    优先加载 _KNOWLEDGE_FILES 中定义的文件（保序），
    然后扫描目录中剩余的 .md / .txt 文件。
    目录不存在或无内容时返回空字符串。
    """
    if not os.path.isdir(KNOWLEDGE_DIR):
        return ""

    sections = []

    loaded_files = set()
    for filename, title in _KNOWLEDGE_FILES.items():
        path = os.path.join(KNOWLEDGE_DIR, filename)
        if os.path.exists(path):
            content = _read_file(path)
            if content:
                sections.append(f"{title}\n{content}")
                loaded_files.add(filename)

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