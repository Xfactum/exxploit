"""
stress_test.py - High-Concurrency Load Tester for C2 Server
Simulates botnet traffic to verify stability, rate limiting, and performance.
Using `requests` and `concurrent.futures` for maximum compatibility.
"""

import time
import random
import sys
import os
import signal
import subprocess
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Configuration
C2_HOST = "127.0.0.1"
C2_PORT = 8081  # Use different port to avoid conflict
C2_URL = f"http://{C2_HOST}:{C2_PORT}"
NUM_BOTS = 200 # Reduced for thread safety
requests_per_bot = 5
CONCURRENCY = 20

# Metrics (Thread-safe-ish for simple counters)
stats = {
    'req_total': 0,
    'req_success': 0,
    'req_failed': 0,
    'req_rate_limited': 0,
    'start_time': 0,
    'end_time': 0
}

def bot_behavior(bot_id):
    """Simulate a single bot's lifecycle."""
    session = requests.Session()
    try:
        # 1. Check in (beacon)
        payload = {
            'id': f'bot-{bot_id}',
            'os': 'win10',
            'data': 'initial_checkin'
        }
        try:
            resp = session.post(f"{C2_URL}/beacon", json=payload, timeout=2)
            # Simple atomic increment (GIL protects us here mostly)
            stats['req_total'] += 1
            if resp.status_code == 200:
                stats['req_success'] += 1
            elif resp.status_code == 503: # Our custom rate limit response
                stats['req_rate_limited'] += 1
            else:
                stats['req_failed'] += 1
        except Exception:
            stats['req_failed'] += 1
        
        # Random delay
        time.sleep(random.uniform(0.1, 0.5))
        
        # 2. Request payload (stage 2)
        try:
            resp = session.get(f"{C2_URL}/stage/2/keylogger", timeout=2)
            stats['req_total'] += 1
            if resp.status_code == 200:
                stats['req_success'] += 1
            elif resp.status_code == 503:
                stats['req_rate_limited'] += 1
            else:
                stats['req_failed'] += 1
        except Exception:
            stats['req_failed'] += 1

    except Exception:
        pass

def attack():
    """Launch the swarm."""
    print(f"[*] Launching {NUM_BOTS} bots with concurrency {CONCURRENCY}...")
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        # Submit all bot tasks
        futures = [executor.submit(bot_behavior, i) for i in range(NUM_BOTS)]
        # Wait for all to complete
        for future in futures:
            future.result()
            
    end = time.time()
    
    stats['start_time'] = start
    stats['end_time'] = end

def start_c2_process():
    """Start C2 server in background."""
    env = os.environ.copy()
    env['C2_PORT'] = str(C2_PORT)
    env['C2_HOST'] = C2_HOST
    # Disable rate limiter for valid testing? No, we want to test it.
    
    process = subprocess.Popen(
        [sys.executable, "c2_server.py"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    print(f"[*] Started C2 server (PID: {process.pid}) on port {C2_PORT}")
    time.sleep(3) # Wait for startup
    return process

def main():
    # 1. Start Server
    c2_proc = start_c2_process()
    
    try:
        # 2. Run Stress Test
        attack()
        
        # 3. Report
        duration = stats['end_time'] - stats['start_time']
        rps = stats['req_total'] / duration if duration > 0 else 0
        
        print("\n" + "="*40)
        print("STRESS TEST RESULTS")
        print("="*40)
        print(f"Total Requests:   {stats['req_total']}")
        print(f"Successful:       {stats['req_success']}")
        print(f"Rate Limited:     {stats['req_rate_limited']} (Expected 503s)")
        print(f"Failed:           {stats['req_failed']}")
        print(f"Duration:         {duration:.2f}s")
        print(f"Throughput:       {rps:.2f} req/s")
        print("="*40)
        
        # Benchmarks
        if rps > 50:
            print("[+] Performance: GOOD (>50 req/s)")
        elif rps > 20:
             print("[+] Performance: OK (>20 req/s)")
        else:
            print("[-] Performance: LOW (<20 req/s)")
            
    except KeyboardInterrupt:
        print("\n[!] Interrupted")
    finally:
        # Cleanup
        os.kill(c2_proc.pid, signal.SIGTERM)
        print("[*] C2 server stopped")

if __name__ == "__main__":
    main()
