import os
import requests
import time
import math
import yfinance as yf
from typing import List, Dict
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

load_dotenv()

QDRANT_HOST = os.getenv('QDRANT_HOST', '127.0.0.1')
QDRANT_PORT = 6333
COLLECTION_NAME = os.getenv('QDRANT_COLLECTION', 'real_time_knowledge')
OLLAMA_URL = os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')

qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, check_compatibility=False)
embedder = SentenceTransformer('all-MiniLM-L6-v2')

STOCK_MAP = {
    'apple': 'AAPL', 'microsoft': 'MSFT', 'google': 'GOOGL', 'alphabet': 'GOOGL',
    'amazon': 'AMZN', 'nvidia': 'NVDA', 'meta': 'META', 'facebook': 'META',
    'tesla': 'TSLA', 'amd': 'AMD', 'intel': 'INTC', 'bitcoin': 'BTC-USD'
}

def fetch_historical_metrics(tickers: List[str]) -> str:
    combined_history = ""
    for symbol in tickers:
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="1mo")
            if hist.empty: continue
            pct_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
            high_price = hist['High'].max()
            combined_history += f"- {symbol}: {pct_change:.2f}% Monthly Growth | 1-Month High: ${high_price:.2f}\n"
        except Exception: pass
    return combined_history

def get_adaptive_context(query: str) -> str:
    now = time.time()
    detected_tickers = [ticker for name, ticker in STOCK_MAP.items() if name in query.lower()]
    
    live_docs = []
    search_queries = [query]
    for ticker in detected_tickers:
        search_queries.append(f"{ticker} price update")
        search_queries.append(f"{ticker} news sentiment")

    try:
        for sq in search_queries:
            query_vector = embedder.encode(sq).tolist()
            results = qdrant.query_points(collection_name=COLLECTION_NAME, query=query_vector, limit=5).points
            for p in results:
                payload = p.payload or {}
                live_docs.append(f"[{payload.get('type')} | {payload.get('sentiment')}] {payload.get('content')}")
        context_str = "--- LIVE STREAM & SENTIMENT DATA ---\n" + "\n".join(list(set(live_docs)))
    except Exception as e:
        context_str = f"--- LIVE STREAM (OFFLINE) ---\nCould not reach Qdrant Vector Store: {e}"
    
    if 'month' in query.lower() or 'compare' in query.lower() or 'buy' in query.lower() or 'better' in query.lower():
        history_str = fetch_historical_metrics(detected_tickers)
        context_str += f"\n\n--- HISTORICAL ARCHIVE ---\n{history_str}"
        
    return context_str

def query_adaptive_agent(query: str, context: str):
    factual_triggers = ['price', 'what is', 'how much', 'current value']
    strategic_triggers = [
        'buy', 'compare', 'better', 'should', 'analyze', 'trend', 
        'direction', 'headed', 'outlook', 'movement', 'recommend', 'worth'
    ]
    
    is_strategic = any(k in query.lower() for k in strategic_triggers)
    
    if not is_strategic:
        prompt = f"""<|system|>
You are a High-Speed Market Data Terminal. Provide a CONCISE, ONE-LINE data response. 
Include the current price and a brief momentum indicator (e.g., 'Trending Up').

Context:
{context}
<|user|>
Question: {query}
<|assistant|>
Answer:"""
    else:
        prompt = f"""<|system|>
You are a Senior Market Intelligence Agent. Provide a structured Strategic Analysis.
MANDATORY REPORT STRUCTURE:
1. **EXECUTIVE SUMMARY**: Factual summary of the current trend/direction.
2. **QUANTITATIVE MOMENTUM**: Analyze the direction of recent price updates.
3. **SENTIMENT VALIDATION**: How news headlines support or contradict this direction.
4. **RISK ASSESSMENT**: Potential traps or reversals.

Context:
{context}
<|user|>
Question: {query}
<|assistant|>
Answer:"""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "options": {"num_ctx": 4096, "temperature": 0}},
            timeout=120
        )
        response_json = response.json()
        if 'error' in response_json:
            return f"⚠️ **Ollama Error:** {response_json['error']}"
        return response_json.get('response', 'Error')
    except requests.exceptions.RequestException as e:
        return f"⚠️ **Intelligence Core Offline:** Could not connect to Ollama at {OLLAMA_URL}. Ensure Ollama is running and the Llama 3.2 model is pulled.\n\nError details: {e}"

def process_query(query: str):
    """Entry point for the Web Frontend — do NOT remove."""
    context = get_adaptive_context(query)
    answer = query_adaptive_agent(query, context)
    return {"answer": answer, "is_strategic": len(answer) > 150}

def main():
    print(f"🚀 [ADAPTIVE INTELLIGENCE CORE] Intent-Aware Mode Active.")
    while True:
        query = input("\nQuery Market Intelligence: ")
        if query.lower() in ['exit', 'quit']: break
        res = process_query(query)
        print(f"\n✨ Response:\n{'='*75 if res['is_strategic'] else '-'*20}\n{res['answer']}")

if __name__ == "__main__":
    main()
