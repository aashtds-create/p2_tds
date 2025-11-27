# Robustness Improvements for Unknown Test Cases

## Critical Robustness Features

### 1. Better Task Type Detection
**Problem:** Unknown task types → falls back to LLM (slow + unreliable)
**Solution:** More comprehensive pattern matching

```python
def _identify_task_type(self, content: str) -> str:
    content_lower = content.lower()
    
    # Add more patterns
    patterns = {
        "audio": ["audio", "transcribe", "listen", "sound", "speak", "voice"],
        "video": ["video", "watch", "mp4", "youtube", "stream"],
        "pdf": ["pdf", "document", "download pdf"],
        "csv": ["csv", "spreadsheet", "excel", "table", "data file"],
        "image": ["image", "picture", "photo", "screenshot", "png", "jpg"],
        "api": ["api", "endpoint", "rest", "http get", "fetch"],
        "scraping": ["scrape", "website", "web page", "html"],
        "computation": ["calculate", "compute", "formula", "equation", "sha", "hash"],
        "alphametic": ["alphametic", "cryptarithmetic", "puzzle"],
        "sql": ["sql", "database", "query", "select"],
        "regex": ["regex", "regular expression", "pattern matching"],
        "json": ["json", "parse json", "json object"],
    }
    
    for task_type, keywords in patterns.items():
        if any(keyword in content_lower for keyword in keywords):
            return task_type
    
    return "unknown"
```

---

### 2. Graceful Error Handling
**Problem:** One error crashes entire quiz chain
**Solution:** Try-catch with fallbacks, continue to next question

```python
async def solve(self, url: str):
    try:
        # Main solving logic
        answer = await self.executor.execute(instructions)
    except Exception as e:
        logger.error(f"Error solving {url}: {e}")
        # Submit None or "ERROR" and continue
        answer = None
    
    try:
        await self._submit_answer(submit_url, answer)
    except Exception as e:
        logger.error(f"Submission failed: {e}")
        # Don't crash - just log and move on
```

---

### 3. Multiple Answer Extraction Methods
**Problem:** LLM returns verbose text instead of clean answer
**Solution:** Post-process LLM responses

```python
def extract_clean_answer(llm_response: str) -> str:
    """Extract answer from verbose LLM response"""
    
    # Remove common prefixes
    prefixes = ["The answer is", "Answer:", "Result:", "Solution:"]
    for prefix in prefixes:
        if llm_response.startswith(prefix):
            llm_response = llm_response[len(prefix):].strip()
    
    # Remove markdown code blocks
    llm_response = re.sub(r'```.*?```', '', llm_response, flags=re.DOTALL)
    
    # Extract numbers if answer should be numeric
    if re.match(r'^\d+$', llm_response.strip()):
        return llm_response.strip()
    
    # Extract first number if mixed text
    numbers = re.findall(r'\b\d+\b', llm_response)
    if numbers:
        return numbers[0]
    
    return llm_response.strip()
```

---

### 4. Content Type Handling
**Problem:** Different content types need different handling
**Solution:** Auto-detect and handle

```python
async def download_file(self, url: str) -> bytes:
    """Smart file downloader with content type detection"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        content_type = response.headers.get('content-type', '')
        
        if 'json' in content_type:
            return response.json()
        elif 'csv' in content_type or url.endswith('.csv'):
            return pd.read_csv(io.StringIO(response.text))
        elif 'pdf' in content_type:
            return response.content  # Pass to PDF processor
        elif 'audio' in content_type:
            return response.content  # Pass to audio processor
        else:
            return response.text
```

---

### 5. Timeout Protection
**Problem:** One slow question uses up entire 1-hour window
**Solution:** Per-question timeout with smart abort

```python
# In solver.py
async def solve(self, url: str):
    # Give each question max 90 seconds
    try:
        async with asyncio.timeout(90):
            # Main solving logic
            ...
    except asyncio.TimeoutError:
        logger.warning(f"Question timeout after 90s: {url}")
        # Submit best guess or None and move on
        await self._submit_answer(submit_url, None)
```

---

### 6. Rate Limit Buffer
**Problem:** Gemini rate limits (10 req/min) can block progress
**Solution:** Track API calls, add buffer

```python
class RateLimiter:
    def __init__(self, max_calls=10, period=60):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
    
    async def acquire(self):
        now = time.time()
        self.calls = [c for c in self.calls if now - c < self.period]
        
        if len(self.calls) >= self.max_calls:
            wait_time = self.period - (now - self.calls[0]) + 1
            logger.warning(f"Rate limit reached, waiting {wait_time}s")
            await asyncio.sleep(wait_time)
        
        self.calls.append(now)
```

---

## Test Everything Locally First

Before actual test, run through:
1. All demo variations (demo, demo2, demo3, etc.)
2. Intentional error cases (broken URLs, wrong formats)
3. Large data files (big CSVs, long audio)
4. Rate limit scenarios (send many requests fast)
