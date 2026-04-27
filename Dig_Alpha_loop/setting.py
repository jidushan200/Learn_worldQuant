"""
全局配置 - 路径、参数、常量（纯配置，不含任何函数）
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ═══════════════════════════════════════════════════════════
#  目录结构
# ═══════════════════════════════════════════════════════════

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 参考资料（knowledge 目录）
KNOWLEDGE_DIR       = os.path.join(BASE_DIR, "knowledge")
ALPHA_EXAMPLES_FILE = os.path.join(KNOWLEDGE_DIR, "alpha_examples.txt")
PAPER_NOTES_FILE    = os.path.join(KNOWLEDGE_DIR, "paper_notes.txt")

# 策略提示文件（根目录）
INITIAL_PROMPT_FILE = os.path.join(BASE_DIR, "strategy_prompt.txt")

# Alpha 列表文件
ALPHAS_FILE = os.path.join(BASE_DIR, "alphas.json")

# 日志目录（logger.py 用）
LOGS_DIR      = os.path.join(BASE_DIR, "logs")
LOG_BASE_NAME = "alpha_sim"

# 迭代输出
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOG_FILE   = os.path.join(OUTPUT_DIR, "run_log.txt")

# Web 可视化
WEB_DIR = os.path.join(BASE_DIR, "web")

# 确保目录存在
for _d in [KNOWLEDGE_DIR, LOGS_DIR, OUTPUT_DIR, WEB_DIR]:
    os.makedirs(_d, exist_ok=True)

# ═══════════════════════════════════════════════════════════
#  WorldQuant Brain 凭据
# ═══════════════════════════════════════════════════════════

WQ_USERNAME = os.getenv("WQ_USERNAME", "")
WQ_PASSWORD = os.getenv("WQ_PASSWORD", "")

# ═══════════════════════════════════════════════════════════
#  WorldQuant Brain API 端点
# ═══════════════════════════════════════════════════════════

API_BASE             = "https://api.worldquantbrain.com"
API_AUTH_URL         = f"{API_BASE}/authentication"          # ← 新增
API_SIMULATION_URL   = f"{API_BASE}/simulations"
API_ALPHA_URL        = f"{API_BASE}/alphas/{{alpha_id}}"
API_YEARLY_STATS_URL = f"{API_BASE}/alphas/{{alpha_id}}/recordsets/yearly-stats"
BRAIN_URL_PREFIX     = "https://platform.worldquantbrain.com/alpha/"

# ═══════════════════════════════════════════════════════════
#  运行参数
# ═══════════════════════════════════════════════════════════

BATCH_SIZE               = 6        # 每轮 AI 生成多少个 alpha
MAX_ITERATIONS           = 100       # 最大迭代轮数
MAX_IMPROVE_ATTEMPTS     = 3        # 每个 alpha 最多改进几次
MAX_WAIT_SEC             = 600      # 回测等待超时（秒）
MAX_RETRY                = 3        # HTTP 请求最大重试次数
MAX_CONCURRENT           = 3        # 最大并发回测线程数
SESSION_REFRESH_INTERVAL = 1800     # Session 刷新间隔（秒，30 分钟）

# ═══════════════════════════════════════════════════════════
#  目标门槛
# ═══════════════════════════════════════════════════════════

TARGET_GRADE   = "SPECTACULAR"     #不要删：INFERIOR (极差) → AVERAGE (合格) → GOOD (良好) → EXCELLENT (优秀) → SPECTACULAR (顶级)
TARGET_SHARPE  = 3
TARGET_FITNESS = 2

# ═══════════════════════════════════════════════════════════
#  Grade 比较
# ═══════════════════════════════════════════════════════════

GRADE_SCORE = {
    "INFERIOR":     1,
    "AVERAGE":      2,
    "GOOD":         3,
    "EXCELLENT":    4,
    "SPECTACULAR":  5,
}

# ═══════════════════════════════════════════════════════════
#  提交 / 过滤门槛
# ═══════════════════════════════════════════════════════════

MIN_SHARPE_TO_IMPROVE = -0.5
MIN_GRADE_TO_SUBMIT   = "GOOD"

# ═══════════════════════════════════════════════════════════
#  Token 控制常量（Prompt 大小管理）
# ═══════════════════════════════════════════════════════════

MAX_HISTORY_ROUNDS = 3       # prompt 中只放最近 3 轮详情
MAX_EXAMPLES_CHARS = 4000    # alpha_examples.txt 最多 4000 字符
MAX_PAPERS_CHARS   = 3000    # paper_notes.txt 最多 3000 字符
MAX_IDEA_CHARS     = 1500    # strategy_prompt.txt 最多 1500 字符

# ═══════════════════════════════════════════════════════════
#  默认回测 Setting
# ═══════════════════════════════════════════════════════════

SIMULATION_SETTINGS = {
    "instrumentType": "EQUITY",
    "region":         "USA",
    "universe":       "TOP3000",
    "delay":          1,
    "decay":          0,
    "neutralization": "SUBINDUSTRY",
    "truncation":     0.08,
    "pasteurization": "ON",
    "unitHandling":   "VERIFY",
    "nanHandling":    "OFF",
    "language":       "FASTEXPR",
    "visualization":  False,
}

DEFAULT_SETTING = SIMULATION_SETTINGS   # 别名

# ═══════════════════════════════════════════════════════════
#  Setting 合法值（用于校验 AI 输出）
# ═══════════════════════════════════════════════════════════

VALID_REGIONS        = {"USA"}
VALID_UNIVERSES      = {"TOP200", "TOP500", "TOP1000", "TOP2000", "TOP3000"}
VALID_NEUTRALIZATION = {"NONE", "MARKET", "SECTOR", "INDUSTRY", "SUBINDUSTRY"}
VALID_DELAY          = {0, 1}
VALID_DECAY_RANGE    = (0, 20)
VALID_TRUNCATION     = (0.01, 0.10)

# fields.md 字段约束
FIELDS_FILE      = os.path.join(KNOWLEDGE_DIR, "fields.md")
MAX_FIELDS_CHARS = 30000    # 放入 prompt 的字段文档最大字符数