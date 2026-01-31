"""
stealth.py - Human-Like Behavior & CAPTCHA Solving Module

Provides anti-detection measures and CAPTCHA solving integration for
evading bot detection during scanning and automation.

Supported CAPTCHA Services:
- 2Captcha (https://2captcha.com)
- Anti-Captcha (https://anti-captcha.com)
- CapSolver (https://capsolver.com)

Set API key via environment variable:
    export CAPTCHA_API_KEY=your_key_here
    export CAPTCHA_SERVICE=2captcha  # or anticaptcha, capsolver
"""

import asyncio
import random
import time
import os
import logging
import requests
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# --- Configuration ---

@dataclass
class StealthConfig:
    """Configuration for stealth behavior."""
    # Timing (milliseconds)
    min_delay_ms: int = 500
    max_delay_ms: int = 3000
    typing_delay_min: int = 30
    typing_delay_max: int = 150
    
    # Mouse behavior
    enable_mouse_jitter: bool = True
    mouse_pause_chance: float = 0.1
    
    # Request patterns
    randomize_user_agent: bool = True
    randomize_viewport: bool = True
    add_random_headers: bool = True
    
    # CAPTCHA
    captcha_service: str = os.environ.get('CAPTCHA_SERVICE', '2captcha')
    captcha_api_key: str = os.environ.get('CAPTCHA_API_KEY', '')
    captcha_timeout: int = 120


# --- Human-Like User Agents ---

USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Chrome macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Chrome Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.3; rv:122.0) Gecko/20100101 Firefox/122.0",
    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
]

COMMON_HEADERS = [
    ('Accept-Language', ['en-US,en;q=0.9', 'en-GB,en;q=0.9', 'en;q=0.8']),
    ('Accept-Encoding', ['gzip, deflate, br']),
    ('Accept', ['text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8']),
    ('Sec-Fetch-Dest', ['document']),
    ('Sec-Fetch-Mode', ['navigate']),
    ('Sec-Fetch-Site', ['none', 'same-origin', 'cross-site']),
    ('Sec-Fetch-User', ['?1']),
    ('Upgrade-Insecure-Requests', ['1']),
]

VIEWPORT_PRESETS = [
    (1920, 1080),  # Full HD Desktop
    (1536, 864),   # Common laptop
    (1440, 900),   # MacBook
    (1366, 768),   # Common laptop
    (2560, 1440),  # QHD Desktop
    (1280, 800),   # Older MacBook
]


# --- Stealth Utilities ---

def get_random_user_agent() -> str:
    """Get a random realistic user agent."""
    return random.choice(USER_AGENTS)


def get_random_viewport() -> Tuple[int, int]:
    """Get a random realistic viewport size."""
    base = random.choice(VIEWPORT_PRESETS)
    # Add slight random variation
    width = base[0] + random.randint(-50, 50)
    height = base[1] + random.randint(-30, 30)
    return (width, height)


def get_stealth_headers(base_headers: Optional[Dict] = None) -> Dict[str, str]:
    """Generate headers that look like a real browser."""
    headers = base_headers.copy() if base_headers else {}
    
    headers['User-Agent'] = get_random_user_agent()
    
    for header_name, options in COMMON_HEADERS:
        if header_name not in headers:
            headers[header_name] = random.choice(options)
    
    return headers


def human_delay(min_ms: int = 500, max_ms: int = 2000) -> None:
    """Sleep for a human-like random duration."""
    delay = random.randint(min_ms, max_ms) / 1000.0
    # Add occasional longer pauses (simulating reading/thinking)
    if random.random() < 0.1:
        delay += random.uniform(1.0, 3.0)
    time.sleep(delay)


async def async_human_delay(min_ms: int = 500, max_ms: int = 2000) -> None:
    """Async version of human delay."""
    delay = random.randint(min_ms, max_ms) / 1000.0
    if random.random() < 0.1:
        delay += random.uniform(1.0, 3.0)
    await asyncio.sleep(delay)


# --- Human-Like Typing ---

async def human_type(page, text: str, selector: Optional[str] = None) -> None:
    """
    Type text with human-like timing variations.
    
    Args:
        page: Playwright page object
        text: Text to type
        selector: Optional selector to click first
    """
    if selector:
        await page.click(selector)
        await async_human_delay(200, 500)
    
    for i, char in enumerate(text):
        # Base typing delay
        delay = random.randint(30, 120)
        
        # Occasional longer pauses (thinking/errors)
        if random.random() < 0.05:
            delay += random.randint(200, 500)
        
        # Faster typing in the middle of words
        if char.isalnum() and i > 0 and text[i-1].isalnum():
            delay = int(delay * 0.7)
        
        # Slower for special characters
        if not char.isalnum():
            delay = int(delay * 1.3)
        
        await page.keyboard.type(char, delay=delay)
    
    # Pause after finishing typing
    await async_human_delay(300, 800)


