import re
from pathlib import Path

from auth_client import create_authenticated_session
from submit_alpha import submit_and_wait


def load_alpha_expr(expr_file: str = "alpha_expr.txt") -> str:
    """读取表达式文件并清理注释，返回第一条有效表达式。"""
    p = Path(expr_file)
    if not p.exists():
        raise FileNotFoundError(f"未找到表达式文件: {expr_file}")

    text = p.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"表达式文件为空: {expr_file}")

    # 1) 去掉块注释 /* ... */
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)

    # 2) 去掉行注释 //... 和 #...，并过滤空行
    lines = []
    for line in text.splitlines():
        line = re.sub(r"//.*$", "", line).strip()
        line = re.sub(r"#.*$", "", line).strip()
        if line:
            lines.append(line)

    if not lines:
        raise ValueError(f"表达式文件没有有效表达式: {expr_file}")

    return lines[0]


def main():
    # 1) 创建已认证会话
    sess = create_authenticated_session(".env")
    print("auth ok")

    try:
        # 2) 从文件读取表达式
        alpha_expr = load_alpha_expr("alpha_expr.txt")
        print("loaded expr:", alpha_expr)

        # 3) 单独定义 simulation settings（页面配置）
        simulation_settings = {
            "instrumentType": "EQUITY",
            "region": "USA",
            "universe": "TOP3000",
            "delay": 1,
            "decay": 4,
            "neutralization": "SUBINDUSTRY",
            "truncation": 0.08,
            "pasteurization": "ON",
            "unitHandling": "VERIFY",
            "nanHandling": "OFF",
            "language": "FASTEXPR",
            "visualization": False
        }

        # 4) 组装提交体 payload
        alpha_payload = {
            "type": "REGULAR",
            "settings": simulation_settings,
            "regular": alpha_expr
        }

        # 5) 提交并等待结果
        alpha_id, err, raw = submit_and_wait(sess, alpha_payload)

        if err:
            print("fail:", err)
            print("expr:", alpha_expr)
            if raw:
                print("raw:", raw)
        else:
            print("expr:", alpha_expr)
            print("alpha_id:", alpha_id)

    finally:
        # 6) 释放连接
        sess.close()


if __name__ == "__main__":
    main()