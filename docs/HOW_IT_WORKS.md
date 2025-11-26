# 🎓 How Your App Works: Complete Explanation

## 📌 **Quick Overview**

Your app follows this flow:
```
POST /quiz → Validate → Render Page → Parse → Execute → Submit → Loop
```

Let's understand each part with actual code examples!

---

## 1️⃣ **Entry Point: API Endpoint**

### **What Happens When Professor Sends Request?**

```python
# Professor sends:
POST http://your-server.com/quiz
{
  "email": "student@iitm.ac.in",
  "secret": "your_secret",
  "url": "https://quiz-server.com/quiz-1"
}
```

### **Your Code Handles It:**

**File:** `src/api/endpoint.py` (lines 53-85)

```python
@app.post("/quiz")
async def handle_quiz(request: QuizRequest):
    # Step 1: Verify secret (line 66)
    if not verify_secret(request.secret):
        raise HTTPException(status_code=403)
    
    # Step 2: Set deadline - 3 minutes from now (line 76)
    deadline = datetime.now() + timedelta(minutes=3)
    
    # Step 3: Start async task - DON'T WAIT (line 80)
    asyncio.create_task(solve_quiz_async(...))
    
    # Step 4: Return 200 immediately (line 82)
    return {"status": "accepted", "message": "processing..."}
```

### **Why This Design?**

**🚫 Wrong way (blocking):**
```python
@app.post("/quiz")
async def handle_quiz(request):
    result = await solve_quiz(...)  # Professor waits 40+ seconds!
    return result
```

**✅ Right way (non-blocking):**
```python
@app.post("/quiz")
async def handle_quiz(request):
    asyncio.create_task(solve_quiz(...))  # Background task
    return immediately  # Professor gets 200 in < 1s
```

**Benefits:**
- Professor's server doesn't timeout
- Your app can take 40+ seconds to solve
- Follows async best practices

---

## 2️⃣ **Background Task Starts**

### **What Happens After Returning 200?**

**File:** `src/api/endpoint.py` (lines 88-100)

```python
async def solve_quiz_async(url, secret, email, deadline):
    try:
        # Create solver instance
        solver = QuizSolver(secret=secret, email=email, deadline=deadline)
        
        # Start solving (this takes 40+ seconds)
        await solver.solve(url)
        
        logger.info("Quiz completed!")
    except Exception as e:
        logger.error(f"Error: {e}")
```

**This function runs in background while your API is free to accept new requests!**

---

## 3️⃣ **Quiz Solver: The Main Orchestrator**

### **The Solver's Job:**

**File:** `src/quiz_solver/solver.py`

Let me explain the key logic:

```python
class QuizSolver:
    async def solve(self, initial_url):
        current_url = initial_url
        
        # Loop through quiz pages
        while current_url:
            # 1. Visit page and render JavaScript
            page_content = await self._render_page(current_url)
            
            # 2. Parse instructions
            task = await self._parse_instructions(page_content)
            
            # 3. Execute the task (fetch data, process, etc.)
            answer = await self._execute_task(task)
            
            # 4. Submit answer
            result = await self._submit_answer(current_url, answer)
            
            # 5. Check if correct
            if result['correct']:
                current_url = result.get('url')  # Next page
            else:
                # Retry or move to next
                current_url = result.get('url')
```

### **Why a While Loop?**

Professor's quiz is **chained**:
```
/quiz-1 (correct) → /quiz-2 (correct) → /quiz-3 (correct) → Done!
```

Your app automatically follows the chain until `url` is `null`.

---

## 4️⃣ **Page Renderer: Handling JavaScript**

### **The Problem:**

Professor's quiz uses JavaScript:
```html
<script>
  document.getElementById("content").innerHTML = atob("encoded_text");
</script>
```

Regular `requests.get()` won't execute JavaScript!

### **The Solution: Playwright**

**File:** `src/quiz_solver/renderer.py`

