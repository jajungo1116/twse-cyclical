"""
台股景氣循環類股 - 每日資料抓取腳本
資料來源: FinMind API (https://finmindtrade.com)
產出: data.json (給前端讀取)
"""
import requests
import json
import os
from datetime import datetime, timedelta
import time

# ===== 設定區 =====
FINMIND_TOKEN = os.environ.get("FINMIND_TOKEN", "")
FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"

# 你要監控的景氣循環類股清單
# 結構: { 類股代號: { 名稱, 分類, 成分股清單 } }
SECTORS = {
    "memory": {
        "name_zh": "記憶體",
        "name_en": "MEMORY",
        "category": "tech_cycle",
        "stocks": ["2408", "2344", "6770", "3260", "4967", "8271", "2451", "5289"],
    },
    "mlcc": {
        "name_zh": "被動元件",
        "name_en": "PASSIVE",
        "category": "tech_cycle",
        "stocks": ["2327", "2492", "3017"],  # 國巨 華新科 奇鋐(誤,改禾伸堂)
    },
    "panel": {
        "name_zh": "面板",
        "name_en": "PANEL",
        "category": "tech_cycle",
        "stocks": ["2409", "3481"],  # 友達 群創
    },
    "wafer": {
        "name_zh": "矽晶圓",
        "name_en": "WAFER",
        "category": "tech_cycle",
        "stocks": ["6488", "5483", "5碼"],
    },
    "steel": {
        "name_zh": "鋼鐵",
        "name_en": "STEEL",
        "category": "raw_materials",
        "stocks": ["2002", "2007", "2014"],  # 中鋼 燁興 中鴻
    },
    "cement": {
        "name_zh": "水泥",
        "name_en": "CEMENT",
        "category": "raw_materials",
        "stocks": ["1101", "1102", "1110"],  # 台泥 亞泥 東泥
    },
    "plastics": {
        "name_zh": "塑化",
        "name_en": "PETROCHEM",
        "category": "raw_materials",
        "stocks": ["1301", "1303", "1326", "6505"],  # 台塑 南亞 台化 台塑化
    },
    "paper": {
        "name_zh": "造紙",
        "name_en": "PAPER",
        "category": "raw_materials",
        "stocks": ["1903", "1904", "1905"],  # 士紙 正隆 華紙
    },
    "container": {
        "name_zh": "貨櫃航運",
        "name_en": "CONTAINER",
        "category": "shipping",
        "stocks": ["2603", "2609", "2615"],  # 長榮 陽明 萬海
    },
    "bulk": {
        "name_zh": "散裝航運",
        "name_en": "BULK",
        "category": "shipping",
        "stocks": ["2606", "2607", "2637"],  # 裕民 榮運 慧洋-KY
    },
    "auto": {
        "name_zh": "汽車",
        "name_en": "AUTO",
        "category": "traditional",
        "stocks": ["2207", "2201"],  # 和泰車 裕隆
    },
    "construct": {
        "name_zh": "營建",
        "name_en": "CONSTRUCT",
        "category": "traditional",
        "stocks": ["2548", "2542", "1808"],  # 華固 興富發 潤泰新
    },
}

# 修正錯誤的代號(矽晶圓)
SECTORS["wafer"]["stocks"] = ["6488", "5483", "8016"]  # 環球晶 中美晶 矽創
# 修正被動元件
SECTORS["mlcc"]["stocks"] = ["2327", "2492", "3026"]  # 國巨 華新科 禾伸堂

