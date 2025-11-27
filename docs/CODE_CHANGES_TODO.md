# CODE CHANGES TO IMPLEMENT TODAY

## ⚡ Priority 1: Speed & Timeout (30 min to implement)

### Change 1: Add Per-Question Timeout
**File:** `src/quiz_solver/solver.py`
**Location:** Inside `solve()` method

```python
async def solve(self, url: str):
    """Solve a quiz at the given URL"""
    self.current_url = url
    
    try:
        # ADD THIS: 90-second timeout per question
        async with asyncio.timeout(90):
            logger.info(f"Solving quiz at {url}")
            
            # Existing code stays here...
            content = await self.renderer.render(url)
            instructions = await self.parser.parse(content)
            self.executor.current_page_content = content
            
            answer = await self.executor.execute(instructions, base_url=url)
            logger.info(f"Generated answer: {answer}")
            
            # Submit logic...
            
    except asyncio.TimeoutError:
        logger.error(f"⏰ TIMEOUT after 90s on {url}, moving on...")
        # Try to submit None and continue
        try:
            await self._submit_answer(submit_url, None)
        except:
            pass
    except Exception as e:
        logger.error(f"Error solving quiz at {url}: {e}")
```

**Testing:** Run demo - should complete in < 90s

---

### Change 2: Keep Browser Alive
**File:** `src/api/endpoint.py`
**Add:** New method to handle continuous quiz chains

```python
async def solve_quiz_chain(solver: QuizSolver, start_url: str):
    """Solve chain of questions without restarting browser"""
    current_url = start_url
    question_count = 0
    max_questions = 100  # Safety limit
    
    try:
        while current_url and question_count < max_questions:
            question_count += 1
            logger.info(f"📝 Question {question_count}: {current_url}")
            
            # Solve returns next URL from submission result
            next_url = await solver.solve(current_url)
            
            if next_url:
                current_url = next_url
                logger.info(f"✅ Proceeding to question {question_count + 1}")
            else:
                logger.info(f"🏁 Quiz chain complete! Solved {question_count} questions")
                break
                
    finally:
        # Close browser only at the end
        await solver.renderer.close()
        logger.info(f"Browser closed after {question_count} questions")
```

**Then modify** `solver.solve()` to return next URL:

```python
# In solver.py, after submission
result = response.json()
logger.info(f"Submission result: {result}")

if result.get("correct"):
    logger.info("Answer correct!")
    next_url = result.get("url")
    if next_url:
        logger.info(f"Proceeding to next URL: {next_url}")
        return next_url  # ADD THIS: Return next URL
else:
    logger.warning(f"Answer incorrect: {result.get('reason')}")
    
return None  # No more questions
```

**Testing:** Should reuse browser across questions

---

## 🧹 Priority 2: Answer Cleaning (15 min to implement)

### Change 3: Clean LLM Answers
**File:** `src/llm/client.py`
**Add:** Helper method

```python
def _clean_answer(self, raw_answer: str) -> str:
    """Remove verbose text from LLM responses"""
    if not raw_answer:
        return None
    
    # Remove common prefixes
    prefixes_to_remove = [
        "The answer is ",
        "Answer: ",
        "Result: ",
        "Solution: ",
        "Based on the data, ",
        "According to ",
        "I found that ",
    ]
    
    for prefix in prefixes_to_remove:
        if raw_answer.lower().startswith(prefix.lower()):
            raw_answer = raw_answer[len(prefix):].strip()
    
    # Remove quotes if present
    if raw_answer.startswith('"') and raw_answer.endswith('"'):
        raw_answer = raw_answer[1:-1]
    if raw_answer.startswith("'") and raw_answer.endswith("'"):
        raw_answer = raw_answer[1:-1]
    
    # Remove trailing punctuation
    raw_answer = raw_answer.rstrip('.,!?;:')
    
    return raw_answer.strip()
```

**Then use it** in `solve_task()`:

```python
async def solve_task(self, question: str, data: Any = None) -> Any:
    """Use LLM to solve a generic task"""
    # ... existing code ...
    response = await self.chat_completion(messages)
    
    # ADD THIS: Clean the response
    if response:
        response = self._clean_answer(response)
    
    return response
```

**Testing:** Try demo - should return clean "anything you want"

---

## 🎯 Priority 3: Better Task Detection (20 min to implement)

### Change 4: Expand Task Type Patterns
**File:** `src/quiz_solver/parser.py`
**Replace:** `_identify_task_type()` method

