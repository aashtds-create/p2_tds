# 🏗️ Architecture Deep Dive: How Your App Works

## 🎯 **The Big Picture**

Your app is a **quiz-solving bot** that:
1. Receives a quiz URL via API
2. Visits the page (renders JavaScript)
3. Reads instructions
4. Fetches/processes data (PDF, CSV, API, Audio, etc.)
5. Uses AI (Gemini) to understand and solve
6. Submits answer
7. Repeats for next quiz page (if any)

---

## 📊 **Data Flow Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│  1. INCOMING REQUEST                                         │
│  POST /quiz { email, secret, url }                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  2. API ENDPOINT (src/api/endpoint.py)                      │
│  - Validates secret                                          │
│  - Returns 200 immediately                                   │
│  - Starts async task                                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  3. QUIZ SOLVER (src/quiz_solver/solver.py)                 │
│  - Main orchestrator                                         │
│  - Loops through quiz pages                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  4. PAGE RENDERER (src/quiz_solver/renderer.py)             │
│  - Uses Playwright (headless Chrome)                         │
│  - Executes JavaScript                                       │
│  - Extracts text content                                     │
│  - Finds media URLs (audio, PDF, CSV)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  5. INSTRUCTION PARSER (src/quiz_solver/parser.py)          │
│  - Extracts: question, data source, task type                │
│  - Uses regex FIRST (fast)                                   │
│  - Falls back to LLM if regex fails                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  6. TASK EXECUTOR (src/quiz_solver/executor.py)             │
│  - Routes to appropriate handler based on task type          │
│  - Handles: API, scraping, PDF, CSV, audio                   │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┬──────────────┬──────────┐
        │                         │              │          │
        ▼                         ▼              ▼          ▼
┌──────────────┐  ┌──────────────┐  ┌─────────┐  ┌───────┐
│ API Client   │  │ Scraper      │  │ PDF     │  │ Audio │
│              │  │ (Playwright) │  │ Extract │  │ Gemini│
└──────┬───────┘  └──────┬───────┘  └────┬────┘  └───┬───┘
       │                 │               │           │
       └─────────────────┴───────────────┴───────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  7. LLM CLIENT (src/llm/client.py)                          │
│  - Sends data + question to Gemini                          │
│  - Gets answer                                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  8. SUBMIT ANSWER (back to solver.py)                       │
│  - POST to submit URL                                        │
│  - Check if correct                                          │
│  - Get next URL (if any)                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
            Loop back to step 3 if next URL exists
                     │
                     ▼
                  ✅ Done!
```

---

## 🔍 **Component-by-Component Breakdown**

### **1. API Endpoint** (`src/api/endpoint.py`)

**What it does:**
```python
@app.post("/quiz")
async def quiz_endpoint(request: QuizRequest):
    # 1. Validate secret
    if not verify_secret(request.secret, request.email):
        raise HTTPException(status_code=403)
    
    # 2. Return 200 immediately (don't block)
    asyncio.create_task(solve_quiz_async(...))
    return {"status": "processing"}
    
    # 3. Async task solves quiz in background
```

**Why this design?**
- ✅ **Non-blocking**: Returns immediately so professor's server doesn't wait
- ✅ **Async**: Solves quiz in background
- ✅ **Fast response**: < 1 second to return 200

**Key Code:**
```python
# Verify secret (simple check)
def verify_secret(secret: str, email: str) -> bool:
    return secret == expected_secret

# Start async task
asyncio.create_task(solver.solve_quiz(email, secret, url))
```

---

### **2. Quiz Solver** (`src/quiz_solver/solver.py`)

**What it does:**
```python
class QuizSolver:
    async def solve_quiz(self, email, secret, url):
        while url:  # Loop through quiz pages
            # 1. Render page (JavaScript execution)
            content = await self._render_page(url)
            
            # 2. Parse instructions
            task = await self._parse_instructions(content)
            
            # 3. Execute task
            answer = await self._execute_task(task)
            
            # 4. Submit answer
            result = await self._submit_answer(email, secret, url, answer)
            
            # 5. Get next URL (if any)
            url = result.get('url')
```

**Why this design?**
- ✅ **Loop-based**: Handles multiple quiz pages automatically
- ✅ **Modular**: Each step is separate function
- ✅ **Error handling**: Try-catch at each step

**Key Logic:**
```python
# Main loop
while url and not is_complete:
    # Solve one page
    # Get next URL
    # Repeat