```python
class PageRenderer:
    async def render(self, url):
        # 1. Launch real Chrome browser (headless)
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 2. Navigate to URL
        await page.goto(url, wait_until='networkidle')
        
        # 3. JavaScript executes automatically!
        # 4. Extract rendered content
        text = await page.inner_text('body')
        
        # 5. Find media files (audio, PDF, etc.)
        audio_urls = await page.evaluate('''
            Array.from(document.querySelectorAll('audio'))
                 .map(el => el.src)
        ''')
        
        pdf_urls = await page.evaluate('''
            Array.from(document.querySelectorAll('a[href$=".pdf"]'))
                 .map(el => el.href)
        ''')
        
        # 6. Combine everything
        full_content = text + f"\n[MEDIA FILES FOUND]\n{audio_urls}\n{pdf_urls}"
        
        return full_content
```

### **Why This Works:**

1. **Real browser**: Executes JavaScript like a human browsing
2. **Waits for loading**: `networkidle` = all network requests done
3. **Extracts everything**: Text + media URLs
4. **Reliable**: Industry-standard tool

---

## 5️⃣ **Instruction Parser: Understanding the Task**

### **What the Parser Does:**

Takes messy HTML/text and extracts:
- **Question**: "What is the sum of values in column X?"
- **Data source**: "https://example.com/data.csv"
- **Task type**: "csv", "pdf", "audio", "scraping", etc.

### **Two-Strategy Approach:**

**File:** `src/quiz_solver/parser.py`

#### **Strategy 1: Regex (Fast)**

```python
def _regex_parse(self, content):
    # Extract URLs
    urls = re.findall(r'https?://[^\s<>"]+', content)
    
    # Detect task type
    if '.pdf' in content.lower():
        task_type = 'pdf'
    elif '.csv' in content.lower():
        task_type = 'csv'
    elif 'audio' in content.lower() or '.opus' in content.lower():
        task_type = 'audio'
    # ... more patterns
    
    return {' question': ..., 'source': urls[0], 'type': task_type}
```

**Pros:** Fast (microseconds)
**Cons:** Brittle (only works for simple patterns)

#### **Strategy 2: LLM (Flexible)**

```python
async def _llm_parse(self, content):
    prompt = f"""
    Parse this quiz instruction and extract:
    
    1. Question being asked
    2. Data source URL (if any)
    3. Task type (api/scraping/pdf/csv/audio)
    
    Content:
    {content}
    
    Return as JSON.
    """
    
    response = await llm_client.generate(prompt)
    return parse_json(response)
```

**Pros:** Flexible (handles any wording)
**Cons:** Slower (2-3 seconds)

### **Why Use Both?**

```python
# Try fast method first
result = regex_parse(content)
if result.is_complete():
    return result  # Got everything, fast!

# Fall back to smart method
return await llm_parse(content)  # Flexible but slower
```

Best of both worlds! ⚡🧠

---

## 6️⃣ **Task Executor: Routing to Handlers**

### **The Router:**

**File:** `src/quiz_solver/executor.py`

```python
class TaskExecutor:
    async def execute(self, task, base_url):
        # Route based on task type
        if task['type'] == 'api':
            return await self._handle_api_task(task)
        
        elif task['type'] == 'scraping':
            return await self._handle_scraping_task(task, base_url)
        
        elif task['type'] == 'pdf':
            return await self._handle_pdf_task(task)
        
        elif task['type'] == 'csv':
            return await self._handle_csv_task(task)
        
        elif task['type'] == 'audio':
            return await self._handle_audio_task(task, base_url)
        
        else:
            # Fallback: Send to LLM
            return await self._handle_with_llm(task)
```

### **Example: Audio Task Handler**

