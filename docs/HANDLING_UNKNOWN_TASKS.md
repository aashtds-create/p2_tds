# Handling Unknown/Novel Task Types

## Philosophy: Graceful Degradation

When your professor throws a curveball:
1. **Try to understand** (parse the question)
2. **Identify the pattern** (what type of task is this?)
3. **Apply the right tool** (computational, scraping, LLM)
4. **If all fails, let LLM try** (Gemini is smart!)
5. **Never crash** (submit best guess and move on)

---

## 🎯 Strategy 1: Enhanced Task Type Detection

### Current Approach (Limited)
```python
if "scrape" in content:
    return "scraping"
elif "audio" in content:
    return "audio"
# Only handles 8-10 types
```

### Improved Approach (Comprehensive)
```python
def _identify_task_type_advanced(self, content: str) -> dict:
    """
    Advanced task detection with confidence scores
    Returns: {"type": "scraping", "confidence": 0.9, "hints": [...]}
    """
    content_lower = content.lower()
    
    # Build feature vector
    features = {
        "has_url": bool(re.search(r'https?://', content)),
        "has_file_extension": bool(re.search(r'\.(csv|pdf|mp3|png|jpg)', content)),
        "has_computation_words": any(w in content_lower for w in 
            ['calculate', 'compute', 'sum', 'count', 'filter', 'hash']),
        "has_extraction_words": any(w in content_lower for w in 
            ['scrape', 'extract', 'get', 'find', 'download']),
        "has_analysis_words": any(w in content_lower for w in 
            ['analyze', 'compare', 'identify', 'determine']),
        "has_code_indicators": bool(re.search(r'SHA\d+|MD5|base64|regex', content)),
        "has_data_words": any(w in content_lower for w in 
            ['data', 'table', 'rows', 'columns', 'records']),
        "has_media_words": any(w in content_lower for w in 
            ['audio', 'video', 'image', 'picture', 'sound']),
    }
    
    # Score different task types
    scores = {}
    
    # Computational tasks
    if features['has_code_indicators'] or features['has_computation_words']:
        scores['computation'] = 0.8
    
    # Scraping tasks
    if features['has_url'] and features['has_extraction_words']:
        scores['scraping'] = 0.9
    
    # Data analysis tasks
    if features['has_file_extension'] and features['has_data_words']:
        scores['data_analysis'] = 0.85
    
    # Media processing tasks
    if features['has_media_words'] and features['has_file_extension']:
        scores['media_processing'] = 0.9
    
    # Return best match with confidence
    if scores:
        best_type = max(scores, key=scores.get)
        return {
            "type": best_type,
            "confidence": scores[best_type],
            "hints": features
        }
    else:
        return {"type": "unknown", "confidence": 0.0, "hints": features}
```

---

## 🎯 Strategy 2: LLM-Assisted Task Planning

### When You Don't Know What to Do
```python
async def plan_task_execution(self, question: str, content: str) -> dict:
    """
    Ask LLM to create an execution plan for unknown tasks
    """
    planning_prompt = f"""
    You are a task planner. Given this quiz question, break it down into steps.
    
    Question: {question}
    Content: {content[:500]}
    
    Return a JSON plan with:
    {{
        "steps": [
            {{"action": "download_file", "target": "url", "reason": "..."}},
            {{"action": "extract_data", "method": "regex", "pattern": "..."}},
            {{"action": "compute", "formula": "...", "reason": "..."}}
        ],
        "expected_output": "number|text|json",
        "complexity": "easy|medium|hard"
    }}
    """
    
    plan = await self.llm_client.chat_completion([
        {"role": "system", "content": "You are a task planning expert."},
        {"role": "user", "content": planning_prompt}
    ], json_mode=True)
    
    return json.loads(plan)
```

---

## 🎯 Strategy 3: Universal Computational Solver

