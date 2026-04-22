# ---------- AI 生成的 alpha 文件路径 ----------
# 文件格式为 JSON，结构如下：
# [
#   {"name": "debt_momentum", "expr": "group_rank(ts_delta(debt, 5), subindustry)"},
#   {"name": "capex_rank",    "expr": "rank(capex / assets)"}
# ]
ALPHAS_FILE = "./alphas.json"

# ---------- 回测参数 ----------
SIMULATION_SETTINGS = {
    "instrumentType": "EQUITY",       # 资产类型：股票
    "region":         "USA",          # 市场：美国
    "universe":       "TOP3000",      # 股票池：市值前3000
    "delay":          1,              # 延迟：1天
    "decay":          4,              # 衰减：不衰减
    "neutralization": "MARKET",  # 中性化：子行业
    "truncation":     0.08,           # 截断：单只股票权重上限8%
    "pasteurization": "ON",           # 去极值：开启
    "unitHandling":   "VERIFY",       # 单位检查：验证
    "nanHandling":    "OFF",          # NaN处理：关闭
    "language":       "FASTEXPR",     # 表达式语言
    "visualization":  False           # 可视化：关闭
}

# ---------- 超时 / 刷新 / 重试 ----------
MAX_WAIT_SEC             = 1800   # 单个 alpha 回测最长等待时间（秒）
SESSION_REFRESH_INTERVAL = 1800   # Session 刷新间隔（秒），防止 token 过期
MAX_RETRY                = 5      # 遇到 429 限流时最多重试次数
MAX_CONCURRENT           = 3      # 最大并发 simulate 数量

# ---------- 输出文件路径 ----------
OUTPUT_ALL    = "all_results.jsonl"     # 全部 alpha 结果
OUTPUT_PASSED = "passed_alphas.jsonl"   # 仅通过筛选的 alpha

# ---------- 日志 ----------
LOGS_DIR      = "logs"                # 日志文件夹
LOG_BASE_NAME = "simulation_log"      # 日志文件名前缀，完整名如 simulation_log.20260419.log

# ---------- 网页输出 ----------
WEB_DIR          = "web"                                          # 网页文件夹
BRAIN_URL_PREFIX = "https://platform.worldquantbrain.com/alpha/"  # alpha 详情页前缀，拼接 alpha_id 即可访问