```python
async def _handle_audio_task(self, task, base_url):
    # 1. Download audio
    audio_url = task['source']
    audio_bytes = await httpx.get(audio_url).content
    
    # 2. Transcribe (Gemini Audio API)
    transcript = await self.audio_processor.process(audio_bytes, audio_url)
    # Result: "Download CSV from https://...data.csv and sum values >= 100"
    
    # 3. Extract CSV URL from transcript
    csv_url = extract_url(transcript['text'])
    
    # 4. Download & process CSV
    csv_df = await self.csv_processor.process(csv_url)
    
    # 5. Extract cutoff value
    cutoff = extract_number(transcript['text'], pattern=r'>=\s*(\d+)')
    
    # 6. Filter and sum
    filtered = csv_df[csv_df.iloc[:, 0] >= cutoff]
    answer = filtered.iloc[:, 0].sum()
    
    return answer
```

### **Why This Design?**

Each handler is **independent**:
- Easy to test
- Easy to modify
- Easy to add new task types

---

## 7️⃣ **Audio Processor: The Smart Part**

### **The Challenge:**

Audio task involves:
1. Transcribe audio (speech → text)
2. Understand instructions in transcript
3. Download data file
4. Process data
5. Calculate answer

### **Your Solution:**

**File:** `src/data_processing/audio_processor.py`

```python
class AudioProcessor:
    async def process(self, audio_bytes, audio_url):
        # Priority 1: Gemini Audio API (Fast & Reliable)
        try:
            return await self._transcribe_with_gemini(audio_bytes, audio_url)
        except Exception as e:
            logger.warning(f"Gemini failed: {e}")
        
        # Priority 2: SpeechRecognition (Free Backup)
        try:
            return await self._transcribe_with_speech_recognition(audio_bytes)
        except:
            logger.info("SpeechRecognition not available")
        
        # Priority 3: Local Whisper (Slow but Always Works)
        return await self._transcribe_with_local_whisper(audio_bytes)
```

### **Gemini Transcription (Primary Method):**

```python
async def _transcribe_with_gemini(self, audio_bytes, audio_url):
    # 1. Detect audio format from URL
    mime_type = "audio/opus" if audio_url.endswith('.opus') else "audio/mpeg"
    
    # 2. Encode audio as base64
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    
    # 3. Create multimodal request
    request = {
        "contents": [{
            "parts": [
                # Part 1: Audio data
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": audio_base64
                    }
                },
                # Part 2: Instruction
                {
                    "text": "Transcribe this audio. Return only the text."
                }
            ]
        }]
    }
    
    # 4. Call Gemini API
    response = await gemini_api.generate_content(request)
    
    # 5. Extract text
    return response['candidates'][0]['content']['parts'][0]['text']
```

### **Why Gemini?**

| Feature | Gemini | Local Whisper |
|---------|--------|---------------|
| Speed | 4-5s | 50s |
| Accuracy | High | High |
| API Key | Already have! | None needed |
| Deployment | Easy | Complex |
| Cost | Free tier | Free |

**Winner:** Gemini! ✅

---

## 8️⃣ **LLM Client: The Brain**

### **When LLM is Called:**

1. Parsing instructions (if regex fails)
2. Answering questions about data
3. Understanding complex tasks

### **How it Works:**

**File:** `src/llm/client.py`

```python
class LLMClient:
    async def generate_answer(self, question, data):
        # Build a smart prompt
        prompt = f"""
        You are a data analysis assistant.
        
        Question: {question}
        
        Data:
        {data}
        
        Provide ONLY the direct answer value.
        - If number: return just the number
        - If string: return just the string
        - No explanations
        - No markdown
        - No extra text
        
        Answer:
        """
        
        # Call Gemini
        response = await self._call_gemini_api(prompt)
        
        return response.strip()
```

### **Why Specific Prompt?**

**Early Problem:**
```python
# Question: "What is the sum?"
# Data: [1, 2, 3]
# LLM Response: "The sum of the values is 6."  ❌

# Your code expects: 6
# Result: Wrong answer!
```

**Solution:**
```python
prompt += "Return ONLY the answer value. No explanations."
# LLM Response: "6"  ✅
```

---

## 9️⃣ **Submitting Answer**

### **Final Step:**

**File:** `src/quiz_solver/solver.py`