### Handle ANY Mathematical/Programming Task
```python
class UniversalComputationSolver:
    """
    Solves computational tasks by generating and executing Python code
    """
    
    async def solve_by_code_generation(self, question: str, data: dict = None) -> Any:
        """
        Generate Python code to solve the problem, then execute it safely
        """
        code_prompt = f"""
        Generate Python code to solve this problem:
        
        Question: {question}
        Available data: {data}
        
        Requirements:
        - Use only standard library (no external packages except pandas, hashlib, re)
        - Store final answer in variable 'result'
        - Code must be safe (no network calls, no file system access)
        
        Return ONLY the Python code, no explanations.
        """
        
        code = await self.llm_client.chat_completion([
            {"role": "system", "content": "You are a Python code generation expert."},
            {"role": "user", "content": code_prompt}
        ])
        
        # Clean the code
        code = code.replace("```python", "").replace("```", "").strip()
        
        # Execute safely
        try:
            result = await self._execute_safe_code(code, data)
            return result
        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            return None
    
    async def _execute_safe_code(self, code: str, data: dict) -> Any:
        """
        Execute Python code in a restricted environment
        """
        import hashlib
        import re
        import json
        from datetime import datetime
        
        # Create safe globals
        safe_globals = {
            'hashlib': hashlib,
            're': re,
            'json': json,
            'datetime': datetime,
            'data': data,
            'result': None
        }
        
        # Execute code
        exec(code, safe_globals)
        
        # Return result
        return safe_globals.get('result')
```

---

## 🎯 Strategy 4: Smart Resource Detection

### Auto-detect and download ANY resource
```python
async def detect_and_fetch_resources(self, content: str, base_url: str) -> dict:
    """
    Automatically detect and fetch all resources mentioned in content
    """
    resources = {
        'urls': [],
        'files': [],
        'data': {},
        'media': []
    }
    
    # Extract all URLs
    urls = re.findall(r'https?://[^\s<>"]+|/[^\s<>"]+', content)
    
    for url in urls:
        # Resolve relative URLs
        if url.startswith('/'):
            url = urljoin(base_url, url)
        
        # Detect resource type by extension or content-type
        file_ext = url.split('.')[-1].lower()
        
        if file_ext in ['csv', 'xlsx', 'json', 'txt']:
            # Download and parse data file
            data = await self._download_and_parse_data(url)
            resources['data'][url] = data
            
        elif file_ext in ['mp3', 'wav', 'opus', 'm4a']:
            # Download audio
            audio_bytes = await self._download_file(url)
            resources['media'].append({'type': 'audio', 'url': url, 'data': audio_bytes})
            
        elif file_ext in ['png', 'jpg', 'jpeg', 'gif']:
            # Download image
            image_bytes = await self._download_file(url)
            resources['media'].append({'type': 'image', 'url': url, 'data': image_bytes})
            
        elif file_ext in ['pdf']:
            # Download PDF
            pdf_bytes = await self._download_file(url)
            resources['files'].append({'type': 'pdf', 'url': url, 'data': pdf_bytes})
            
        else:
            # Generic URL (might be webpage to scrape)
            resources['urls'].append(url)
    
    return resources
```

---

## 🎯 Strategy 5: Multi-Modal LLM Analysis

### Use Gemini for EVERYTHING it can handle
```python
async def analyze_with_multimodal_llm(self, question: str, resources: dict) -> Any:
    """
    Send question + all resources to Gemini for analysis
    """
    # Build multimodal request
    parts = [{"text": f"Question: {question}\n\nAnalyze and answer:"}]
    
    # Add text data
    for url, data in resources['data'].items():
        if isinstance(data, str):
            parts.append({"text": f"\n\nData from {url}:\n{data[:1000]}"})
    
    # Add images
    for media in resources['media']:
        if media['type'] == 'image':
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(media['data']).decode()
                }
            })
    
    # Add audio
    for media in resources['media']:
        if media['type'] == 'audio':
            parts.append({
                "inline_data": {
                    "mime_type": "audio/mpeg",
                    "data": base64.b64encode(media['data']).decode()
                }
            })
    
    # Send to Gemini
    response = await self._call_gemini_multimodal(parts)
    return response
```

---

## 🎯 Strategy 6: Confidence-Based Decision Making

