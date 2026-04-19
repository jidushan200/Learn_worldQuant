from auth_client import create_authenticated_session
from fetch_fields import get_datafields
from setting import SEARCH_SCOPE, DATASET_ID

def main():
    # 1. 认证
    sess, status = create_authenticated_session()
    print(f"认证状态: {status}\n")

    # 2. 拉取字段（内部自动过滤 + 保存 CSV）
    _, datafields = get_datafields(
        s=sess,
        searchScope=SEARCH_SCOPE,
        dataset_id=DATASET_ID
    )

if __name__ == '__main__':
    main()