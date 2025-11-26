"""
PDF processing handler
"""
import httpx
import logging
import io
import pdfplumber
from typing import Any, Dict

logger = logging.getLogger(__name__)

class PDFProcessor:
    """
    Handles PDF processing tasks
    """
    
    async def process(self, url: str) -> Dict[str, Any]:
        """
        Download and extract text from a PDF
        
        Args:
            url: PDF URL
            
        Returns:
            Extracted text content and tables
        """
        try:
            logger.info(f"Downloading PDF from {url}")
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                pdf_bytes = response.content
            
            logger.info("Extracting text from PDF")
            text_content = []
            tables = []
            
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        text_content.append(f"--- Page {i+1} ---\n{text}")
                    
                    page_tables = page.extract_tables()
                    for table in page_tables:
                        tables.append({
                            "page": i+1,
                            "table": table
                        })
            
            return {
                "text": "\n".join(text_content),
                "tables": tables
            }
        except Exception as e:
            logger.error(f"PDF processing failed for {url}: {e}")
            raise
