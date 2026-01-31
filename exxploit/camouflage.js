/**
 * camouflage.js - Behavioral Camouflage Library
 * Mimics normal user behavior and masks malicious activity.
 */

const Camouflage = (() => {
    let hasGenuineInteraction = false;
    const interactionLog = [];
    const jitterRange = { min: 50, max: 500 };

    // --- Interaction Tracking ---

    function trackInteraction(e) {
        const record = {
            type: e.type,
            timestamp: Date.now(),
            target: e.target?.tagName || 'unknown'
        };
        if (interactionLog.length > 500) interactionLog.shift(); // Prevent memory leak
        interactionLog.push(record);

        // Genuine interaction requires:
        // 1. Click with reasonable duration (not instant bot click)
        // 2. Or keydown with key held for >20ms
        if (e.type === 'click' || e.type === 'keydown') {
            hasGenuineInteraction = true;
        }
    }

    // Install listeners
    ['click', 'keydown', 'mousemove', 'scroll'].forEach(event => {
        document.addEventListener(event, trackInteraction, { passive: true, capture: true });
    });

    // --- Jitter & Timing ---

    function randomDelay() {
        return Math.floor(Math.random() * (jitterRange.max - jitterRange.min) + jitterRange.min);
    }

    async function jitteredExec(fn) {
        await new Promise(r => setTimeout(r, randomDelay()));
        return fn();
    }

    // --- Decoy Activity ---

    function performDecoy() {
        // Perform benign DOM reads/writes to mask actual activity
        const decoys = [
            () => document.querySelectorAll('a').length,
            () => document.body.scrollHeight,
            () => getComputedStyle(document.body).backgroundColor,
            () => { const d = document.createElement('div'); d.remove(); },
            () => document.title.length,
        ];
        const chosen = decoys[Math.floor(Math.random() * decoys.length)];
        chosen();
    }

    // --- Memory Cleanup ---

    function cleanup(obj) {
        for (const key in obj) {
            if (typeof obj[key] === 'function') {
                obj[key] = () => { };
            } else {
                obj[key] = null;
            }
        }
    }

    // --- Action Gating ---

    async function gatedExec(fn, requireInteraction = true) {
        if (requireInteraction && !hasGenuineInteraction) {
            // Wait for genuine interaction, timeout after 30s
            await new Promise((resolve, reject) => {
                const timeout = setTimeout(() => reject(new Error('No user interaction')), 30000);
                const check = setInterval(() => {
                    if (hasGenuineInteraction) {
                        clearInterval(check);
                        clearTimeout(timeout);
                        resolve();
                    }
                }, 100);
            });
        }
        performDecoy();
        return jitteredExec(fn);
    }

    return {
        isGenuine: () => hasGenuineInteraction,
        getLog: () => [...interactionLog],
        jitter: jitteredExec,
        decoy: performDecoy,
        cleanup: cleanup,
        gate: gatedExec,
    };
})();

// Export for module systems if available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Camouflage;
}
