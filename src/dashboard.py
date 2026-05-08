from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import json
import asyncio
from typing import List
from pydantic import BaseModel

app = FastAPI()

# Store latest metrics
class Metric(BaseModel):
    symbol: str
    embed_ms: float
    index_ms: float
    total_ms: float
    timestamp: str

metrics_history: List[Metric] = []
active_connections: List[WebSocket] = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        active_connections.remove(websocket)

@app.post("/update_metrics")
async def update_metrics(metric: Metric):
    metrics_history.append(metric)
    if len(metrics_history) > 50:
        metrics_history.pop(0)
    
    # Broadcast to all connected UI clients
    for connection in active_connections:
        await connection.send_json(metric.dict())
    return {"status": "ok"}

@app.get("/")
async def get():
    return HTMLResponse(html_content)

html_content = """
<!DOCTYPE html>
<html>
    <head>
        <title>Streaming RAG Telemetry</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            .glass { background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2); }
            body { background: #0f172a; color: #f8fafc; font-family: 'Inter', sans-serif; }
        </style>
    </head>
    <body class="p-8">
        <div class="max-w-7xl mx-auto">
            <header class="mb-8 flex justify-between items-center">
                <div>
                    <h1 class="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">Streaming Intelligence Telemetry</h1>
                    <p class="text-slate-400">Sub-second Visibility Monitor (2026 Edition)</p>
                </div>
                <div id="status" class="px-4 py-2 rounded-full bg-red-500/20 text-red-400 border border-red-500/50">Disconnected</div>
            </header>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div class="glass p-6 rounded-2xl">
                    <h3 class="text-slate-400 text-sm font-medium mb-2 uppercase tracking-wider">Avg Visibility Latency</h3>
                    <div id="avg-total" class="text-3xl font-mono text-emerald-400">0.0ms</div>
                </div>
                <div class="glass p-6 rounded-2xl">
                    <h3 class="text-slate-400 text-sm font-medium mb-2 uppercase tracking-wider">Embedding Engine</h3>
                    <div id="avg-embed" class="text-3xl font-mono text-blue-400">0.0ms</div>
                </div>
                <div class="glass p-6 rounded-2xl">
                    <h3 class="text-slate-400 text-sm font-medium mb-2 uppercase tracking-wider">Indexing Speed</h3>
                    <div id="avg-index" class="text-3xl font-mono text-purple-400">0.0ms</div>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div class="glass p-6 rounded-2xl">
                    <h3 class="text-lg font-semibold mb-4">Latency Trend (Real-time)</h3>
                    <canvas id="latencyChart" height="200"></canvas>
                </div>
                <div class="glass p-6 rounded-2xl overflow-hidden flex flex-col h-[400px]">
                    <h3 class="text-lg font-semibold mb-4">Event Stream</h3>
                    <div id="event-log" class="space-y-2 overflow-y-auto flex-1 font-mono text-sm">
                        <!-- Events will appear here -->
                    </div>
                </div>
            </div>
        </div>

        <script>
            const ws = new WebSocket(`ws://${window.location.host}/ws`);
            const status = document.getElementById('status');
            const log = document.getElementById('event-log');
            
            const ctx = document.getElementById('latencyChart').getContext('2d');
            const chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Total Visibility Latency (ms)',
                        data: [],
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } },
                        x: { grid: { display: false } }
                    },
                    plugins: { legend: { display: false } }
                }
            });

            ws.onopen = () => {
                status.innerText = 'Live Connection Active';
                status.className = 'px-4 py-2 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/50';
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                // Update stats
                document.getElementById('avg-total').innerText = data.total_ms.toFixed(1) + 'ms';
                document.getElementById('avg-embed').innerText = data.embed_ms.toFixed(1) + 'ms';
                document.getElementById('avg-index').innerText = data.index_ms.toFixed(1) + 'ms';

                // Add to chart
                chart.data.labels.push(new Date().toLocaleTimeString());
                chart.data.datasets[0].data.push(data.total_ms);
                if (chart.data.labels.length > 20) {
                    chart.data.labels.shift();
                    chart.data.datasets[0].data.shift();
                }
                chart.update();

                // Add to log
                const item = document.createElement('div');
                item.className = 'p-3 rounded-lg bg-slate-800/50 border border-slate-700 animate-in fade-in slide-in-from-right-4 duration-300';
                item.innerHTML = `<span class="text-emerald-400">[${data.symbol}]</span> Freshness: <span class="text-blue-400">${data.total_ms.toFixed(1)}ms</span> <span class="text-slate-500 float-right">${data.timestamp}</span>`;
                log.prepend(item);
                if (log.children.length > 50) log.lastChild.remove();
            };

            ws.onclose = () => {
                status.innerText = 'Disconnected';
                status.className = 'px-4 py-2 rounded-full bg-red-500/20 text-red-400 border border-red-500/50';
            };
        </script>
    </body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
