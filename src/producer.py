import json
import time
import yfinance as yf
from confluent_kafka import Producer
from datetime import datetime
import os
import random
from dotenv import load_dotenv

load_dotenv()

# Kafka configuration
conf = {
    'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', '127.0.0.1:9092'),
    'client.id': 'advanced-aliasing-producer'
}

producer = Producer(conf)
topic = os.getenv('KAFKA_TOPIC', 'live_stream')

# Expanded Stock Universe with Human-Readable Names
STOCK_MAP = {
    'AAPL': 'Apple Inc.',
    'MSFT': 'Microsoft Corporation',
    'GOOGL': 'Alphabet Inc. (Google)',
    'AMZN': 'Amazon.com Inc.',
    'NVDA': 'NVIDIA Corporation',
    'META': 'Meta Platforms (Facebook)',
    'TSLA': 'Tesla Inc.',
    'NFLX': 'Netflix Inc.',
    'AMD': 'Advanced Micro Devices (AMD)',
    'INTC': 'Intel Corporation',
    'ADBE': 'Adobe Inc.',
    'CRM': 'Salesforce Inc.',
    'ORCL': 'Oracle Corporation',
    'AVGO': 'Broadcom Inc.',
    'QCOM': 'Qualcomm Inc.',
    'BTC-USD': 'Bitcoin'
}

def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')

def fetch_enhanced_data(symbol, company_name):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        
        current_price = info.last_price or 0
        market_cap = info.market_cap or 0
        cap_str = f"${market_cap/1e12:.2f}T" if market_cap > 0 else "N/A"
        
        messages = []
        
        # 1. Price Message with Explicit Company Name for Semantic Search
        messages.append({
            "type": "PRICE_UPDATE",
            "timestamp": datetime.now().isoformat(),
            "producer_start_time": time.time(),
            "symbol": symbol,
            "company_name": company_name,
            "content": f"{company_name} ({symbol}) is currently trading at ${current_price:,.2f}. Market Cap: {cap_str}.",
            "metadata": {"price": current_price, "source": "YahooFinance"}
        })
        
        # 2. News Message with Explicit Company Name
        news = ticker.news or []
        for article in news[:2]:
            title = article.get('title')
            if not title: continue
            
            messages.append({
                "type": "NEWS_ARTICLE",
                "timestamp": datetime.now().isoformat(),
                "producer_start_time": time.time(),
                "symbol": symbol,
                "company_name": company_name,
                "content": f"LATEST NEWS for {company_name}: {title}",
                "metadata": {
                    "link": article.get('link', '#'),
                    "publisher": article.get('publisher', 'Unknown'),
                    "source": "YahooFinance-News"
                }
            })
            
        return messages
    except Exception as e:
        print(f"⚠️ Warning: {symbol} skip: {e}")
        return []

print(f"🚀 Advanced Aliasing Producer Online.")
print(f"Tracking {len(STOCK_MAP)} entities...")

try:
    while True:
        symbols = list(STOCK_MAP.keys())
        random.shuffle(symbols)
        
        for symbol in symbols:
            company_name = STOCK_MAP[symbol]
            msgs = fetch_enhanced_data(symbol, company_name)
            for data in msgs:
                producer.produce(
                    topic, 
                    key=symbol, 
                    value=json.dumps(data).encode('utf-8'),
                    callback=delivery_report
                )
                print(f"📡 {symbol} ({company_name}) Update sent.")
            
            producer.poll(0)
            time.sleep(0.5)
            
        time.sleep(10)
except KeyboardInterrupt:
    print("Stopping...")
finally:
    producer.flush()
