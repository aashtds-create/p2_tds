"""
Dynamic code executor for novel tasks
Generates and safely executes Python code based on LLM instructions
"""
import logging
import subprocess
import tempfile
import os
import sys
from typing import Any, Dict, Optional, Tuple
import asyncio

logger = logging.getLogger(__name__)

class CodeExecutor:
    """
    Dynamically generates and executes Python code for novel tasks
    Similar to agent-based approach but within our hybrid architecture
    """
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.timeout = 30  # seconds for code execution
        self.max_generation_retries = 3
    
    async def solve_with_code(self, task_description: str, data: Any = None) -> Optional[str]:
        """
        Generate Python code to solve the task and execute it
        
        Args:
            task_description: Description of what needs to be done
            data: Any data needed for the task
            
        Returns:
            Result from code execution
        """
        try:
            logger.info(f"Attempting dynamic code generation for task: {task_description[:120]}...")
            logger.info(f"CodeExecutor data summary: {self._summarize_data(data)}")
            
            # Step 1: Generate code (with retries)
            code = None
            for attempt in range(1, self.max_generation_retries + 1):
                code = await self._generate_code(task_description, data)
                if code:
                    break
                logger.warning(f"Code generation attempt {attempt} failed, retrying...")
                await asyncio.sleep(1 * attempt)
            
            if not code:
                logger.error("Failed to generate code after multiple attempts")
                return None
            
            logger.info(f"Generated code ({len(code)} chars)")
            logger.debug(f"Code:\n{code}")
            
            # Step 2: Execute code
            result = await self._execute_code(code)
            
            if result:
                logger.info(f"Code execution successful: {result[:200]}")
                return result
            else:
                logger.error("Code execution failed")
                return None
                
        except Exception as e:
            logger.error(f"Error in solve_with_code: {e}", exc_info=True)
            return None
    
    async def _generate_code(self, task_description: str, data: Any) -> Optional[str]:
        """
        Use LLM to generate Python code for the task
        """
        # Prepare data context
        data_context = ""
        if data:
            if isinstance(data, str):
                data_context = f"Data available as string:\n{data[:500]}"
            elif isinstance(data, dict):
                data_context = f"Data available as dict: {list(data.keys())}"
            elif isinstance(data, list):
                data_context = f"Data available as list with {len(data)} items"
            else:
                data_context = f"Data type: {type(data).__name__}"
        
        prompt = f"""
Generate Python code to solve this task:

Task: {task_description}

{data_context}

CRITICAL REQUIREMENTS:
1. Write COMPLETE, WORKING Python code
2. Include ALL necessary imports
3. Handle errors gracefully
4. Print ONLY the final answer using print()
5. Do not use input() or interactive features
6. Code must be executable standalone
7. If task requires packages, import them (pandas, numpy, etc.)
8. Keep code under 50 lines if possible

Example output format:
```python
import pandas as pd
import numpy as np

# Your code here
result = ...
print(result)
```

Generate the code now (inside ```python code blocks):
"""
        
        response = await self.llm_client.chat_completion([
            {"role": "system", "content": "You are an expert Python programmer. Generate clean, working code."},
            {"role": "user", "content": prompt}
        ])
        
        if not response:
            logger.warning("LLM returned empty response while generating code")
            return None
        
        # Extract code from response
        code = self._extract_code_from_response(response)
        if not code:
            logger.warning("LLM response did not contain executable code")
        return code
    
    def _extract_code_from_response(self, response: str) -> Optional[str]:
        """
        Extract Python code from LLM response
        Handles ```python code blocks or raw code
        """
        import re
        
        # Try to find ```python code blocks
        pattern = r'```python\s*(.*?)\s*```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        if matches:
            # Return the first code block
            return matches[0].strip()
        
        # Try just ``` blocks
        pattern = r'```\s*(.*?)\s*```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # If no code blocks, assume entire response is code
        # (but be careful - filter out explanatory text)
        lines = response.split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            # Start of code (likely has import or def)
            if line.strip().startswith(('import ', 'from ', 'def ', 'class ')):
                in_code = True
            
            if in_code:
                code_lines.append(line)
        
        if code_lines:
            return '\n'.join(code_lines)
        
        # Last resort: return response as-is
        return response.strip()
    
    def _summarize_data(self, data: Any) -> str:
        """Summarize data structure for logging purposes"""
        if data is None:
            return "No data provided"
        if isinstance(data, str):
            return f"String (len={len(data)})"
        if isinstance(data, list):
            return f"List (len={len(data)}) - first item type: {type(data[0]).__name__ if data else 'N/A'}"
        if isinstance(data, dict):
            keys = list(data.keys())
            return f"Dict keys: {keys[:5]}{'...' if len(keys) > 5 else ''}"
        return f"Data type: {type(data).__name__}"
    
    async def _execute_code(self, code: str) -> Optional[str]:
        """
        Execute Python code safely in subprocess
        """
        try:
            # Create temporary file for code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute in subprocess with timeout
                process = await asyncio.create_subprocess_exec(
                    sys.executable, temp_file,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                # Wait with timeout
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=self.timeout
                    )
                    
                    # Check exit code
                    if process.returncode == 0:
                        # Success! Return stdout
                        result = stdout.decode('utf-8').strip()
                        return result
                    else:
                        # Error
                        error = stderr.decode('utf-8')
                        logger.error(f"Code execution error: {error}")
                        return None
                        
                except asyncio.TimeoutError:
                    logger.error(f"Code execution timeout ({self.timeout}s)")
                    process.kill()
                    return None
                    
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error executing code: {e}", exc_info=True)
            return None
    
    async def solve_statistical_task(self, task: str, data: Any) -> Optional[str]:
        """
        Specialized handler for statistical/ML tasks
        """
        prompt = f"""
Task: {task}

Generate Python code using pandas, numpy, scipy, or sklearn to solve this.

Requirements:
- Import necessary libraries
- Load/process data if needed
- Perform statistical analysis or ML
- Print ONLY the final answer

Example for "calculate mean":
```python
import pandas as pd
import numpy as np
data = [1, 2, 3, 4, 5]
mean = np.mean(data)
print(mean)
```

Generate code for the given task:
"""
        
        return await self.solve_with_code(prompt, data)
    
    async def solve_geospatial_task(self, task: str, data: Any) -> Optional[str]:
        """
        Specialized handler for geo-spatial tasks
        """
        prompt = f"""
Task: {task}

Generate Python code for geo-spatial analysis.

You can use:
- geopy for distance calculations
- Basic coordinate math
- Standard libraries

Example for "distance between two coordinates":
```python
from math import radians, sin, cos, sqrt, atan2

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    return distance

# Example usage
dist = haversine(40.7128, -74.0060, 34.0522, -118.2437)  # NY to LA
print(dist)
```

Generate code for: {task}
"""
        
        return await self.solve_with_code(prompt, data)

