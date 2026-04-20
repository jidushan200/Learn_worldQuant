import os
import pandas as pd
import json
from datetime import datetime
from setting import OUTPUT_PASSED, WEB_DIR, BRAIN_URL_PREFIX


def generate_web():
    today = datetime.now().strftime("%Y-%m-%d")  # 页面标题日期
    today_file = datetime.now().strftime("%Y%m%d")  # 文件命名日期

    # ── 确保 web 文件夹存在 ───────────────────────────────────
    os.makedirs(WEB_DIR, exist_ok=True)

    # ── 读取通过筛选的 alpha，文件不存在或为空则跳过 ───────────
    if not os.path.exists(OUTPUT_PASSED):
        print("  ⚠️ passed_alphas.csv 不存在，跳过生成网页")
        return

    # 逐行读取 JSONL，解析为列表
    with open(OUTPUT_PASSED, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    if not records:
        print("  ⚠️ 没有完成回测的 alpha，跳过生成网页")
        return

    df = pd.DataFrame(records)

    # url 已在 _save 里写入，缺失时补充
    if "url" not in df.columns:
        df["url"] = BRAIN_URL_PREFIX + df["alpha_id"].astype(str)

    # ── 构建 JS items 数组，传入前端动态渲染 ─────────────────
    js_items = []
    for _, row in df.iterrows():
        returns = row.get("returns")
        ret_str = f"{returns * 100:.2f}%" if pd.notna(returns) else "N/A"
        expr = str(row.get("expr", "N/A")).replace("`", "'")  # 防止 JS 模板字符串冲突
        field_id = str(row.get("field_id", "N/A"))
        sharpe = row.get("sharpe", "N/A")
        fitness = row.get("fitness", "N/A")
        turnover = row.get("turnover", "N/A")
        alpha_id = str(row["alpha_id"])

        js_items.append(
            f'  {{ id: "{alpha_id}", field: "{field_id}", '
            f'expr: `{expr}`, sharpe: "{sharpe}", '
            f'fitness: "{fitness}", turnover: "{turnover}", returns: "{ret_str}" }}'
        )

    js_array = "[\n" + ",\n".join(js_items) + "\n]"
    count = len(df)

    html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>通过的 Alpha — {today}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: 'Segoe UI', Arial, sans-serif;
      background: #f5f5f5;
      padding: 30px;
      color: #333;
    }}
    h1 {{ color: #2c3e50; margin-bottom: 8px; font-size: 22px; }}
    .summary {{ color: #888; margin-bottom: 24px; font-size: 15px; }}
    .btn-all {{
      display: inline-block;
      margin-bottom: 28px;
      padding: 9px 22px;
      background: #2980b9;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-family: 'Segoe UI', Arial, sans-serif;
      font-size: 14px;
      font-weight: bold;
      transition: opacity 0.2s;
    }}
    .btn-all:hover {{ opacity: 0.85; }}
    table {{
      border-collapse: collapse;
      width: 100%;
      background: white;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    }}
    th {{
      background: #2c3e50;
      color: white;
      padding: 13px 16px;
      text-align: left;
      font-size: 14px;
    }}
    td {{
      padding: 10px 16px;
      border-bottom: 1px solid #f0f0f0;
      font-size: 14px;
    }}
    tr:hover td {{ background: #f0f7ff; }}
    .expr {{
      font-family: monospace;
      font-size: 13px;
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
<p class="summary">共 <strong>{count}</strong> 个 alpha 完成回测</p>
<button class="btn-all" id="btnAll">▶ 一键访问全部 ({count})</button>

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
    <tbody id="tableBody"></tbody>
  </table>

  <script>
    const BASE  = "{BRAIN_URL_PREFIX}";
    const items = {js_array};

    const tbody = document.getElementById("tableBody");

    // ── 动态渲染每行 alpha ──────────────────────────────────
    items.forEach((item, index) => {{
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${{index + 1}}</td>
        <td>${{item.field}}</td>
        <td class="expr">${{item.expr}}</td>
        <td class="tag-sharpe">${{item.sharpe}}</td>
        <td class="tag-fitness">${{item.fitness}}</td>
        <td class="tag-turnover">${{item.turnover}}</td>
        <td class="tag-returns">${{item.returns}}</td>
        <td><a href="${{BASE}}${{item.id}}" target="_blank">${{item.id}}</a></td>
      `;
      tbody.appendChild(tr);
    }});

    // ── 一键打开：每隔 300ms 打开一个，防止浏览器拦截 ────────
    document.getElementById("btnAll").addEventListener("click", () => {{
      items.forEach((item, i) => {{
        setTimeout(() => window.open(BASE + item.id, "_blank"), i * 300);
      }});
    }});
  </script>

</body>
</html>"""

    # ── 写入文件，如 web/20260419.html ────────────────────────
    output_path = os.path.join(WEB_DIR, f"{today_file}.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  🌐 网页已生成: {output_path}  ({count} 个 alpha)\n")