```

---

### **3. Page Renderer** (`src/quiz_solver/renderer.py`)

**What it does:**
```python
class PageRenderer:
    async def render(self, url):
        # 1. Launch headless Chrome
        browser = await playwright.chromium.launch()
        
        # 2. Navigate to URL
        page = await browser.new_page()
        await page.goto(url)
        
        # 3. Wait for JavaScript to execute
        await page.wait_for_load_state('networkidle')
        
        # 4. Extract text content
        text = await page.inner_text('body')
        
        # 5. Find media files (audio, PDF, CSV)
        media_urls = await self._extract_media_urls(page)
        
        return text + media_urls
```

**Why use Playwright?**
- ✅ **JavaScript execution**: Quiz pages use `atob()` and DOM manipulation
- ✅ **Real browser**: Handles any web tech (CSS, JS, etc.)
- ✅ **Reliable**: Industry-standard tool

**Key Feature:**
```python
# Extract media file URLs
audio_urls = await page.evaluate('''
    Array.from(document.querySelectorAll('audio, video'))
         .map(el => el.src)
''')
```

**Why Important:**
- Professor's quiz uses JavaScript to hide/reveal content
- Static HTML parsing wouldn't work
- Need full browser rendering

---

### **4. Instruction Parser** (`src/quiz_solver/parser.py`)

**What it does:**
```python
class InstructionParser:
    async def parse(self, content):
        # Strategy 1: Try regex (fast!)
        result = self._regex_parse(content)
        if result.is_complete():
            return result
        
        # Strategy 2: Use LLM (flexible!)
        result = await self._llm_parse(content)
        return result
```

**Why two strategies?**

**Regex (Fast):**
```python
# Extract URL from "Download file from https://..."
url_pattern = r'https?://[^\s<>"]+'
urls = re.findall(url_pattern, content)
```
- ✅ **Fast**: Microseconds
- ❌ **Brittle**: Only works for simple patterns

**LLM (Flexible):**
```python
# Send to Gemini with structured prompt
prompt = f"""
Parse this quiz instruction:
{content}

Extract:
1. Question
2. Data source URL
3. Task type (scraping/api/pdf/audio/csv)
"""
```
- ✅ **Flexible**: Handles any wording
- ✅ **Smart**: Understands context
- ❌ **Slower**: 2-3 seconds

**Why This Design:**
- Try fast method first
- Fall back to smart method if needed
- Best of both worlds!

---

### **5. Task Executor** (`src/quiz_solver/executor.py`)

**What it does:**
```python
class TaskExecutor:
    async def execute(self, task):
        # Route to appropriate handler
        if task.type == 'api':
            return await self._handle_api_task(task)
        elif task.type == 'scraping':
            return await self._handle_scraping_task(task)
        elif task.type == 'pdf':
            return await self._handle_pdf_task(task)
        elif task.type == 'audio':
            return await self._handle_audio_task(task)
        elif task.type == 'csv':
            return await self._handle_csv_task(task)
```

**Why this design?**
- ✅ **Single Responsibility**: Each handler does one thing
- ✅ **Easy to extend**: Add new task type = new handler
- ✅ **Clean**: No giant if-else chains

**Example Handler:**
```python
async def _handle_audio_task(self, task):
    # 1. Download audio
    audio_bytes = await self._download(task.url)
    
    # 2. Transcribe (Gemini Audio API)
    transcript = await self.audio_processor.process(audio_bytes)
    
    # 3. Find CSV URL in transcript
    csv_url = extract_url(transcript)
    
    # 4. Download CSV
    df = await self.csv_processor.process(csv_url)
    
    # 5. Process data (filter, sum, etc.)
    answer = process_data(df, task.instructions)
    
    return answer
```

---

### **6. Data Processors**

#### **Audio Processor** (`src/data_processing/audio_processor.py`)

**What it does:**
```python
class AudioProcessor:
    async def process(self, url):
        # 1. Download audio
        audio_bytes = await download(url)
        
        # 2. Try transcription methods (priority order)
        # Method 1: Gemini Audio API (fast, reliable)
        try:
            return await self._gemini_transcribe(audio_bytes)
        except:
            pass
        
        # Method 2: SpeechRecognition (free backup)
        try:
            return await self._speech_recognition(audio_bytes)
        except:
            pass
        
        # Method 3: Local Whisper (slow but works offline)
        return await self._local_whisper(audio_bytes)
