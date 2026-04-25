# ============================================================
#  setting.py  —— WorldQuant BRAIN 自动化 Alpha 挖掘 配置
# ============================================================

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
MAX_WAIT_SEC             = 1800
SESSION_REFRESH_INTERVAL = 1800
MAX_RETRY                = 5
MAX_CONCURRENT           = 3

# ---------- 日志 ----------
LOGS_DIR      = "logs"
LOG_BASE_NAME = "simulation_log"

# ---------- 网页输出 ----------
WEB_DIR          = "web"
BRAIN_URL_PREFIX = "https://platform.worldquantbrain.com/alpha/"

# ---------- AI 递归优化 ----------
#ALPHAS_PER_ROUND：每轮生成的Alpha数量
#TARGET_GRADE目标评分
MAX_ITERATIONS      = 50
TARGET_SHARPE       = 1.5
TARGET_FITNESS      = 1.00
TARGET_GRADE        = "GOOD"
ALPHAS_PER_ROUND    = 6
INITIAL_PROMPT_FILE = "strategy_prompt.txt"

# ---------- Setting 锁定策略 ----------
SETTING_CHANGE_THRESHOLD = 4

# ---------- AI 辅助知识库发送次数 ----------
KNOWLEDGE_DIR         = "knowledge"
KNOWLEDGE_EVERY_ROUND = False