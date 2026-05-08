# Real-Time RAG (Streaming Intelligence)

A project implementing a live semantic layer where incoming data streams are vectorized and indexed within milliseconds for immediate LLM reasoning.

## 🚀 Getting Started

### 1. Prerequisites
- **Docker Desktop**: Required for Qdrant and Kafka.
- **Ollama**: Installed and running locally.
- **Python 3.10+**

### 2. Setup
1. **Start Infrastructure**:
   ```bash
   docker-compose up -d
   ```
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Pull LLM Model**:
   ```bash
   ollama pull llama3:8b
   ```

### 3. Running the System
The system consists of three main components that should run in separate terminals:

1. **Start the Ingestion Layer** (Simulates live data):
   ```bash
   python src/producer.py
   ```

2. **Start the Stream Processor** (Embeds and Indexes):
   ```bash
   python src/processor.py
   ```

3. **Start the Query Interface** (Interact with the AI):
   ```bash
   python src/query_engine.py
   ```

## 🛠️ Architecture
- **Ingestion**: Redpanda (Kafka compatible)
- **Vector DB**: Qdrant
- **Embedding**: Sentence-Transformers (all-MiniLM-L6-v2)
- **Orchestration**: LangGraph
- **LLM**: Ollama (Llama 3)