import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import setting
from auth_client import create_authenticated_session
from submit_alpha import submit_and_wait
from logger import log_success


def load_alpha_expr(expr_file: str = setting.EXPR_FILE) -> str:
    p = Path(expr_file)
    if not p.exists():
        raise FileNotFoundError(f"未找到表达式文件: {expr_file}")

    text = p.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"表达式文件为空: {expr_file}")

    # 去掉 /* */ 块注释
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)

    lines = []
    for line in text.splitlines():
        line = re.sub(r"//.*$", "", line).strip()  # 去掉 // 行注释
        line = re.sub(r"#.*$", "", line).strip()   # 去掉 # 行注释
        if line:
            lines.append(line)

    if not lines:
        raise ValueError(f"表达式文件没有有效表达式: {expr_file}")

    return lines[0]


def pretty_raw(raw: Any) -> str:
    """格式化打印原始返回内容，方便排查错误"""
    if raw is None:
        return ""
    if isinstance(raw, (dict, list)):
        return json.dumps(raw, ensure_ascii=False, indent=2)
    return str(raw)


def run_account(account: str, alpha_expr: str) -> int:
    """单个账号的完整流程：登录 -> 提交 -> 等待结果 -> 写日志"""
    sess = None
    # 从 ACCOUNTS dict 拼别名，例如 "1446579723-ACC1"
    alias = f"{setting.ACCOUNTS[account]}-{account}"
    try:
        # 用指定账号登录，返回 session 和状态码
        sess, auth_status_code = create_authenticated_session(setting.ENV_FILE, account)
        print(f"[{alias}] auth status_code: {auth_status_code}")

        # 构造提交 payload
        alpha_payload = {
            "type": "REGULAR",
            "settings": setting.get_setting(),
            "regular": alpha_expr,
        }

        # 提交并等待 simulate 完成
        alpha_id, err, raw = submit_and_wait(
            sess=sess,
            alpha_payload=alpha_payload,
            max_wait_sec=setting.MAX_WAIT_SEC,
        )

        # 提交失败，打印错误信息
        if err:
            print(f"[{alias}] fail: {err}")
            print(f"[{alias}] expr: {alpha_expr}")
            if raw is not None:
                print(f"[{alias}] raw:")
                print(pretty_raw(raw))
            return 1

        # 提交成功，打印结果
        alpha_url = f"https://platform.worldquantbrain.com/alpha/{alpha_id}"
        print(f"[{alias}] expr: {alpha_expr}")
        print(f"[{alias}] alpha_id: {alpha_id}")
        print(f"[{alias}] alpha_url: {alpha_url}")

        # 写入日志
        log_success(
            log_file=setting.LOG_FILE,
            account=alias,
            expr=alpha_expr,
            alpha_id=alpha_id,
        )
        return 0

    except Exception as e:
        print(f"[{alias}] fatal: {e}")
        return 2

    finally:
        # 无论成功失败都关闭 session
        if sess is not None:
            sess.close()


def main() -> int:
    # 读取表达式
    try:
        alpha_expr = load_alpha_expr(setting.EXPR_FILE)
        print("loaded expr:", alpha_expr)
    except Exception as e:
        print("fatal:", e)
        return 2

    results = {}
    # 并发跑所有账号，每个账号一个线程
    with ThreadPoolExecutor(max_workers=len(setting.ACCOUNTS)) as executor:
        futures = {
            executor.submit(run_account, account, alpha_expr): account
            for account in setting.ACCOUNTS
        }
        # 哪个账号先完成就先打印结果
        for future in as_completed(futures):
            account = futures[future]
            try:
                results[account] = future.result()
            except Exception as e:
                print(f"[{account}] unexpected: {e}")
                results[account] = 2

    # 所有账号跑完后打印汇总
    print("\n========== 汇总 ==========")
    for account, code in results.items():
        alias = f"{setting.ACCOUNTS[account]}-{account}"
        status = "✅ 成功" if code == 0 else "❌ 失败"
        print(f"  {alias}: {status}")

    return 0 if all(c == 0 for c in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())