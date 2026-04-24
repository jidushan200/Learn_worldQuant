import os
import json
from datetime import datetime
from setting import LOGS_DIR, LOG_BASE_NAME, WEB_DIR, BRAIN_URL_PREFIX


def _get_today_log_path() -> str | None:
    today = datetime.now().strftime("%Y%m%d")
    if not os.path.exists(LOGS_DIR):
        return None
    for filename in os.listdir(LOGS_DIR):
        if filename.startswith(LOG_BASE_NAME) and today in filename:
            return os.path.join(LOGS_DIR, filename)
    return None


def _build_session_block(s: dict) -> str:
    rows = ""
    for i, r in enumerate(s["alphas"], 1):
        returns  = r.get("returns")
        ret_str  = f"{returns * 100:.2f}%" if isinstance(returns, (int, float)) else "N/A"
        turnover = r.get("turnover")
        to_str   = f"{turnover * 100:.1f}%" if isinstance(turnover, (int, float)) else "N/A"
        expr     = str(r.get("expr", "N/A")).replace("`", "'")
        field_id = str(r.get("field_id", "N/A"))
        sharpe   = r.get("sharpe", "N/A")
        fitness  = r.get("fitness", "N/A")
        alpha_id = str(r["alpha_id"])
        url      = r.get("url") or (BRAIN_URL_PREFIX + alpha_id)

        rows += f"""
        <tr>
          <td>{i}</td>
          <td>{field_id}</td>
          <td class="expr">{expr}</td>
          <td class="tag-sharpe">{sharpe}</td>
          <td class="tag-fitness">{fitness}</td>
          <td class="tag-turnover">{to_str}</td>
          <td class="tag-returns">{ret_str}</td>
          <td><a href="{url}" target="_blank">{alpha_id}</a></td>
        </tr>"""

    return f"""
  <div class="session-block">
    <div class="session-header">
      🕐 {s["timestamp"]}　共提交 {s["total"]} 个，成功 {len(s["alphas"])} 个
    </div>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>字段</th>
          <th>Alpha 表达式</th>
          <th>Sharpe</th>
          <th>Fitness</th>
          <th>Turnover</th>
          <th>Returns</th>
          <th>链接</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
  </div>"""


def generate_web():
    today      = datetime.now().strftime("%Y-%m-%d")
    today_file = datetime.now().strftime("%Y%m%d")
    os.makedirs(WEB_DIR, exist_ok=True)

    log_path = _get_today_log_path()
    if not log_path:
        print("  ⚠️  今日日志文件不存在，跳过生成网页")
        return

    # ── 读取日志，以 type=start 为每次运行的分界 ──────────────
    sessions        = []
    current_session = None

    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            if obj.get("type") == "start":
                current_session = {
                    "timestamp": obj.get("timestamp", ""),
                    "total":     obj.get("total", "?"),
                    "alphas":    []
                }
                sessions.append(current_session)

            elif (
                obj.get("type") == "result"
                and current_session is not None
                and obj.get("alpha_id")
                and not obj.get("error")
            ):
                current_session["alphas"].append(obj)

    valid_sessions = [s for s in sessions if s["alphas"]]
    if not valid_sessions:
        print("  ⚠️  今日没有成功回测的 alpha，跳过生成网页")
        return

    total_count    = sum(len(s["alphas"]) for s in valid_sessions)
    session_blocks = "".join(_build_session_block(s) for s in valid_sessions)

    html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Alpha 回测结果 — {today}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: 'Segoe UI', Arial, sans-serif;
      background: #f5f5f5;
      padding: 30px;
      color: #333;
    }}
    h1 {{
      color: #2c3e50;
      margin-bottom: 8px;
      font-size: 22px;
    }}
    .summary {{
      color: #888;
      margin-bottom: 24px;
      font-size: 15px;
    }}
    .session-block {{
      margin-bottom: 40px;
    }}
    .session-header {{
      background: #2c3e50;
      color: white;
      padding: 10px 16px;
      border-radius: 6px 6px 0 0;
      font-size: 14px;
      font-weight: bold;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      background: white;
      box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    }}
    th {{
      background: #34495e;
      color: white;
      padding: 11px 14px;
      text-align: left;
      font-size: 13px;
    }}
    td {{
      padding: 9px 14px;
      border-bottom: 1px solid #f0f0f0;
      font-size: 13px;
    }}
    tr:hover td {{ background: #f0f7ff; }}
    .expr {{
      font-family: monospace;
      font-size: 12px;
      color: #555;
    }}
    a {{
      color: #2980b9;
      text-decoration: none;
      font-weight: bold;
    }}
    a:hover {{ text-decoration: underline; }}
    .tag-sharpe   {{ color: #27ae60; font-weight: bold; }}
    .tag-fitness  {{ color: #8e44ad; font-weight: bold; }}
    .tag-turnover {{ color: #e67e22; font-weight: bold; }}
    .tag-returns  {{ color: #2980b9; font-weight: bold; }}
  </style>
</head>
<body>
  <h1>Alpha 回测结果 — {today}</h1>
  <p class="summary">今日累计 <strong>{total_count}</strong> 个成功，共 {len(valid_sessions)} 次执行</p>
  {session_blocks}
</body>
</html>"""

    output_path = os.path.join(WEB_DIR, f"{today_file}.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  🌐 网页已生成: {output_path}  (今日累计 {total_count} 个 alpha)\n")