STOCK_NAMES = {
    "2408": "南亞科", "2344": "華邦電", "6770": "力積電", "3260": "威剛",
    "4967": "十銓", "8271": "宇瞻", "2451": "創見", "5289": "宜鼎",
    "2327": "國巨", "2492": "華新科", "3026": "禾伸堂",
    "2409": "友達", "3481": "群創",
    "6488": "環球晶", "5483": "中美晶", "8016": "矽創",
    "2002": "中鋼", "2007": "燁興", "2014": "中鴻",
    "1101": "台泥", "1102": "亞泥", "1110": "東泥",
    "1301": "台塑", "1303": "南亞", "1326": "台化", "6505": "台塑化",
    "1903": "士紙", "1904": "正隆", "1905": "華紙",
    "2603": "長榮", "2609": "陽明", "2615": "萬海",
    "2606": "裕民", "2607": "榮運", "2637": "慧洋-KY",
    "2207": "和泰車", "2201": "裕隆",
    "2548": "華固", "2542": "興富發", "1808": "潤泰新",
}


def fetch_finmind(dataset, data_id=None, start_date=None, end_date=None, retry=3):
    """通用 FinMind API 抓取函式"""
    headers = {"Authorization": f"Bearer {FINMIND_TOKEN}"}
    params = {"dataset": dataset}
    if data_id:
        params["data_id"] = data_id
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date

    for attempt in range(retry):
        try:
            resp = requests.get(FINMIND_URL, headers=headers, params=params, timeout=30)
            if resp.status_code == 200:
                return resp.json().get("data", [])
            elif resp.status_code == 402:
                print(f"  ⚠ Rate limit hit, sleeping 60s...")
                time.sleep(60)
            else:
                print(f"  ⚠ HTTP {resp.status_code}: {resp.text[:100]}")
        except Exception as e:
            print(f"  ⚠ Error (attempt {attempt+1}): {e}")
            time.sleep(2)
    return []


def get_pbr_data(stock_id, days=1300):
    """抓取個股 PBR 歷史資料 (約 5 年)"""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    data = fetch_finmind("TaiwanStockPER", stock_id, start_date, end_date)
    # 過濾掉 PBR=0 的異常值
    return [d for d in data if d.get("PBR", 0) > 0]


def get_price_data(stock_id, days=30):
    """抓取近期股價"""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return fetch_finmind("TaiwanStockPrice", stock_id, start_date, end_date)


def get_monthly_revenue(stock_id):
    """抓取月營收"""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
    return fetch_finmind("TaiwanStockMonthRevenue", stock_id, start_date, end_date)


def calc_percentile(value, history):
    """計算當前值在歷史資料中的百分位"""
    if not history or value is None:
        return None
    sorted_vals = sorted(history)
    below = sum(1 for v in sorted_vals if v < value)
    return round(below / len(sorted_vals) * 100, 1)


def determine_phase(pbr_percentile, revenue_yoy):
    """根據 PBR 位階與營收年增率判斷循環階段"""
    if pbr_percentile is None:
        return "unknown"
    if pbr_percentile < 25:
        return "bottom" if (revenue_yoy or 0) < 10 else "recovery"
    elif pbr_percentile < 50:
        return "recovery"
    elif pbr_percentile < 75:
        return "expansion"
    elif pbr_percentile < 90:
        return "peak"
    else:
        return "overheat"


