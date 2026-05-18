# =================================================================================
# 
# 專案名稱：電子酒單&庫存前後端管理系統 (GSA 動態同步工具)
# 開發設計：Sommelier Yannick "Y.K." Liu
# 版權所有 (c) 2026 Yannick "Y.K." Liu. 保留所有權利。
#
# =================================================================================

import pandas as pd
import json
import requests
from io import StringIO

SHEET_ID = "107NpWDkYD0lhIoC-ewLHZouWJoAfd8GTifBa8YTDMSQ"

def fetch_and_clean():
    all_wines = []
    categories = []
    
    # 透過Google Sheets API (GSA)獲取試算表所有tabs
    meta_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:json"
    
    try:
        res = requests.get(meta_url)
        # 解析JSON封包取得動態Tabs
        start_idx = res.text.find("{")
        end_idx = res.text.rfind("}") + 1
        meta_data = json.loads(res.text[start_idx:end_idx])
        
        # 動態抓取所有Tabs
        sheet_names = [sheet['name'] for sheet in meta_data.get('table', {}).get('parsedParams', {}).get('sheets', [])]
    except Exception as e:
        print(f"動態獲取分頁結構失敗: {e}")
        return

    base_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

    for name in sheet_names:
        # 排除REC與CRM
        if "REC" in name or "CRM" in name:
            continue
            
        try:
            # 使用sheet參數直接存取
            url = f"{base_url}&sheet={requests.utils.quote(name)}"
            response = requests.get(url)
            response.encoding = 'utf-8'
            
            # 從第3列開始讀取
            df = pd.read_csv(StringIO(response.text), skiprows=2, header=None)
            
            # 確保第五欄(Index 4:酒名)不為空
            df = df[df[4].notnull() & (df[4].astype(str).str.strip() != "")]
            df = df.fillna("")
            
            # 於橫列末端追加分頁名稱作為Category
            df[df.shape[1]] = name
            
            all_wines.extend(df.values.tolist())
            categories.append(name)
            print(f"成功動態同步分頁: {name}")
            
        except Exception as e:
            print(f"同步分頁 {name} 失敗: {e}")

    # 輸出完全符合前端規格的JSON結構
    output_data = {
        "wines": all_wines,
        "categories": categories
    }

    with open('wine_data.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
    print("\n[完成] 靜態JSON檔案已自動生成，無縫對接前端。")

if __name__ == "__main__":
    fetch_and_clean()
