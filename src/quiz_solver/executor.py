"""
Task execution - routes to appropriate handlers
"""
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

from src.quiz_solver.parser import QuizInstructions
from src.data_processing.scraper import WebScraper
from src.data_processing.pdf_processor import PDFProcessor
from src.data_processing.api_client import APIClient
from src.data_processing.analyzer import DataAnalyzer
from src.data_processing.audio_processor import AudioProcessor
from src.data_processing.csv_processor import CSVProcessor
from src.llm.client import LLMClient
import logging

logger = logging.getLogger(__name__)


class TaskExecutor:
    """
    Executes quiz tasks based on instructions
    """
    
    def __init__(self, deadline: datetime):
        self.deadline = deadline
        self.scraper = WebScraper()
        self.pdf_processor = PDFProcessor()
        self.api_client = APIClient()
        self.analyzer = DataAnalyzer()
        self.audio_processor = AudioProcessor()
        self.csv_processor = CSVProcessor()
        self.llm_client = LLMClient()
        self.current_page_content = None  # Store page content for multi-step tasks
    
    async def execute(self, instructions: QuizInstructions, base_url: str = None) -> Any:
        """
        Execute the quiz task
        
        Args:
            instructions: Parsed quiz instructions
            base_url: Base URL for resolving relative URLs
            
        Returns:
            Answer in the required format
        """
        # Check if we have time
        if datetime.now() >= self.deadline:
            raise TimeoutError("Deadline exceeded")
        
        # Route to appropriate handler
        if instructions.task_type == "pdf":
            return await self._handle_pdf_task(instructions, base_url)
        elif instructions.task_type == "api":
            return await self._handle_api_task(instructions, base_url)
        elif instructions.task_type == "scraping":
            return await self._handle_scraping_task(instructions, base_url)
        elif instructions.task_type == "audio":
            return await self._handle_audio_task(instructions, base_url)
        elif instructions.task_type == "visualization":
            return await self._handle_visualization_task(instructions, base_url)
        elif instructions.task_type == "analysis":
            return await self._handle_analysis_task(instructions, base_url)
        else:
            # Use LLM to handle unknown/complex tasks
            return await self._handle_llm_task(instructions)
    
    def _resolve_url(self, url: str, base_url: str = None) -> str:
        """Resolve relative URLs to absolute URLs"""
        if not url:
            return url
        if base_url and not url.startswith(('http://', 'https://')):
            return urljoin(base_url, url)
        return url
    
    async def _handle_pdf_task(self, instructions: QuizInstructions, base_url: str = None) -> Any:
        """Handle PDF-based tasks"""
        if not instructions.data_source:
            raise ValueError("No data source provided")
        
        # Resolve relative URLs
        pdf_url = self._resolve_url(instructions.data_source, base_url)
        
        # Download and process PDF
        pdf_data = await self.pdf_processor.process(pdf_url)
        
        # Use LLM or analyzer to answer question
        answer = await self.llm_client.solve_task(
            question=instructions.question,
            data=pdf_data
        )
        
        return answer
    
    async def _handle_api_task(self, instructions: QuizInstructions, base_url: str = None) -> Any:
        """Handle API-based tasks"""
        if not instructions.data_source:
            raise ValueError("No data source provided")
        
        # Resolve relative URLs
        api_url = self._resolve_url(instructions.data_source, base_url)
        
        # Fetch data from API
        api_data = await self.api_client.fetch(api_url)
        
        # Process and answer
        answer = await self.llm_client.solve_task(
            question=instructions.question,
            data=api_data
        )
        
        return answer
    
    async def _handle_scraping_task(self, instructions: QuizInstructions, base_url: str = None) -> Any:
        """Handle web scraping tasks"""
        if not instructions.data_source:
            raise ValueError("No data source provided")
        
        # Resolve relative URLs
        scrape_url = self._resolve_url(instructions.data_source, base_url)
        
        # Scrape the website
        scraped_data = await self.scraper.scrape(scrape_url)
        
        # Process and answer
        answer = await self.llm_client.solve_task(
            question=instructions.question,
            data=scraped_data
        )
        
        return answer
    
    async def _handle_audio_task(self, instructions: QuizInstructions, base_url: str = None) -> Any:
        """Handle audio transcription tasks"""
        if not instructions.data_source:
            raise ValueError("No audio source provided")
        
        # Resolve relative URLs
        audio_url = self._resolve_url(instructions.data_source, base_url)
        
        # Process audio (transcribe)
        audio_data = await self.audio_processor.process(audio_url)
        transcription = audio_data.get("text", "")
        
        logger.info(f"Audio transcription: {transcription}")
        
        # Check if the audio mentions downloading files (CSV, PDF, etc.)
        additional_data = None
        if "csv" in transcription.lower() and self.current_page_content:
            # Extract CSV URL from page content
            import re
            csv_urls = re.findall(r'Data files \(CSV/PDF/etc\): ([^\n]+)', self.current_page_content)
            if csv_urls:
                csv_url_str = csv_urls[0]
                csv_url = csv_url_str.split(',')[0].strip()  # Get first CSV
                csv_url = self._resolve_url(csv_url, base_url)
                logger.info(f"Found CSV URL in audio instructions: {csv_url}")
                try:
                    csv_data = await self.csv_processor.process(csv_url)
                    additional_data = csv_data
                except Exception as e:
                    logger.error(f"Failed to process CSV: {e}")
        
        # If we have CSV data with numerical operations, calculate directly
        if additional_data and "dataframe" in additional_data:
            df = additional_data["dataframe"]
            
            # Parse the cutoff value from page content or transcription
            import re
            cutoff_match = re.search(r'Cutoff:\s*(\d+)', self.current_page_content or "")
            if cutoff_match:
                cutoff = int(cutoff_match.group(1))
                logger.info(f"Found cutoff value: {cutoff}")
                
                # Get first column (by position, not name)
                first_col = df.iloc[:, 0]  # Get first column by position
                logger.info(f"Processing first column: {df.columns[0]}")
                logger.info(f"Column data type: {first_col.dtype}")
                
                # Filter values >= cutoff and sum
                filtered = first_col[first_col >= cutoff]
                result = int(filtered.sum())
                
                logger.info(f"Filtered {len(filtered)} values >= {cutoff}")
                logger.info(f"Sum of filtered values: {result}")
                
                return result
        
        # Otherwise, use LLM (for simpler cases)
        full_data = {
            "instructions": transcription,
            "audio_file": audio_url
        }
        
        # Don't send huge CSV data to LLM, just summary
        if additional_data:
            full_data["data_summary"] = {
                "rows": additional_data.get("rows"),
                "columns": additional_data.get("columns"),
                "sample": additional_data.get("head")
            }
        
        # Use LLM to answer based on transcription
        answer = await self.llm_client.solve_task(
            question=instructions.question or transcription,
            data=full_data
        )
        
        return answer
    
    async def _handle_analysis_task(self, instructions: QuizInstructions, base_url: str = None) -> Any:
        """Handle data analysis tasks"""
        # This would involve fetching data, then analyzing
        # For now, delegate to LLM
        return await self._handle_llm_task(instructions)
    
    async def _handle_visualization_task(self, instructions: QuizInstructions, base_url: str = None) -> Any:
        """Handle visualization tasks"""
        # Generate visualization and return as base64
        # Implementation would create chart and encode
        return await self._handle_llm_task(instructions)
    
    async def _handle_llm_task(self, instructions: QuizInstructions) -> Any:
        """Use LLM to solve complex/unknown tasks"""
        return await self.llm_client.solve_task(
            question=instructions.question,
            data=None
        )

