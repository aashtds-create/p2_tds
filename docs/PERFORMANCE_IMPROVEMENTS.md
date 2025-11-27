# Performance Improvements for 1-Hour Timed Test

## Critical Speed Optimizations

### 1. Reduce Playwright Overhead
**Problem:** Browser initialization takes 5-10 seconds per question
**Solution:** Reuse browser instance across all questions

```python
# Current: New browser for each page
async def render(self, url: str):
    await self._init_browser()  # Slow!
    page = await self.browser.new_page()
    
# Improved: Keep browser alive, just new pages
# Already implemented in renderer.py - just need to NOT close browser
```

**Impact:** Save 5-10 seconds per question → Extra 6-12 questions in 1 hour!

---

### 2. Parallel Processing Where Possible
**Problem:** Sequential processing is slow
**Solution:** Download multiple resources simultaneously

```python
# Current: Sequential
audio = await download_audio(url)
csv = await download_csv(url)

# Improved: Parallel
audio, csv = await asyncio.gather(
    download_audio(url),
    download_csv(url)
)
```

**Impact:** Save 2-5 seconds per multi-resource question

---

### 3. Skip Vision When Text Extraction Works
**Problem:** Gemini Vision is slow (4-8 seconds)
**Solution:** Only use vision as fallback

```python
# Already implemented!
if len(content.strip()) < 50:
    logger.warning("Trying vision extraction...")
    canvas_content = await self._extract_canvas_content(page)
```

**Impact:** Save 4-8 seconds on most questions

---

### 4. Reduce LLM Calls
**Problem:** Each LLM call = 2-5 seconds + rate limit risk
**Solution:** Better regex parsing, computational solvers

**Priority:**
1. Regex patterns for common formats (already implemented)
2. Computational solvers for math puzzles (already implemented)
3. Only use LLM when truly needed

**Impact:** Save 2-5 seconds per question

---

### 5. Optimize CSV Processing
**Problem:** Loading huge CSVs into memory
**Solution:** Stream processing for large files

```python
# If CSV > 10MB, use chunked reading
if file_size > 10_000_000:
    for chunk in pd.read_csv(url, chunksize=10000):
        # Process incrementally
```

**Impact:** Handle larger datasets without timeout

---

## Speed Target

**Current average:** ~60 seconds per question (3-task chain)
**Target:** ~30-40 seconds per question
**Result:** Solve 60-90 questions in 1 hour (instead of 30-40)

---

## Quick Wins (Implement First)

1. ✅ Keep browser instance alive (don't restart each time)
2. ✅ Use asyncio.gather() for parallel downloads
3. ✅ Add timeout shortcuts (if > 50s on one question, submit best guess and move on)
4. ✅ Cache common patterns (e.g., submit URL is always /submit)

