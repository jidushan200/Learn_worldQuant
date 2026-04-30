"""
解析 AI 返回的 alpha JSON —— 新格式：[{name, expr, setting}, ...]
"""

import json
import re
from setting import DEFAULT_SETTING


def parse_alpha_list(raw: str) -> list[dict]:
    """
    从 AI 原始回复中提取 alpha 列表。
    返回 [{name, expr, setting}, ...]
    """
    text = raw.strip()

    # 去掉 markdown 代码块
    m = re.search(r"```(?:json)?\s*(\[.*?])\s*```", text, re.S)
    if m:
        text = m.group(1)
    else:
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            text = text[start:end + 1]

    try:
        arr = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON 解析失败: {e}")
        print(f"     原始文本前200字: {text[:200]}")
        return []

    if not isinstance(arr, list):
        print("  ❌ AI 返回的不是 JSON 数组")
        return []

    results = []
    for i, item in enumerate(arr):
        if not isinstance(item, dict):
            print(f"  ⚠️  第 {i} 个元素不是对象，跳过")
            continue

        # 兼容 expr / expression 两种 key
        expr = item.get("expr") or item.get("expression") or ""
        expr = expr.strip()
        if not expr:
            print(f"  ⚠️  第 {i} 个元素没有 expr，跳过")
            continue

        name = item.get("name") or item.get("desc") or f"alpha_{i}"
        name = name.strip()

        # setting：AI 提供的优先，否则用默认值
        raw_setting = item.get("setting") or item.get("settings") or {}
        setting = {**DEFAULT_SETTING}
        if isinstance(raw_setting, dict):
            setting.update(raw_setting)

        results.append({
            "name": name,
            "expr": expr,
            "setting": setting,
        })

    print(f"  ✅ 成功解析 {len(results)} 个 alpha")
    return results