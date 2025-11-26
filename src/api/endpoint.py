"""
Main API endpoint for quiz solver
"""
import os
import sys
import time
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

# Load environment variables (for local development)
# In production (Railway/Render), env vars are set directly
load_dotenv()  # Try current directory
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))  # Try src/.env
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))  # Try project root/.env

# Add project root to sys.path to allow imports from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from src.utils.auth import verify_secret
from src.quiz_solver.solver import QuizSolver

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Analysis Quiz Solver")

# Configuration
SECRET = os.getenv("SECRET", "")
EMAIL = os.getenv("EMAIL", "")


class QuizRequest(BaseModel):
    email: str
    secret: str
    url: str
    # Other fields may be present


class QuizResponse(BaseModel):
    status: str
    message: str


@app.post("/quiz", response_model=QuizResponse)
async def handle_quiz(request: QuizRequest, http_request: Request):
    """
    Main endpoint that receives quiz tasks
    
    Returns:
        - 200: Valid request, processing started
        - 400: Invalid JSON
        - 403: Invalid secret
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
    logger.info(f"Starting quiz solver with deadline: {deadline}")
    
    # Start async quiz solving (don't await - return immediately)
    asyncio.create_task(solve_quiz_async(request.url, request.secret, request.email, deadline))
    
    return QuizResponse(
        status="accepted",
        message="Quiz task received and processing started"
    )


async def solve_quiz_async(url: str, secret: str, email: str, deadline: datetime):
    """
    Async function to solve the quiz
    This runs in the background after returning 200
    """
    try:
        logger.info(f"Processing quiz at URL: {url}")
        solver = QuizSolver(secret=secret, email=email, deadline=deadline)
        await solver.solve(url)
        logger.info("Quiz processing completed")
    except Exception as e:
        logger.error(f"Error solving quiz: {e}", exc_info=True)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

