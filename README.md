# 🧮 JEE Math AI - Intelligent Mathematics Problem Solver

<div align="center">

![JEE Math AI](https://img.shields.io/badge/JEE-Math_AI-blue?style=for-the-badge)
![Next.js](https://img.shields.io/badge/Next.js-14-black?style=for-the-badge&logo=next.js)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue?style=for-the-badge&logo=typescript)
![API Version](https://img.shields.io/badge/API-v1.0.0-green?style=for-the-badge)

**An AI-powered full-stack application for solving JEE Mathematics problems with multimodal input support and human-in-the-loop learning.**

[Features](#-features) • [Demo](#-demo) • [Installation](#-installation) • [API Docs](#-api-documentation) • [Contributing](#-contributing)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

JEE Math AI is a production-ready, full-stack application designed to help JEE (Joint Entrance Examination) aspirants solve complex mathematics problems. It leverages OpenAI's GPT-4, Vision, and Whisper APIs to provide step-by-step solutions through multiple input modalities.

### Key Highlights

- 🎨 **Modern Dark UI** - Beautiful, responsive interface with shades of black
- 🤖 **Multi-Agent System** - Specialized AI agents for parsing, routing, solving, and verification
- 📸 **Multimodal Input** - Text, images, and voice recordings
- 🧠 **RAG Pipeline** - Retrieval-Augmented Generation for enhanced accuracy
- 👤 **HITL Support** - Human-in-the-loop for quality assurance
- 💾 **Session Management** - Track and revisit previous problems
- ⚡ **Real-time Processing** - Fast, efficient problem solving

---

## ✨ Features

### Core Functionality

| Feature | Description |
|---------|-------------|
| **Text Upload** | Type or paste mathematical problems directly |
| **Image Upload** | Upload photos of handwritten or printed problems |
| **Voice Input** | Speak your question and get it transcribed automatically |
| **Step-by-Step Solutions** | Detailed explanations with formulas and reasoning |
| **Math Rendering** | LaTeX/KaTeX support for proper equation display |
| **Session History** | Access previous questions and solutions |
| **Feedback System** | Rate solutions and flag incorrect answers |
| **HITL Review** | Human review for flagged or low-confidence solutions |

### Advanced Features

- 🔄 **Auto-transcription** for audio files using Whisper API
- 🎯 **Problem type detection** (algebra, calculus, geometry, etc.)
- 📊 **Confidence scoring** for AI-generated solutions
- 🔍 **Solution verification** through multi-agent validation
- 📱 **Responsive design** for mobile and desktop
- 🌙 **Dark mode** by default for reduced eye strain

---

## 🛠 Tech Stack

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript 5.0
- **Styling:** Tailwind CSS 3.3
- **UI Components:** Lucide React (icons)
- **Math Rendering:** KaTeX + react-markdown
- **HTTP Client:** Axios
- **Package Manager:** pnpm

### Backend (Python FastAPI)
- **Framework:** FastAPI
- **Runtime:** Python 3.10+
- **Server:** Uvicorn (ASGI)
- **Database:** Supabase (PostgreSQL)
- **AI/ML:** 
  - Google Gemini (via google-generativeai)
  - LangGraph for multi-agent orchestration
  - LangChain for RAG pipeline
- **File Handling:** python-multipart
- **Validation:** Pydantic
- **HTTP Client:** httpx

### Multi-Agent System
- **LangGraph:** Agent orchestration and workflow
- **LangChain Community:** RAG and embeddings
- **Agents:**
  - Parser Agent (text/image/audio extraction)
  - Intent Router Agent (problem classification)
  - Solver Agent (solution generation)
  - Verifier Agent (solution validation)
  - Explainer Agent (step-by-step formatting)

### Services
- **OCR/ASR Service:** Image and audio processing
- **RAG Service:** Retrieval-Augmented Generation
- **Memory Service:** Session and context management
- **File Service:** Upload and storage handling

### DevOps
- **Containerization:** Docker + Docker Compose
- **Backend Deployment:** Railway / Render / AWS
- **Frontend Deployment:** Vercel
- **Database:** Supabase (managed PostgreSQL)
- **CI/CD:** GitHub Actions
- **API Testing:** Postman collection included

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Frontend (Next.js + TypeScript)             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │   Text     │  │   Image    │  │   Voice    │            │
│  │   Input    │  │   Upload   │  │   Input    │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
                           │
                      HTTPS/REST API
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend (Python FastAPI + Uvicorn)              │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              LangGraph Multi-Agent System              │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐   │  │
│  │  │ Parser  │→│ Router  │→│ Solver  │→│ Verifier │   │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └──────────┘   │  │
│  │                      ↓                                │  │
│  │                 ┌──────────┐                          │  │
│  │                 │Explainer │                          │  │
│  │                 └──────────┘                          │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Upload    │  │   Solve    │  │    HITL    │            │
│  │  Routes    │  │   Routes   │  │   Routes   │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│                                                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ OCR/ASR    │  │    RAG     │  │   Memory   │            │
│  │  Service   │  │  Service   │  │  Service   │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
           │              │              │
           ▼              ▼              ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Supabase   │  │Google Gemini │  │File Storage  │
│ (PostgreSQL) │  │   Vision     │  │  (Supabase)  │
│              │  │   + Flash    │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Multi-Agent Workflow

```
User Input (Text/Image/Audio)
        ↓
┌─────────────────┐
│ Parser Agent    │ - Extracts problem from input
│ (Gemini Vision) │ - OCR for images, ASR for audio
└────────┬────────┘
         ↓
┌─────────────────┐
│ Intent Router   │ - Classifies problem type
│                 │ - Routes to appropriate solver
└────────┬────────┘
         ↓
┌─────────────────┐
│ Solver Agent    │ - Generates solution steps
│ (Gemini Flash)  │ - Uses RAG for context
└────────┬────────┘
         ↓
┌─────────────────┐
│ Verifier Agent  │ - Validates solution
│                 │ - Checks for errors
└────────┬────────┘
         ↓
┌─────────────────┐
│ Explainer Agent │ - Formats output
│                 │ - Adds explanations
└────────┬────────┘
         ↓
    Final Solution
```

---

## 📦 Installation

### Prerequisites

**Frontend:**
- Node.js 18+ and pnpm
- React/Next.js knowledge

**Backend:**
- Python 3.10+
- pip (Python package manager)
- Supabase account ([Get here](https://supabase.com))
- Google AI API key ([Get here](https://makersuite.google.com/app/apikey))

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/jee-math-ai.git
cd jee-math-ai

# 2. Set up Backend (Python FastAPI)
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp ../.env.example .env
# Edit .env and add your API keys:
# - GOOGLE_API_KEY
# - SUPABASE_URL
# - SUPABASE_KEY

# Run backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Backend runs at http://localhost:8000

# 3. Set up Frontend (Next.js) - In a new terminal
cd frontend

# Install dependencies
pnpm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local and add:
# - NEXT_PUBLIC_API_URL=http://localhost:8000

# Run frontend
pnpm dev

# Frontend runs at http://localhost:3000
```

### Docker Setup (Easier)

```bash
# Start all services (backend + frontend)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Access the app at **http://localhost:3000**  
API docs at **http://localhost:8000/docs**

---

## ⚙️ Configuration

### Backend Environment Variables

Create a `.env` file in the root directory:

```env
# Google AI (Required)
GOOGLE_API_KEY=your_google_api_key_here

# Supabase (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

# Server Configuration
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development

# File Upload Configuration
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=./uploads

# AI Model Configuration
GEMINI_MODEL=gemini-1.5-flash
GEMINI_VISION_MODEL=gemini-1.5-pro-vision

# RAG Configuration (Optional)
ENABLE_RAG=true
VECTOR_STORE=supabase
```

### Frontend Environment Variables

Create `.env.local` in the `frontend/` directory:

```env
# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Environment
NODE_ENV=development
```

### Production Configuration

#### Backend (.env)
```env
GOOGLE_API_KEY=prod_google_api_key
SUPABASE_URL=https://your-prod-project.supabase.co
SUPABASE_KEY=prod_supabase_key
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000
```

#### Frontend (.env.production)
```env
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_WS_URL=wss://api.your-domain.com
```

### Supabase Setup

1. **Create Supabase Project**
   - Go to [supabase.com](https://supabase.com)
   - Create new project
   - Get your project URL and keys

2. **Set Up Database Tables**
   ```sql
   -- Sessions table
   CREATE TABLE sessions (
     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
     session_id TEXT UNIQUE NOT NULL,
     upload_type TEXT NOT NULL,
     status TEXT NOT NULL,
     created_at TIMESTAMPTZ DEFAULT NOW(),
     updated_at TIMESTAMPTZ DEFAULT NOW()
   );

   -- Solutions table
   CREATE TABLE solutions (
     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
     session_id TEXT REFERENCES sessions(session_id),
     solution JSONB NOT NULL,
     confidence FLOAT,
     created_at TIMESTAMPTZ DEFAULT NOW()
   );

   -- Feedback table
   CREATE TABLE feedback (
     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
     session_id TEXT REFERENCES sessions(session_id),
     rating INTEGER,
     is_correct BOOLEAN,
     comments TEXT,
     created_at TIMESTAMPTZ DEFAULT NOW()
   );
   ```

3. **Enable Storage**
   - Create a bucket named `uploads`
   - Set public access for uploaded files

See [ENV_CONFIG.md](./ENV_CONFIG.md) for complete configuration guide.

---

## 🚀 Usage

### Basic Workflow

1. **Upload a Problem**
   - Type: Enter your math problem in the text box
   - Image: Click 📎 to upload an image of the problem
   - Voice: Click 🎤 to record your question

2. **Get Solution**
   - AI processes your input
   - Displays step-by-step solution with formulas
   - Shows confidence score

3. **Provide Feedback**
   - Click 👍 for correct solutions
   - Click 👎 for incorrect solutions
   - Helps improve the AI system

4. **Review History**
   - Access previous questions from sidebar
   - Sessions are saved automatically
   - Click to reload any past problem

### Example Problems

```
Text Input:
"Solve the quadratic equation: x² + 5x + 6 = 0"

Image Upload:
[Upload photo of handwritten calculus problem]

Voice Input:
"What is the derivative of sine x times cosine x?"
```

---

## 📚 API Documentation

### Base URL

```
Development: http://localhost:8000/api/v1
Production:  https://api.your-domain.com/api/v1
```

### Interactive API Docs

FastAPI provides automatic interactive documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Quick Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload/image` | POST | Upload image with math problem |
| `/upload/audio` | POST | Upload audio recording |
| `/upload/text` | POST | Upload text problem |
| `/upload/{session_id}` | GET | Get upload status |
| `/solve` | POST | Solve uploaded problem |
| `/solve/{session_id}` | GET | Get solution status |
| `/solve/{session_id}/feedback` | POST | Submit feedback |
| `/session` | GET | List all sessions |
| `/session/{session_id}` | GET | Get session details |
| `/session/{session_id}` | DELETE | Delete session |
| `/hitl/decide` | POST | Submit HITL decision |
| `/hitl/{session_id}/status` | GET | Get HITL status |
| `/hitl/{session_id}/history` | GET | Get HITL history |
| `/health` | GET | Health check |

### Example Request (Python)

```python
import requests

# Upload text problem
response = requests.post(
    "http://localhost:8000/api/v1/upload/text",
    json={"text": "Find the integral of x² from 0 to 5"}
)

data = response.json()
session_id = data["session_id"]

# Solve problem
response = requests.post(
    "http://localhost:8000/api/v1/solve",
    json={
        "session_id": session_id,
        "require_steps": True
    }
)

solution = response.json()
print(solution["solution"])
```

### Example Request (cURL)

```bash
# Upload text problem
curl -X POST http://localhost:8000/api/v1/upload/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Find the integral of x² from 0 to 5"}'

# Response
{
  "success": true,
  "session_id": "abc-123-xyz",
  "message": "Text uploaded successfully",
  "timestamp": "2026-03-09T10:30:00.000Z"
}

# Solve problem
curl -X POST http://localhost:8000/api/v1/solve \
  -H "Content-Type: application/json" \
  -d '{"session_id": "abc-123-xyz", "require_steps": true}'
```

### Example Request (JavaScript/Frontend)

```javascript
// Upload and solve
const response = await axios.post('http://localhost:8000/api/v1/upload/text', {
  text: 'Solve x² + 5x + 6 = 0'
});

const { session_id } = response.data;

const solution = await axios.post('http://localhost:8000/api/v1/solve', {
  session_id,
  require_steps: true
});

console.log(solution.data);
```

**Full API Documentation:** [API.md](./API.md)  
**Postman Collection:** [JEE_Math_AI.postman_collection.json](./JEE_Math_AI.postman_collection.json)

---

## 📁 Project Structure

```
jee-math-ai/
├── backend/                    # Python FastAPI Backend
│   ├── agents/                 # Multi-Agent System
│   │   ├── parser_agent.py     # Input parsing (text/image/audio)
│   │   ├── intent_router_agent.py  # Problem classification
│   │   ├── solver_agent.py     # Solution generation
│   │   ├── verifier_agent.py   # Solution validation
│   │   ├── explainer_agent.py  # Output formatting
│   │   └── graph.py            # LangGraph workflow
│   ├── api/                    # API Routes
│   │   ├── upload.py           # File upload endpoints
│   │   ├── solve.py            # Problem solving endpoints
│   │   ├── hitl.py             # HITL endpoints
│   │   └── session.py          # Session management
│   ├── core/                   # Core Configuration
│   │   ├── config.py           # App settings
│   │   ├── gemini_client.py    # Google AI client
│   │   └── supabase_client.py  # Database client
│   ├── models/                 # Data Models
│   │   ├── domain.py           # Domain models
│   │   ├── schemas.py          # Pydantic schemas
│   │   └── database.py         # DB models
│   ├── services/               # Business Logic
│   │   ├── ocr_asr_service.py  # OCR/ASR processing
│   │   ├── rag_service.py      # RAG pipeline
│   │   ├── memory_service.py   # Context management
│   │   └── file_service.py     # File handling
│   ├── utils/                  # Utilities
│   │   ├── logger.py           # Logging
│   │   ├── validators.py       # Validation
│   │   ├── formatters.py       # Output formatting
│   │   └── exceptions.py       # Custom exceptions
│   ├── main.py                 # FastAPI app entry
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile              # Backend container
│
├── frontend/                   # Next.js Frontend
│   ├── app/                    # Next.js App Router
│   │   ├── page.tsx            # Home page
│   │   ├── layout.tsx          # Root layout
│   │   └── globals.css         # Global styles
│   ├── components/             # React Components
│   │   └── JEEMathChatbot.tsx  # Main chat UI
│   ├── public/                 # Static assets
│   ├── package.json            # Node dependencies
│   ├── tsconfig.json           # TypeScript config
│   ├── tailwind.config.ts      # Tailwind config
│   └── Dockerfile              # Frontend container
│
├── .github/                    # GitHub Configuration
│   └── workflows/
│       └── deploy.yml          # CI/CD pipeline
│
├── docker-compose.yml          # Multi-container setup
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

---

## 🌐 Deployment

### Frontend Deployment (Vercel)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push -u origin main
   ```

2. **Deploy Frontend to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Set root directory to `frontend/`
   - Add environment variable:
     - `NEXT_PUBLIC_API_URL=https://your-api-domain.com`
   - Deploy

### Backend Deployment

#### Option 1: Railway (Recommended)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
cd backend
railway init

# Add environment variables in Railway dashboard:
# - GOOGLE_API_KEY
# - SUPABASE_URL
# - SUPABASE_KEY

# Deploy
railway up
```

#### Option 2: Render

1. Create new **Web Service** on [render.com](https://render.com)
2. Connect GitHub repository
3. Settings:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables
5. Deploy

#### Option 3: AWS EC2

```bash
# SSH into EC2 instance
ssh -i key.pem ubuntu@your-ec2-ip

# Install Python and dependencies
sudo apt update
sudo apt install python3-pip python3-venv

# Clone repo
git clone your-repo-url
cd jee-math-ai/backend

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up environment variables
nano .env
# Add all required variables

# Run with Gunicorn (production)
pip install gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Set up Nginx reverse proxy
sudo apt install nginx
# Configure nginx to proxy to port 8000
```

### Docker Deployment

```bash
# Build and push images
docker build -t your-registry/jee-math-backend:latest ./backend
docker build -t your-registry/jee-math-frontend:latest ./frontend

docker push your-registry/jee-math-backend:latest
docker push your-registry/jee-math-frontend:latest

# Deploy with docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables for Production

**Backend:**
```env
GOOGLE_API_KEY=prod_key
SUPABASE_URL=https://prod.supabase.co
SUPABASE_KEY=prod_key
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000
```

**Frontend:**
```env
NEXT_PUBLIC_API_URL=https://api.your-domain.com
```

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions.

---

## 🧪 Testing

### Backend Tests (Python)

```bash
cd backend

# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Test specific module
pytest tests/test_agents.py
```

### Frontend Tests

```bash
cd frontend

# Install test dependencies
pnpm add -D jest @testing-library/react @testing-library/jest-dom

# Run tests
pnpm test

# Test with coverage
pnpm test:coverage
```

### Manual API Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test upload
curl -X POST http://localhost:8000/api/v1/upload/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Solve x + 5 = 10"}'

# Test with httpx (Python)
python -c "
import httpx
response = httpx.post(
    'http://localhost:8000/api/v1/upload/text',
    json={'text': 'Solve x + 5 = 10'}
)
print(response.json())
"
```

### Interactive API Testing

FastAPI provides built-in interactive documentation:

1. **Swagger UI:** http://localhost:8000/docs
   - Test all endpoints directly in browser
   - See request/response schemas
   - Try out API calls

2. **ReDoc:** http://localhost:8000/redoc
   - Beautiful API documentation
   - Export OpenAPI spec

**Testing Guide:** [TESTING.md](./TESTING.md)

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit your changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```
4. **Push to branch**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open a Pull Request**

### Development Guidelines

- Follow TypeScript best practices
- Write tests for new features
- Update documentation
- Use conventional commits
- Ensure all tests pass

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines.

---

## 📊 Performance

- **Page Load:** < 2 seconds
- **API Response:** < 1 second (text)
- **AI Solution:** 3-8 seconds (varies by complexity)
- **Image Upload:** < 3 seconds
- **Voice Transcription:** < 5 seconds

---

## 🔐 Security

- API keys stored in environment variables
- File upload validation (type, size)
- Input sanitization
- HTTPS enforced in production
- Rate limiting (configurable)
- Session-based security

---

## 📈 Roadmap

### Phase 1 (Current)
- [x] Multimodal input support
- [x] Step-by-step solutions
- [x] Session management
- [x] Basic HITL support

### Phase 2 (Next)
- [ ] Advanced RAG pipeline with vector DB
- [ ] Multi-agent optimization
- [ ] Practice problem generator
- [ ] Progress tracking dashboard

### Phase 3 (Future)
- [ ] Real-time collaboration
- [ ] Mobile app (React Native)
- [ ] Competitive exam mode
- [ ] Performance analytics

---

## 🐛 Troubleshooting

### Common Issues

**Backend Not Starting**
```bash
# Check Python version
python --version  # Should be 3.10+

# Check if port 8000 is in use
lsof -i :8000

# Kill process if needed
kill -9 <PID>

# Check virtual environment is activated
which python  # Should point to venv/bin/python
```

**Supabase Connection Failed**
```bash
# Test Supabase connection
python -c "
from supabase import create_client
import os
url = 'YOUR_SUPABASE_URL'
key = 'YOUR_SUPABASE_KEY'
supabase = create_client(url, key)
print('Connected!')
"

# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_KEY
```

**Google AI API Error**
```bash
# Verify API key
echo $GOOGLE_API_KEY

# Test API
python -c "
import google.generativeai as genai
genai.configure(api_key='YOUR_API_KEY')
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content('Hello')
print(response.text)
"

# Check quota: https://makersuite.google.com/app/apikey
```

**Frontend Can't Connect to Backend**
```bash
# Check backend is running
curl http://localhost:8000/health

# Check CORS settings in backend/main.py
# Verify NEXT_PUBLIC_API_URL in frontend/.env.local

# Check network
ping localhost
```

**Module Not Found Error**
```bash
# Reinstall dependencies
cd backend
pip install -r requirements.txt --force-reinstall

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

**Upload Size Limit Error**
```bash
# Increase max file size in backend/core/config.py
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Or in .env
MAX_FILE_SIZE=20971520  # 20MB
```

---

## 📞 Support

- **Documentation:** [Full Docs](./docs/)
- **Issues:** [GitHub Issues](https://github.com/yourusername/jee-math-ai/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/jee-math-ai/discussions)
- **Email:** support@jeemath.ai

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Google AI** for Gemini API (Vision, Flash models)
- **FastAPI** team for the excellent Python web framework
- **LangChain** for multi-agent orchestration tools
- **Supabase** for database and storage infrastructure
- **Next.js** team for the amazing React framework
- **Tailwind CSS** for utility-first styling
- **Vercel** for seamless frontend deployment
- **JEE aspirants** for inspiration and feedback
- **Open Source Community** for amazing tools and libraries

---

## 💡 Tips for Students

1. **Be Specific** - Provide complete problem statements
2. **Use Clear Images** - Ensure handwriting is legible
3. **Review Steps** - Understand the methodology, not just the answer
4. **Provide Feedback** - Help improve the AI system
5. **Practice Regularly** - Use the session history to track progress

---

<div align="center">

**Built with ❤️ for JEE aspirants**

Made by [Your Name](https://github.com/yourusername)

[⬆ Back to Top](#-jee-math-ai---intelligent-mathematics-problem-solver)

</div>
