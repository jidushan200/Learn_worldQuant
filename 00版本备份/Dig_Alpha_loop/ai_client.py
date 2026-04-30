"""
AI 客户端 - Responses API 流式请求（gpt-5.4）
"""

import requests
import json
import os
from dotenv import load_dotenv
from auth_client import get_required_env

# 加载 .env 文件中的环境变量
load_dotenv()

# 直接从环境变量读取，与 load_credentials 风格一致
API_KEY = get_required_env("PACKY_API_KEY")
MODEL = get_required_env("PACKY_MODEL")
BASE_URL = get_required_env("PACKY_BASE_URL")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def chat(system_msg: str, user_msg: str, max_tokens: int = 4096) -> str:
    """Responses API 流式请求，返回完整字符串，drop-in 替换原 chat()"""
    payload = {
        "model": MODEL,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": f"{system_msg}\n\n{user_msg}"}
                ],
            },
        ],
        "store": False,
        "include": ["reasoning.encrypted_content"],
        "stream": True,
    }

    try:
        r = requests.post(
            f"{BASE_URL}/responses",
            headers=HEADERS,
            json=payload,
            timeout=(30, 300),
            stream=True,
        )
        r.raise_for_status()
        r.encoding = "utf-8"
    except requests.exceptions.HTTPError as e:
        print(f"[API 请求失败] {e}")
        try:
            print(f"[响应内容] {e.response.text}")
        except Exception:
            pass
        return ""
    except requests.exceptions.RequestException as e:
        print(f"[API 请求失败] {e}")
        return ""

    collected = []
    for line in r.iter_lines(decode_unicode=True):
        if not line:
            continue
        if line.startswith("event:"):
            continue
        if not line.startswith("data: "):
            continue
        raw = line[6:]
        if raw == "[DONE]":
            break
        try:
            chunk = json.loads(raw)
            if chunk.get("type") == "response.output_text.delta":
                delta = chunk.get("delta", "")
                if delta:
                    collected.append(delta)
        except (json.JSONDecodeError, KeyError, IndexError):
            continue

    result = "".join(collected)
    if not result:
        print("[警告] 流式响应为空")
    return result


if __name__ == "__main__":
    print("测试流式请求...")
    reply = chat(
        "你是量化专家，只用中文回答。",
        "用一句话解释什么是 alpha 因子。"
    )
    print(f"回复({len(reply)}字): {reply}")