```

**Why this priority order?**
1. **Gemini** (primary): Fast (4s), accurate, same API key
2. **SpeechRecognition** (backup): Free, no key needed
3. **Local Whisper** (fallback): Slow (50s) but always works

**Gemini Implementation:**
```python
async def _gemini_transcribe(self, audio_bytes, url):
    # 1. Encode audio as base64
    audio_base64 = base64.b64encode(audio_bytes).decode()
    
    # 2. Detect MIME type from URL
    mime_type = "audio/opus" if url.endswith('.opus') else "audio/mpeg"
    
    # 3. Call Gemini with multimodal prompt
    response = await gemini_api.generate_content({
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": mime_type, "data": audio_base64}},
                {"text": "Transcribe this audio. Return only the text."}
            ]
        }]
    })
    
    return response.text
```

**Why Gemini?**
- ✅ Same API key (already have)
- ✅ Multimodal (handles audio + text)
- ✅ Fast (4-5 seconds vs 50s for Whisper)
- ✅ Reliable (Google infrastructure)

---

#### **CSV Processor** (`src/data_processing/csv_processor.py`)

**What it does:**
```python
class CSVProcessor:
    async def process(self, url):
        # 1. Download CSV
        csv_content = await download(url)
        
        # 2. Detect if has header
        first_line = csv_content.splitlines()[0]
        has_header = not first_line.replace(',', '').isdigit()
        
        # 3. Load into pandas
        if has_header:
            df = pd.read_csv(io.StringIO(csv_content))
        else:
            df = pd.read_csv(io.StringIO(csv_content), header=None)
        
        return df
```

**Why detect header?**
- Some CSVs have headers: `name,value,date`
- Some don't: `123,456,789`
- Wrong assumption = wrong column selection

---

#### **PDF Processor** (`src/data_processing/pdf_processor.py`)

**What it does:**
```python
class PDFProcessor:
    async def process(self, url):
        # 1. Download PDF
        pdf_bytes = await download(url)
        
        # 2. Extract text (try pdfplumber first)
        try:
            text = self._extract_with_pdfplumber(pdf_bytes)
        except:
            # Fallback: PyMuPDF
            text = self._extract_with_pymupdf(pdf_bytes)
        
        return text
```

**Why two PDF libraries?**
- pdfplumber: Better for tables
- PyMuPDF: Better for complex layouts
- Having both = more robust

---

### **7. LLM Client** (`src/llm/client.py`)

**What it does:**
```python
class LLMClient:
    async def generate_answer(self, question, data):
        # Build prompt
        prompt = f"""
        Question: {question}
        Data: {data}
        
        Provide ONLY the direct answer value.
        No explanations, no markdown, no extra text.
        """
        
        # Call Gemini
        response = await self._call_gemini(prompt)
        
        return response
```

**Why specific prompt?**
- Early issue: LLM added "The answer is 42" instead of just "42"
- Solution: Strict prompt → "ONLY the direct answer value"

**System Prompt:**
```python
SYSTEM_PROMPT = """
You are a data analysis assistant.
Answer quiz questions accurately.
Return ONLY the answer value - no explanations.
Format: number, string, boolean, or JSON as specified.
"""
```

---

## 🎯 **Key Design Decisions & Why**

### **1. Async Everything**

**Why?**
```python
# Sync (blocking)
def download(url):  # Waits 2s
    return requests.get(url)  

def process():
    data1 = download(url1)  # Wait 2s
    data2 = download(url2)  # Wait 2s
    # Total: 4s

# Async (parallel)
async def download(url):
    return await httpx.get(url)

async def process():
    data1, data2 = await asyncio.gather(
        download(url1),  # Both run in parallel
        download(url2)
    )
    # Total: 2s
```

✅ **2x faster** for parallel operations!

---

### **2. LLM-Based Parsing (Not Hardcoded Rules)**

**Alternative (Brittle):**
```python
# Hardcoded parsing - breaks easily
if "download" in text and "pdf" in text:
    task_type = "pdf"
