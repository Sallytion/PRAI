# PRAI - Automated GitHub Pull Request Review Agent

An intelligent, multi-agent system powered by **Groq** (10x faster AI) and **MongoDB** that automatically analyzes GitHub Pull Requests and generates comprehensive, structured review comments.

## 🚀 Features

- **🔐 GitHub OAuth Integration**: Secure authentication with GitHub
- **🤖 Multi-Agent Analysis**: Specialized AI agents powered by Groq
  - Logic & Correctness Agent
  - Code Quality & Readability Agent
  - Performance Analysis Agent
  - Security Vulnerabilities Agent
- **⚡ Lightning Fast**: Up to 10x faster reviews with Groq
- **📊 Real-time PR Monitoring**: Webhook-based continuous monitoring
- **💬 Structured Review Comments**: Clear, actionable feedback
- **🎯 Repository Management**: Easy repository selection and management
- **📈 Review History**: Track all reviews and insights
- **💰 Cost-Effective**: Free tier available (MongoDB Atlas + Groq)

## 🏗️ Architecture

```
┌─────────────────┐
│   Frontend UI   │
│   (React/HTML)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│     FastAPI Backend             │
│  ┌──────────────────────────┐  │
│  │  Auth & User Management  │  │
│  └──────────────────────────┘  │
│  ┌──────────────────────────┐  │
│  │  GitHub Webhook Handler  │  │
│  └──────────────────────────┘  │
│  ┌──────────────────────────┐  │
│  │  PR Analysis Endpoints   │  │
│  └──────────────────────────┘  │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│   CrewAI Multi-Agent System     │
│  ┌────────────────────────────┐ │
│  │  Code Logic Analyzer       │ │
│  └────────────────────────────┘ │
│  ┌────────────────────────────┐ │
│  │  Readability Specialist    │ │
│  └────────────────────────────┘ │
│  ┌────────────────────────────┐ │
│  │  Performance Optimizer     │ │
│  └────────────────────────────┘ │
│  ┌────────────────────────────┐ │
│  │  Security Auditor          │ │
│  └────────────────────────────┘ │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│     External Services           │
│  - GitHub API                   │
│  - MongoDB Database             │
│  - Groq LLM (Lightning Fast!)   │
└─────────────────────────────────┘
```

## 📋 Prerequisites

- Python 3.10+
- MongoDB
- GitHub OAuth App credentials
- Groq API Key (FREE tier available!)

## 🛠️ Installation

### 1. Clone the repository

```bash
cd PRAI
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 5. Start MongoDB

```bash
# Mac (Homebrew)
brew services start mongodb-community

# Windows
mongod

# Docker (all platforms)
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 6. Start the application

**Just one command!**

```bash
# Use the startup script (recommended)
./start.sh  # Mac/Linux
start.bat   # Windows

# Or manually
uvicorn app.main:app --reload --port 8000
```

No Redis, no Celery, no migrations needed! 🎉

## 🔧 GitHub OAuth Setup

1. Go to GitHub Settings > Developer settings > OAuth Apps
2. Create a new OAuth App
3. Set Authorization callback URL: `http://localhost:8000/auth/github/callback`
4. Copy Client ID and Client Secret to `.env` file

## 🪝 GitHub Webhook Setup

1. Go to your repository Settings > Webhooks
2. Add a new webhook
3. Payload URL: `https://your-domain.com/api/webhooks/github`
4. Content type: `application/json`
5. Select events: Pull requests, Pull request reviews
6. Add the webhook secret to `.env`

## 📚 API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🎯 Usage

### 1. Login with GitHub
Navigate to `http://localhost:8000` and click "Login with GitHub"

### 2. Select Repository
Choose the repository you want to monitor from your list

### 3. Configure Webhook
Set up the webhook in your repository (instructions provided in UI)

### 4. Automatic Reviews
- Open a PR in your repository
- The system automatically detects it
- Multi-agent analysis begins
- Review comments are posted

### 5. Manual Review
Use the UI to trigger reviews on existing PRs

## 🧪 Testing

```bash
pytest tests/
```

## 📦 Project Structure

```
PRAI/
├── app/
│   ├── main.py                 # FastAPI application entry
│   ├── config.py               # Configuration (MongoDB + Groq)
│   ├── agents/                 # CrewAI agents (Groq-powered)
│   │   ├── logic_agent.py
│   │   ├── readability_agent.py
│   │   ├── performance_agent.py
│   │   └── security_agent.py
│   ├── api/                    # API routes
│   │   ├── auth.py
│   │   ├── webhooks.py
│   │   ├── repositories.py
│   │   └── reviews.py
│   ├── core/                   # Core functionality
│   │   ├── database.py         # MongoDB connection
│   │   ├── github_client.py
│   │   ├── diff_parser.py
│   │   └── review_generator.py
│   ├── models/                 # Beanie documents
│   │   ├── user.py
│   │   ├── repository.py
│   │   ├── pull_request.py
│   │   └── review.py
│   └── tasks/                  # Background tasks
│       └── review_tasks.py
├── frontend/                   # Frontend code
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── requirements.txt
├── .env.example
├── SETUP_GUIDE.md             # Detailed setup instructions
├── MONGODB_GROQ_MIGRATION.md  # Migration guide
└── README.md
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License

## 💰 Cost & Performance

| Feature | Traditional Setup | PRAI |
|---------|------------------|---------|
| **Database** | PostgreSQL (~$25/mo) | MongoDB (FREE) |
| **Message Queue** | Redis (~$15/mo) | None needed |
| **LLM** | OpenAI ($) | Groq (FREE tier) |
| **Inference Speed** | 1x | **10x faster** ⚡ |
| **Total Cost** | $40+/month | **$0/month** 🎉 |

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [CrewAI](https://www.crewai.com/)
- Lightning-fast AI by [Groq](https://groq.com/)
- Database by [MongoDB](https://www.mongodb.com/)
- Integrated with [GitHub API](https://docs.github.com/en/rest)
