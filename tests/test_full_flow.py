import asyncio
import logging
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock

from src.quiz_solver.solver import QuizSolver
from src.llm.client import LLMClient

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_full_flow():
    # Mock LLM Client to avoid API key requirement
    LLMClient.solve_task = AsyncMock(return_value=12345)
    LLMClient.parse_instruction = AsyncMock(return_value={
        "question": "What is the answer?",
        "data_source": "https://example.com/data",
        "task_type": "scraping",
        "submit_url": "https://tds-llm-analysis.s-anand.net/demo/submit", # Fake submit URL for safety or use real one if safe
        "expected_format": "number"
    })
    
    # Use the real demo URL
    url = "https://tds-llm-analysis.s-anand.net/demo"
    email = "test@example.com"
    secret = "test_secret"
    deadline = datetime.now() + timedelta(minutes=3)
    
    solver = QuizSolver(secret=email, email=email, deadline=deadline)
    
    # We need to mock the submit answer part because we don't want to actually submit to the live demo 
    # with fake credentials and get a 403, although the demo might accept anything.
    # Let's try to run it and see what happens. If it fails on submission, that's fine, 
    # as long as it gets to that point.
    
    # Actually, let's mock _submit_answer to just print the payload
    solver._submit_answer = AsyncMock()
    
    print(f"Starting solver test on {url}")
    await solver.solve(url)
    
    print("\n--- Test Results ---")
    print(f"Renderer called: {solver.renderer.browser is not None}") # It should be closed but initialized
    # Check if submit was called
    if solver._submit_answer.called:
        print("Submission attempted!")
        args = solver._submit_answer.call_args
        print(f"Submission URL: {args[0][0]}")
        print(f"Answer: {args[0][1]}")
    else:
        print("Submission NOT attempted.")

if __name__ == "__main__":
    asyncio.run(test_full_flow())
