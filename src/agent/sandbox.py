"""
Unified Code Execution Sandbox
Executes LLM-generated Python code in a controlled environment.
"""
import sys
import io
import base64
import logging
import warnings
import json
import re
import math
import random
import datetime

# Allowed libraries
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import pypdf

logger = logging.getLogger(__name__)

class CodeSandbox:
    """
    Executes Python code for data analysis, scraping, and general problem solving.
    """
    
    def __init__(self):
        pass
        
    def execute(self, code: str, context_data: dict = None) -> dict:
        """
        Execute Python code.
        
        Args:
            code: Python code string
            context_data: Optional dictionary of variables to inject into scope
            
        Returns:
            Dict with 'output' (stdout), 'image' (base64 plot), 'error' (if any)
        """
        # Capture stdout
        old_stdout = sys.stdout
        redirected_output = io.StringIO()
        sys.stdout = redirected_output
        
        # Prepare execution context
        context = {
            "requests": requests,
            "pd": pd,
            "np": np,
            "plt": plt,
            "BeautifulSoup": BeautifulSoup,
            "pypdf": pypdf,
            "json": json,
            "re": re,
            "math": math,
            "random": random,
            "datetime": datetime,
            "print": print, # Ensure print goes to stdout
        }
        
        if context_data:
            context.update(context_data)
            
        result_image = None
        error_msg = None
        
        try:
            logger.info("Executing sandbox code...")
            
            # Suppress warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                exec(code, context)
            
            # Check for plots
            if plt.get_fignums():
                logger.info("Plot detected, converting to base64")
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                result_image = base64.b64encode(buf.read()).decode('utf-8')
                plt.close('all')
                
        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")
            error_msg = str(e)
            print(f"Error: {e}") # Print to stdout so LLM sees it
            
        finally:
            sys.stdout = old_stdout
            
        return {
            "output": redirected_output.getvalue(),
            "image": result_image,
            "error": error_msg
        }
