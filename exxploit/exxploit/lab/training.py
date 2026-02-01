"""
training.py - exxploit Training Lab Orchestrator
Launches a FULLY ISOLATED simulated environment for safe practice.

ISOLATION MECHANISMS:
- Separate ports (5000 target, 8081 C2) vs production defaults
- Separate log directory (~/.exxploit/lab_logs/)
- LAB_MODE=1 environment flag set for all processes
- Separate session file (~/.exxploit/lab_sessions.json)
"""

import subprocess
import sys
import time
import os
import webbrowser
import shutil
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

# --- Isolation Configuration ---
LAB_C2_PORT = 8081  # Different from production default (8080)
LAB_TARGET_PORT = 5000

# Use a central config directory for lab data
CONFIG_DIR = Path.home() / ".exxploit"
LAB_LOG_DIR = CONFIG_DIR / "lab_logs"
LAB_SESSION_FILE = CONFIG_DIR / "lab_sessions.json"

def setup_isolation():
    """Create isolated directories and clear old lab data."""
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
    # Create fresh lab log directory
    if LAB_LOG_DIR.exists():
        shutil.rmtree(LAB_LOG_DIR)
    LAB_LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Remove old lab session file
    if LAB_SESSION_FILE.exists():
        LAB_SESSION_FILE.unlink()
    
    console.print(f"[dim]Lab logs: {LAB_LOG_DIR}[/dim]")

def run_lab():
    console.print(Panel.fit("[bold cyan]🛡️ Welcome to the exxploit Training Lab 🛡️[/bold cyan]", border_style="cyan"))
    console.print("[yellow]⚠️  LAB MODE: All activity is isolated from live systems.[/yellow]\n")
    
    setup_isolation()
    
    # Build isolated environment
    env = os.environ.copy()
    env['LAB_MODE'] = '1'  # Flag for all child processes
    env['C2_PORT'] = str(LAB_C2_PORT)
    env['C2_LOG_DIR'] = str(LAB_LOG_DIR)
    env['EXXPLOIT_SESSION_FILE'] = str(LAB_SESSION_FILE)
    
    # 1. Start C2 Server (isolated)
    # Using module-based execution to avoid path issues
    c2_proc = subprocess.Popen(
        [sys.executable, "-m", "exxploit.server.c2"],
        stdout=open(LAB_LOG_DIR / 'c2_stdout.log', 'w'),
        stderr=open(LAB_LOG_DIR / 'c2_stderr.log', 'w'),
        env=env
    )
    console.print(f"[+] [green]C2 Server started[/green] on http://127.0.0.1:{LAB_C2_PORT} (LAB)")

    # 2. Start Vulnerable Target (isolated)
    target_proc = subprocess.Popen(
        [sys.executable, "-m", "exxploit.lab.vulnerable_app"],
        stdout=open(LAB_LOG_DIR / 'target_stdout.log', 'w'),
        stderr=open(LAB_LOG_DIR / 'target_stderr.log', 'w'),
        env=env
    )
    console.print(f"[+] [red]Target Application started[/red] on http://127.0.0.1:{LAB_TARGET_PORT} (LAB)")
    
    time.sleep(2) # Wait for startup

    # Check if processes are actually running
    if c2_proc.poll() is not None:
        console.print("[bold red]Error: C2 Server failed to start. Check logs in ~/.exxploit/lab_logs[/bold red]")
        target_proc.terminate()
        return

    if target_proc.poll() is not None:
        console.print("[bold red]Error: Target Application failed to start. Check logs in ~/.exxploit/lab_logs[/bold red]")
        c2_proc.terminate()
        return

    # 3. Instructions
    instructions = f"""
# 🎯 Mission Objective
Exploit the target application running at **http://localhost:{LAB_TARGET_PORT}**

### Step 1: Scan for Vulnerabilities
Open a NEW terminal and run:
```bash
exxploit scan http://127.0.0.1:{LAB_TARGET_PORT}
```

### Step 2: Launch Attack
Use the `payload` command to generate an attack string.
Example (Reflected XSS):
```bash
exxploit payload keylogger --c2 http://127.0.0.1:{LAB_C2_PORT}
```
Copy the output and paste it into the **Search** box on the target site.

### Step 3: Verify Success
Watch the C2 logs here or open http://127.0.0.1:{LAB_C2_PORT}/health
    """
    console.print(Markdown(instructions))
    
    # 4. Open Browser
    try:
        if console.input("\n[?] Open target in browser? (y/n): ").lower() == 'y':
            webbrowser.open(f"http://127.0.0.1:{LAB_TARGET_PORT}")
    except EOFError:
        pass # Non-interactive mode or automated test

    console.print("\n[bold yellow]Press Ctrl+C to stop the lab environment...[/bold yellow]")
    
    try:
        # Monitor Loop
        while True:
            # Check if processes died
            if c2_proc.poll() is not None:
                console.print("[red]Critical: C2 Server has stopped unexpectedly.[/red]")
                break
            if target_proc.poll() is not None:
                console.print("[red]Critical: Target App has stopped unexpectedly.[/red]")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[*] Shutting down lab...")
    finally:
        c2_proc.terminate()
        target_proc.terminate()
        console.print("[+] Cleanup complete.")

if __name__ == "__main__":
    run_lab()
