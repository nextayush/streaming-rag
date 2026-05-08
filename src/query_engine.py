import os
import requests
from typing import List, Dict
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

load_dotenv()

# Configuration
QDRANT_HOST = os.getenv('QDRANT_HOST', '127.0.0.1')
QDRANT_PORT = int(os.getenv('QDRANT_PORT', 6333))
COLLECTION_NAME = os.getenv('QDRANT_COLLECTION', 'real_time_knowledge')
OLLAMA_URL = os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3:8b')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL_NAME', 'all-MiniLM-L6-v2')

# Initialize Clients
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, check_compatibility=False)
embedder = SentenceTransformer(EMBEDDING_MODEL)

def get_relevant_context(query: str, limit: int = 5) -> List[Dict]:
    query_vector = embedder.encode(query).tolist()
    
    search_results = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit
    ).points
    
    contexts = []
    for res in search_results:
        contexts.append({
            "content": res.payload['content'],
            "timestamp": res.payload['timestamp'],
            "symbol": res.payload['symbol']
        })
    return contexts

def query_ollama(query: str, context_docs: List[Dict]):
    context_str = "\n".join([
        f"- {doc['content']} (Recorded at: {doc['timestamp']})" 
        for doc in context_docs
    ])
    
    # Print retrieved context for debugging
    print("\n--- RETRIEVED CONTEXT ---")
    print(context_str)
    print("-------------------------\n")
    
    prompt = f"""<|system|>
You are a Real-Time Intelligence Assistant. Use the following pieces of retrieved real-time information to answer the user's question.
If you don't know the answer based on the context, just say that you don't have real-time data on that yet. 
Be concise and factual.

Context:
{context_str}
<|user|>
Question: {query}
<|assistant|>
Answer:"""

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": 2048,
                "temperature": 0.1
            }
        }
    )
    
    if response.status_code == 200:
        return response.json()['response']
    else:
        return f"Error: {response.text}"

def run_rag_loop():
    print(f"--- Real-Time RAG Interface (Model: {OLLAMA_MODEL}) ---")
    print("Type 'exit' to quit.")
    
    while True:
        user_query = input("\nQuery: ")
        if user_query.lower() in ['exit', 'quit']:
            break
        
        print("Searching real-time memory...")
        context = get_relevant_context(user_query)
        
        if not context:
            print("No real-time context found for this query.")
            continue
            
        print(f"Found {len(context)} relevant events. Thinking...")
        answer = query_ollama(user_query, context)
        
        print("\nAI Response:")
        print("-" * 50)
        print(answer)
        print("-" * 50)

if __name__ == "__main__":
    run_rag_loop()
