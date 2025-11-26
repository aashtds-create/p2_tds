import asyncio
import logging
from src.quiz_solver.parser import InstructionParser

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_parser():
    parser = InstructionParser()
    
    # Sample content from the project statement
    sample_content = """
    Q834. Download file.
    What is the sum of the "value" column in the table on page 2?
    
    Post your answer to https://example.com/submit with this JSON payload:
    
    {
      "email": "your email",
      "secret": "your secret",
      "url": "https://example.com/quiz-834",
      "answer": 12345 // the correct answer
    }
    """
    
    try:
        print("Parsing sample content...")
        instructions = await parser.parse(sample_content)
        print("\n--- Parsed Instructions ---\n")
        print(f"Question: {instructions.question[:50]}...")
        print(f"Data Source: {instructions.data_source}")
        print(f"Task Type: {instructions.task_type}")
        print(f"Submit URL: {instructions.submit_url}")
        print(f"Expected Format: {instructions.expected_format}")
        print("\n---------------------------\n")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_parser())
