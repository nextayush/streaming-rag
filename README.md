# Real-Time RAG (Streaming Intelligence)

A project implementing a live semantic layer where incoming data streams are vectorized and indexed within milliseconds for immediate LLM reasoning.

## 🚀 Getting Started

### 1. Prerequisites
- **Docker Desktop**: Required for Qdrant and Kafka.
- **Ollama**: Installed and running locally.
- **Python 3.10+**

### 2. Setup
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Pull LLM Model**:
   ```bash
   ollama pull llama3:8b
   ```

### 3. Running the System
We have implemented a unified startup script that handles the Docker infrastructure and all Python services.

**Start everything with one command:**
```bash
python start_all.py
```

This script will automatically:
1. Boot up the Docker infrastructure (Redpanda, Redpanda Console, Qdrant).
2. Start the **Ingestion Layer** (`src/producer.py`).
3. Start the **Stream Processor** (`src/processor.py`).
4. Launch the **Unified Web Dashboard** (`src/dashboard.py`).

**Access the Interfaces:**
- **Web Dashboard**: Interact with the RAG system at [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Redpanda Console**: View streaming topics at [http://127.0.0.1:8080](http://127.0.0.1:8080)

To shut down the entire system gracefully (including spinning down Docker containers), simply press `Ctrl + C` in the terminal where `start_all.py` is running.

## 🛠️ Architecture
- **Ingestion**: Redpanda (Kafka compatible)
- **Vector DB**: Qdrant
- **Embedding**: Sentence-Transformers (all-MiniLM-L6-v2)
- **Orchestration**: LangGraph
- **LLM**: Ollama (Llama 3)
- **Dashboard Interface**: FastAPI, Uvicorn, and WebSockets