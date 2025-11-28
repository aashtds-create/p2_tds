"""
API client handler
"""
import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class APIClient:
    """
    Handles API data fetching tasks
    """
    
    async def fetch(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Fetch data from an API
        
        Args:
            url: API endpoint URL
            headers: Optional headers
            
        Returns:
            JSON response data or text wrapped in dict
        """
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Fetching API data from {url}")
                response = await client.get(url, headers=headers or {}, timeout=30.0)
                response.raise_for_status()
                
                try:
                    return response.json()
                except:
                    return {"text": response.text}
            except Exception as e:
                logger.error(f"API fetch failed for {url}: {e}")
                raise
