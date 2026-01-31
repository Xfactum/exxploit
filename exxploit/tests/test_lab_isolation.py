"""
test_lab_isolation.py - Verify Lab Mode Does Not Pollute Live Data
"""

import os
import sys
import subprocess
import time
import shutil
import requests

# Directories
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAB_LOG_DIR = os.path.join(PROJECT_ROOT, 'tests', 'lab_logs')
LIVE_LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')

def test_lab_isolation():
    print("=" * 50)
    print("LAB ISOLATION VERIFICATION TEST")
    print("=" * 50)
    
    # --- Setup: Clear any existing test artifacts ---
    if os.path.exists(LAB_LOG_DIR):
        shutil.rmtree(LAB_LOG_DIR)
    
    # Record live log state BEFORE lab
    live_files_before = set(os.listdir(LIVE_LOG_DIR)) if os.path.exists(LIVE_LOG_DIR) else set()
    print(f"[1] Live logs before: {len(live_files_before)} files")
    
    # --- Start Lab C2 Server in LAB_MODE ---
    env = os.environ.copy()
    env['LAB_MODE'] = '1'
    env['C2_PORT'] = '8082'  # Different port for test
    env['C2_LOG_DIR'] = LAB_LOG_DIR
    
    print("[2] Starting C2 in LAB_MODE...")
    c2_proc = subprocess.Popen(
        [sys.executable, os.path.join(PROJECT_ROOT, 'c2_server.py')],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    time.sleep(2)  # Wait for startup
    
    # --- Send Test Beacon ---
    print("[3] Sending test beacon...")
    try:
        resp = requests.post('http://127.0.0.1:8082/beacon', json={'test': 'isolation_check'}, timeout=2)
        print(f"    Response: {resp.status_code}")
    except Exception as e:
        print(f"    Error: {e}")
    
    # --- Cleanup: Stop Server ---
    c2_proc.terminate()
    c2_proc.wait()
    print("[4] C2 stopped")
    
    # --- Verify Isolation ---
    print("\n[5] VERIFICATION RESULTS:")
    
    # Check lab logs exist
    lab_log_file = os.path.join(LAB_LOG_DIR, 'c2_events.json')
    lab_logs_exist = os.path.exists(lab_log_file)
    print(f"    Lab logs created: {'✅ YES' if lab_logs_exist else '❌ NO'} ({lab_log_file})")
    
    # Check live logs were NOT modified
    live_files_after = set(os.listdir(LIVE_LOG_DIR)) if os.path.exists(LIVE_LOG_DIR) else set()
    new_live_files = live_files_after - live_files_before
    live_unchanged = len(new_live_files) == 0
    print(f"    Live logs unchanged: {'✅ YES' if live_unchanged else '❌ NO'} (new files: {new_live_files})")
    
    # Final Result
    print("\n" + "=" * 50)
    if lab_logs_exist and live_unchanged:
        print("✅ ISOLATION VERIFIED: Lab mode does NOT pollute live data.")
    else:
        print("❌ ISOLATION FAILED: Check the results above.")
    print("=" * 50)
    
    # Cleanup lab artifacts
    if os.path.exists(LAB_LOG_DIR):
        shutil.rmtree(LAB_LOG_DIR)
        print("[6] Cleaned up lab artifacts")

if __name__ == "__main__":
    test_lab_isolation()
