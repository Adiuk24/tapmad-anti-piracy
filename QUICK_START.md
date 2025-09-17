# ⚡ TAPMAD ANTI-PIRACY PLATFORM - QUICK START GUIDE

## 🚀 **5-Minute Deployment**

This guide will get your platform running in under 5 minutes for development and testing.

---

## 📋 **Prerequisites Check**

```bash
# Check if Docker is installed
docker --version
docker-compose --version

# If not installed, run:
# curl -fsSL https://get.docker.com | sh
# sudo usermod -aG docker $USER
# newgrp docker
```

---

## ⚡ **Quick Start (5 Minutes)**

### **Step 1: Clone & Setup**
```bash
# Clone repository
git clone <your-repo-url>
cd tapmad-anti-piracy

# Copy environment template
cp env.template .env
```

### **Step 2: Configure Environment (2 minutes)**
```bash
# Edit .env file with your API keys
nano .env

# MINIMUM REQUIRED SETTINGS:
ENV=development
API_KEY=your_strong_api_key_here

# For local AI (choose one):
LOCAL_AI_PROVIDER=ollama
LOCAL_AI_ENDPOINT=http://localhost:11434
LOCAL_AI_MODEL=llama2:7b

# OR
LOCAL_AI_PROVIDER=llama_cpp
LOCAL_AI_ENDPOINT=http://localhost:8080
LOCAL_AI_MODEL=llama-2-7b-chat.Q4_K_M.gguf
```

### **Step 3: Start Platform (2 minutes)**
```bash
# Start the platform
docker-compose up -d

# Check status
docker-compose ps

# Wait for services to start (about 1-2 minutes)
sleep 120
```

### **Step 4: Verify & Access (1 minute)**
```bash
# Check if API is running
curl http://localhost:8000/health

# Check if dashboard is running
curl -I http://localhost:3000

# Access your platform:
# 🌐 Dashboard: http://localhost:3000
# 📚 API Docs: http://localhost:8000/docs
# ✅ Health: http://localhost:8000/health
```

---

## 🎉 **You're Ready!**

Your Tapmad Anti-Piracy Platform is now running! 

**What You Can Do Now:**
- ✅ Access the dashboard
- ✅ Test API endpoints
- ✅ Monitor system health
- ✅ Start content detection
- ✅ Configure AI models

**Remember**: This is a development setup. For production, follow the `TECHNICAL_DEPLOYMENT.md` guide.

---

*Last Updated: September 2024*  
*Version: 1.0*  
*Platform: Tapmad Anti-Piracy System*
