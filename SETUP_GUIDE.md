# PRAI Setup Guide

## 📋 Complete Installation and Setup Instructions

### Prerequisites

Before you begin, ensure you have the following installed:

1. **Python 3.10 or higher**
   - Download from [python.org](https://www.python.org/downloads/)
   - Verify: `python --version`

2. **MongoDB**
   - Download from [mongodb.com](https://www.mongodb.com/try/download/community)
   - Or use Docker: `docker run -d -p 27017:27017 --name mongodb mongo:latest`

3. **Git**
   - Download from [git-scm.com](https://git-scm.com/)

---

## 🚀 Step-by-Step Setup

### 1. GitHub OAuth App Configuration

1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Click "New OAuth App"
3. Fill in the details:
   - **Application name**: PRAI PR Review Agent
   - **Homepage URL**: `http://localhost:8000`
   - **Authorization callback URL**: `http://localhost:8000/auth/github/callback`
4. Click "Register application"
5. Copy the **Client ID** and **Client Secret** (you'll need these later)

### 2. Groq API Key

1. Go to [Groq Console](https://console.groq.com/)
2. Sign up for a free account
3. Navigate to API keys section
4. Create a new API key
5. Copy the key (it starts with `gsk_...`)

### 3. MongoDB Setup

MongoDB will automatically create the database when you first connect. No manual setup needed!

**Verify MongoDB is running:**

```bash
# Test connection
mongosh --eval "db.adminCommand('ping')"

# Should return: { ok: 1 }
```

### 4. Project Setup

```bash
# Navigate to the project directory
cd PRAI

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Environment Configuration

Create a `.env` file from the example:

```bash
# On Windows:
copy .env.example .env

# On Mac/Linux:
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```env
# Application Settings
APP_NAME=PRAI PR Review Agent
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=your-random-secret-key-here-change-this

# MongoDB Database
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=PRAI_db

# GitHub OAuth (from Step 1)
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here
GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback

# GitHub Webhook Secret (generate a random string)
GITHUB_WEBHOOK_SECRET=your_random_webhook_secret_here

# Groq LLM (from Step 2)
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# JWT Secret (generate a random string)
JWT_SECRET_KEY=your-random-jwt-secret-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Webhook Base URL (change in production)
WEBHOOK_BASE_URL=http://localhost:8000
```

**To generate secure secret keys:**

```python
# Run this in Python to generate random secrets
import secrets
print(secrets.token_urlsafe(32))
```

### 6. Start the Application

#### Option A: Use the startup script (Recommended)

**On Windows:**
```bash
start.bat
```

**On Mac/Linux:**
```bash
chmod +x start.sh
./start.sh
```

#### Option B: Start manually

**Just one command needed!**

```bash
uvicorn app.main:app --reload --port 8000
```

That's it! No Redis, no Celery worker, no database migrations needed.

---

## 🌐 Accessing the Application

Once all services are running:

1. **Main Application**: http://localhost:8000
2. **API Documentation (Swagger)**: http://localhost:8000/docs
3. **Alternative API Docs (ReDoc)**: http://localhost:8000/redoc

---

## 🔧 Configuration for Production

### 1. Use a Public URL with Ngrok (for testing webhooks locally)

```bash
# Install ngrok from ngrok.com
ngrok http 8000

# Copy the https URL provided (e.g., https://abc123.ngrok.io)
# Update your .env:
WEBHOOK_BASE_URL=https://abc123.ngrok.io
```

### 2. Update GitHub OAuth App

Go back to your GitHub OAuth App settings and update:
- Homepage URL: Your ngrok URL or production URL
- Callback URL: `https://your-url.com/auth/github/callback`

### 3. Environment Variables for Production

Update `.env` for production:

```env
ENVIRONMENT=production
DEBUG=False
WEBHOOK_BASE_URL=https://your-production-domain.com
```

---

## 🎯 Using the Application

### First Time Setup

1. **Login with GitHub**
   - Click "Login with GitHub" on the homepage
   - Authorize the application

2. **Track a Repository**
   - Go to "Available Repositories" tab
   - Click "Track Repository" for the repo you want to monitor

3. **Set Up Webhook**
   - In the "Tracked Repositories" tab
   - Click "Setup Webhook" button
   - This will automatically configure the webhook in your GitHub repo

4. **Review Pull Requests**
   - Webhooks will automatically trigger reviews for new PRs
   - Or manually trigger reviews from the repository detail page

### Manual Review

1. Navigate to a tracked repository
2. View the list of pull requests
3. Click "🤖 Review Now" on any PR
4. Wait for the multi-agent analysis to complete
5. View the detailed review results

---

## 🔍 Troubleshooting

### MongoDB Connection Issues

```bash
# Test MongoDB connection
mongosh --eval "db.adminCommand('ping')"
# Should return: { ok: 1 }

# If connection fails, check:
# 1. MongoDB is running (mongod process)
# 2. Port 27017 is not blocked
# 3. MONGODB_URL in .env is correct
```

### GitHub OAuth Errors

- Verify Client ID and Secret in `.env`
- Check callback URL matches in GitHub OAuth App settings
- Ensure URL includes the correct port number

### Groq API Errors

- Verify API key is correct and active
- Check rate limits at https://console.groq.com/settings/limits
- Try a different model if one is unavailable:
  - `llama-3.3-70b-versatile` (recommended)
  - `llama-3.1-70b-versatile`
  - `llama-3.1-8b-instant` (faster)

### Webhook Not Working

- Ensure webhook URL is publicly accessible (use ngrok for local testing)
- Check webhook secret matches in `.env` and GitHub settings
- View webhook delivery logs in GitHub repository settings

---

## 📊 Monitoring and Logs

### View Logs

**FastAPI Logs:**
- Displayed in the terminal where uvicorn is running

**Celery Worker Logs:**
- Displayed in the Celery worker terminal
- Shows review processing status

**Redis Monitoring:**
```bash
redis-cli monitor
```

### Database Inspection

```bash
# Connect to MongoDB
mongosh PRAI_db

# Show collections
show collections

# View users
db.users.find().pretty()

# View repositories
db.repositories.find().pretty()

# View reviews
db.reviews.find().pretty()

# Count documents
db.users.countDocuments()
```

---

## 🧪 Testing

### Run Tests

```bash
pytest tests/ -v
```

### Test API Endpoints

Use the Swagger UI at http://localhost:8000/docs to test individual endpoints.

---

## 🚀 Deployment

### Docker Deployment (Recommended)

Create a `docker-compose.yml`:

```yaml
version: '3.8'
services:
  mongodb:
    image: mongo:latest
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    
  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - mongodb
    env_file:
      - .env
    environment:
      - MONGODB_URL=mongodb://mongodb:27017
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

volumes:
  mongodb_data:
```

Then run:
```bash
docker-compose up -d
```

Much simpler - only 2 services instead of 4!

### Cloud Deployment

Recommended platforms:
- **MongoDB Atlas** (Free tier available) + any platform below
- **Heroku**: Easy deployment with MongoDB add-on
- **AWS**: ECS/Fargate with MongoDB Atlas or DocumentDB
- **Google Cloud**: Cloud Run with MongoDB Atlas
- **Azure**: App Service with Azure Cosmos DB (MongoDB API)
- **Render**: Simple deployment with managed MongoDB

---

## 📝 Additional Notes

### API Rate Limits

- GitHub API: 5000 requests/hour for authenticated users
- Groq API: Generous free tier (check console.groq.com for current limits)

### Cost Considerations

- **Groq offers a FREE tier** with generous limits
- Much faster inference than OpenAI (up to 10x)
- MongoDB has a free tier (Atlas M0) with 512MB storage
- Total cost can be $0 for development and small-scale usage!

### Security Best Practices

1. Never commit `.env` file to Git
2. Use strong, random secret keys
3. In production, use HTTPS only
4. Regularly rotate API keys and secrets
5. Set up proper database backups

---

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review API documentation at `/docs`
3. Check application logs for errors
4. Verify all environment variables are set correctly

---

## 🎉 You're All Set!

Your PRAI PR Review Agent should now be fully operational. Open http://localhost:8000 and start reviewing pull requests with AI!
