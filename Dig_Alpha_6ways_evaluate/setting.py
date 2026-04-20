import os

# ── 认证 ──────────────────────────────────────────────────
CREDENTIALS_FILE = "credentials.json"
SESSION_REFRESH_INTERVAL = 1800

# ── 并发 ──────────────────────────────────────────────────
MAX_CONCURRENT = 3

# ── 回测等待 & 重试 ────────────────────────────────────────
MAX_WAIT_SEC = 300
MAX_RETRY    = 5

# ── 探针参数 ───────────────────────────────────────────────
FREQ_WINDOWS      = [5, 22, 66, 252]
BOUND_THRESHOLDS  = [0.01, 0.1, 0.5, 1, 2, 5, 10]
MEDIAN_THRESHOLDS = [0, 0.1, 0.5, 1, 2, 5]
DIST_BINS = [
    (0.0, 0.2),
    (0.2, 0.4),
    (0.4, 0.6),
    (0.6, 0.8),
    (0.8, 1.0),
]
BACKFILL_WINDOWS = [5, 22, 66, 252]

# ── 输出路径 ───────────────────────────────────────────────
OUTPUT_DIR    = "probe_results"
LOGS_DIR      = "logs"
LOG_BASE_NAME = "probe_log"

# ── 字段来源 ───────────────────────────────────────────────
FIELDS_CSV = r"..\Fetch_Fields\fundamental6_fields_ids.csv"