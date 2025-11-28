"""
Task execution - routes to appropriate handlers
"""
from datetime import datetime
from typing import Any
from urllib.parse import urljoin
import re
import logging

from src.quiz_solver.parser import QuizInstructions
from src.data_processing.scraper import WebScraper
from src.data_processing.pdf_processor import PDFProcessor
from src.data_processing.api_client import APIClient
from src.data_processing.analyzer import DataAnalyzer
from src.data_processing.audio_processor import AudioProcessor
from src.data_processing.csv_processor import CSVProcessor
from src.data_processing.computation_solver import ComputationSolver
from src.data_processing.game_solver import GameSolver
from src.data_processing.visualization_generator import VisualizationGenerator
from src.data_processing.code_executor import CodeExecutor
from src.llm.client import LLMClient

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
        self.computation_solver = ComputationSolver()
        self.llm_client = LLMClient()
        self.game_solver = GameSolver(self.llm_client)
        self.visualization_generator = VisualizationGenerator()
        self.visualization_generator.llm_client = self.llm_client  # Inject LLM client
        self.code_executor = CodeExecutor(self.llm_client)  # NEW: Dynamic code execution
        self.current_page_content = None  # Store page content for multi-step tasks
        self.email = None  # Store email for personalized puzzles
        self.previous_answer = None  # Store previous answer for chained puzzles
    
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
        elif instructions.task_type == "game":
            return await self._handle_game_task(instructions, base_url)
        elif instructions.task_type == "statistical":
            return await self._handle_statistical_task(instructions, base_url)
        elif instructions.task_type == "geospatial":
            return await self._handle_geospatial_task(instructions, base_url)
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
        
        # Check if this is a pagination task
        question_lower = instructions.question.lower()
        is_pagination = any(kw in question_lower for kw in ['pagination', 'multiple pages', 'all pages', 'traverse', 'page='])
        
        if is_pagination and '?page=' in api_url:
            logger.info("Detected pagination task - fetching all pages")
            # Fetch all pages
            all_items = []
            page = 1
            max_pages = 100  # Safety limit
            
            while page <= max_pages:
                # Update page number in URL
                current_url = re.sub(r'page=\d+', f'page={page}', api_url)
                logger.info(f"Fetching page {page}: {current_url}")
                
                try:
                    page_data = await self.api_client.fetch(current_url)
                    
                    # Check if data is a list
                    if isinstance(page_data, list):
                        if not page_data:  # Empty list means we're done
                            logger.info(f"Reached end of pagination at page {page}")
                            break
                        all_items.extend(page_data)
                    elif isinstance(page_data, dict) and 'items' in page_data:
                        items = page_data['items']
                        if not items:
                            break
                        all_items.extend(items)
                    else:
                        logger.warning(f"Unexpected data format on page {page}: {type(page_data)}")
                        break
                    
                    page += 1
                except Exception as e:
                    logger.error(f"Error fetching page {page}: {e}")
                    break
            
            logger.info(f"Fetched total of {len(all_items)} items across {page-1} pages")
            
            # Now find the specific item requested
            # Look for ID in question
            import re
            id_match = re.search(r'ID\s*(\d+)', instructions.question, re.IGNORECASE)
            if id_match:
                target_id = int(id_match.group(1))
                logger.info(f"Looking for item with ID {target_id}")
                
                for item in all_items:
                    if isinstance(item, dict) and item.get('id') == target_id:
                        # Return the name field
                        answer = item.get('name', item.get('title', str(item)))
                        logger.info(f"Found item with ID {target_id}: {answer}")
                        return answer
                
                logger.warning(f"Item with ID {target_id} not found in {len(all_items)} items")
            
            # If we can't find it directly, use LLM with all data
            api_data = all_items
        else:
            # Single API fetch (no pagination)
            api_data = await self.api_client.fetch(api_url)
        
        # Process and answer with LLM
        answer = await self.llm_client.solve_task(
            question=instructions.question,
            data=api_data
        )
        
        return answer
    
    async def _handle_scraping_task(self, instructions: QuizInstructions, base_url: str = None) -> Any:
        """Handle web scraping tasks"""
        # If no data_source, use current page content (data is on the current page)
        if not instructions.data_source:
            logger.info("No separate data source - using current page content for scraping task")
            if not self.current_page_content:
                raise ValueError("No data source and no current page content available")
            
            # Enhanced prompt for scraping tasks to help LLM understand what to extract
            enhanced_question = f"""
{instructions.question}

Page Content:
{self.current_page_content}

INSTRUCTIONS:
- Carefully read the page content above
- Look for hidden elements, reversed text, or special patterns
- If text needs to be un-reversed/reversed, do so
- Extract the exact answer requested
- Return ONLY the final answer value (no explanations)

Answer:"""
            
            # Use current page content with enhanced prompt
            answer = await self.llm_client.solve_task(
                question=enhanced_question,
                data=None  # Already included in question
            )
            return answer
        
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
        # Check if this is an alphametic/computational puzzle
        # Use current_page_content (raw) instead of parsed question
        content_to_check = self.current_page_content if self.current_page_content else instructions.question
        
        # Check for computational puzzle types
        is_computational = any([
            "ALPHAMETIC" in content_to_check.upper(),
            "SHA1" in content_to_check,
            "SHA256" in content_to_check,
            "checksum" in content_to_check.lower(),
            "hash" in content_to_check.lower() and "compute" in content_to_check.lower()
        ])
        
        if is_computational:
            logger.info("Detected computational puzzle")
            if self.email:
                result = await self.computation_solver.solve_alphametic(
                    content_to_check, 
                    self.email,
                    previous_answer=self.previous_answer
                )
                if result:
                    return result
            else:
                logger.warning("Email not set for computational puzzle")
        
        # Otherwise delegate to LLM
        return await self._handle_llm_task(instructions)
    
    async def _handle_visualization_task(self, instructions: QuizInstructions, base_url: str = None) -> Any:
        """Handle visualization tasks - generate charts, narratives, etc."""
        logger.info("Handling visualization task")
        
        # Get data if specified
        data = None
        if instructions.data_source:
            # Download/load data
            if instructions.data_source.endswith('.csv'):
                data = await self.csv_processor.load_csv(instructions.data_source, base_url)
            # Add other data sources as needed
        
        # Generate visualization
        result = await self.visualization_generator.generate(
            instructions=instructions.question,
            data=data
        )
        
        if result:
            return result
        
        # Fallback to LLM
        return await self._handle_llm_task(instructions)
    
    async def _handle_game_task(self, instructions: QuizInstructions, base_url: str = None) -> Any:
        """Handle game-based puzzles (Tic-Tac-Toe, Wordle, etc.)"""
        logger.info("Handling game task")
        
        # Use full page content for game context
        content = self.current_page_content if self.current_page_content else instructions.question
        
        # Try game solver
        result = await self.game_solver.solve_game(content)
        
        if result:
            return result
        
        # Fallback to LLM
        return await self._handle_llm_task(instructions)
    
    async def _handle_statistical_task(self, instructions: QuizInstructions, base_url: str = None) -> Any:
        """Handle statistical and ML tasks using code generation"""
        logger.info("Handling statistical/ML task")
        
        # Get data if available
        data = None
        if instructions.data_source:
            # Load CSV or other data
            data_url = self._resolve_url(instructions.data_source, base_url)
            if data_url.endswith('.csv'):
                data = await self.csv_processor.load_csv(data_url, base_url)
        
        # Use code executor for statistical tasks
        result = await self.code_executor.solve_statistical_task(
            task=instructions.question,
            data=data
        )
        
        if result:
            return result
        
        # Fallback to LLM
        return await self._handle_llm_task(instructions)
    
    async def _handle_geospatial_task(self, instructions: QuizInstructions, base_url: str = None) -> Any:
        """Handle geo-spatial tasks using code generation"""
        logger.info("Handling geo-spatial task")
        
        # Use code executor for geo-spatial calculations
        result = await self.code_executor.solve_geospatial_task(
            task=instructions.question,
            data=self.current_page_content
        )
        
        if result:
            return result
        
        # Fallback to LLM
        return await self._handle_llm_task(instructions)
    
    async def _handle_llm_task(self, instructions: QuizInstructions) -> Any:
        """Use LLM to solve complex/unknown tasks"""
        # Check if this is a computational puzzle
        # Use current_page_content (raw) instead of parsed question
        content_to_check = self.current_page_content if self.current_page_content else instructions.question
        
        is_computational = any([
            "ALPHAMETIC" in content_to_check.upper(),
            "SHA1" in content_to_check,
            "SHA256" in content_to_check,
            "MD5" in content_to_check,
            "checksum" in content_to_check.lower(),
            "hash" in content_to_check.lower() and "compute" in content_to_check.lower(),
            "fibonacci" in content_to_check.lower(),
            "prime" in content_to_check.lower()
        ])
        
        if is_computational and self.email:
            logger.info("Detected computational puzzle in LLM task")
            result = await self.computation_solver.solve_alphametic(
                content_to_check,
                self.email,
                previous_answer=self.previous_answer
            )
            if result:
                return result
        
        # Enhanced LLM solve with more context
        return await self._solve_with_enhanced_llm(instructions, content_to_check)
    
    async def _solve_with_enhanced_llm(self, instructions: QuizInstructions, full_content: str) -> Any:
        """
        Enhanced LLM solving with better prompting and context
        Includes code generation fallback for truly novel tasks
        """
        # Build comprehensive context
        context_parts = []
        
        # Add full page content
        if full_content:
            context_parts.append(f"Page Content:\n{full_content}")
        
        # Add previous answer if available (for chained puzzles)
        if self.previous_answer:
            context_parts.append(f"\nPrevious Answer: {self.previous_answer}")
        
        # Add any parsed data source
        if instructions.data_source:
            context_parts.append(f"\nData Source: {instructions.data_source}")
        
        context = "\n\n".join(context_parts)
        
        # Enhanced prompt for unknown tasks
        enhanced_question = f"""
Task: {instructions.question}

{context}

CRITICAL INSTRUCTIONS:
- Analyze the task carefully
- If it requires computation (math, hashing, formulas), show your work
- If it requires data extraction, identify the source and method
- Return ONLY the final answer value (no explanations, no "The answer is...")
- If the answer is a number, return just the number
- If the answer is text, return just the text
- If previous answer is provided, use it if relevant

Answer:"""
        
        logger.info(f"Enhanced LLM prompt length: {len(enhanced_question)} chars")
        
        # Try direct LLM reasoning first
        llm_result = await self.llm_client.solve_task(
            question=enhanced_question,
            data=None
        )
        
        # If LLM returns something, use it
        if llm_result and str(llm_result).strip():
            return llm_result
        
        # If LLM fails or returns empty, try code generation as fallback
        logger.warning("Direct LLM approach failed, trying code generation...")
        code_result = await self.code_executor.solve_with_code(
            task_description=f"{instructions.question}\n\n{context}",
            data=full_content
        )
        
        if code_result:
            logger.info("Code generation successful!")
            return code_result
        
        # If both fail, return the LLM result anyway (might be empty but better than nothing)
        return llm_result

