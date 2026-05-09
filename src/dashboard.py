from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import json
from typing import List
import uvicorn
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from query_engine import process_query

app = FastAPI()

class Metric(BaseModel):
    symbol: str
    embed_ms: float
    index_ms: float
    total_ms: float
    timestamp: str

class QueryRequest(BaseModel):
    query: str

active_connections: List[WebSocket] = []

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True: await websocket.receive_text()
    except: active_connections.remove(websocket)

@app.post("/update_metrics")
async def update_metrics(metric: Metric):
    for conn in active_connections:
        await conn.send_json({"type": "metric", "data": metric.dict()})
    return {"status": "ok"}

@app.post("/query")
async def handle_query(req: QueryRequest):
    try:
        return process_query(req.query)
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        return {"answer": f"Backend Error: {str(e)}\n\n```\n{error_msg}\n```", "is_strategic": False}

@app.get("/")
async def get():
    html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
