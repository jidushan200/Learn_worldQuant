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


def _load_knowledge() -> str:
    """加载 knowledge/ 文件夹下所有 .md 文件作为重定向时的参考资料"""
    knowledge_dir = "knowledge"
    if not os.path.isdir(knowledge_dir):
        return ""

    parts = []
    for filename in sorted(os.listdir(knowledge_dir)):
        if not filename.endswith(".md"):
            continue
        filepath = os.path.join(knowledge_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content:
                label = filename.replace(".md", "").replace("_", " ").title()
                parts.append(f"### {label}\n{content}")
        except Exception as e:
            print(f"  ⚠️ 加载 {filepath} 失败: {e}")
            continue

    return "\n\n".join(parts)