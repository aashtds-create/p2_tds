import os
import logging
import asyncio
from typing import Optional, Dict, Any
import httpx
import json

logger = logging.getLogger(__name__)

# Rate limit handling
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 5  # seconds

class LLMClient:
    """
    Client for interacting with LLM APIs (OpenAI compatible)
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = model
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set. LLM features will be disabled.")

    async def chat_completion(self, messages: list, temperature: float = 0.1, json_mode: bool = False) -> Optional[str]:
        """
        Send a chat completion request (OpenAI or Gemini)
        """
        # Check for Gemini Key first
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            return await self._call_gemini(messages, gemini_key, temperature, json_mode)
            
        if not self.api_key:
            logger.error("Cannot call LLM: API key missing (OPENAI_API_KEY or GEMINI_API_KEY)")
            return None
            
        # OpenAI Implementation
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
            
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"LLM request failed: {e}")
                return None

    async def _call_gemini(self, messages: list, api_key: str, temperature: float, json_mode: bool) -> Optional[str]:
        """
        Call Gemini API via REST with automatic retry on rate limit
        """
        # Convert OpenAI messages to Gemini format
        contents = []
        system_instruction = None
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})
                
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature
            }
        }
        
        if system_instruction:
            payload["system_instruction"] = system_instruction
            
        if json_mode:
            payload["generationConfig"]["response_mime_type"] = "application/json"
        
        # Retry logic with exponential backoff
        for attempt in range(MAX_RETRIES):
            async with httpx.AsyncClient(timeout=120.0) as client:
                try:
                    response = await client.post(url, json=payload)
                    
                    # Handle rate limiting (429)
                    if response.status_code == 429:
                        retry_delay = INITIAL_RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Rate limited (429). Retrying in {retry_delay}s... (attempt {attempt + 1}/{MAX_RETRIES})")
                        await asyncio.sleep(retry_delay)
                        continue
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    # Safely extract text from response
                    if "candidates" in result and len(result["candidates"]) > 0:
                        content = result["candidates"][0].get("content", {})
                        parts = content.get("parts", [])
                        if parts and len(parts) > 0:
                            return parts[0].get("text", "")
                        else:
                            logger.warning("Gemini response has no parts (empty response)")
                            return None
                    else:
                        logger.warning("Gemini response has no candidates")
                        return None
                        
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:
                        retry_delay = INITIAL_RETRY_DELAY * (2 ** attempt)
                        logger.warning(f"Rate limited (429). Retrying in {retry_delay}s... (attempt {attempt + 1}/{MAX_RETRIES})")
                        await asyncio.sleep(retry_delay)
                        continue
                    logger.error(f"Gemini request failed: {e}")
                    logger.error(f"Response status: {e.response.status_code}")
                    logger.error(f"Response: {e.response.text}")
                    return None
                    
                except Exception as e:
                    logger.error(f"Gemini request failed: {e}")
                    return None
        
        logger.error(f"Gemini request failed after {MAX_RETRIES} retries")
        return None

    async def parse_instruction(self, content: str) -> Dict[str, Any]:
        """
        Use LLM to parse quiz instructions into structured format
        """
        system_prompt = """
        You are an expert at parsing quiz instructions. 
        Extract the following fields from the text:
        - question: The main question text
        - data_source: URL or file path to the data source (if any)
        - task_type: One of [scraping, api, pdf, analysis, visualization, unknown]
        - submit_url: The URL to submit the answer to
        - expected_format: One of [number, string, boolean, base64, json]
        
        Return JSON only.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
        
        response = await self.chat_completion(messages, json_mode=True)
        
        if response:
            try:
                # Clean up markdown code blocks if present
                if response.startswith("```json"):
                    response = response.replace("```json", "").replace("```", "")
                elif response.startswith("```"):
                    response = response.replace("```", "")
                    
                return json.loads(response)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM JSON response: {response}")
                return {}
        return {}

    async def solve_task(self, question: str, data: Any = None) -> Any:
        """
        Use LLM to solve a generic task given a question and optional data
        """
        system_prompt = """
        You are an expert data analyst and quiz solver.
        Your goal is to answer the user's question accurately based on the provided data.
        
        CRITICAL INSTRUCTIONS:
        - Return ONLY the direct answer value, with NO extra text, explanation, or formatting
        - If the answer is a number, return ONLY the number (e.g., "36274" not "The answer is 36274")
        - If the answer is text, return ONLY the text value
        - If the answer requires JSON format, return ONLY valid JSON
        - Do NOT include phrases like "The answer is", "Based on", etc.
        - Be concise and precise with your answer
        """
        
        user_content = f"Question: {question}\n"
        if data:
            user_content += f"\nData:\n{str(data)[:10000]}..." # Truncate if too large
        
        user_content += "\n\nRemember: Return ONLY the answer value with no extra text."
            
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        return await self.chat_completion(messages)
