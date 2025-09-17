# 🚀 **TEAM SETUP GUIDE - TAPMAD ANTI-PIRACY**

## 📋 **Quick Start for Your Team**

This guide will get your team up and running with the Tapmad Anti-Piracy platform in under 10 minutes.

---

## 🔧 **Prerequisites**

### **Required Software:**
- **Python 3.11+** (3.13.2 recommended)
- **Git** (for cloning)
- **Docker** (optional, for containerized deployment)

### **macOS Setup:**
```bash
# Install Python (if not already installed)
brew install python@3.13

# Install PostgreSQL (for production)
brew install postgresql@14
```

### **Ubuntu/Debian Setup:**
```bash
# Install Python and dependencies
sudo apt update
sudo apt install python3.13 python3.13-venv python3.13-dev

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib
```

### **Windows Setup:**
1. Download Python 3.13 from [python.org](https://python.org)
2. Install PostgreSQL from [postgresql.org](https://postgresql.org)
3. Install Git from [git-scm.com](https://git-scm.com)

---

## 🚀 **Team Setup (5 Minutes)**

### **Step 1: Clone the Repository**
```bash
git clone https://github.com/Adiuk24/tapmad-anti-piracy.git
cd tapmad-anti-piracy
```

### **Step 2: Set Up Python Environment**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements-dev.txt
```

### **Step 3: Configure Environment**
```bash
# Copy environment template
cp .env.example .env

# Edit the .env file with your settings
nano .env
```

### **Step 4: Start Development Server**
```bash
# Option 1: Use the startup script
./start_dev.sh

# Option 2: Manual start
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

### **Step 5: Verify Installation**
```bash
# Test the API
curl http://localhost:8000/health

# Open API documentation
open http://localhost:8000/docs
```

---

## 🎯 **What Your Team Gets**

### **✅ Complete System:**
- **API Server** with 15+ endpoints
- **Multi-platform Crawlers** (YouTube, Telegram, Facebook, Twitter, Instagram)
- **AI/LLM Integration** (local and external models)
- **Content Fingerprinting** (video/audio analysis)
- **Enforcement System** (DMCA, takedowns)
- **Dashboard** (Next.js React frontend)

### **✅ Production Ready:**
- **Docker Configuration** (docker-compose.yml)
- **Database Migrations** (Alembic)
- **CI/CD Pipeline** (GitHub Actions)
- **Security Features** (authentication, CORS, rate limiting)
- **Monitoring** (health checks, metrics, logging)

---

## 🔑 **API Keys Setup (Optional for Development)**

For full functionality, add these API keys to your `.env` file:

```bash
# YouTube Data API v3
YOUTUBE_API_KEY=your_youtube_api_key

# Telegram Bot API
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# Facebook Graph API
FACEBOOK_ACCESS_TOKEN=your_facebook_token

# Twitter API v2
TWITTER_BEARER_TOKEN=your_twitter_token

# Instagram Basic Display
INSTAGRAM_ACCESS_TOKEN=your_instagram_token
```

**Note:** The system works in development mode without these keys using simulated data.

---

## 🐳 **Docker Deployment (Alternative)**

If you prefer Docker:

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

---

## 📚 **Documentation**

- **`README.md`** - Complete system overview
- **`DEPLOYMENT.md`** - Detailed deployment guide
- **`QUICK_START.md`** - Fast setup instructions
- **`SECURITY.md`** - Security best practices
- **`API Documentation`** - Available at `http://localhost:8000/docs`

---

## 🆘 **Troubleshooting**

### **Import Errors:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements-dev.txt
```

### **Port Already in Use:**
```bash
# Kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn src.api.app:app --reload --port 8001
```

### **Database Connection Issues:**
```bash
# For development, the system uses SQLite by default
# No additional setup required
```

---

## 🎉 **Success!**

Once you see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Started reloader process
```

Your team is ready to develop! 🚀

---

## 📞 **Support**

- **GitHub Issues**: [Create an issue](https://github.com/Adiuk24/tapmad-anti-piracy/issues)
- **Documentation**: Check the `docs/` folder
- **API Testing**: Use `http://localhost:8000/docs`

---

*Happy coding! 🎯*
