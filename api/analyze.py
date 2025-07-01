from fastapi import FastAPI, Request
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 또는 ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_company_name(ticker):
    try:
        url = f"https://finance.naver.com/item/main.naver?code={ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        response.encoding = 'euc-kr'
        soup = BeautifulSoup(response.text, 'html.parser')
        company_name = soup.select_one('div.wrap_company h2 a')
        return company_name.text.strip() if company_name else ""
    except Exception as e:
        print(f"Error in get_company_name: {e}")
        return ""

def get_stock_history(ticker, months=6):
    try:
        url = f"https://fchart.stock.naver.com/sise.nhn?symbol={ticker}&timeframe=day&count={months*31}&requestType=0"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        content = response.text
        if 'item data=' in content:
            data_points = content.split('item data=')[1:]
            data = []
            for point in data_points:
                try:
                    data_str = point.split('"')[1]
                    values = data_str.split('|')
                    if len(values) >= 6:
                        date = datetime.strptime(values[0], '%Y%m%d')
                        data.append({
                            'date': date,
                            'open': float(values[1]),
                            'high': float(values[2]),
                            'low': float(values[3]),
                            'close': float(values[4]),
                            'volume': float(values[5])
                        })
                except:
                    continue
            if not data:
                return pd.DataFrame()
            df = pd.DataFrame(data)
            df = df.set_index('date')
            df = df.sort_index(ascending=True)
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"Error in get_stock_history: {e}")
        return pd.DataFrame()

@app.post("/analyze")
async def analyze(request: Request):
    body = await request.json()
    tickers = body.get("tickers", [])
    results = []
    for ticker in tickers:
        hist = get_stock_history(ticker)
        company_name = get_company_name(ticker)
        if not hist.empty:
            df = hist.copy()
            df['EMA12'] = df['close'].ewm(span=12, adjust=False).mean()
            df['EMA26'] = df['close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = df['EMA12'] - df['EMA26']
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['MACD_Gap'] = df['MACD'] - df['Signal']
            macd_range = df['MACD_Gap'].max() - df['MACD_Gap'].min()
            df['MACD_Norm'] = (df['MACD_Gap'] - df['MACD_Gap'].min()) / macd_range * 200 - 100 if macd_range != 0 else 0
            df['MA20'] = df['close'].rolling(window=20, min_periods=1).mean()
            df['STD20'] = df['close'].rolling(window=20, min_periods=1).std()
            df['BB_Position'] = ((df['close'] - df['MA20']) / (df['STD20'] * 2)) * 100
            df['BB_Position'] = df['BB_Position'].clip(-100, 100)
            current_price = df['close'].iloc[-1]
            macd = round(df['MACD_Norm'].iloc[-1], 2)
            bb_position = round(df['BB_Position'].iloc[-1], 2)
            action = "HOLD"
            if macd > 80 and bb_position > 80:
                action = "SELL"
            elif -100 <= macd <= -80 and bb_position < -80:
                action = "BUY"
            results.append({
                "ticker": ticker,
                "company_name": company_name,
                "current_price": current_price,
                "macd": macd,
                "bb_position": bb_position,
                "action": action
            })
        else:
            results.append({
                "ticker": ticker,
                "company_name": company_name,
                "current_price": "N/A",
                "macd": "N/A",
                "bb_position": "N/A",
                "action": "N/A"
            })
    return {"results": results}

# Vercel용 handler
handler = app
