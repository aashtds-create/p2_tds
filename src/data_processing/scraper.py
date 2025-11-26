"""
Web scraping handler
"""
import logging
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
            logger.info(f"Scraping {url}")
            content = await self.renderer.render(url)
            logger.info(f"Scraped content: {content[:500]}...")  # Log first 500 chars
            return content
        except Exception as e:
            logger.error(f"Scraping failed for {url}: {e}")
            raise
        finally:
            await self.renderer.close()