# --- Human-Like Mouse Movement ---

async def human_mouse_move(page, x: int, y: int) -> None:
    """
    Move mouse with human-like curved path.
    
    Args:
        page: Playwright page object
        x, y: Target coordinates
    """
    # Get current position (default to center if unknown)
    current_x = page.mouse._x if hasattr(page.mouse, '_x') else 500
    current_y = page.mouse._y if hasattr(page.mouse, '_y') else 400
    
    # Generate intermediate points for curved movement
    steps = random.randint(5, 15)
    
    for i in range(steps):
        progress = (i + 1) / steps
        
        # Add slight curves (bezier-like)
        curve_offset_x = random.uniform(-20, 20) * (1 - progress)
        curve_offset_y = random.uniform(-15, 15) * (1 - progress)
        
        interp_x = current_x + (x - current_x) * progress + curve_offset_x
        interp_y = current_y + (y - current_y) * progress + curve_offset_y
        
        await page.mouse.move(interp_x, interp_y)
        await asyncio.sleep(random.uniform(0.01, 0.03))
    
    # Final position
    await page.mouse.move(x, y)


async def human_click(page, selector: str) -> None:
    """
    Click element with human-like behavior.
    
    Args:
        page: Playwright page object
        selector: Element selector to click
    """
    element = await page.query_selector(selector)
    if not element:
        logger.warning(f"Element not found: {selector}")
        return
    
    box = await element.bounding_box()
    if not box:
        # Fallback to direct click
        await element.click()
        return
    
    # Click at slightly random position within element
    click_x = box['x'] + box['width'] * random.uniform(0.3, 0.7)
    click_y = box['y'] + box['height'] * random.uniform(0.3, 0.7)
    
    # Move mouse to target
    await human_mouse_move(page, click_x, click_y)
    
    # Brief pause before clicking
    await asyncio.sleep(random.uniform(0.1, 0.3))
    
    # Click with slight position variation
    await page.mouse.click(click_x, click_y)
    
    # Pause after click
    await async_human_delay(200, 600)


async def human_scroll(page, direction: str = 'down', amount: int = 300) -> None:
    """
    Scroll with human-like behavior.
    
    Args:
        page: Playwright page object
        direction: 'up' or 'down'
        amount: Approximate scroll amount in pixels
    """
    # Add variation to scroll amount
    actual_amount = amount + random.randint(-50, 50)
    
    if direction == 'up':
        actual_amount = -actual_amount
    
    # Scroll in small increments
    steps = random.randint(3, 7)
    step_amount = actual_amount / steps
    
    for _ in range(steps):
        await page.mouse.wheel(0, step_amount)
        await asyncio.sleep(random.uniform(0.05, 0.15))
    
    # Pause after scrolling
    await async_human_delay(300, 800)


# --- CAPTCHA Solving ---

