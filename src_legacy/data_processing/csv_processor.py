"""
CSV processing handler
"""
import httpx
import logging
import pandas as pd
import io
from typing import Any, Dict

logger = logging.getLogger(__name__)

class CSVProcessor:
    """
    Handles CSV file download and processing
    """
    
    async def process(self, url: str) -> Dict[str, Any]:
        """
        Download and parse CSV file
        
        Args:
            url: CSV file URL
            
        Returns:
            Parsed CSV data as dict with dataframe and summary
        """
        try:
            logger.info(f"Downloading CSV from {url}")
            
            # Download CSV
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                csv_content = response.text
            
            # Try to detect if CSV has a header or not
            # If the first value looks like a number, it probably doesn't have a header
            first_line = csv_content.split('\n')[0]
            try:
                # Try parsing first line as number
                float(first_line.split(',')[0].strip())
                has_header = False
                logger.info("CSV appears to have no header row")
            except (ValueError, IndexError):
                has_header = True
                logger.info("CSV appears to have a header row")
            
            # Parse CSV
            if has_header:
                df = pd.read_csv(io.StringIO(csv_content))
            else:
                df = pd.read_csv(io.StringIO(csv_content), header=None)
            
            logger.info(f"CSV loaded: {len(df)} rows, {len(df.columns)} columns")
            logger.info(f"Columns: {list(df.columns)}")
            logger.info(f"First few rows:\n{df.head()}")
            
            return {
                "dataframe": df,
                "rows": len(df),
                "columns": list(df.columns),
                "head": df.head().to_dict(),
                "summary": df.describe().to_dict() if len(df) > 0 else {}
            }
            
        except Exception as e:
            logger.error(f"CSV processing failed for {url}: {e}")
            raise