def process_stock(stock_id):
    """處理單一個股: 抓資料 → 計算指標"""
    print(f"  → {stock_id} {STOCK_NAMES.get(stock_id, '?')}")

    # PBR
    pbr_history = get_pbr_data(stock_id)
    time.sleep(0.3)  # 避免 rate limit

    if not pbr_history:
        return None

    current_pbr = pbr_history[-1].get("PBR", 0)
    pbr_values = [d["PBR"] for d in pbr_history]
    pbr_percentile = calc_percentile(current_pbr, pbr_values)
    pbr_5y_high = max(pbr_values) if pbr_values else 0
    pbr_5y_low = min(pbr_values) if pbr_values else 0
    pbr_median = sorted(pbr_values)[len(pbr_values) // 2] if pbr_values else 0

    # 股價
    price_data = get_price_data(stock_id, days=10)
    time.sleep(0.3)
    current_price = price_data[-1].get("close", 0) if price_data else 0
    prev_price = price_data[-2].get("close", current_price) if len(price_data) >= 2 else current_price
    price_chg_pct = round((current_price - prev_price) / prev_price * 100, 2) if prev_price else 0

    # 月營收
    revenue_data = get_monthly_revenue(stock_id)
    time.sleep(0.3)
    latest_yoy = 0
    if revenue_data:
        latest = revenue_data[-1]
        latest_yoy = round(latest.get("revenue_year", 0), 1)

    phase = determine_phase(pbr_percentile, latest_yoy)

    return {
        "stock_id": stock_id,
        "name": STOCK_NAMES.get(stock_id, stock_id),
        "price": current_price,
        "price_chg_pct": price_chg_pct,
        "pbr": round(current_pbr, 2),
        "pbr_percentile": pbr_percentile,
        "pbr_5y_high": round(pbr_5y_high, 2),
        "pbr_5y_low": round(pbr_5y_low, 2),
        "pbr_median": round(pbr_median, 2),
        "revenue_yoy": latest_yoy,
        "phase": phase,
    }


def process_sector(sector_key, sector_info):
    """處理單一類股: 計算所有成分股 → 彙總"""
    print(f"\n[{sector_info['name_zh']}]")
    stocks = []
    for stock_id in sector_info["stocks"]:
        result = process_stock(stock_id)
        if result:
            stocks.append(result)

    if not stocks:
        return None

    # 類股平均指標
    avg_pbr_percentile = round(sum(s["pbr_percentile"] or 0 for s in stocks) / len(stocks), 1)
    avg_revenue_yoy = round(sum(s["revenue_yoy"] or 0 for s in stocks) / len(stocks), 1)
    sector_phase = determine_phase(avg_pbr_percentile, avg_revenue_yoy)

    return {
        "key": sector_key,
        "name_zh": sector_info["name_zh"],
        "name_en": sector_info["name_en"],
        "category": sector_info["category"],
        "avg_pbr_percentile": avg_pbr_percentile,
        "avg_revenue_yoy": avg_revenue_yoy,
        "phase": sector_phase,
        "stocks": stocks,
    }


def generate_signals(sectors):
    """根據各類股狀態產生訊號"""
    signals = []
    for s in sectors:
        if s["avg_pbr_percentile"] >= 85:
            signals.append({
                "level": "warn",
                "sector": s["name_zh"],
                "message": f"{s['name_zh']}類股 PBR 位階達 {s['avg_pbr_percentile']}%，接近 5 年高檔，警戒。",
            })
        elif s["avg_pbr_percentile"] <= 20 and s["avg_revenue_yoy"] > 0:
            signals.append({
                "level": "up",
                "sector": s["name_zh"],
                "message": f"{s['name_zh']}類股 PBR 僅 {s['avg_pbr_percentile']}% 位階，營收年增 {s['avg_revenue_yoy']}%，落底訊號浮現。",
            })
        elif s["avg_pbr_percentile"] <= 15:
            signals.append({
                "level": "watch",
                "sector": s["name_zh"],
                "message": f"{s['name_zh']}類股 PBR 處 {s['avg_pbr_percentile']}% 低位階，但營收尚未轉強，續觀察。",
            })
    return signals


def main():
    if not FINMIND_TOKEN:
        print("⚠ 警告: 未設定 FINMIND_TOKEN，使用免費額度 (300 requests/hour)")
        print("  請至 https://finmindtrade.com 註冊取得 token 以提升額度")

    print(f"\n{'='*50}")
    print(f"台股景氣循環監控 - 資料更新")
    print(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")

    sectors_result = []
    for key, info in SECTORS.items():
        result = process_sector(key, info)
        if result:
            sectors_result.append(result)

    signals = generate_signals(sectors_result)

    output = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_date": datetime.now().strftime("%Y-%m-%d"),
        "sectors": sectors_result,
        "signals": signals,
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 完成！共處理 {len(sectors_result)} 類股，產出 data.json")
    print(f"  訊號數量: {len(signals)}")


if __name__ == "__main__":
    main()
