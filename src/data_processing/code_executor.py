"""
Code execution handler for analysis and visualization
"""
import logging
import sys
import io
import base64
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class CodeExecutor:
    """
    Executes Python code for data analysis and visualization
    """
    
    def execute(self, code: str, data: Any = None) -> Dict[str, Any]:
        """
        Execute Python code with provided data
        
        Args:
            code: Python code to execute
            data: Data to be available in the execution context as 'df' or 'data'
            
        Returns:
            Dictionary containing 'result' (text output) and 'image' (base64 image if generated)
        """
        # Capture stdout
        old_stdout = sys.stdout
        redirected_output = io.StringIO()
        sys.stdout = redirected_output
        
        # Prepare context
        context = {
            "pd": pd,
            "np": np,
            "plt": plt,
            "data": data,
            "df": pd.DataFrame(data) if isinstance(data, (list, dict)) else data
        }
        
        result_image = None
        
        try:
            logger.info("Executing analysis code")
            # Execute code
            exec(code, context)
            
            # Check if a plot was created
            if plt.get_fignums():
                logger.info("Plot detected, converting to base64")
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                result_image = base64.b64encode(buf.read()).decode('utf-8')
                plt.close('all')
                
        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            print(f"Error: {e}")
        finally:
            sys.stdout = old_stdout
            
        return {
            "output": redirected_output.getvalue(),
            "image": result_image
        }
