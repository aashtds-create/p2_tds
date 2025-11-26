import asyncio
import logging
from src.quiz_solver.renderer import PageRenderer

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_renderer():
    renderer = PageRenderer()
    url = "https://tds-llm-analysis.s-anand.net/demo"
    
    try:
        print(f"Rendering {url}...")
        content = await renderer.render(url)
        print("\n--- Extracted Content ---\n")
        print(content[:500] + "..." if len(content) > 500 else content)
        print("\n-------------------------\n")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await renderer.close()

if __name__ == "__main__":
    asyncio.run(test_renderer())
