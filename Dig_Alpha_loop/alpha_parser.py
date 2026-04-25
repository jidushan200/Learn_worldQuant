"""
从 AI 返回的文本中提取 alpha JSON 数组
"""

import json
import re


def parse_alphas_from_response(text: str) -> list[dict]:
    """
    尝试多种方式从 AI 回复中提取 [{"name":..., "expr":...}, ...]
    """

    # 1) ```json ... ``` 代码块
    for m in re.finditer(r"```(?:json)?\s*\n(.*?)\n\s*```", text, re.DOTALL):
        result = _try_parse(m.group(1))
        if result:
            return result

    # 2) 裸 JSON 数组 [...]
    for m in re.finditer(r"(\[\s*\{.*?\}\s*\])", text, re.DOTALL):
        result = _try_parse(m.group(1))
        if result:
            return result

    # 3) 整段文本
    result = _try_parse(text.strip())
    if result:
        return result

    raise ValueError(
        "无法从 AI 响应中提取有效的 alpha JSON。\n"
        f"响应前 500 字：{text[:500]}"
    )


def _try_parse(raw: str) -> list[dict] | None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    if not isinstance(data, list) or not data:
        return None

    valid = []
    for item in data:
        if isinstance(item, dict) and "name" in item and "expr" in item:
            entry = {
                "name": str(item["name"]).strip(),
                "expr": str(item["expr"]).strip(),
            }
            if "setting" in item and isinstance(item["setting"], dict):
                entry["setting"] = item["setting"]
            valid.append(entry)

    return valid if valid else None