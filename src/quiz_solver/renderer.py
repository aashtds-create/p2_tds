"""
Page rendering using headless browser
"""
from playwright.async_api import async_playwright, Browser, Page
import asyncio
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class PageRenderer:
    """
    Handles rendering JavaScript-heavy quiz pages
    """
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright = None
        self.lock = asyncio.Lock()
    
    async def _init_browser(self):
        """Initialize browser if not already done"""
        async with self.lock:
            if self.browser is None:
                logger.info("Initializing Playwright browser")
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(headless=True)
    
    async def render(self, url: str) -> str:
        """
        Render a URL and extract the quiz content
        
        Args:
            url: URL to render
            
        Returns:
            Extracted text content from the page
        """
        await self._init_browser()
        
        if not self.browser:
            raise RuntimeError("Browser initialization failed")

        page = await self.browser.new_page()
        
        try:
            logger.info(f"Navigating to {url}")
            # Navigate to URL
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for any potential dynamic content
            # We try to wait for body to be populated
            await page.wait_for_selector("body", timeout=10000)
            
            # Extract the full text content, not just #result
            # The quiz might be anywhere on the page
            content = await page.evaluate("document.body.innerText")
            
            # Also check for media files (audio, video) and data files (CSV, PDF, etc.)
            media_info = await page.evaluate("""() => {
                const audioElements = Array.from(document.querySelectorAll('audio source, audio'));
                const videoElements = Array.from(document.querySelectorAll('video source, video'));
                const links = Array.from(document.querySelectorAll('a[href]'));
                
                const audioFiles = audioElements.map(el => el.src || el.getAttribute('src')).filter(Boolean);
                const videoFiles = videoElements.map(el => el.src || el.getAttribute('src')).filter(Boolean);
                const allLinks = links.map(a => a.href);
                
                const mediaLinks = allLinks.filter(href => /\\.(mp3|wav|mp4|webm|ogg|m4a)$/i.test(href));
                const dataLinks = allLinks.filter(href => /\\.(csv|xlsx?|json|txt|pdf)$/i.test(href));
                
                return {
                    audio: [...new Set([...audioFiles, ...mediaLinks.filter(l => /\\.(mp3|wav|ogg|m4a)$/i.test(l))])],
                    video: [...new Set([...videoFiles, ...mediaLinks.filter(l => /\\.(mp4|webm)$/i.test(l))])],
                    data: [...new Set(dataLinks)]
                };
            }""")
            
            # Append media and data files info to content if found
            if media_info.get('audio') or media_info.get('video') or media_info.get('data'):
                content += f"\n\n[MEDIA FILES FOUND]\n"
                if media_info.get('audio'):
                    content += f"Audio: {', '.join(media_info['audio'])}\n"
                if media_info.get('video'):
                    content += f"Video: {', '.join(media_info['video'])}\n"
                if media_info.get('data'):
                    content += f"Data files (CSV/PDF/etc): {', '.join(media_info['data'])}\n"
            
            logger.info(f"Extracted {len(content)} characters from {url}")
            return content
        except Exception as e:
            logger.error(f"Error rendering {url}: {e}")
            raise
        finally:
            await page.close()
    
    async def close(self):
        """Clean up browser resources"""
        async with self.lock:
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

