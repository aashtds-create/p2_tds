"""
Main API endpoint for quiz solver
"""
import os
import sys
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import logging

from src.utils.auth import verify_secret
from src.agent.core import QuizAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Analysis Quiz Solver")

# Configuration
SECRET = os.getenv("SECRET", "")
EMAIL = os.getenv("EMAIL", "")

# Store background tasks to prevent GC
background_tasks = set()

class QuizRequest(BaseModel):
    email: str
    secret: str
    url: str

class QuizResponse(BaseModel):
    status: str
    message: str

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle malformed JSON with HTTP 400 as per project requirements"""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid JSON payload"}
    )

@app.post("/quiz", response_model=QuizResponse)
async def handle_quiz(request: QuizRequest):
    """
    Main endpoint that receives quiz tasks
    """
    logger.info(f"Received quiz request for email: {request.email}")

    # Verify secret
    if not verify_secret(request.secret):
        logger.warning("Invalid secret provided")
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    # Validate email matches
    if request.email != EMAIL:
        logger.warning(f"Email mismatch: expected {EMAIL}, got {request.email}")
        raise HTTPException(status_code=403, detail="Email mismatch")
    
    # Start timer (3 minutes from now)
    deadline = datetime.now() + timedelta(minutes=3)
    logger.info(f"Starting quiz agent with deadline: {deadline}")
    
    # Start async quiz solving
    task = asyncio.create_task(solve_quiz_async(request.url, request.secret, request.email, deadline))
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)
    
    return QuizResponse(
        status="accepted",
        message="Quiz task received and processing started"
    )

async def solve_quiz_async(url: str, secret: str, email: str, deadline: datetime):
    """
    Async function to solve the quiz using QuizAgent
    """
    try:
        logger.info(f"Processing quiz at URL: {url}")
        agent = QuizAgent(secret=secret, email=email, deadline=deadline)
        await agent.solve(url)
        logger.info("Quiz processing completed")
    except Exception as e:
        logger.error(f"Error solving quiz: {e}", exc_info=True)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
