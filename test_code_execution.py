import asyncio
import logging
import pandas as pd
from src.data_processing.code_executor import CodeExecutor
from src.data_processing.analyzer import DataAnalyzer
from unittest.mock import AsyncMock

logging.basicConfig(level=logging.INFO)

async def test_code_executor():
    print("\n--- Testing CodeExecutor ---")
    executor = CodeExecutor()
    
    # Test 1: Simple calculation
    code = "print(1 + 1)"
    result = executor.execute(code)
    print(f"Result 1 (1+1): {result['output'].strip()}")
    assert result['output'].strip() == "2"
    
    # Test 2: Dataframe operation
    data = {"a": [1, 2, 3], "b": [4, 5, 6]}
    code = "print(df['a'].sum())"
    result = executor.execute(code, data)
    print(f"Result 2 (sum): {result['output'].strip()}")
    assert result['output'].strip() == "6"
    
    # Test 3: Plotting
    code = """
plt.plot([1, 2, 3], [1, 2, 3])
plt.title("Test Plot")
"""
    result = executor.execute(code)
    print(f"Result 3 (plot): Image present? {bool(result['image'])}")
    assert result['image'] is not None

async def test_analyzer():
    print("\n--- Testing DataAnalyzer ---")
    
    # Mock LLM Client
    mock_llm = AsyncMock()
    mock_llm.chat_completion.return_value = "print(df['value'].mean())"
    
    analyzer = DataAnalyzer(mock_llm)
    data = {"value": [10, 20, 30]}
    
    result = await analyzer.analyze(data, "What is the mean?")
    print(f"Analyzer Result: {result}")
    assert result == "20.0"

if __name__ == "__main__":
    asyncio.run(test_code_executor())
    asyncio.run(test_analyzer())
