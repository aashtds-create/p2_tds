# Test Day Strategy: 1-Hour Timed Evaluation

## 📊 What Professor is Testing

### Skills Breakdown
| Skill Category | Demo | Demo2 | Likely Test Cases |
|----------------|------|-------|-------------------|
| **Web Scraping** | ✅ | ❌ | Dynamic pages, hidden elements, JavaScript |
| **Audio Processing** | ✅ | ❌ | Multiple audio formats, noisy audio, long files |
| **Data Analysis** | ✅ | ❌ | Large CSVs, complex filters, aggregations |
| **Computer Vision** | ❌ | ✅ | Canvas, images, charts, screenshots |
| **Computation** | ❌ | ✅ | Math puzzles, hashing, formulas, sequences |
| **API Integration** | ✅ | ❌ | REST APIs, JSON parsing, authentication |
| **Error Handling** | Both | Both | Malformed data, timeouts, rate limits |

---

## 🎯 Test Format (Based on Professor's Description)

```
Start URL → Solve Q1 → Get URL2 → Solve Q2 → Get URL3 → ...
           (60s)            (45s)            (90s)

Total: 1 hour = 3600 seconds
Estimate: 30-60 questions possible
Goal: Maximize correct answers
```

**Key Insight:** Early questions give next URL even if wrong (learning buffer)

---

## 🚀 Your Current Strengths

✅ **Handles multi-step workflows** (demo passes all 3 tasks)
✅ **Canvas extraction** (Gemini Vision for demo2)
✅ **Computational solving** (SHA1 formulas)
✅ **Audio transcription** (Gemini Audio API)
✅ **CSV processing** (Smart filtering without sending to LLM)
✅ **Robust error handling** (Retry logic, timeouts)
✅ **Deployed and tested** (Production-ready on Render)

---

## ⚠️ Current Weaknesses (Fix Before Test!)

### 1. **Speed** (60s/question is too slow)
**Target:** 30-40s/question
**Fixes:**
- Keep browser alive between questions
- Parallel downloads
- Skip unnecessary LLM calls

### 2. **Timeout Management**
**Problem:** One hard question could waste entire hour
**Fix:** 90s hard limit per question

### 3. **Answer Cleaning**
**Problem:** LLM returns "The answer is 42" instead of "42"
**Fix:** Post-process to extract clean answer

### 4. **Task Type Coverage**
**Problem:** Only handles ~8 task types explicitly
**Fix:** Add more patterns (video, SQL, regex, JSON parsing)

---

## 🛠️ CRITICAL Improvements (Implement TODAY)

### Priority 1: Per-Question Timeout ⏱️
```python
# Add to solver.py
async with asyncio.timeout(90):  # 90s max per question
    answer = await self.executor.execute(instructions)
```
**Why:** Prevent getting stuck
**Impact:** Could be difference between 20 and 50 questions

---

### Priority 2: Keep Browser Alive 🌐
```python
# Modify solver to keep browser open
async def solve_chain(self, start_url):
    try:
        while url:
            next_url = await self.solve(url)
            url = next_url
    finally:
        await self.renderer.close()  # Only close at END
```
**Why:** Save 5-10s per question
**Impact:** Extra 10-15 questions in 1 hour

---

### Priority 3: Answer Cleaning 🧹
```python
# Add to executor before returning answer
answer = self._clean_answer(answer)
```
**Why:** Avoid "secret mismatch" errors
**Impact:** Higher accuracy

---

### Priority 4: More Task Types 🎯
```python
# Expand parser.py
task_types = {
    "video": ["video", "watch", "mp4"],
    "image": ["image", "picture", "ocr"],
    "sql": ["sql", "database", "query"],
    "regex": ["regex", "pattern", "match"],
    "json": ["json", "parse json"],
    # ... etc
}
```
**Why:** Better routing = faster solving
**Impact:** Handle more variety

---

## 📈 Expected Test Progression

### Phase 1: Easy Questions (Q1-10)
- Simple API calls
- Basic scraping
- Clear instructions
**Strategy:** Speed through these, build buffer time

### Phase 2: Medium Questions (Q11-30)
- Audio/video processing
- CSV analysis
- Multi-step workflows
**Strategy:** Use your strong points

### Phase 3: Hard Questions (Q31+)
- Complex computations
- Edge cases
- Unusual formats
**Strategy:** Use timeouts, submit best guess, move on

---

## 🎮 Test Day Playbook

### Before Test Starts
1. ✅ Verify deployment is live
2. ✅ Check Gemini API key is valid (not leaked!)
3. ✅ Test both demo and demo2 pass
4. ✅ Clear any rate limit issues (wait 1 min)
5. ✅ Have Render logs open in another tab

### During Test (1 Hour)
**Minute 0-5:** Submit first question, watch logs
**Minute 5-10:** Check if chain is working smoothly
**Minute 10-50:** Let it run, monitor for errors
**Minute 50-60:** Check progress, debug any stuck questions

### Monitoring Checklist
- [ ] Questions being solved? (watch "Quiz processing completed")
- [ ] Proceeding to next URL? (watch "Proceeding to next URL")
- [ ] Any rate limits? (watch for 429 errors)
- [ ] Any timeouts? (should skip and continue)
- [ ] Submit URL correct? (should be /submit)

---

## 🐛 Common Issues and Fixes

| Issue | Symptom | Fix |
|-------|---------|-----|
| **Rate Limit** | 429 errors | Wait 60s, retry logic handles it |
| **Timeout** | Stuck on one question | 90s timeout kicks in, moves on |
| **Wrong URL** | 405 Method Not Allowed | Fixed (always uses /submit) |
| **Canvas Content** | 0 chars extracted | Vision extraction handles it |
| **LLM Verbose** | "Secret mismatch" | Need answer cleaning (Priority 3) |

---

## 🎯 Success Metrics

**Good Performance:**
- 30+ questions answered
- 70%+ accuracy
- No catastrophic failures

**Excellent Performance:**
- 50+ questions answered
- 80%+ accuracy
- Handled edge cases gracefully

---

## 💡 Last-Minute Tips

1. **Don't over-optimize** - Your app is already strong
2. **Focus on speed** - Implement Priority 1 & 2 above
3. **Trust your fallbacks** - LLM will handle unknowns
4. **Monitor, don't interfere** - Watch logs but let it run
5. **Have backup plan** - If Render fails, know how to restart

---

## 🔗 Quick Links

- **Deployment:** https://p2-tds.onrender.com/quiz
- **Render Logs:** https://dashboard.render.com/
- **Gemini API:** https://aistudio.google.com/apikey
- **Test URL:** https://tds-llm-analysis.s-anand.net/

---

## ✅ Final Checklist Before Test

- [ ] Implement per-question timeout (90s)
- [ ] Implement browser reuse (don't close between questions)
- [ ] Implement answer cleaning
- [ ] Test demo passes
- [ ] Test demo2 passes
- [ ] Test 5-question chain locally (if possible)
- [ ] API key valid and not leaked
- [ ] Deployment live and healthy
- [ ] Logs accessible
- [ ] Backup plan ready

---

**You're ready! Your app has solid foundations. The improvements above will give you the edge to handle more questions faster. Good luck! 🚀**