### Try multiple approaches, pick best result
```python
async def solve_with_confidence(self, question: str, content: str) -> dict:
    """
    Try multiple solving strategies, return result with highest confidence
    """
    results = []
    
    # Strategy 1: Computational solver
    try:
        comp_result = await self.computation_solver.solve(content, self.email)
        if comp_result:
            results.append({
                'answer': comp_result,
                'confidence': 0.95,
                'method': 'computational'
            })
    except Exception as e:
        logger.warning(f"Computational solver failed: {e}")
    
    # Strategy 2: Direct LLM
    try:
        llm_result = await self.llm_client.solve_task(question, content)
        if llm_result:
            results.append({
                'answer': llm_result,
                'confidence': 0.7,
                'method': 'llm_direct'
            })
    except Exception as e:
        logger.warning(f"LLM solver failed: {e}")
    
    # Strategy 3: Code generation
    try:
        code_result = await self.universal_solver.solve_by_code_generation(question)
        if code_result:
            results.append({
                'answer': code_result,
                'confidence': 0.8,
                'method': 'code_generation'
            })
    except Exception as e:
        logger.warning(f"Code generation failed: {e}")
    
    # Pick result with highest confidence
    if results:
        best_result = max(results, key=lambda x: x['confidence'])
        logger.info(f"Best solution: {best_result['method']} (confidence: {best_result['confidence']})")
        return best_result['answer']
    else:
        logger.error("All solving strategies failed")
        return None
```

---

## 🎯 Strategy 7: Learning from Errors

### Track what works and what doesn't
```python
class TaskLearner:
    """
    Learn from successful/failed attempts to improve over time
    """
    
    def __init__(self):
        self.success_patterns = {}
        self.failure_patterns = {}
    
    def record_success(self, task_type: str, method: str, question_features: dict):
        """Record a successful solve"""
        key = f"{task_type}_{method}"
        if key not in self.success_patterns:
            self.success_patterns[key] = []
        self.success_patterns[key].append(question_features)
    
    def record_failure(self, task_type: str, method: str, question_features: dict, error: str):
        """Record a failed solve"""
        key = f"{task_type}_{method}"
        if key not in self.failure_patterns:
            self.failure_patterns[key] = []
        self.failure_patterns[key].append({
            'features': question_features,
            'error': error
        })
    
    def suggest_method(self, question_features: dict) -> str:
        """Suggest best method based on past successes"""
        scores = {}
        for key, patterns in self.success_patterns.items():
            # Calculate similarity to past successful patterns
            similarity = self._calculate_similarity(question_features, patterns)
            scores[key] = similarity
        
        if scores:
            return max(scores, key=scores.get).split('_')[1]
        return "llm_direct"  # Default
```

---

## 📋 Implementation Priority

### What to Build NOW (Before Test)

**Priority 1: Universal Fallback (30 min)**
```python
# In executor.py
async def handle_unknown_task(self, question: str, content: str) -> Any:
    """
    When no specific handler matches, try everything
    """
    # 1. Try computational
    # 2. Try code generation
    # 3. Try multimodal LLM
    # 4. Return best guess
```

**Priority 2: Better Resource Detection (20 min)**
```python
# Auto-detect and fetch ALL resources in page
resources = await self.detect_and_fetch_resources(content, base_url)
```

**Priority 3: Improved LLM Prompting (15 min)**
```python
# Give LLM MORE context and CLEARER instructions
```

---

## 🎓 Example: Handling Novel Task Types

### Professor's Creative Questions

**Example 1: "Find the Fibonacci number mentioned in this audio file, then compute its prime factors"**
- ✅ Audio transcription (you have)
- ✅ Number extraction (regex)
- 🆕 Prime factorization (need computational solver)

**Example 2: "Scrape this webpage, extract all email addresses, and return them sorted by domain"**
- ✅ Scraping (you have)
- ✅ Regex for emails (easy to add)
- ✅ Sorting logic (Python)

**Example 3: "Download the image, use OCR to extract text, then solve the math equation"**
- 🆕 Image OCR (Gemini Vision can do this!)
- ✅ Math solving (computational solver)

**Example 4: "Merge these two CSVs, filter by condition X, and return the average"**
- ✅ CSV download (you have)
- ✅ Pandas operations (easy to add)

---

## 🚀 Quick Win: Universal Handler

Let me add a universal handler RIGHT NOW:

