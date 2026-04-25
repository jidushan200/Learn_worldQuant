"""
AI 调用层 —— 支持 packy / poe / openai / anthropic
PackyAPI 走 OpenAI 兼容接口（https://www.packyapi.com/v1）
Poe    走 OpenAI 兼容接口（https://api.poe.com/v1）
"""

import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv(override=False)


def _provider() -> str:
    p = (os.environ.get("AI_PROVIDER") or "").strip().lower()
    if not p:
        raise RuntimeError(
            "请在 .env 中配置 AI_PROVIDER\n"
            "可选值: packy / poe / openai / anthropic"
        )
    return p


# ═══════════════════════════════════════════════════════════
#  公开接口
# ═══════════════════════════════════════════════════════════

def chat(system_prompt: str, user_prompt: str) -> str:
    p = _provider()
    dispatch = {
        "packy":     _chat_packy,
        "poe":       _chat_poe,
        "openai":    _chat_openai,
        "anthropic": _chat_anthropic,
    }
    fn = dispatch.get(p)
    if fn is None:
        raise ValueError(
            f"不支持的 AI_PROVIDER={p}，可选: packy / poe / openai / anthropic"
        )

    last_err = None
    for attempt in range(1, 4):
        try:
            return fn(system_prompt, user_prompt)
        except Exception as e:
            last_err = e
            wait = 5 * attempt
            print(f"  ⚠️  AI 调用失败 (attempt {attempt}/3)，{wait}s 后重试: {e}")
            if attempt < 3:
                time.sleep(wait)
    raise last_err


def judge(result_json: str) -> dict:
    from setting import JUDGE_ENABLED, JUDGE_PROMPT_TMPL

    if not JUDGE_ENABLED:
        return {"verdict": "SKIP", "comment": "研判未启用"}

    prompt = JUDGE_PROMPT_TMPL.format(result_json=result_json)
    raw = chat("", prompt)

    verdict = "PASS" if "PASS" in raw.upper() else "FAIL"
    return {"verdict": verdict, "comment": raw}


# ═══════════════════════════════════════════════════════════
#  PackyAPI（OpenAI 兼容接口，推荐）
# ═══════════════════════════════════════════════════════════

def _chat_packy(system_prompt: str, user_prompt: str) -> str:
    api_key  = (os.environ.get("PACKY_API_KEY")  or "").strip()
    model    = (os.environ.get("PACKY_MODEL")    or "gpt-5.4").strip()
    base_url = (os.environ.get("PACKY_BASE_URL")
                or "https://www.packyapi.com/v1").strip().rstrip("/")

    if not api_key:
        raise RuntimeError(
            "请在 .env 中配置 PACKY_API_KEY\n"
            "获取方式: https://www.packyapi.com → 控制台 → 令牌管理 → 创建令牌"
        )

    messages = [{"role": "user", "content": user_prompt}]

    body = {
        "model":       model,
        "messages":    messages,
        "temperature": 0.7,
        "max_tokens":  4096,
    }

    # Claude 模型不支持 messages 里的 system role，需用顶层 system 参数
    # 非 Claude 模型（如 gpt-4o）则放到 messages 里
    if system_prompt:
        if model.startswith("claude"):
            body["system"] = system_prompt
        else:
            messages.insert(0, {"role": "system", "content": system_prompt})

    resp = requests.post(
        f"{base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
        },
        json=body,
        timeout=120,
    )

    if resp.status_code != 200:
        raise RuntimeError(
            f"PackyAPI 错误: HTTP {resp.status_code}\n{resp.text[:500]}"
        )

    return resp.json()["choices"][0]["message"]["content"]

# ═══════════════════════════════════════════════════════════
#  Poe（OpenAI 兼容接口）
# ═══════════════════════════════════════════════════════════

def _chat_poe(system_prompt: str, user_prompt: str) -> str:
    api_key = (os.environ.get("POE_API_KEY") or "").strip()
    model   = (os.environ.get("POE_MODEL")   or "gpt-5.4").strip()

    if not api_key:
        raise RuntimeError(
            "请在 .env 中配置 POE_API_KEY\n"
            "获取方式: https://poe.com/api → 创建 API Key"
        )

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    resp = requests.post(
        "https://api.poe.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
        },
        json={
            "model":       model,
            "messages":    messages,
            "temperature": 0.7,
            "max_tokens":  4096,
        },
        timeout=120,
    )

    if resp.status_code != 200:
        raise RuntimeError(
            f"Poe API 错误: HTTP {resp.status_code}\n{resp.text[:500]}"
        )

    return resp.json()["choices"][0]["message"]["content"]


# ═══════════════════════════════════════════════════════════
#  OpenAI（直连或任何兼容接口）
# ═══════════════════════════════════════════════════════════

def _chat_openai(system_prompt: str, user_prompt: str) -> str:
    api_key  = (os.environ.get("OPENAI_API_KEY")  or "").strip()
    model    = (os.environ.get("OPENAI_MODEL")     or "gpt-4o").strip()
    base_url = (os.environ.get("OPENAI_BASE_URL")
                or "https://api.openai.com/v1").strip().rstrip("/")

    if not api_key:
        raise RuntimeError("请在 .env 中配置 OPENAI_API_KEY")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    resp = requests.post(
        f"{base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
        },
        json={
            "model":       model,
            "messages":    messages,
            "temperature": 0.7,
            "max_tokens":  4096,
        },
        timeout=120,
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"OpenAI 错误: HTTP {resp.status_code}\n{resp.text[:500]}"
        )

    return resp.json()["choices"][0]["message"]["content"]


# ═══════════════════════════════════════════════════════════
#  Anthropic（直连官方 API）
# ═══════════════════════════════════════════════════════════

def _chat_anthropic(system_prompt: str, user_prompt: str) -> str:
    api_key = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
    model   = (os.environ.get("ANTHROPIC_MODEL")
               or "claude-sonnet-4-20250514").strip()

    if not api_key:
        raise RuntimeError("请在 .env 中配置 ANTHROPIC_API_KEY")

    body = {
        "model":      model,
        "max_tokens": 4096,
        "messages":   [{"role": "user", "content": user_prompt}],
    }
    if system_prompt:
        body["system"] = system_prompt

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key":         api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type":      "application/json",
        },
        json=body,
        timeout=120,
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"Anthropic 错误: HTTP {resp.status_code}\n{resp.text[:500]}"
        )

    return resp.json()["content"][0]["text"]