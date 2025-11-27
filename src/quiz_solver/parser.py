"""
Parse quiz instructions from rendered content
"""
import re
import logging
from dataclasses import dataclass
from typing import Optional, List
from src.llm.client import LLMClient

logger = logging.getLogger(__name__)

@dataclass
class QuizInstructions:
    """Structured representation of quiz instructions"""
    question: str
    data_source: Optional[str] = None  # URL, API endpoint, or file path
    task_type: str = "unknown"  # scraping, api, pdf, analysis, visualization
    submit_url: str = ""
    expected_format: str = "number"  # number, string, boolean, base64, json


class InstructionParser:
    """
    Parses natural language quiz instructions
    """
    
    def __init__(self):
        self.llm_client = LLMClient()
    
    async def parse(self, content: str) -> QuizInstructions:
        """
        Parse quiz content and extract structured instructions
        
        Args:
            content: Raw text from rendered quiz page
            
        Returns:
            QuizInstructions object
        """
        # Try regex-based extraction first (faster, cheaper)
        submit_url = self._extract_submit_url(content)
        data_source = self._extract_data_source(content)
        task_type = self._identify_task_type(content)
        expected_format = self._extract_answer_format(content)
        
        # If critical info is missing or ambiguous, use LLM
        if not submit_url or not data_source or task_type == "unknown":
            logger.info("Regex parsing incomplete, falling back to LLM")
            llm_result = await self.llm_client.parse_instruction(content)
            
            if llm_result:
                return QuizInstructions(
                    question=llm_result.get("question", content),
                    data_source=llm_result.get("data_source") or data_source,
                    task_type=llm_result.get("task_type") or task_type,
                    submit_url=llm_result.get("submit_url") or submit_url,
                    expected_format=llm_result.get("expected_format") or expected_format
                )
        
        return QuizInstructions(
            question=content,
            data_source=data_source,
            task_type=task_type,
            submit_url=submit_url,
            expected_format=expected_format
        )
    
    def _extract_submit_url(self, content: str) -> str:
        """Extract submission URL from content"""
        # Look for patterns like "Post to https://..."
        url_pattern = r'https?://[^\s<>"\'\)]+'
        urls = re.findall(url_pattern, content)
        
        # Prioritize URLs containing 'submit'
        for url in urls:
            if 'submit' in url.lower():
                return url
        
        # Default to standard submit endpoint
        # Most quizzes submit to /submit regardless of what the question says
        return "https://tds-llm-analysis.s-anand.net/submit"
    
    def _extract_data_source(self, content: str) -> Optional[str]:
        """Extract data source URL or file path"""
        # Check for audio files first
        audio_match = re.search(r'Audio:\s*(https?://[^\s,\)]+)', content, re.IGNORECASE)
        if audio_match:
            return audio_match.group(1)
        
        url_pattern = r'https?://[^\s<>"\'\)]+'
        urls = re.findall(url_pattern, content)
        
        # Filter out submit URLs
        for url in urls:
            if 'submit' not in url.lower():
                return url
        
        return None
    
    def _identify_task_type(self, content: str) -> str:
        """Identify the type of task"""
        content_lower = content.lower()
        
        # Check for media files first
        if '[media files found]' in content_lower and 'audio:' in content_lower:
            return "audio"
        elif 'audio' in content_lower or 'transcribe' in content_lower or 'listen' in content_lower:
            return "audio"
        elif 'download' in content_lower or 'pdf' in content_lower:
            return "pdf"
        elif 'api' in content_lower or 'endpoint' in content_lower:
            return "api"
        elif 'scrape' in content_lower or 'website' in content_lower:
            return "scraping"
        elif 'visualize' in content_lower or 'chart' in content_lower:
            return "visualization"
        elif 'sum' in content_lower or 'count' in content_lower or 'filter' in content_lower:
            return "analysis"
        else:
            return "unknown"
    
    def _extract_answer_format(self, content: str) -> str:
        """Determine expected answer format"""
        content_lower = content.lower()
        
        if 'json' in content_lower:
            return "json"
        elif 'image' in content_lower or 'base64' in content_lower:
            return "base64"
        elif 'true' in content_lower or 'false' in content_lower:
            return "boolean"
        elif 'string' in content_lower or 'text' in content_lower:
            return "string"
        else:
            return "number"  # Default

