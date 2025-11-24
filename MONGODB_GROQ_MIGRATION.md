# MongoDB + Groq Migration Guide

## Changes Made

### 1. Dependencies Updated ✅
- Replaced `PostgreSQL` (SQLAlchemy/asyncpg) with `MongoDB` (Motor/Beanie)
- Replaced `Redis + Celery` with FastAPI BackgroundTasks
- Replaced `langchain-openai` with `langchain-groq`

### 2. Configuration Updated ✅
- `MONGODB_URL` instead of `DATABASE_URL`
- `MONGODB_DB_NAME` for database name
- `GROQ_API_KEY` instead of `OPENAI_API_KEY`
- `GROQ_MODEL` (default: llama-3.3-70b-versatile)
- Removed `REDIS_URL`

### 3. Database Models Converted ✅
All models now use Beanie (MongoDB ODM):
- `User` - MongoDB Document with indexes
- `Repository` - References User by string ID
- `PullRequest` - References Repository by string ID
- `Review` - References User and PullRequest by string IDs

### 4. Agents Updated ✅
All four agents now use Groq:
- `logic_agent.py` - Uses ChatGroq
- `readability_agent.py` - Uses ChatGroq
- `performance_agent.py` - Uses ChatGroq
- `security_agent.py` - Uses ChatGroq

### 5. Background Tasks Updated ✅
- Removed Celery worker dependency
- Updated `process_pr_review()` to async function using Beanie

---

## API Endpoints That Need Updates

The following API files need to be updated to work with MongoDB/Beanie:

### `app/api/auth.py`
**Changes needed:**
```python
# Old (SQLAlchemy)
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
user = await db.execute(select(User).where(User.github_id == github_user['id']))

# New (Beanie)
# No database dependency needed
user = await User.find_one(User.github_id == github_user['id'])
```

### `app/api/repositories.py`
**Changes needed:**
```python
# Old
repos = await db.execute(select(Repository).where(Repository.user_id == user_id))

# New
repos = await Repository.find(Repository.user_id == str(user_id)).to_list()
```

### `app/api/reviews.py`
**Changes needed:**
```python
# Old
review = await db.execute(select(Review).where(Review.id == review_id))

# New
review = await Review.get(review_id)
```

### `app/api/webhooks.py`
**Changes needed:**
```python
# Old
repo = await db.execute(select(Repository).where(...))

# New
repo = await Repository.find_one(Repository.github_repo_id == repo_id)
```

---

## Installation Steps

### 1. Install MongoDB

**Windows:**
```powershell
# Download from https://www.mongodb.com/try/download/community
# Or use Chocolatey:
choco install mongodb

# Start MongoDB
mongod
```

**Mac:**
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

**Linux:**
```bash
sudo apt-get install mongodb
sudo systemctl start mongodb
```

**Docker (All platforms):**
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 2. Get Groq API Key

1. Go to https://console.groq.com/
2. Sign up for a free account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `gsk_...`)

### 3. Update Dependencies

```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install new dependencies
pip install -r requirements.txt
```

### 4. Update `.env` File

```env
# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=PRAI_db

# Groq
GROQ_API_KEY=gsk_your_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Remove these lines:
# DATABASE_URL=...
# REDIS_URL=...
# OPENAI_API_KEY=...
```

### 5. No Database Migrations Needed!

MongoDB is schemaless, so:
- No Alembic migrations required
- Collections are created automatically
- Indexes are created on first document insert

---

## Running the Application

### Start MongoDB (if not using Docker)
```bash
# Windows
mongod

# Mac (if installed via Homebrew)
brew services start mongodb-community

# Linux
sudo systemctl start mongodb
```

### Start the Application
```bash
# No need to start Redis or Celery worker!
uvicorn app.main:app --reload --port 8000
```

That's it! The application now runs with just one command.

---

## Updated Startup Scripts

### Windows (`start.bat`)
```batch
@echo off
echo Starting PRAI PR Review Agent...

REM Activate virtual environment
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate

REM Install dependencies
pip install -r requirements.txt

REM Start MongoDB (if using local install)
echo Starting MongoDB...
start mongod

REM Wait a bit for MongoDB to start
timeout /t 3

REM Start FastAPI
echo Starting API server...
uvicorn app.main:app --reload --port 8000

pause
```

### Unix (`start.sh`)
```bash
#!/bin/bash
echo "Starting PRAI PR Review Agent..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start MongoDB (if using Homebrew on Mac)
if command -v brew &> /dev/null; then
    brew services start mongodb-community
fi

# Start FastAPI
echo "Starting API server..."
uvicorn app.main:app --reload --port 8000
```

---

## Benefits of MongoDB + Groq

### MongoDB Benefits:
✅ No schema migrations needed  
✅ Flexible document structure  
✅ Better for storing JSON/nested data (review results)  
✅ Easier to scale horizontally  
✅ No need for separate Redis instance  

### Groq Benefits:
✅ **Much faster inference** (up to 10x faster than OpenAI)  
✅ **Free tier available** with generous limits  
✅ Open-source models (Llama 3.3 70B)  
✅ Lower latency for real-time reviews  
✅ Cost-effective for high-volume usage  

---

## Quick API Reference Updates

### Creating Documents
```python
# Create user
user = User(github_id=123, username="john", access_token="token")
await user.insert()

# Or
await User(github_id=123, username="john", access_token="token").create()
```

### Querying Documents
```python
# Find one
user = await User.find_one(User.github_id == 123)

# Find many
users = await User.find(User.is_active == True).to_list()

# Get by ID
user = await User.get("507f1f77bcf86cd799439011")
```

### Updating Documents
```python
user = await User.find_one(User.github_id == 123)
user.username = "new_name"
await user.save()
```

### Deleting Documents
```python
user = await User.find_one(User.github_id == 123)
await user.delete()
```

---

## Troubleshooting

### MongoDB Connection Issues
```bash
# Check if MongoDB is running
mongo --eval "db.adminCommand('ping')"

# Or with mongosh (newer versions)
mongosh --eval "db.adminCommand('ping')"
```

### Groq API Errors
- Verify API key is correct
- Check rate limits: https://console.groq.com/settings/limits
- Try different model if one is unavailable

### Model Options
```env
# Fastest (recommended)
GROQ_MODEL=llama-3.3-70b-versatile

# More capable
GROQ_MODEL=llama-3.1-70b-versatile

# Smaller/faster
GROQ_MODEL=llama-3.1-8b-instant
```

---

## Next Steps

1. **Complete API Migration**: Update all API endpoints to use Beanie queries
2. **Test**: Verify GitHub OAuth, repository tracking, and PR reviews work
3. **Optimize**: Add indexes, caching if needed
4. **Deploy**: MongoDB Atlas + any cloud provider

For production deployment with MongoDB Atlas:
```env
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
```
