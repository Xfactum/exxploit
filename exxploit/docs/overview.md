# exxploit Kit Overview

> **Author:** HACKThief  
> **Version:** 1.0.0  
> **Purpose:** Professional XSS exploitation framework for authorized security testing

---

## 🎯 What Does It Do?

**exxploit** is a complete toolkit for finding and exploiting Cross-Site Scripting (XSS) vulnerabilities in web applications. Think of it as a professional penetration testing weapon that:

1. **Finds weaknesses** in websites where user input isn't properly sanitized
2. **Generates attack payloads** (malicious JavaScript) that exploit those weaknesses
3. **Collects stolen data** (keystrokes, cookies, credentials) via a Command & Control server
4. **Evades detection** using sophisticated anti-analysis techniques

---

## 🔄 How It Works (Workflow)

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   1. SCAN   │───▶│  2. CRAFT   │───▶│  3. INJECT  │───▶│ 4. COLLECT  │
│  Find XSS   │    │   Payload   │    │   Attack    │    │    Data     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### Step 1: Reconnaissance (`exxploit scan`)
You give it a URL with a test marker (`INJECT`), and it:
- Tests multiple XSS payloads automatically
- Identifies which injection contexts work (HTML, attributes, JavaScript, etc.)
- Uses stealth mode to avoid triggering bot detection

### Step 2: Weaponization (`exxploit payload`)
Based on scan results, you generate obfuscated JavaScript payloads:
- Choose from 9+ payload types (keylogger, cookie stealer, crypto clipper, etc.)
- Apply encoding (Base64, CharCode, JsFuck) to evade WAFs
- Payloads automatically phone home to your C2 server

### Step 3: Delivery (`exxploit attack`)
Automated browser (Playwright) injects payloads into target:
- Checks VPN status for OpSec
- Takes proof-of-exploitation screenshots
- Handles CAPTCHA if configured

### Step 4: Collection (`exxploit server`)
Your C2 server receives stolen data:
- Keystrokes, cookies, session tokens
- Clipboard contents, file downloads
- All encrypted and logged to JSON

---

## 💣 Payload Arsenal

| Payload | What It Steals | Stealth Level |
|---------|----------------|---------------|
| **keylogger** | Every keystroke the victim types | ⭐⭐⭐⭐⭐ |
| **clipboard** | Cookies, localStorage, session tokens | ⭐⭐⭐⭐ |
| **miner** | Swaps crypto wallet addresses in clipboard | ⭐⭐⭐⭐ |
| **download** | Files dragged/dropped on the page | ⭐⭐⭐ |
| **exfil** | Any data via DNS/WebSocket/Beacon | ⭐⭐⭐⭐⭐ |
| **virus** | Multi-stage loader with persistence | ⭐⭐⭐⭐ |
| **replicate** | Self-spreading worm via iframes | ⭐⭐⭐ |
| **evasion** | (Helper) Detects debuggers/VMs | ⭐⭐⭐⭐⭐ |
| **camouflage** | (Helper) Mimics human behavior | ⭐⭐⭐⭐⭐ |

---

## 🛡️ Anti-Detection Features

### Evasion Module
- **DevTools Detection**: Self-destructs if victim opens F12
- **VM Detection**: Checks CPU cores, RAM, GPU to spot sandboxes
- **Headless Browser Detection**: Identifies Puppeteer/Selenium bots
- **Timing Analysis**: Detects speed anomalies from automation

### Camouflage Module
- **Mouse Jitter**: Simulates natural cursor movement
- **Typing Delay**: Human-like keystroke timing
- **Scroll Behavior**: Random scroll patterns
- **Action Gating**: Waits for real user interaction before triggering

---

## 🖥️ Command & Control (C2)

The C2 server (`c2_server.py`) is your data collection hub:

- **Production-Ready**: Runs on Waitress WSGI server
- **Rate Limited**: Prevents resource exhaustion attacks
- **Stealth Headers**: Mimics legitimate CDN responses
- **Structured Logging**: JSON logs for easy analysis

### Endpoints
| Endpoint | Purpose |
|----------|---------|
| `/beacon` | Payload check-in |
| `/stage/2/<payload>` | Serve additional payloads |
| `/upload` | Receive exfiltrated data |
| `/css/<data>` | CSS-based exfiltration |
| `/logs` | View collected data |

---

## 🎓 Training Mode

New operators can practice safely:

```bash
exxploit lab
```

This starts:
- **Vulnerable Target** (localhost:5000) - Intentionally broken Flask app
- **Isolated C2** (localhost:8081) - Sandboxed from production

All lab activity is completely isolated from live data.

---

## 📋 Quick Reference

```bash
# Start training environment
exxploit lab

# Scan a target for XSS
exxploit scan "https://target.com/search?q=INJECT"

# Generate a keylogger payload
exxploit payload keylogger --obfuscate base64

# Start C2 server
exxploit server --port 8080

# Full automated attack
exxploit attack https://target.com --payloads "evasion,keylogger,exfil"

# View collected sessions
exxploit sessions
```

---

## ⚠️ Legal Notice

This toolkit is for **authorized security testing only**. Unauthorized access to computer systems is a criminal offense. Always obtain written permission before testing.
