"""
QuizAgent Core
The main brain that orchestrates rendering, planning, and execution.
"""
import logging
import asyncio
import json
import re
from datetime import datetime
from typing import Any, Dict, Optional

from src.llm.client import LLMClient
from src.agent.renderer import PageRenderer
from src.agent.sandbox import CodeSandbox

logger = logging.getLogger(__name__)

class QuizAgent:
    """
    Agentic solver for quiz tasks.
    Uses LLM to plan and write code, and Sandbox to execute it.
    """
    
    def __init__(self, secret: str, email: str, deadline: datetime):
        self.secret = secret
        self.email = email
        self.deadline = deadline
        
        self.llm = LLMClient()
        self.renderer = PageRenderer()
        self.sandbox = CodeSandbox()
        
        # Memory
        self.history = []
        self.current_url = None
        
    async def solve(self, start_url: str):
        """
        Main loop: Solve quizzes until done or deadline.
        """
        self.current_url = start_url
        
        while self.current_url:
            if datetime.now() >= self.deadline:
                logger.error("Deadline exceeded")
                break
                
            logger.info(f"Solving quiz at: {self.current_url}")
            
            try:
                # 1. Observe (Render Page)
                page_content = await self.renderer.render(self.current_url)
                
                # 2. Plan & Execute (LLM + Sandbox)
                answer = await self._solve_single_task(page_content)
                
                # 3. Submit
                # Note: The LLM code usually submits, but we need to handle the result.
                # Actually, the project statement says we POST to a submit URL.
                # The LLM generated code should probably return the answer, and WE submit it?
                # OR the LLM generated code does the submission itself?
                # Let's let the LLM generate code that returns the FINAL ANSWER value.
                # Then WE submit it using the submit URL found on the page.
                
                # Wait, the submit URL is dynamic.
                # Let's ask the LLM to extract the submit URL and the answer payload.
                
                submit_info = await self._extract_submission_info(page_content, answer)
                
                if submit_info:
                    next_url = await self._submit_answer(submit_info)
                    if next_url:
                        self.current_url = next_url
                    else:
                        logger.info("No next URL. Quiz complete?")
                        break
                else:
                    logger.error("Failed to extract submission info")
                    break
                    
            except Exception as e:
                logger.error(f"Error in solve loop: {e}")
                break
                
        await self.renderer.close()

    async def _solve_single_task(self, page_content: str) -> Any:
        """
        Solve the task on the current page.
        Returns the answer value.
        """
        max_retries = 3
        
        # Pass current_url to context
        context_data = {
            "page_content": page_content,
            "current_url": self.current_url
        }

        for attempt in range(max_retries):
            # Generate Plan/Code
            code = await self._generate_solution_code(page_content, attempt_error=None)
            
            if not code:
                logger.error("Failed to generate code")
                return None
                
            # Execute
            result = self.sandbox.execute(code, context_data=context_data)
            
            output = result.get("output", "").strip()
            error = result.get("error")
            
            if error:
                logger.warning(f"Execution error: {error}. Retrying...")
                # Could feed error back to LLM to fix code, but for now simple retry
                continue
                
            # Heuristic: The answer is usually the last line of output
            lines = output.split('\n')
            if lines:
                answer = lines[-1].strip()
                logger.info(f"Proposed answer: {answer}")
                return answer
                
        return None

    async def _generate_solution_code(self, page_content: str, attempt_error: str = None) -> str:
        """
        Ask LLM to write Python code to solve the problem.
        """
        system_prompt = """
        You are an expert Python programmer and quiz solver.
        Your goal is to solve the puzzle described in the page content.
        
        Write Python code to:
        1. Parse the page content (provided as variable `page_content`).
        2. Extract necessary data (URLs, numbers, text).
        3. Perform any required actions (download files, calculate, scrape).
        4. PRINT the final answer value on the last line.
        
        Available libraries: requests, pandas, numpy, matplotlib.pyplot, BeautifulSoup, pypdf, json, re, math, urllib.
        
        CRITICAL:
        - The variable `page_content` is already available in your scope. DO NOT redefine it.
        - The variable `current_url` is available in your scope. Use it to resolve relative URLs: `url = urllib.parse.urljoin(current_url, relative_path)`.
        - If you need to download a file, finding the URL in `page_content` is your first step.
        - Use `requests` to fetch data.
        - PRINT ONLY THE FINAL ANSWER at the end.
        - Do not print debug info unless necessary (or print to stderr).
        """
        
        user_prompt = f"Page Content:\n{page_content[:10000]}\n\nSolve this puzzle."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.llm.chat_completion(messages)
        
        if response:
            # Extract code block
            code = response.replace("```python", "").replace("```", "").strip()
            return code
        return None

    async def _extract_submission_info(self, page_content: str, answer: Any) -> Optional[Dict]:
        """
        Ask LLM to parse the submission URL and payload format from the page.
        """
        system_prompt = """
        Extract the submission details from the page content.
        Return a JSON object with:
        - submit_url: The full URL to POST to.
        - payload: The JSON payload structure (keys and values).
        
        Use the provided 'answer' value to fill in the answer field.
        The 'email' should be: {self.email}
        The 'secret' should be: {self.secret}
        The 'url' (if requested) should be: {self.current_url}
        """
        
        user_prompt = f"Page Content:\n{page_content[:5000]}\n\nAnswer Value: {answer}\n\nExtract submission JSON."
        
        messages = [
            {"role": "system", "content": system_prompt.format(self=self)},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.llm.chat_completion(messages, json_mode=True)
        
        if response:
            try:
                # Clean markdown
                if response.startswith("```json"):
                    response = response.replace("```json", "").replace("```", "")
                return json.loads(response)
            except json.JSONDecodeError:
                pass
        return None

    async def _submit_answer(self, submit_info: Dict) -> Optional[str]:
        """
        Submit the answer and return the next URL if any.
        """
        url = submit_info.get("submit_url")
        payload = submit_info.get("payload")
        
        if not url or not payload:
            return None
            
        logger.info(f"Submitting to {url}...")
        
        try:
            # Let's use sandbox to keep it simple.
            
            # Resolve URL if relative
            from urllib.parse import urljoin
            full_url = urljoin(self.current_url, url)
            
            code = f"""
import requests
import json

url = "{full_url}"
payload = {json.dumps(payload)}

try:
    resp = requests.post(url, json=payload, timeout=10)
    print(json.dumps(resp.json()))
except Exception as e:
    print(f"Error: {{e}}")
            """
            
            result = self.sandbox.execute(code)
            output = result.get("output", "").strip()
            
            try:
                response_data = json.loads(output)
                logger.info(f"Submission response: {response_data}")
                
                if response_data.get("correct"):
                    logger.info("✅ Answer correct!")
                    return response_data.get("url") # Next URL
                else:
                    logger.warning(f"❌ Answer incorrect: {response_data.get('reason')}")
                    # Retry logic could go here
                    return None
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid submission response: {output}")
                return None
                
        except Exception as e:
            logger.error(f"Submission failed: {e}")
            return None
