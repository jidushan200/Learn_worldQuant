# ============================================================
# Alpha 表达式模板（手动修改这里）
# {field_id} 会被自动替换成每个字段的 id
# ============================================================
ALPHA_TEMPLATE = "group_rank({field_id}, subindustry)"

# 例子：
# "rank({field_id})"
# "group_rank({field_id}, subindustry)"
# "rank({field_id} / cap)"
# "rank(ts_delta({field_id}, 5))"
# ============================================================


# ---------- 字段来源 ----------
FIELDS_CSV = r"F:\Cal_Prince\Fetch_Fields\fundamental6_fields_ids.csv"

# ---------- 回测参数 ----------
SIMULATION_SETTINGS = {
    "instrumentType": "EQUITY",       # 资产类型：股票
    "region":         "USA",          # 市场：美国
    "universe":       "TOP3000",      # 股票池：市值前3000
    "delay":          1,              # 延迟：1天
    "decay":          0,              # 衰减：不衰减
    "neutralization": "SUBINDUSTRY",  # 中性化：子行业
    "truncation":     0.08,           # 截断：单只股票权重上限8%
    "pasteurization": "ON",           # 去极值：开启
    "unitHandling":   "VERIFY",       # 单位检查：验证
    "nanHandling":    "OFF",          # NaN处理：关闭
    "language":       "FASTEXPR",     # 表达式语言
    "visualization":  False,          # 可视化：关闭
}

# ---------- 超时 / 刷新 / 重试 ----------
MAX_WAIT_SEC             = 1800   # 单个 alpha 回测最长等待时间（秒）
SESSION_REFRESH_INTERVAL = 1800   # Session 刷新间隔（秒），防止 token 过期
MAX_RETRY                = 5      # 遇到 429 限流时最多重试次数
MAX_CONCURRENT           = 3      # 最大并发 simulate 数量

# ---------- 输出文件路径 ----------
OUTPUT_ALL    = "all_results.csv"     # 全部 alpha 结果
OUTPUT_PASSED = "passed_alphas.csv"   # 仅通过筛选的 alpha

LOGS_DIR     = "logs"               # 日志文件夹
LOG_BASE_NAME = "simulation_log"