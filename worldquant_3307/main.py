import json
import re
from pathlib import Path
from typing import Any

import setting
from auth_client import create_authenticated_session
from submit_alpha import submit_and_wait


def load_alpha_expr(expr_file: str = setting.EXPR_FILE) -> str:
    p = Path(expr_file)
    if not p.exists():
        raise FileNotFoundError(f"未找到表达式文件: {expr_file}")

    text = p.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"表达式文件为空: {expr_file}")

    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)

    lines = []
    for line in text.splitlines():
        line = re.sub(r"//.*$", "", line).strip()
        line = re.sub(r"#.*$", "", line).strip()
        if line:
            lines.append(line)

    if not lines:
        raise ValueError(f"表达式文件没有有效表达式: {expr_file}")

    return lines[0]


def pretty_raw(raw: Any) -> str:
    if raw is None:
        return ""
    if isinstance(raw, (dict, list)):
        return json.dumps(raw, ensure_ascii=False, indent=2)
    return str(raw)


def main() -> int:
    sess = None
    try:
        # 注意：这里接收两个返回值
        sess, auth_status_code = create_authenticated_session(setting.ENV_FILE)
        print(f"auth status_code: {auth_status_code}")

        alpha_expr = load_alpha_expr(setting.EXPR_FILE)
        print("loaded expr:", alpha_expr)

        alpha_payload = {
            "type": "REGULAR",
            "settings": setting.get_setting(),
            "regular": alpha_expr,
        }

        alpha_id, err, raw = submit_and_wait(
            sess=sess,
            alpha_payload=alpha_payload,
            max_wait_sec=setting.MAX_WAIT_SEC,
        )

        if err:
            print("fail:", err)
            print("expr:", alpha_expr)
            if raw is not None:
                print("raw:")
                print(pretty_raw(raw))
            return 1

        print("expr:", alpha_expr)
        print("alpha_id:", alpha_id)
        return 0

    except Exception as e:
        print("fatal:", e)
        return 2

    finally:
        if sess is not None:
            sess.close()


if __name__ == "__main__":
    raise SystemExit(main())