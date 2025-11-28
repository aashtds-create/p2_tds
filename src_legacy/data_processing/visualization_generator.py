"""
Visualization generator for chart-based quiz answers
Generates charts as base64-encoded images or interactive HTML
"""
import logging
import base64
import json
from io import BytesIO
from typing import Any, Dict, Optional
import pandas as pd

logger = logging.getLogger(__name__)

class VisualizationGenerator:
    """
    Generates visualizations (charts, plots) as base64 or JSON
    """
    
    def __init__(self):
        self.llm_client = None  # Will be set by executor
    
    async def generate(self, instructions: str, data: Any) -> str:
        """
        Generate visualization based on instructions
        
        Args:
            instructions: What kind of visualization to create
            data: Data to visualize (DataFrame, list, dict, etc.)
            
        Returns:
            Base64-encoded image or JSON for interactive charts
        """
        try:
            # Detect visualization type
            viz_type = self._detect_viz_type(instructions)
            
            logger.info(f"Generating {viz_type} visualization")
            
            if viz_type == "chart":
                return await self._generate_chart(instructions, data)
            elif viz_type == "interactive":
                return await self._generate_interactive(instructions, data)
            elif viz_type == "narrative":
                return await self._generate_narrative(instructions, data)
            else:
                # Use LLM to figure out what to generate
                return await self._generate_with_llm(instructions, data)
                
        except Exception as e:
            logger.error(f"Error generating visualization: {e}")
            return None
    
    def _detect_viz_type(self, instructions: str) -> str:
        """Detect what type of visualization is requested"""
        instructions_lower = instructions.lower()
        
        if any(word in instructions_lower for word in ["interactive", "plotly", "d3", "html"]):
            return "interactive"
        elif any(word in instructions_lower for word in ["narrative", "story", "explain", "describe"]):
            return "narrative"
        elif any(word in instructions_lower for word in ["chart", "plot", "graph", "visualize", "image"]):
            return "chart"
        else:
            return "unknown"
    
    async def _generate_chart(self, instructions: str, data: Any) -> str:
        """
        Generate static chart as base64 PNG
        """
        try:
            # Lazy import matplotlib (not always needed)
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import matplotlib.pyplot as plt
            
            # Convert data to DataFrame if possible
            if isinstance(data, dict):
                df = pd.DataFrame(data)
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, pd.DataFrame):
                df = data
            else:
                logger.error("Unsupported data type for visualization")
                return None
            
            # Detect chart type from instructions
            chart_type = self._detect_chart_type(instructions)
            
            # Create figure
            plt.figure(figsize=(10, 6))
            
            if chart_type == "bar":
                df.plot(kind='bar', ax=plt.gca())
            elif chart_type == "line":
                df.plot(kind='line', ax=plt.gca())
            elif chart_type == "scatter":
                # Assume first 2 columns for x, y
                if len(df.columns) >= 2:
                    plt.scatter(df.iloc[:, 0], df.iloc[:, 1])
            elif chart_type == "pie":
                # Assume first column for values
                df.iloc[:, 0].plot(kind='pie', ax=plt.gca())
            elif chart_type == "histogram":
                df.iloc[:, 0].plot(kind='hist', ax=plt.gca())
            else:
                # Default: try to plot
                df.plot(ax=plt.gca())
            
            plt.title(self._extract_title(instructions) or "Chart")
            plt.tight_layout()
            
            # Save to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close()
            
            # Return as data URI
            data_uri = f"data:image/png;base64,{image_base64}"
            logger.info(f"Generated chart, size: {len(data_uri)} bytes")
            
            return data_uri
            
        except ImportError:
            logger.error("matplotlib not installed, cannot generate charts")
            return None
        except Exception as e:
            logger.error(f"Error creating chart: {e}")
            return None
    
    def _detect_chart_type(self, instructions: str) -> str:
        """Detect what kind of chart to create"""
        instructions_lower = instructions.lower()
        
        if "bar" in instructions_lower:
            return "bar"
        elif "line" in instructions_lower:
            return "line"
        elif "scatter" in instructions_lower:
            return "scatter"
        elif "pie" in instructions_lower:
            return "pie"
        elif "histogram" in instructions_lower or "distribution" in instructions_lower:
            return "histogram"
        else:
            return "auto"
    
    def _extract_title(self, instructions: str) -> Optional[str]:
        """Try to extract chart title from instructions"""
        # Simple heuristic: look for "title:" or quoted text
        import re
        
        # Look for "title: Something"
        title_match = re.search(r'title[:\s]+([^,\n]+)', instructions, re.IGNORECASE)
        if title_match:
            return title_match.group(1).strip()
        
        # Look for quoted text
        quoted_match = re.search(r'"([^"]+)"', instructions)
        if quoted_match:
            return quoted_match.group(1)
        
        return None
    
    async def _generate_interactive(self, instructions: str, data: Any) -> str:
        """
        Generate interactive visualization (Plotly or similar)
        Returns JSON or HTML
        """
        try:
            # Try plotly
            import plotly.express as px
            import plotly.io as pio
            
            # Convert data to DataFrame
            if isinstance(data, dict):
                df = pd.DataFrame(data)
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, pd.DataFrame):
                df = data
            else:
                return None
            
            # Create interactive plot
            chart_type = self._detect_chart_type(instructions)
            
            if chart_type == "bar":
                fig = px.bar(df)
            elif chart_type == "line":
                fig = px.line(df)
            elif chart_type == "scatter" and len(df.columns) >= 2:
                fig = px.scatter(df, x=df.columns[0], y=df.columns[1])
            else:
                fig = px.line(df)
            
            # Return as JSON or HTML based on request
            if "json" in instructions.lower():
                return json.dumps(fig.to_dict())
            else:
                # Return HTML
                html = pio.to_html(fig, include_plotlyjs='cdn')
                # Return as base64 if needed
                if "base64" in instructions.lower():
                    html_base64 = base64.b64encode(html.encode('utf-8')).decode('utf-8')
                    return f"data:text/html;base64,{html_base64}"
                return html
                
        except ImportError:
            logger.warning("plotly not installed, falling back to static chart")
            return await self._generate_chart(instructions, data)
        except Exception as e:
            logger.error(f"Error creating interactive viz: {e}")
            return None
    
    async def _generate_narrative(self, instructions: str, data: Any) -> str:
        """
        Generate narrative/text description of data
        """
        if not self.llm_client:
            logger.error("LLM client not set, cannot generate narrative")
            return None
        
        # Convert data to string representation
        if isinstance(data, pd.DataFrame):
            data_str = data.to_string(max_rows=20)
        elif isinstance(data, (dict, list)):
            data_str = json.dumps(data, indent=2)[:2000]  # Limit size
        else:
            data_str = str(data)[:2000]
        
        prompt = f"""
Generate a narrative analysis based on this data and instructions:

Instructions: {instructions}

Data:
{data_str}

Provide a clear, insightful narrative summary.
"""
        
        response = await self.llm_client.chat_completion([
            {"role": "system", "content": "You are a data storyteller."},
            {"role": "user", "content": prompt}
        ])
        
        return response
    
    async def _generate_with_llm(self, instructions: str, data: Any) -> str:
        """
        Use LLM to decide how to generate visualization
        """
        if not self.llm_client:
            logger.error("LLM client not set")
            return None
        
        # Ask LLM what to do
        prompt = f"""
You need to create a visualization based on these instructions:
{instructions}

Data available: {type(data).__name__}

What should be generated? Respond with ONE of:
- "chart:bar" - bar chart
- "chart:line" - line chart  
- "chart:scatter" - scatter plot
- "narrative" - text description
- "json" - JSON data structure

Respond with just the type, nothing else.
"""
        
        response = await self.llm_client.chat_completion([
            {"role": "system", "content": "You are a visualization expert."},
            {"role": "user", "content": prompt}
        ])
        
        if "narrative" in response.lower():
            return await self._generate_narrative(instructions, data)
        elif "json" in response.lower():
            # Return data as JSON
            if isinstance(data, pd.DataFrame):
                return data.to_json(orient='records')
            return json.dumps(data)
        else:
            # Default to chart
            return await self._generate_chart(instructions, data)