class CaptchaSolver:
    """
    CAPTCHA solving integration for 2Captcha, Anti-Captcha, and CapSolver.
    
    Usage:
        solver = CaptchaSolver()
        solution = await solver.solve_recaptcha_v2(site_key, page_url)
    """
    
    def __init__(self, config: Optional[StealthConfig] = None):
        self.config = config or StealthConfig()
        self.api_key = self.config.captcha_api_key
        self.service = self.config.captcha_service.lower()
        
        if not self.api_key:
            logger.warning("No CAPTCHA API key configured. Set CAPTCHA_API_KEY environment variable.")
    
    def is_configured(self) -> bool:
        """Check if CAPTCHA solving is available."""
        return bool(self.api_key)
    
    async def solve_recaptcha_v2(self, site_key: str, page_url: str) -> Optional[str]:
        """
        Solve reCAPTCHA v2 and return the token.
        
        Args:
            site_key: The reCAPTCHA site key
            page_url: URL of the page with CAPTCHA
            
        Returns:
            CAPTCHA token or None if failed
        """
        if not self.is_configured():
            logger.error("CAPTCHA API key not configured")
            return None
        
        try:
            if self.service == '2captcha':
                return await self._solve_2captcha_v2(site_key, page_url)
            elif self.service == 'anticaptcha':
                return await self._solve_anticaptcha_v2(site_key, page_url)
            elif self.service == 'capsolver':
                return await self._solve_capsolver_v2(site_key, page_url)
            else:
                logger.error(f"Unknown CAPTCHA service: {self.service}")
                return None
        except Exception as e:
            logger.error(f"CAPTCHA solving failed: {e}")
            return None
    
    async def _solve_2captcha_v2(self, site_key: str, page_url: str) -> Optional[str]:
        """Solve using 2Captcha service."""
        # Submit task
        submit_url = "https://2captcha.com/in.php"
        submit_params = {
            'key': self.api_key,
            'method': 'userrecaptcha',
            'googlekey': site_key,
            'pageurl': page_url,
            'json': 1,
        }
        
        resp = requests.post(submit_url, data=submit_params, timeout=30)
        data = resp.json()
        
        if data.get('status') != 1:
            logger.error(f"2Captcha submit failed: {data.get('error_text', 'Unknown error')}")
            return None
        
        task_id = data['request']
        logger.info(f"2Captcha task submitted: {task_id}")
        
        # Poll for result
        result_url = "https://2captcha.com/res.php"
        start_time = time.time()
        
        while time.time() - start_time < self.config.captcha_timeout:
            await asyncio.sleep(5)
            
            result_params = {
                'key': self.api_key,
                'action': 'get',
                'id': task_id,
                'json': 1,
            }
            
            resp = requests.get(result_url, params=result_params, timeout=30)
            data = resp.json()
            
            if data.get('status') == 1:
                logger.info("2Captcha solved successfully")
                return data['request']
            elif data.get('request') != 'CAPCHA_NOT_READY':
                logger.error(f"2Captcha error: {data.get('error_text', data.get('request'))}")
                return None
        
        logger.error("2Captcha timeout")
        return None
    
    async def _solve_anticaptcha_v2(self, site_key: str, page_url: str) -> Optional[str]:
        """Solve using Anti-Captcha service."""
        # Create task
        create_url = "https://api.anti-captcha.com/createTask"
        task_data = {
            'clientKey': self.api_key,
            'task': {
                'type': 'RecaptchaV2TaskProxyless',
                'websiteURL': page_url,
                'websiteKey': site_key,
            }
        }
        
        resp = requests.post(create_url, json=task_data, timeout=30)
        data = resp.json()
        
        if data.get('errorId') != 0:
            logger.error(f"Anti-Captcha create failed: {data.get('errorDescription')}")
            return None
        
        task_id = data['taskId']
        logger.info(f"Anti-Captcha task created: {task_id}")
        
        # Poll for result
        result_url = "https://api.anti-captcha.com/getTaskResult"
        start_time = time.time()
        
        while time.time() - start_time < self.config.captcha_timeout:
            await asyncio.sleep(5)
            
            result_data = {
                'clientKey': self.api_key,
                'taskId': task_id,
            }
            
            resp = requests.post(result_url, json=result_data, timeout=30)
            data = resp.json()
            
            if data.get('status') == 'ready':
                logger.info("Anti-Captcha solved successfully")
                return data['solution']['gRecaptchaResponse']
            elif data.get('errorId') != 0:
                logger.error(f"Anti-Captcha error: {data.get('errorDescription')}")
                return None
        
        logger.error("Anti-Captcha timeout")
        return None
    
    async def _solve_capsolver_v2(self, site_key: str, page_url: str) -> Optional[str]:
        """Solve using CapSolver service."""
        create_url = "https://api.capsolver.com/createTask"
        task_data = {
            'clientKey': self.api_key,
            'task': {
                'type': 'ReCaptchaV2TaskProxyLess',
                'websiteURL': page_url,
                'websiteKey': site_key,
            }
        }
        
        resp = requests.post(create_url, json=task_data, timeout=30)
        data = resp.json()
        
        if data.get('errorId') != 0:
            logger.error(f"CapSolver create failed: {data.get('errorDescription')}")
            return None
        
        task_id = data['taskId']
        logger.info(f"CapSolver task created: {task_id}")
        
        # Poll for result
        result_url = "https://api.capsolver.com/getTaskResult"
        start_time = time.time()
        
        while time.time() - start_time < self.config.captcha_timeout:
            await asyncio.sleep(3)
            
            result_data = {
                'clientKey': self.api_key,
                'taskId': task_id,
            }
            
            resp = requests.post(result_url, json=result_data, timeout=30)
            data = resp.json()
            
            if data.get('status') == 'ready':
                logger.info("CapSolver solved successfully")
                return data['solution']['gRecaptchaResponse']
            elif data.get('errorId') != 0:
                logger.error(f"CapSolver error: {data.get('errorDescription')}")
                return None
        
        logger.error("CapSolver timeout")
        return None
    
    async def detect_captcha(self, page) -> Optional[Dict[str, Any]]:
        """
        Detect if a CAPTCHA is present on the page.
        
        Returns:
            Dict with CAPTCHA info or None if not found
        """
        # Check for reCAPTCHA v2
        recaptcha_frame = await page.query_selector('iframe[src*="recaptcha"]')
        if recaptcha_frame:
            # Extract site key from the page
            site_key = await page.evaluate('''() => {
                const el = document.querySelector('.g-recaptcha');
                return el ? el.getAttribute('data-sitekey') : null;
            }''')
            
            if site_key:
                return {
                    'type': 'recaptcha_v2',
                    'site_key': site_key,
                }
        
        # Check for reCAPTCHA v3 (invisible)
        recaptcha_v3 = await page.query_selector('script[src*="recaptcha/api.js?render="]')
        if recaptcha_v3:
            src = await recaptcha_v3.get_attribute('src')
            if 'render=' in src:
                site_key = src.split('render=')[1].split('&')[0]
                return {
                    'type': 'recaptcha_v3',
                    'site_key': site_key,
                }
        
        # Check for hCaptcha
        hcaptcha = await page.query_selector('.h-captcha, iframe[src*="hcaptcha"]')
        if hcaptcha:
            site_key = await page.evaluate('''() => {
                const el = document.querySelector('.h-captcha');
                return el ? el.getAttribute('data-sitekey') : null;
            }''')
            return {
                'type': 'hcaptcha',
                'site_key': site_key,
            }
        
        return None
    
    async def solve_on_page(self, page) -> bool:
        """
        Detect and solve any CAPTCHA on the page.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if solved or no CAPTCHA, False if failed
        """
        captcha = await self.detect_captcha(page)
        
        if not captcha:
            return True  # No CAPTCHA found
        
        logger.info(f"CAPTCHA detected: {captcha['type']}")
        
        if not self.is_configured():
            logger.error("CAPTCHA detected but no API key configured!")
            logger.error("Set CAPTCHA_API_KEY environment variable with your 2Captcha/Anti-Captcha/CapSolver key")
            return False
        
        if captcha['type'] == 'recaptcha_v2':
            token = await self.solve_recaptcha_v2(
                captcha['site_key'],
                page.url
            )
            
            if token:
                # Inject the token into the page
                await page.evaluate(f'''(token) => {{
                    document.querySelector('#g-recaptcha-response').value = token;
                    // Try to trigger callback
                    if (window.___grecaptcha_cfg) {{
                        const clients = window.___grecaptcha_cfg.clients;
                        if (clients) {{
                            Object.keys(clients).forEach(key => {{
                                const client = clients[key];
                                if (client && client.callback) {{
                                    client.callback(token);
                                }}
                            }});
                        }}
                    }}
                }}''', token)
                return True
        
        return False


