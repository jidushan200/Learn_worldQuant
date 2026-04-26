import requests
from requests.auth import HTTPBasicAuth
import json

EMAIL = "kongkong3307@163.com"
PASSWORD = "zkm94031607"
BRAIN_BASE = "https://api.worldquantbrain.com"
ALPHA_ID = "om9dYJ5k"

ACCEPT_V2 = {"accept": "application/json;version=2.0"}

session = requests.Session()
session.auth = HTTPBasicAuth(EMAIL, PASSWORD)

r = session.post(f"{BRAIN_BASE}/authentication")
print(f"登录: {r.status_code}")

# ===== 1. 获取 alpha 完整数据 =====
r = session.get(f"{BRAIN_BASE}/alphas/{ALPHA_ID}", headers=ACCEPT_V2)
alpha_data = r.json()
is_data = alpha_data.get("is", {})
checks = is_data.get("checks", [])

# ===== Aggregate Data =====
print(f"\n{'='*70}")
print(f"  Alpha: {ALPHA_ID}")
print(f"{'='*70}")
print(f"  Aggregate Data")
print(f"  Sharpe   {is_data.get('sharpe')}    Turnover  {is_data.get('turnover',0)*100:.2f}%")
print(f"  Fitness  {is_data.get('fitness')}    Returns   {is_data.get('returns',0)*100:.2f}%")
print(f"  Drawdown {is_data.get('drawdown',0)*100:.2f}%  Margin    {is_data.get('margin',0)*10000:.2f}‱")

# ===== Checks 表格 =====
print(f"\n  Checks ({len(checks)} 项)")
print(f"{'='*70}")
ch_headers = ["Name", "Result", "Value", "Limit"]
ch_rows = []
for c in checks:
    ch_rows.append([
        c.get("name", ""),
        c.get("result", ""),
        str(c.get("value", "")),
        str(c.get("limit", "")),
    ])
col_w = [max(len(h), *(len(r[i]) for r in ch_rows)) for i, h in enumerate(ch_headers)]

def pr(cells, ws):
    print("| " + " | ".join(f"{c:<{ws[i]}}" for i, c in enumerate(cells)) + " |")

def div(ws):
    print("+" + "+".join("-" * (w + 2) for w in ws) + "+")

div(col_w)
pr(ch_headers, col_w)
div(col_w)
for row in ch_rows:
    pr(row, col_w)
div(col_w)

# ===== 2. Yearly Stats =====
r2 = session.get(f"{BRAIN_BASE}/alphas/{ALPHA_ID}/recordsets/yearly-stats", headers=ACCEPT_V2)
print(f"\nyearly-stats 状态码: {r2.status_code}")
print(f"yearly-stats Content-Type: {r2.headers.get('content-type')}")
print(f"yearly-stats 内容长度: {len(r2.text)}")
print(f"yearly-stats 前200字符: {r2.text[:200]}")

if r2.status_code == 200 and r2.text.strip():
    data = r2.json()
    props = [p['name'] for p in data['schema']['properties']]
    records = [dict(zip(props, row)) for row in data['records']]

    print(f"\n{'='*70}")
    print(f"  Yearly Performance")
    print(f"{'='*70}")

    headers = ["Year", "Sharpe", "Turnover", "Fitness", "Returns", "Drawdown", "Margin", "Long Count", "Short Count"]
    rows = []
    for rec in records:
        rows.append([
            rec['year'],
            f"{rec['sharpe']:.2f}",
            f"{rec['turnover']*100:.2f}%",
            f"{rec['fitness']:.2f}",
            f"{rec['returns']*100:.2f}%",
            f"{rec['drawdown']*100:.2f}%",
            f"{rec['margin']*10000:.2f}‱",
            str(rec['longCount']),
            str(rec['shortCount']),
        ])

    col_widths = [max(len(h), *(len(row[i]) for row in rows)) for i, h in enumerate(headers)]

    def print_row(cells):
        print("| " + " | ".join(f"{c:>{col_widths[i]}}" for i, c in enumerate(cells)) + " |")

    def print_divider():
        print("+" + "+".join("-" * (w + 2) for w in col_widths) + "+")

    print_divider()
    print_row(headers)
    print_divider()
    for row in rows:
        print_row(row)
    print_divider()
else:
    print(f"\n⚠️ yearly-stats 请求失败或返回空内容")