```python
async def _submit_answer(self, quiz_url, answer):
    # 1. Build payload
    payload = {
        "email": self.email,
        "secret": self.secret,
        "url": quiz_url,
        "answer": answer  # Could be number, string, JSON, base64
    }
    
    # 2. POST to submit endpoint
    response = await httpx.post(submit_url, json=payload)
    
    # 3. Parse response
    result = response.json()
    # {
    #   "correct": true/false,
    #   "url": "next_quiz_url" or null,
    #   "reason": "explanation if wrong"
    # }
    
    # 4. Log result
    if result['correct']:
        logger.info("✅ Answer correct!")
    else:
        logger.error(f"❌ Wrong: {result['reason']}")
    
    return result
```

### **Then What?**

```python
# Back in solve() loop:
while current_url:
    answer = solve_one_page(current_url)
    result = submit_answer(answer)
    
    if result['correct']:
        current_url = result.get('url')  # Move to next page
    else:
        # Could retry, but demo just moves on
        current_url = result.get('url')
```

---

## 🔄 **Complete Example: Audio Task**

Let's trace one complete audio task:

```
T=0s: Professor POSTs to /quiz

T=0.1s: Your API returns 200 ✅

T=0.1s: Background task starts:
  solver = QuizSolver()
  solver.solve(url)

T=3s: Playwright renders page with JavaScript
  Content: "Listen to audio.opus and download CSV..."

T=6s: Parser extracts:
  - question: "sum values >= cutoff"
  - source: "https://.../audio.opus"
  - type: "audio"

T=7s: Executor routes to audio handler

T=7.5s: Download audio.opus (0.5s)

T=11.5s: Gemini transcribes (4s)
  Result: "Download CSV from https://.../data.csv
           Pick first column and sum values >= 36274"

T=11.6s: Extract CSV URL from transcript

T=12.5s: Download CSV (1s)

T=13s: Load CSV into pandas (0.5s)

T=13.1s: Filter: df[df.iloc[:, 0] >= 36274]

T=13.2s: Sum: filtered.sum() = 42539047

T=13.3s: Submit answer

T=13.8s: Response: {"correct": true, "url": null}

T=13.8s: Done! ✅
```

**Total time: ~14 seconds** (Well under 3 minutes!)

---

## 🎯 **Key Takeaways**

### **1. Async is Critical**
```python
# Wrong (slow)
def process():
    a = download1()  # wait 2s
    b = download2()  # wait 2s
    # Total: 4s

# Right (fast)
async def process():
    a, b = await asyncio.gather(
        download1(),
        download2()
    )
    # Total: 2s
```

### **2. Fallback Strategy**
```python
try:
    return fast_method()  # Gemini API
except:
    try:
        return medium_method()  # SpeechRecognition
    except:
        return slow_method()  # Local Whisper
```

### **3. LLM as Smart Parser**
```python
# Don't hardcode rules
if "download" in text and "pdf" in text:
    type = "pdf"

# Let LLM understand
type = llm.parse(text)  # Flexible!
```

### **4. Playwright for JS Pages**
```python
# Wrong
html = requests.get(url).text  # No JS execution

# Right
page = browser.new_page()
page.goto(url)  # JS executes!
text = page.inner_text('body')
```

---

## 🧠 **Mental Model**

Your app is like a **smart intern**:

1. **Gets task** (API)
2. **Opens browser** (Playwright)
3. **Reads carefully** (Parser)
4. **Fetches what's needed** (Processors)
5. **Thinks** (LLM)
6. **Submits work** (Answer)
7. **Gets next task** (Loop)

Each component has **one job** and does it well.

---

## 💡 **Design Principles**

1. **Flexibility**: LLM handles variations
2. **Reliability**: Multiple fallbacks
3. **Speed**: Async + fast methods first
4. **Simplicity**: Clear, modular code
5. **Extensibility**: Easy to add features

---

**Now you understand the foundation! Ready to add new features?** 🚀

