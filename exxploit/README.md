# exxploit

> **Launch-Grade XSS Payload Toolkit & C2 Framework**

[![CI](https://github.com/example/exxploit/workflows/CI/badge.svg)](https://github.com/example/exxploit/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey.svg)](https://github.com/example/exxploit)

A professional red-teaming framework for XSS payload generation, automated exploitation, and session-based C2 management. Designed for authorized security auditing with advanced evasion capabilities.

---

## ⚡ Key Features

- **🕵️ Zero-Day Evasion**: Detects and bypasses DevTools, headless browsers, and sandboxed environments (`evasion.js`).
- **🔐 Session Management**: Automatic secure key generation per engagement. Isolates targets to prevent cross-contamination.
- **🛡️ Production C2**: High-performance Waitress-based C2 server with rate limiting, caching, and async logging.
- **🎓 Training Lab**: Built-in isolated simulation environment (`exxploit lab`) for safe practice.
- **🎭 Behavioral Camouflage**: Mimics human jitter/interaction to mask malicious activity (`camouflage.js`).
- **🧩 Polymorphic Payloads**: Auto-generates unique signatures for every request.

---

## 🚀 Installation

### Linux / macOS
```bash
git clone https://github.com/example/exxploit
cd exxploit
pip install -r requirements.txt
pip install -e .
playwright install chromium
```

### Windows
```powershell
git clone https://github.com/example/exxploit
cd exxploit
python -m pip install -r requirements.txt
python -m pip install -e .
playwright install chromium
```

---

## 🎓 Quick Start: Training Lab

New to `exxploit`? Start the isolated training environment to practice safely.

```bash
exxploit lab
```
This launches a **vulnerable target app** (port 5000) and a **C2 server** (port 8081) in a sandboxed mode. Follow the onscreen instructions to scan and exploit the target.

---

## 🛠️ Usage Guide

### 1. Session Management (Recommended)
Create a new engagement session to automatically generate unique encryption keys.

```bash
# Create session for a target
exxploit session new acme-crop --target https://acme.com

# List active sessions
exxploit session list
```

### 2. Start C2 Server
Launch the Command & Control server. It automatically uses the key from your active session.

```bash
# Start on default port 8080
exxploit server

# Expose to network (e.g. on VPS)
exxploit server --host 0.0.0.0 --port 8080
```

### 3. Scan for Vulnerabilities
Scan a target URL for XSS vectors.

```bash
exxploit scan "http://target.com/search?q=INJECT"
```

### 4. Generate Payloads
Generate obfuscated JavaScript payloads linked to your C2.

```bash
# Basic keylogger
exxploit payload keylogger

# Advanced chain (Evasion -> Camouflage -> Keylogger)
exxploit attack --payloads "evasion,keylogger"
```

---

## 📦 Payload Modules

| Module | Description |
|--------|-------------|
| **evasion** | Detects analysis environments (VMs, debuggers) and self-destructs. |
| **camouflage** | Adds fake user interaction (mouse events, scroll) to mask bot behavior. |
| **keylogger** | Captures keystrokes and exfiltrates via WebRTC/Beacon. |
| **miner** | Crypto-clipper that swaps wallet addresses in clipboard/DOM. |
| **clipboard** | Harvests session tokens, cookies, and LocalStorage data. |
| **download** | Steals files via drag-and-drop hijacking. |
| **replicate** | Self-replicating worm (iframe injection). |

---

## 🏗️ Architecture

- **Core**: Python-based CLI (`typer`) and Payload Factory.
- **C2 Server**: specialized Flask/Waitress server for payload delivery and data aggregation.
- **Automation**: Playwright-based bot (`GhostAuditBot`) for verifying exploits.

### Directory Structure
- `exxploit/`: Core python package.
- `*.js`: JavaScript payload templates.
- `tests/`: Unit tests and `training.py` lab.
- `logs/`: C2 event logs (JSON structured).

---

## ⚠️ Legal Disclaimer

**This tool is for authorized security testing and educational purposes only.**
Using this tool against systems you do not have explicit permission to test is illegal and violates the terms of service. The authors accept no liability for any misuse of this software.

---

## License
MIT
