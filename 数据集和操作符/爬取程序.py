import requests
import pandas as pd
import time
import os

# 1. 配置信息（请确保这里的 cookie 是最新的）
BASE_URL = "https://api.worldquantbrain.com/data-fields"
HEADERS = {
    "accept": "",
    "cookie": "",
    "user-agent": "",
    "referer": "https://platform.worldquantbrain.com/",
}

def download_all_fields_to_excel(filename="WorldQuant_Fields_Full.xlsx"):
    if os.path.exists(filename):
        print(f"发现已有的文件 {filename}，正在读取以尝试断点续传...")
        try:
            df_existing = pd.read_excel(filename)
            all_results = df_existing.to_dict('records')
            offset = len(all_results)
            print(f"成功加载了 {offset} 条历史数据，将从此处继续抓取。")
        except Exception as e:
            print(f"读取历史数据失败: {e}，将从头重新开始。")
            all_results = []
            offset = 0
    else:
        all_results = []
        offset = 0
        
    limit = 20  # 每次抓取20条
    
    print("开始爬取数据，请稍候...")
    
    while True:
        params = {
            'delay': '1',
            'instrumentType': 'EQUITY',
            'limit': limit,
            'offset': offset,
            'region': 'USA',
            'universe': 'TOP3000'
        }
        
        try:
            response = requests.get(BASE_URL, params=params, headers=HEADERS)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if not results:
                    print(f"\n抓取完成！共获得 {len(all_results)} 条字段信息。")
                    break
                
                all_results.extend(results)
                print(f"当前进度: 已抓取 {len(all_results)} 条...", end='\r')
                
                # 更新位移
                offset += limit
                
                # 必须保留延迟，模拟真人操作，保护账号
                time.sleep(1) 
                
            elif response.status_code == 401:
                print("\n错误：Token 已失效，请去网页重新复制 Cookie。")
                break
            else:
                print(f"\n请求失败，状态码：{response.status_code}")
                break
                
        except Exception as e:
            print(f"\n运行中发生异常: {e}")
            break

    # 2. 转换为 DataFrame 并导出
    if all_results:
        df = pd.DataFrame(all_results)
        
        # 整理列名（让 Excel 看起来更清晰）
        # 假设返回的 JSON key 包含 id, name, description, category, type 等
        df.to_excel(filename, index=False)
        print(f"文件已保存至: {filename}")
    else:
        print("未抓取到任何数据。")

# 执行脚本
if __name__ == "__main__":
    download_all_fields_to_excel()