import json
import threading
from datetime import datetime

# 线程锁，防止多个账号同时写日志文件时内容错乱
_lock = threading.Lock()


def log_success(log_file: str, account: str, expr: str, alpha_id: str):
    # 构建一条日志记录
    record = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 提交时间
        "account": account,                                      # 账号名
        "expr": expr,                                            # 表达式
        "alpha_id": alpha_id,                                    # 提交成功后的 alpha ID
        "alpha_url": f"https://platform.worldquantbrain.com/alpha/{alpha_id}",  # 直达链接
    }
    # 加锁后再写文件，保证并发时每条记录完整写入，不会互相穿插
    with _lock:
        # 追加模式写入，不会覆盖历史记录
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")