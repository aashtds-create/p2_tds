"""
Data analysis handler
"""
import logging
import pandas as pd
from typing import Any, Dict, Optional
from src.data_processing.code_executor import CodeExecutor

logger = logging.getLogger(__name__)

class DataAnalyzer:
    """
    Handles data analysis tasks using LLM-generated code
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.executor = CodeExecutor()
    
    async def analyze(self, data: Any, query: str) -> Any:
        """
        Analyze data based on a query using Code Execution
        
        Args:
            data: Data to analyze (DataFrame, list, dict)
            query: Analysis query
            
        Returns:
            Analysis result (text or image)
        """
        if not self.llm_client:
            logger.warning("LLM client not provided to DataAnalyzer")
            return "Analysis failed: LLM client missing"

        # 1. Generate Code
        system_prompt = """
        You are a Python data analysis expert.
        Generate Python code to analyze the provided data 'df' based on the user's query.
        
        Rules:
        - The data is available as a pandas DataFrame named 'df'.
        - If the user asks for a plot/chart, use matplotlib.pyplot as 'plt'.
        - PRINT the final answer using `print()`.
        - Do NOT show the dataframe unless asked.
        - Return ONLY the Python code, no markdown formatting.
        """
        
        # Prepare data sample
        data_sample = str(data)[:2000]
        if isinstance(data, pd.DataFrame):
            data_sample = data.head().to_markdown()
            
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Query: {query}\nData Sample:\n{data_sample}"}
        ]
        
        code = await self.llm_client.chat_completion(messages)
        
        if not code:
            return "Failed to generate analysis code"
            
        # Clean code
        code = code.replace("```python", "").replace("```", "").strip()
        
        # 2. Execute Code
        result = self.executor.execute(code, data)
        
        # 3. Return result
        if result.get("image"):
            return result["image"] # Return base64 image if plot generated
        return result.get("output", "").strip()

