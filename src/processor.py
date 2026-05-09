import json
import os
import uuid
import time
import requests
from typing import TypedDict, List
from dotenv import load_dotenv
from confluent_kafka import Consumer, KafkaError
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from langgraph.graph import StateGraph, END
from datetime import datetime

load_dotenv()

KAFKA_CONF = {
    'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', '127.0.0.1:9092'),
    'group.id': 'rag-multimodal-processor',
    'auto.offset.reset': 'latest'
}
TOPIC = os.getenv('KAFKA_TOPIC', 'live_stream')
QDRANT_HOST = os.getenv('QDRANT_HOST', '127.0.0.1')
QDRANT_PORT = 6333
COLLECTION_NAME = os.getenv('QDRANT_COLLECTION', 'real_time_knowledge')
DASHBOARD_URL = "http://127.0.0.1:8000/update_metrics"

qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, check_compatibility=False)
embedder = SentenceTransformer('all-MiniLM-L6-v2')
analyzer = SentimentIntensityAnalyzer()

class ProcessorState(TypedDict):
    raw_data: dict
    semantic_data: dict
    embedding: List[float]
    latencies: dict

def analysis_node(state: ProcessorState):
    data = state['raw_data']
    sentiment_score = 0
    sentiment_label = "NEUTRAL"
    
    if data['type'] == "NEWS_ARTICLE":
        scores = analyzer.polarity_scores(data['content'])
        sentiment_score = scores['compound']
        if sentiment_score >= 0.05: sentiment_label = "POSITIVE"
        elif sentiment_score <= -0.05: sentiment_label = "NEGATIVE"
        
    state['semantic_data'] = {
        "content": data['content'],
        "sentiment": sentiment_label,
        "sentiment_score": sentiment_score,
        "type": data['type'],
        "weight": 1.5 if abs(sentiment_score) > 0.5 else 1.0
    }
    return state

def embed_node(state: ProcessorState):
    start_time = time.time()
    text_to_embed = f"[{state['semantic_data']['sentiment']}] {state['semantic_data']['content']}"
    state['embedding'] = embedder.encode(text_to_embed).tolist()
    state['latencies'] = {"embed_ms": (time.time() - start_time) * 1000}
    return state

def index_node(state: ProcessorState):
    start_time = time.time()
    data = state['raw_data']
    semantic = state['semantic_data']
    
    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=state['embedding'],
                payload={
                    **data,
                    **semantic,
                    "ingest_timestamp": time.time()
                }
            )
        ]
    )
    
    total_ms = (time.time() - data['producer_start_time']) * 1000
    try:
        requests.post(DASHBOARD_URL, json={
            "symbol": data['symbol'],
            "embed_ms": state['latencies']['embed_ms'],
            "index_ms": (time.time() - start_time) * 1000,
            "total_ms": total_ms,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }, timeout=0.1)
    except: pass
    return state

workflow = StateGraph(ProcessorState)
workflow.add_node("analyze", analysis_node)
workflow.add_node("embed", embed_node)
workflow.add_node("index", index_node)
workflow.set_entry_point("analyze")
workflow.add_edge("analyze", "embed")
workflow.add_edge("embed", "index")
workflow.add_edge("index", END)
processor_app = workflow.compile()

def run_consumer():
    consumer = Consumer(KAFKA_CONF)
    consumer.subscribe([TOPIC])
    print(f"🧠 Multi-Modal Sentiment Processor Online.")
    while True:
        msg = consumer.poll(1.0)
        if msg is None or msg.error(): continue
        try:
            raw_data = json.loads(msg.value().decode('utf-8'))
            processor_app.invoke({"raw_data": raw_data})
        except Exception as e: print(f"Error: {e}")

if __name__ == "__main__":
    run_consumer()
