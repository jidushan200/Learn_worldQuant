import pandas as pd
from setting import FIELDS_CSV, ALPHA_TEMPLATE, SIMULATION_SETTINGS


def build_alpha_list() -> list[dict]:
    """
    读取字段 id 列表，套入 ALPHA_TEMPLATE 模板，
    生成可直接提交给 WQBrain API 的 payload 列表

    Returns:
        list[dict]: 每个元素包含：
                    - field_id : 来源字段 id（用于日志追踪，不提交给 API）
                    - payload  : 实际提交给 API 的 dict
    """

    # 读取字段 id CSV，取 id 列
    df = pd.read_csv(FIELDS_CSV)
    field_ids = df['id'].tolist()
    print(f"读取到 {len(field_ids)} 个字段\n")

    alpha_list = []
    for field_id in field_ids:

        # 将模板中的 {field_id} 替换为实际字段 id
        expr = ALPHA_TEMPLATE.format(field_id=field_id)

        # 构造实际提交给 API 的 payload
        payload = {
            "type":     "REGULAR",
            "settings": SIMULATION_SETTINGS,
            "regular":  expr,
        }

        # 用一个包装 dict 同时携带 field_id，方便 main.py 追踪来源
        alpha_list.append({
            "field_id": field_id,  # 仅用于日志，不传给 API
            "payload":  payload,   # 实际提交给 API 的内容
        })

    return alpha_list


if __name__ == '__main__':
    # 单独运行此文件时，打印构造结果用于调试
    alphas = build_alpha_list()
    print(f"共构造 {len(alphas)} 个 alpha")
    print(f"第一个字段: {alphas[0]['field_id']}  表达式: {alphas[0]['payload']['regular']}")
    print(f"最后一个字段: {alphas[-1]['field_id']}  表达式: {alphas[-1]['payload']['regular']}")