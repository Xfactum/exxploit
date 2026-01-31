"""
training.py - exxploit Training Lab Orchestrator
Launches a FULLY ISOLATED simulated environment for safe practice.

ISOLATION MECHANISMS:
- Separate ports (5000 target, 8081 C2) vs production defaults
- Separate log directory (tests/lab_logs/)
- LAB_MODE=1 environment flag set for all processes
- Separate session file (lab_sessions.json)
"""

import subprocess
import sys
import time
import os
import signal
import webbrowser
import shutil
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

# --- Isolation Configuration ---
LAB_C2_PORT = 8081  # Different from production default (8080)
LAB_TARGET_PORT = 5000
LAB_LOG_DIR = os.path.join(os.path.dirname(__file__), 'lab_logs')
LAB_SESSION_FILE = os.path.join(os.path.dirname(__file__), 'lab_sessions.json')

def setup_isolation():
    """Create isolated directories and clear old lab data."""
    # Create fresh lab log directory
    if os.path.exists(LAB_LOG_DIR):
        shutil.rmtree(LAB_LOG_DIR)
    os.makedirs(LAB_LOG_DIR, exist_ok=True)
    
    # Remove old lab session file
    if os.path.exists(LAB_SESSION_FILE):
        os.remove(LAB_SESSION_FILE)
    
    console.print(f"[dim]Lab logs: {LAB_LOG_DIR}[/dim]")

def run_lab():
    console.print(Panel.fit("[bold cyan]🛡️ Welcome to the exxploit Training Lab 🛡️[/bold cyan]", border_style="cyan"))
    console.print("[yellow]⚠️  LAB MODE: All activity is isolated from live systems.[/yellow]\n")
    
    setup_isolation()
    
    # Build isolated environment
    env = os.environ.copy()
    env['LAB_MODE'] = '1'  # Flag for all child processes
    env['C2_PORT'] = str(LAB_C2_PORT)
    env['C2_LOG_DIR'] = LAB_LOG_DIR
    env['EXXPLOIT_SESSION_FILE'] = LAB_SESSION_FILE
    
    # 1. Start C2 Server (isolated)
    c2_proc = subprocess.Popen(
        [sys.executable, "c2_server.py"],
        stdout=open(os.path.join(LAB_LOG_DIR, 'c2_stdout.log'), 'w'),
        stderr=open(os.path.join(LAB_LOG_DIR, 'c2_stderr.log'), 'w'),
        env=env
    )
    console.print(f"[+] [green]C2 Server started[/green] on http://127.0.0.1:{LAB_C2_PORT} (LAB)")

    # 2. Start Vulnerable Target (isolated)
    target_proc = subprocess.Popen(
        [sys.executable, "tests/vulnerable_app.py"],
        stdout=open(os.path.join(LAB_LOG_DIR, 'target_stdout.log'), 'w'),
        stderr=open(os.path.join(LAB_LOG_DIR, 'target_stderr.log'), 'w'),
        env=env
    )
    console.print(f"[+] [red]Target Application started[/red] on http://127.0.0.1:{LAB_TARGET_PORT} (LAB)")
    
    time.sleep(2) # Wait for startup

    # 3. Instructions
    instructions = """
    # 🎯 Mission Objective
    Exploit the target application running at **http://localhost:5000**
    
    ### Step 1: Scan for Vulnerabilities
    Open a NEW terminal and run:
    ```bash
    exxploit scan http://127.0.0.1:5000
    ```
    
    ### Step 2: Launch Attack
    Use the `payload` command to generate an attack string.
    Example (Reflected XSS):
    ```bash
    exxploit payload keylogger --c2 http://127.0.0.1:8081
    ```
    Copy the output and paste it into the **Search** box on the target site.

    ### Step 3: Verify Success
    Watch the C2 logs here or open http://127.0.0.1:8081/health
    """
    console.print(Markdown(instructions))
    
    # 4. Open Browser
    if console.input("\n[?] Open target in browser? (y/n): ").lower() == 'y':
        webbrowser.open("http://127.0.0.1:5000")

    console.print("\n[bold yellow]Press Ctrl+C to stop the lab environment...[/bold yellow]")
    
    try:
        # Monitor Loop
        while True:
            # Simple log tailing simulation could go here
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[*] Shutting down lab...")
        c2_proc.terminate()
        target_proc.terminate()
        console.print("[+] Cleanup complete.")

if __name__ == "__main__":
    run_lab()
