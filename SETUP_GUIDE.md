# KCL Ticketing System - Setup Instructions

## Prerequisites

Before running the setup, ensure you have installed:

1. **Python 3.8+** - [Download here](https://www.python.org/downloads/)
2. **Node.js 14+** - [Download here](https://nodejs.org/)

## Quick Setup

### For Windows Users

```bash
# First time setup (installs everything automatically)
.\setup-all.bat

# Daily startup (run both servers)
.\start-all.bat
```

### For Mac/Linux Users

```bash
# First time: Make scripts executable
chmod +x setup-all.sh start-all.sh

# First time setup (installs everything automatically)
./setup-all.sh

# Daily startup (run both servers)
./start-all.sh
```

## What the Setup Script Does

The automated setup script will:

1. **Check Prerequisites** ✅
   - Verifies Python 3.8+ is installed
   - Verifies Node.js 14+ is installed

2. **Setup Backend** ✅
   - Installs all Python dependencies from requirements.txt
   - Runs database migrations
   - Configures Django settings

3. **Setup Frontend** ✅
   - Installs all Node.js/React dependencies
   - Configures React environment

4. **AI Chatbot** ✅
   - Uses Google Gemini via the `GEMINI_API_KEY` environment variable

**Total setup time**: 5-15 minutes (depending on internet speed)

## AI Chatbot Setup

The AI Chatbot now uses the Google Gemini API:

1. Obtain a Gemini API key from your Google Cloud project.
2. Set the `GEMINI_API_KEY` environment variable locally (e.g. in your `.env` file).
3. Restart your Django server so the new key is picked up.

## Servers

After setup, the application runs on:

- **Backend (Django)**: http://localhost:8000
- **Frontend (React)**: http://localhost:3000
- **API Endpoints**: http://localhost:8000/api/
- **AI Chatbot API**: http://localhost:8000/api/ai-chatbot/chat/

## Troubleshooting

### AI Chatbot shows "Chat request failed"

1. Check Ollama is installed:
   ```bash
   ollama version
   ```

2. Check if llama2 model is installed:
   ```bash
   ollama list
   ```
   Should show `llama2:latest`

3. If model is missing, install it:
   ```bash
   ollama pull llama2
   ```

4. Test Ollama is working:
   ```bash
   ollama run llama2 "Hi"
   ```

5. Restart your Django server

### Python/Node.js Not Found

- Make sure Python 3.8+ is installed: `python --version`
- Make sure Node.js 14+ is installed: `node --version`
- On Mac/Linux, try `python3` instead of `python`

### Port Already in Use

- **Port 8000**: Stop other Django servers, or use `python manage.py runserver 8001`
- **Port 3000**: Stop other React apps, or React will offer port 3001

## What Gets Installed

- **Backend**: Django, Django REST Framework, CORS headers, Gemini client
- **Frontend**: React, react-scripts, routing, state management
- **Database**: SQLite with all migrations applied

## Need More Help?

- Check [README_SETUP.md](README_SETUP.md) for detailed manual setup
- Check [TESTING.md](TESTING.md) for testing documentation
- Use the AI Chatbot for quick questions (if `GEMINI_API_KEY` is configured)
