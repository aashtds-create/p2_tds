# LLM Analysis Quiz Solver

An automated quiz-solving application that uses AI to parse instructions, scrape data, process multimedia content, and submit answers through a REST API.

## 🎯 Features

- **Multi-modal AI Processing**: Uses Google Gemini 2.5 Flash for text and audio processing
- **Web Scraping**: Playwright-based browser automation for JavaScript-rendered pages
- **Data Processing**: Handles CSV, PDF, and API data sources
- **Audio Transcription**: Gemini Audio API with fallbacks to SpeechRecognition and local Whisper
- **Async Architecture**: FastAPI with asynchronous processing for optimal performance

## 📁 Project Structure

```
project2/
├── src/
│   ├── api/
│   │   └── endpoint.py           # FastAPI server and quiz endpoint
│   ├── data_processing/
│   │   ├── analyzer.py           # Data analysis
│   │   ├── api_client.py         # API data fetching
│   │   ├── audio_processor.py    # Audio transcription (Gemini, SpeechRecognition, Whisper)
│   │   ├── csv_processor.py      # CSV data processing
│   │   ├── pdf_processor.py      # PDF text extraction
│   │   └── scraper.py            # Web scraping
│   ├── llm/
│   │   └── client.py             # LLM client (Gemini API)
│   ├── quiz_solver/
│   │   ├── executor.py           # Task execution router
│   │   ├── parser.py             # Instruction parsing
│   │   ├── renderer.py           # Page rendering (Playwright)
│   │   └── solver.py             # Main quiz solver orchestrator
│   └── utils/
│       └── auth.py               # Authentication utilities
├── docs/
│   ├── GEMINI_AUDIO_SETUP.md     # Audio transcription setup guide
│   ├── PROJECT_GUIDE.md          # Detailed project documentation
│   ├── QUICK_START.md            # Quick start guide
│   └── project_statement.md      # Original assignment requirements
├── tests/
│   ├── test_full_flow.py         # End-to-end tests
│   ├── test_gemini_models.py     # Gemini API tests
│   ├── test_parser.py            # Parser unit tests
│   └── test_renderer.py          # Renderer unit tests
├── .env                          # Environment variables (not in git)
├── .gitignore
├── LICENSE
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Gemini API Key ([Get one here](https://aistudio.google.com/app/apikey))
- FFmpeg (for audio processing): `sudo apt install ffmpeg`

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd project2
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
playwright install chromium
```

4. **Set up environment variables:**
   
   Create `src/.env` file:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

5. **Run the server:**
```bash
   python src/api/endpoint.py
   ```

   Server will start at `http://localhost:8000`

### Usage

Send a POST request to `/quiz` endpoint:

```bash
curl -X POST http://localhost:8000/quiz \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "secret": "your_secret",
    "url": "https://quiz-server.com/quiz"
  }'
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key for text and audio processing | Yes |

### Optional Dependencies

For offline audio transcription, install local Whisper:
```bash
pip install openai-whisper
```

## 📚 Documentation

- **[Quick Start Guide](docs/QUICK_START.md)** - Get started in 5 minutes
- **[Project Guide](docs/PROJECT_GUIDE.md)** - Detailed architecture and concepts
- **[Gemini Audio Setup](docs/GEMINI_AUDIO_SETUP.md)** - Audio transcription configuration
- **[Project Statement](docs/project_statement.md)** - Original assignment requirements

## 🧪 Testing

Run tests:
```bash
# All tests
pytest tests/

# Specific test file
python tests/test_parser.py
```

## 🎯 Performance

- **Quiz completion time**: ~40-50 seconds
- **Audio transcription**: ~4-5 seconds (Gemini API)
- **Web scraping**: ~2-3 seconds per page
- **API calls**: ~2-3 seconds per request

## 🛠️ Tech Stack

- **Backend**: FastAPI, Uvicorn
- **AI/ML**: Google Gemini 2.5 Flash (text + audio)
- **Web Scraping**: Playwright
- **Data Processing**: Pandas, NumPy
- **PDF Processing**: pdfplumber, PyMuPDF
- **Audio**: Gemini Audio API, SpeechRecognition, Whisper (fallback)

## 📦 Dependencies

See [requirements.txt](requirements.txt) for full list.

Key dependencies:
- `fastapi` - Web framework
- `playwright` - Browser automation
- `pandas` - Data processing
- `httpx` - Async HTTP client
- `pdfplumber` - PDF extraction

## 🚢 Deployment

### 🚂 Railway (Recommended)

Railway is the easiest option for deploying this app:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Set environment variables
railway variables set GEMINI_API_KEY=your_key
railway variables set SECRET=your_secret
railway variables set EMAIL=your_email@ds.study.iitm.ac.in
```

Your app will be live at `https://your-project.up.railway.app`!

### 🐳 Docker

The project includes a Dockerfile ready for deployment:

```bash
# Build
docker build -t quiz-solver .

# Run
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your_key \
  -e SECRET=your_secret \
  -e EMAIL=your_email \
  quiz-solver
```

### ⚠️ Why Not Vercel?

Vercel doesn't support Playwright (browser automation) and has strict timeout limits.
Use Railway, Render, or Fly.io instead.

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment guide.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini for multimodal AI capabilities
- FastAPI for the excellent web framework
- Playwright for reliable browser automation
