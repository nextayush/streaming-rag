import json
import time
import random
from confluent_kafka import Producer
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Kafka configuration
conf = {
    'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', '127.0.0.1:9092'),
    'client.id': 'stock-producer'
}

producer = Producer(conf)
topic = os.getenv('KAFKA_TOPIC', 'live_stream')

def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

def generate_mock_data():
    stocks = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX']
    events = [
        "is launching a new AI-powered product today.",
        "reported higher than expected quarterly earnings.",
        "announced a strategic partnership with a major cloud provider.",
        "is facing regulatory scrutiny over data privacy.",
        "saw a sharp increase in stock price after the keynote.",
        "is expanding its operations into the European market.",
        "suffered a minor security breach, according to sources.",
        "is investing heavily in quantum computing research."
    ]
    
    symbol = random.choice(stocks)
    event = random.choice(events)
    price_change = round(random.uniform(-5.0, 5.0), 2)
    
    content = f"{symbol} {event} Stock price changed by {price_change}%."
    
    return {
        "timestamp": datetime.now().isoformat(),
        "source": "live_ticker",
        "symbol": symbol,
        "content": content,
        "metadata": {
            "price_change": price_change,
            "priority": "high" if abs(price_change) > 3 else "normal"
        }
    }

print(f"Starting producer, sending messages to topic: {topic}")

try:
    while True:
        data = generate_mock_data()
        producer.produce(
            topic, 
            key=data['symbol'], 
            value=json.dumps(data).encode('utf-8'),
            callback=delivery_report
        )
        producer.poll(0)
        print(f"Sent: {data['content']}")
        time.sleep(2)  # Send a new event every 2 seconds
except KeyboardInterrupt:
    print("Stopping producer...")
finally:
    producer.flush()
