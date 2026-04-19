from time import sleep
import textwrap
import pandas as pd
from auth_client import create_authenticated_session
from setting import SEARCH_SCOPE, DATASET_ID, FIELD_TYPE, OUTPUT_CSV


def get_datafields(
    s,
    searchScope: dict,
    dataset_id: str = '',
    search: str = '',
    field_type: str = FIELD_TYPE,
    output_csv: str = OUTPUT_CSV
) -> tuple:
    """
    拉取 WorldQuant BRAIN 数据字段，过滤后保存 CSV

    参数:
        s           : 已认证的 requests.Session
        searchScope : 包含 region / delay / universe / instrumentType
        dataset_id  : 指定数据集，如 'fundamental6'
        search      : 关键词搜索（与 dataset_id 二选一）
        field_type  : 过滤字段类型，默认 'MATRIX'
        output_csv  : 保存路径，默认 'fundamental6_fields.csv'

    返回:
        tuple: (df_filtered, datafields)
            df_filtered : 过滤后的完整 DataFrame
            datafields  : 字段 id 的 numpy array
    """

    instrument_type = searchScope['instrumentType']
    region          = searchScope['region']
    delay           = searchScope['delay']
    universe        = searchScope['universe']
    limit           = 50

    # ---------- 构造 URL ----------
    if search:
        url_template = (
            "https://api.worldquantbrain.com/data-fields?"
            f"instrumentType={instrument_type}"
            f"&region={region}&delay={delay}&universe={universe}"
            f"&search={search}&limit={limit}&offset={{x}}"
        )
        total = 200
    else:
        url_template = (
            "https://api.worldquantbrain.com/data-fields?"
            f"instrumentType={instrument_type}"
            f"&region={region}&delay={delay}&universe={universe}"
            f"&dataset.id={dataset_id}&limit={limit}&offset={{x}}"
        )
        first = s.get(url_template.format(x=0))
        first.raise_for_status()
        total = first.json()['count']
        print(f"共发现 {total} 个字段，开始分页拉取...")

    # ---------- 分页拉取 ----------
    all_fields = []
    for offset in range(0, total, limit):

        for attempt in range(5):
            resp = s.get(url_template.format(x=offset))

            if resp.status_code == 429:
                wait = int(resp.headers.get('Retry-After', 10))
                print(f"  触发限流，等待 {wait} 秒后重试...")
                sleep(wait)
                continue

            resp.raise_for_status()
            break

        results = resp.json().get('results', [])
        if not results:
            break
        all_fields.extend(results)
        print(f"  已拉取 {len(all_fields)} / {total}")
        sleep(1)

    # ---------- 过滤 + 保存 ----------
    df = pd.DataFrame(all_fields)
    df_filtered = df[df['type'] == field_type].reset_index(drop=True)

    # 保存完整 CSV
    df_filtered.to_csv(output_csv, index=False)
    print(f"\n过滤后剩 {len(df_filtered)} 个 {field_type} 字段")
    print(f"已保存至 {output_csv}")

    # 额外保存只有 id 列的 CSV
    ids_csv = output_csv.replace('.csv', '_ids.csv')
    df_filtered[['id']].to_csv(ids_csv, index=False)
    print(f"已保存 id 列表至 {ids_csv}\n")

    datafields = df_filtered['id'].values
    content = ', '.join(datafields)
    wrapped = textwrap.fill(content, width=220)
    print(f"字段 id 列表:\n[{wrapped}]\n")

    return df_filtered, datafields


# ============================================================
# 直接运行时的测试入口
# ============================================================
if __name__ == '__main__':
    sess, status = create_authenticated_session()
    print(f"认证状态: {status}\n")

    df, datafields = get_datafields(
        s=sess,
        searchScope=SEARCH_SCOPE,
        dataset_id=DATASET_ID
    )
    print(df[['id', 'description', 'coverage']].head(10))