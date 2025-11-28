"""
Page rendering using headless browser
"""
from playwright.async_api import async_playwright, Browser, Page
import asyncio
from typing import Optional
import logging
import base64
import os
import httpx

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
            
            # Extract both text content AND HTML content for hidden elements
            # Some puzzles have hidden elements that innerText won't capture
            text_content = await page.evaluate("document.body.innerText")
            html_content = await page.evaluate("document.body.innerHTML")
            
            # Combine both - prioritize text but include HTML for parsing
            content = f"{text_content}\n\n[RAW HTML FOR HIDDEN ELEMENTS]:\n{html_content}"
            
            # If content is empty or too short, try canvas extraction with Gemini Vision
            if len(content.strip()) < 50:
                logger.warning(f"Text extraction returned only {len(content)} chars. Trying vision extraction for canvas content...")
                canvas_content = await self._extract_canvas_content(page)
                if canvas_content:
                    content = canvas_content
                    logger.info("Successfully extracted content from canvas using Gemini Vision")
            
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
    
    async def _extract_canvas_content(self, page: Page) -> Optional[str]:
        """
        Extract content from canvas-rendered pages using Gemini Vision
        
        Args:
            page: Playwright page object
            
        Returns:
            Extracted text from the screenshot, or None if failed
        """
        try:
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not gemini_api_key:
                logger.warning("GEMINI_API_KEY not set, cannot extract canvas content")
                return None
            
            # Take a screenshot
            screenshot_bytes = await page.screenshot(full_page=True, type="png")
            
            # Encode as base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Call Gemini Vision API
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_api_key}"
            
            payload = {
                "contents": [{
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": screenshot_base64
                            }
                        },
                        {
                            "text": "Extract all text from this image. Return the exact text as it appears, maintaining formatting and structure. If there are instructions, puzzles, or questions, extract them word-for-word."
                        }
                    ]
                }]
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload)
                
                if response.status_code != 200:
                    logger.error(f"Gemini Vision API error {response.status_code}: {response.text}")
                    return None
                
                result = response.json()
                
                # Extract text from response
                if "candidates" in result and result["candidates"]:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        parts = candidate["content"]["parts"]
                        if parts and "text" in parts[0]:
                            return parts[0]["text"].strip()
                
                logger.error(f"Unexpected Gemini Vision response format: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting canvas content: {e}")
            return None
    
    async def close(self):
        """Clean up browser resources"""
        async with self.lock:
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

