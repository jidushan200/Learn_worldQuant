import os
from auth_client import create_authenticated_session
from fetch_fields import get_datafields
from setting import SEARCH_SCOPE, DATASET_IDS, FIELD_TYPE, OUTPUT_DIR

def main():
    # 1. 自动创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 2. 认证
    sess, status = create_authenticated_session()
    print(f"认证状态: {status}\n")

    # 3. 遍历所有数据集
    all_results = {}
    for dataset_id, dataset_name in DATASET_IDS.items():
        print(f"{'='*50}")
        print(f"正在拉取数据集: {dataset_id}")
        print(f"{'='*50}")
        df, datafields = get_datafields(
            s=sess,
            searchScope=SEARCH_SCOPE,
            dataset_id=dataset_id,
            field_type=FIELD_TYPE,
            output_csv=os.path.join(OUTPUT_DIR, f"full_{dataset_id}_{dataset_name}_fields.csv")
        )
        all_results[dataset_id] = datafields

    # 4. 汇总打印
    print("\n========== 全部完成 ==========")
    for dataset_id, fields in all_results.items():
        print(f"{dataset_id}: {len(fields)} 个 MATRIX 字段")

if __name__ == '__main__':
    main()