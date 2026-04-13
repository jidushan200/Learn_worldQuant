from copy import deepcopy
from typing import Any, Dict

# 基础配置
ENV_FILE = ".env"
EXPR_FILE = "alpha_expr.txt"
MAX_WAIT_SEC = 1800

# 网站上的 Setting
SETTING: Dict[str, Any] = {
    "instrumentType": "EQUITY",
    "region": "USA",
    "universe": "TOP3000",
    "delay": 1,
    "decay": 4,
    "neutralization": "SUBINDUSTRY",
    "truncation": 0.08,
    "pasteurization": "ON",
    "unitHandling": "VERIFY",
    "nanHandling": "OFF",
    "language": "FASTEXPR",
    "visualization": False,
}


def get_setting() -> Dict[str, Any]:
    return deepcopy(SETTING)