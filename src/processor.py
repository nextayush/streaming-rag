import json
import os
import uuid
from typing import TypedDict, Annotated, List
from dotenv import load_dotenv
from confluent_kafka import Consumer, KafkaError
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from langgraph.graph import StateGraph, END

load_dotenv()

# Configuration
KAFKA_CONF = {
    'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', '127.0.0.1:9092'),
    'group.id': 'rag-processor-group',
    'auto.offset.reset': 'earliest'
}
TOPIC = os.getenv('KAFKA_TOPIC', 'live_stream')
QDRANT_HOST = os.getenv('QDRANT_HOST', '127.0.0.1')
QDRANT_PORT = int(os.getenv('QDRANT_PORT', 6333))
COLLECTION_NAME = os.getenv('QDRANT_COLLECTION', 'real_time_knowledge')
MODEL_NAME = os.getenv('EMBEDDING_MODEL_NAME', 'all-MiniLM-L6-v2')

# Initialize Clients
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
embedder = SentenceTransformer(MODEL_NAME)

# Ensure collection exists
try:
    qdrant.get_collection(COLLECTION_NAME)
    print(f"Collection '{COLLECTION_NAME}' already exists.")
except Exception:
    print(f"Creating collection '{COLLECTION_NAME}'...")
    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=384,  # size for all-MiniLM-L6-v2
            distance=models.Distance.COSINE
        )
    )

# LangGraph State
class ProcessorState(TypedDict):
    raw_data: dict
    embedding: List[float]
    status: str

def embed_node(state: ProcessorState):
    content = state['raw_data']['content']
    print(f"Embedding: {content[:50]}...")
    vector = embedder.encode(content).tolist()
    return {"embedding": vector, "status": "embedded"}

def index_node(state: ProcessorState):
    data = state['raw_data']
    vector = state['embedding']
    
    point_id = str(uuid.uuid4())
    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            models.PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "content": data['content'],
                    "timestamp": data['timestamp'],
                    "source": data['source'],
                    "symbol": data['symbol'],
                    **data.get('metadata', {})
                }
            )
        ]
    )
    print(f"Indexed: {data['symbol']} at {data['timestamp']}")
    return {"status": "indexed"}

# Build Graph
workflow = StateGraph(ProcessorState)
workflow.add_node("embed", embed_node)
workflow.add_node("index", index_node)
workflow.set_entry_point("embed")
workflow.add_edge("embed", "index")
workflow.add_edge("index", END)
processor_app = workflow.compile()

def run_consumer():
    consumer = Consumer(KAFKA_CONF)
    consumer.subscribe([TOPIC])
    
    print(f"Starting consumer on topic: {TOPIC}")
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(msg.error())
                    break
            
            # Process message
            try:
                raw_data = json.loads(msg.value().decode('utf-8'))
                initial_state = {"raw_data": raw_data}
                processor_app.invoke(initial_state)
            except Exception as e:
                print(f"Error processing message: {e}")
                
    except KeyboardInterrupt:
        print("Stopping consumer...")
    finally:
        consumer.close()

if __name__ == "__main__":
    run_consumer()
