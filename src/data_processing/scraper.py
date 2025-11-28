"""
Web scraping handler
"""
import logging
import httpx
from src.quiz_solver.renderer import PageRenderer

logger = logging.getLogger(__name__)

class WebScraper:
    """
    Handles web scraping tasks
    """
    
    def __init__(self):
        self.renderer = PageRenderer()
    
    async def scrape(self, url: str) -> str:
        """
        Scrape content from a URL
        
        Args:
            url: URL to scrape
            
        Returns:
            Scraped content
        """
        try:
            logger.info(f"Scraping {url} with Playwright renderer")
            content = await self.renderer.render(url)
            logger.info(f"Scraped content: {content[:500]}...")  # Log first 500 chars
            return content
        except Exception as e:
            logger.error(f"Scraping via Playwright failed for {url}: {e}")
            # Fallback: direct HTTP fetch (useful for simple HTML/JSON endpoints)
            try:
                logger.info(f"Falling back to direct HTTP fetch for {url}")
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    text = resp.text
                    logger.info(f"HTTP fallback content length: {len(text)}")
                    return text
            except Exception as e2:
                logger.error(f"HTTP fallback scraping failed for {url}: {e2}")
                raise
        finally:
            await self.renderer.close()