elif "scrape" in text:
    task_type = "scraping"
# What if professor says "fetch the document"?
```

**Our Approach (Flexible):**
```python
# LLM understands natural language
llm_parse(text)  # Understands any wording
```

✅ **Handles variations** professor might use!

---

### **3. Fallback Strategy**

**Pattern used everywhere:**
```python
try:
    # Method 1 (fast/best)
    result = fast_method()
except:
    try:
        # Method 2 (slower/backup)
        result = backup_method()
    except:
        # Method 3 (slowest/always works)
        result = fallback_method()
```

**Examples:**
- Audio: Gemini → SpeechRecognition → Whisper
- PDF: pdfplumber → PyMuPDF
- Parsing: Regex → LLM

✅ **Reliability through redundancy!**

---

### **4. Playwright (Not requests/BeautifulSoup)**

**Why not simple HTTP?**
```python
# This WON'T work for professor's quiz
html = requests.get(url).text
# Quiz uses: document.innerHTML = atob(...)
# JavaScript not executed!
```

**Why Playwright?**
```python
# This WORKS
browser = playwright.chromium.launch()
page = browser.new_page()
page.goto(url)  # Executes JavaScript
text = page.inner_text('body')  # Gets rendered content
```

✅ **Handles JavaScript-heavy pages!**

---

## 📈 **Performance Characteristics**

| Operation | Time | Why |
|-----------|------|-----|
| API Response | < 1s | Returns immediately, processes async |
| Page Render | 2-3s | Playwright startup + JS execution |
| LLM Call | 2-5s | Gemini API (depends on length) |
| Audio (Gemini) | 4-5s | Multimodal API |
| Audio (Whisper) | 50s | Local model (fallback) |
| PDF Extract | 1-2s | Library processing |
| CSV Load | < 1s | pandas is fast |
| **Total Quiz** | 40-50s | End-to-end (3 tasks) |

---

## 🔄 **Example: Audio Task Flow**

Let's trace a real audio task:

```
1. Professor POSTs: { url: "https://.../demo-audio?id=123" }
   Time: 0s

2. Your API returns 200 immediately
   Time: 0.1s

3. Background task starts:
   - Playwright launches: 2s
   - Navigate to page: 1s
   - Extract content: 0.5s
   Time: 3.5s

4. Parse instructions:
   - Regex fails (complex wording)
   - LLM parses: 3s
   - Finds: audio URL + question
   Time: 6.5s

5. Download audio file:
   - GET audio.opus: 0.5s
   Time: 7s

6. Transcribe audio:
   - Gemini Audio API: 4s
   - Gets: "Download CSV from ... filter values >= cutoff"
   Time: 11s

7. Extract CSV URL from transcript:
   - Regex: < 0.1s
   Time: 11s

8. Download CSV:
   - GET data.csv: 1s
   - Load into pandas: 0.5s
   Time: 12.5s

9. Process data:
   - Filter values >= cutoff: 0.1s
   - Sum: 0.1s
   Time: 12.7s

10. Submit answer:
    - POST to submit: 0.5s
    Time: 13.2s

Total: ~13 seconds ✅ (well under 3 minutes!)
```

---

## 🧠 **Why This Architecture is Strong**

### **1. Flexibility**
- ✅ LLM parses any instruction wording
- ✅ Handles multiple data types
- ✅ Easy to add new task types

### **2. Reliability**
- ✅ Multiple fallbacks for each operation
- ✅ Error handling at every step
- ✅ Graceful degradation

### **3. Speed**
- ✅ Async for parallel operations
- ✅ Fast methods first (regex before LLM)
- ✅ Efficient libraries (pandas, Playwright)

### **4. Maintainability**
- ✅ Modular design (easy to change one part)
- ✅ Clear separation of concerns
- ✅ Well-documented

---

## 🎓 **Summary: The Mental Model**

Think of your app as a **smart robot assistant**:

1. **Receives task** (API endpoint)
2. **Opens browser** (Playwright)
3. **Reads instructions** (Parser)
4. **Fetches data** (Processors)
5. **Thinks** (LLM)
6. **Submits answer** (HTTP POST)
7. **Repeats** (Loop)

Each component is **independent** but works together through **clear interfaces**.

---

**Ready to add new features? Now you understand the foundation!** 🚀

Questions about any specific part?

