# ---------- AI 生成的 alpha 文件路径 ----------
ALPHAS_FILE = "alphas.json"

# ---------- 回测参数 ----------
SIMULATION_SETTINGS = {
    "instrumentType": "EQUITY",
    "region":         "USA",
    "universe":       "TOP3000",
    "delay":          1,
    "decay":          4,
    "neutralization": "MARKET",
    "truncation":     0.08,
    "pasteurization": "ON",
    "unitHandling":   "VERIFY",
    "nanHandling":    "OFF",
    "language":       "FASTEXPR",
    "visualization":  False
}

# ---------- 超时 / 刷新 / 重试 ----------
MAX_WAIT_SEC             = 1800   # 单个 alpha 回测最长等待时间（秒），超出视为超时
SESSION_REFRESH_INTERVAL = 1800   # 每隔多少秒重新认证一次 session
MAX_RETRY                = 5      # 网络异常 / 限流时的最大重试次数
MAX_CONCURRENT           = 3      # 线程池并发数，即同时提交的 alpha 数量
# ---------- 日志 ----------
LOGS_DIR      = "logs"
LOG_BASE_NAME = "simulation_log"

# ---------- 网页输出 ----------
WEB_DIR          = "web"
BRAIN_URL_PREFIX = "https://platform.worldquantbrain.com/alpha/"