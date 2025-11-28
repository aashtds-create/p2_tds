"""
Main quiz solver orchestrator
"""
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin
import httpx
import logging
import asyncio

from src.quiz_solver.renderer import PageRenderer
from src.quiz_solver.parser import InstructionParser
from src.quiz_solver.executor import TaskExecutor

logger = logging.getLogger(__name__)

class QuizSolver:
    """
    Main class that orchestrates the quiz solving process
    """
    
    def __init__(self, secret: str, email: str, deadline: datetime):
        self.secret = secret
        self.email = email
        self.deadline = deadline
        self.current_url = None  # Track current quiz URL
        self.renderer = PageRenderer()
        self.parser = InstructionParser()
        self.executor = TaskExecutor(deadline=deadline)
        self.executor.email = email  # Pass email for personalized puzzles
    
    async def solve(self, url: str):
        """
        Solve a quiz at the given URL
        
        Args:
            url: Quiz page URL
        """
        self.current_url = url
        
        try:
            logger.info(f"Solving quiz at {url}")
            
            # Step 1: Render the page
            quiz_content = await self.renderer.render(url)
            
            # Step 2: Parse instructions
            instructions = await self.parser.parse(quiz_content)
            logger.info(f"Parsed question: {instructions.question}")
            logger.info(f"Data source: {instructions.data_source}")
            logger.info(f"Task type: {instructions.task_type}")
            
            # Step 3: Execute the task (pass current URL for resolving relative URLs)
            # Store page content in executor for multi-step tasks
            self.executor.current_page_content = quiz_content
            answer = await self.executor.execute(instructions, base_url=url)
            logger.info(f"Generated answer: {answer}")
            
            # Store answer for chained puzzles
            self.executor.previous_answer = str(answer) if answer is not None else None
            
            # Step 4: Submit the answer (resolve relative submit URL)
            submit_url = instructions.submit_url
            
            # Fix: Always use /submit endpoint unless explicitly told otherwise
            if not submit_url or 'submit' not in submit_url:
                submit_url = "https://tds-llm-analysis.s-anand.net/submit"
                logger.info(f"Using default submit URL: {submit_url}")
            elif submit_url and not submit_url.startswith(('http://', 'https://')):
                submit_url = urljoin(url, submit_url)
            
            await self._submit_answer(submit_url, answer)
            
        except Exception as e:
            logger.error(f"Error solving quiz at {url}: {e}")
            # If we have time, maybe retry or just log
            if datetime.now() < self.deadline:
                logger.info("Time remaining, but error occurred. Check logs.")
    
    async def _submit_answer(self, submit_url: str, answer):
        """
        Submit answer to the quiz endpoint
        """
        import json as json_module
        
        payload = {
            "email": self.email,
            "secret": self.secret,
            "url": self.current_url,  # Need to track current URL
            "answer": answer
        }
        
        # Check payload size (must be under 1MB per project requirements)
        payload_json = json_module.dumps(payload)
        payload_size = len(payload_json.encode('utf-8'))
        
        if payload_size > 1_000_000:  # 1MB limit
            logger.error(f"Payload too large: {payload_size:,} bytes (limit: 1MB)")
            # Try to truncate if answer is a string
            if isinstance(answer, str) and len(answer) > 500000:
                answer = answer[:500000] + "... [truncated]"
                payload["answer"] = answer
                payload_size = len(json_module.dumps(payload).encode('utf-8'))
                logger.info(f"Truncated payload size: {payload_size:,} bytes")
        
        logger.info(f"Submitting answer to {submit_url}")
        logger.info(f"Payload size: {payload_size:,} bytes")
        logger.info(f"Answer preview: {str(answer)[:200]}...")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(submit_url, json=payload, timeout=30.0)
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Submission result: {result}")
                
                # Handle response
                if result.get("correct"):
                    logger.info("✅ Answer correct!")
                    # May have next URL
                    next_url = result.get("url")
                    if next_url:
                        logger.info(f"Proceeding to next URL: {next_url}")
                        await self.solve(next_url)
                    else:
                        logger.info("✅ Quiz chain completed successfully!")
                else:
                    reason = result.get('reason', 'No reason provided')
                    logger.warning(f"❌ Answer incorrect: {reason}")
                    
                    # Per project rules: "you may receive the next url to proceed to"
                    # Even if answer is wrong, we can move to next question
                    next_url = result.get("url")
                    if next_url:
                        logger.info(f"Moving to next URL (quiz continues despite wrong answer): {next_url}")
                        await self.solve(next_url)
                    else:
                        logger.warning("No next URL provided after wrong answer")
                        # Could retry if time permits, but for now we stop
            except Exception as e:
                logger.error(f"Submission failed: {e}")

