from copy import deepcopy
from typing import Any, Dict

ENV_FILE = ".env"
EXPR_FILE = "alpha_expr.txt"
MAX_WAIT_SEC = 1800
LOG_FILE = "log.alpha.jsonl"

ACCOUNTS: Dict[str, str] = {
    "ACC7": "3307",
    "ACC1": "3301",
    "ACC2": "3302",
    "ACC4": "3304",
    "ACC5": "3305"
}

SETTING: Dict[str, Any] = {
    "language": "FASTEXPR",
    "instrumentType": "EQUITY",
    "region": "USA",
    "universe": "TOP3000",
    "delay": 1,
    "neutralization": "MARKET",
    "decay": 0,
    "truncation": 0.08,
    "pasteurization": "ON",
    "unitHandling": "VERIFY",
    "nanHandling": "OFF",
    "visualization": False,
}


def get_setting() -> Dict[str, Any]:
    return deepcopy(SETTING)