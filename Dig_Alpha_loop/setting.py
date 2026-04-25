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
MAX_ITERATIONS      = 50            # 循环的次数，main.py有方法
TARGET_SHARPE       = 1.3
TARGET_FITNESS      = 1.00
TARGET_GRADE        = "EXCELLENT"   # 达到此 grade 即停止，顺序: INFERIOR < AVERAGE < GOOD < EXCELLENT < SPECTACULAR
ALPHAS_PER_ROUND    = 8             # 每次生成的Alpha数量
INITIAL_PROMPT_FILE = "strategy_prompt.txt"

# ---------- AI 研判（回测后由 GPT-5.4 评审） ----------
JUDGE_ENABLED     = True
JUDGE_PROMPT_TMPL = (
    "你是一位量化 Alpha 研究员。下面是一条 BRAIN alpha 的回测结果：\n"
    "{result_json}\n\n"
    "请从 Sharpe、Turnover、Drawdown、Fitness 四个维度给出简短评价，"
    "并判断该 alpha 是否值得提交（PASS / FAIL），最后给出改进建议。"
)

# ---------- AI 辅助知识库发送次数 ----------
KNOWLEDGE_DIR         = "knowledge"
KNOWLEDGE_EVERY_ROUND = False       # True=每轮都发知识库, False=只第1轮发