import subprocess
import time
import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=====================================================")
    print("🚀 STARTING STREAMING-RAG INTELLIGENCE CORE")
    print("=====================================================\n")
    
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("[*] Booting up Docker Infrastructure (Kafka, Zookeeper, Qdrant)...")
    try:
        subprocess.run(["docker-compose", "up", "-d"], cwd=root_dir, check=True)
        print("[*] Waiting 5 seconds for infrastructure to initialize...")
        time.sleep(5)
    except Exception as e:
        print(f"❌ Failed to start Docker containers: {e}")
        print("Please ensure Docker Desktop is running.")
        sys.exit(1)
    
    commands = [
        ("Producer", ["python", "src/producer.py"]),
        ("Processor", ["python", "src/processor.py"]),
        ("Dashboard", ["python", "src/dashboard.py"])
    ]
    
    processes = []
    
    try:
        for name, cmd in commands:
            print(f"[*] Booting up {name} Engine...")
            p = subprocess.Popen(cmd, cwd=root_dir)
            processes.append((name, p))
            time.sleep(2)  
            
        print("\n✅ ALL SYSTEMS ONLINE!")
        print("🌐 Unified Dashboard running at: http://127.0.0.1:8000")
        print("\n🛑 Press [Ctrl + C] anytime to gracefully shut down everything.\n")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ INITIATING SHUTDOWN SEQUENCE...")
        
        for name, p in processes:
            print(f"[*] Terminating {name} Engine...")
            p.terminate()
            
        for name, p in processes:
            p.wait()
            
        print("[*] Spinning down Docker containers...")
        subprocess.run(["docker-compose", "stop"], cwd=root_dir)
            
        print("✅ Shutdown complete. Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
