from copy import deepcopy
from typing import Any, Dict

ENV_FILE = ".env"
EXPR_FILE = "alpha_expr.txt"
MAX_WAIT_SEC = 1800
LOG_FILE = "log.alpha.jsonl"

ACCOUNTS: Dict[str, str] = {
    # "ACC1": "1446579723",
    "ACC2": "3301",
    "ACC3": "3302",
    "ACC4": "3304",
    "ACC5": "3305",
    "ACC6": "3307",
}

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