# --- Stealth Session for Requests ---

class StealthSession:
    """
    A requests Session wrapper with human-like behavior.
    """
    
    def __init__(self, config: Optional[StealthConfig] = None):
        self.config = config or StealthConfig()
        self.session = requests.Session()
        self._request_count = 0
        self._last_request_time = 0
        
        # Set realistic headers
        self.session.headers.update(get_stealth_headers())
    
    def _apply_delay(self) -> None:
        """Apply human-like delay between requests."""
        if self._last_request_time > 0:
            elapsed = time.time() - self._last_request_time
            min_delay = self.config.min_delay_ms / 1000.0
            
            if elapsed < min_delay:
                human_delay(self.config.min_delay_ms, self.config.max_delay_ms)
        
        self._last_request_time = time.time()
    
    def _rotate_headers(self) -> None:
        """Rotate headers to appear more human."""
        self._request_count += 1
        
        # Rotate user agent every 5-10 requests
        if self._request_count % random.randint(5, 10) == 0:
            self.session.headers['User-Agent'] = get_random_user_agent()
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """Make a GET request with human-like behavior."""
        self._apply_delay()
        self._rotate_headers()
        return self.session.get(url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """Make a POST request with human-like behavior."""
        self._apply_delay()
        self._rotate_headers()
        return self.session.post(url, **kwargs)