```python
def _identify_task_type(self, content: str) -> str:
    """Identify the type of task with comprehensive patterns"""
    content_lower = content.lower()
    
    # Check in priority order (most specific first)
    
    # Computational/Math puzzles
    if any(keyword in content_lower for keyword in [
        "alphametic", "cryptarithmetic", "sha1", "md5", "hash",
        "calculate key", "compute", "formula"
    ]):
        return "computation"
    
    # Audio (check for both explicit markers and file extensions)
    if any(keyword in content_lower for keyword in [
        "[media files found]", "audio:", "transcribe", "listen",
        ".mp3", ".wav", ".opus", ".m4a", "sound", "voice"
    ]):
        return "audio"
    
    # Video
    if any(keyword in content_lower for keyword in [
        "video:", "watch", ".mp4", ".webm", "youtube", "stream"
    ]):
        return "video"
    
    # PDF
    if any(keyword in content_lower for keyword in [
        ".pdf", "pdf document", "download pdf"
    ]):
        return "pdf"
    
    # CSV/Data analysis
    if any(keyword in content_lower for keyword in [
        ".csv", "spreadsheet", "data file", "csv file", "excel",
        "filter", "sum", "count", "aggregate"
    ]):
        return "analysis"
    
    # Web scraping
    if any(keyword in content_lower for keyword in [
        "scrape", "secret code", "website", "web page", "get the"
    ]):
        return "scraping"
    
    # API calls
    if any(keyword in content_lower for keyword in [
        "api", "endpoint", "rest", "http get", "fetch", "json response"
    ]):
        return "api"
    
    # Image processing
    if any(keyword in content_lower for keyword in [
        "image", "picture", "photo", "screenshot", ".png", ".jpg", "ocr"
    ]):
        return "image"
    
    # Visualization
    if any(keyword in content_lower for keyword in [
        "chart", "graph", "plot", "visualize", "diagram"
    ]):
        return "visualization"
    
    return "unknown"
```

**Testing:** Should detect task types faster

---

## 🔧 Priority 4: Add More Computational Solvers (20 min)

### Change 5: Expand Computation Solver
**File:** `src/data_processing/computation_solver.py`
**Add:** More solver types

```python
async def solve_alphametic(self, content: str, email: str) -> Optional[str]:
    """Solve alphametic puzzles with computational formulas"""
    try:
        logger.info(f"Solving computational puzzle for email: {email}")
        
        # SHA1-based formulas
        if "SHA1" in content and "emailNumber" in content:
            return await self._solve_sha1_formula(content, email)
        
        # MD5-based formulas
        elif "MD5" in content:
            return await self._solve_md5_formula(content, email)
        
        # Simple arithmetic (e.g., "What is 123 + 456?")
        elif re.search(r'\d+\s*[+\-*/]\s*\d+', content):
            return await self._solve_arithmetic(content)
        
        # Fibonacci sequences
        elif "fibonacci" in content.lower():
            return await self._solve_fibonacci(content)
        
        logger.warning("Unknown computational puzzle type")
        return None
        
    except Exception as e:
        logger.error(f"Error solving computation: {e}")
        return None

async def _solve_md5_formula(self, content: str, email: str) -> Optional[str]:
    """Solve MD5-based puzzles"""
    import hashlib
    md5_hash = hashlib.md5(email.encode()).hexdigest()
    logger.info(f"MD5({email}) = {md5_hash}")
    # Extract and apply formula similar to SHA1
    # ... implementation ...
    return None  # Implement based on actual puzzle format

async def _solve_arithmetic(self, content: str) -> Optional[str]:
    """Solve simple arithmetic expressions"""
    # Extract expression like "123 + 456"
    match = re.search(r'(\d+)\s*([+\-*/])\s*(\d+)', content)
    if match:
        a, op, b = int(match.group(1)), match.group(2), int(match.group(3))
        if op == '+': return str(a + b)
        elif op == '-': return str(a - b)
        elif op == '*': return str(a * b)
        elif op == '/': return str(a // b)
    return None

async def _solve_fibonacci(self, content: str) -> Optional[str]:
    """Solve Fibonacci sequence puzzles"""
    # Extract which Fibonacci number is requested
    match = re.search(r'fibonacci\s*\(?(\d+)\)?', content, re.IGNORECASE)
    if match:
        n = int(match.group(1))
        # Calculate nth Fibonacci number
        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
        return str(a)
    return None
```

**Testing:** Create test cases for each type

---

## 📝 Implementation Order

1. **Start with Change 1** (timeout) - Critical for not getting stuck
2. **Then Change 3** (answer cleaning) - Easy win for accuracy
3. **Then Change 4** (task detection) - Better routing
4. **Then Change 2** (browser reuse) - More complex but high impact
5. **Finally Change 5** (more solvers) - Nice to have

---

## 🧪 Testing Each Change

```bash
# After each change:
git add -A
git commit -m "Add [feature name]"
git push origin main

# Wait for Render to deploy (~2 min)
# Then test:
curl -X POST https://p2-tds.onrender.com/quiz \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","secret":"test","url":"https://tds-llm-analysis.s-anand.net/demo"}'

# Watch logs on Render dashboard
```

---

## ⏰ Time Estimate

Total implementation time: **~90 minutes**
- Change 1 (timeout): 30 min
- Change 2 (browser reuse): 30 min
- Change 3 (answer cleaning): 15 min
- Change 4 (task detection): 20 min
- Change 5 (more solvers): 20 min
- Testing each: 5 min × 5 = 25 min

**Do Changes 1, 3, 4 today (minimum viable).**
**Do Changes 2, 5 if you have time.**

---

Good luck! 🚀

