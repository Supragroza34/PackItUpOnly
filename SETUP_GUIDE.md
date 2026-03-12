# KCL Ticketing System - Setup Instructions

## For Windows Users

```bash
# First time setup
.\setup-all.bat

# Daily startup
.\start-all.bat
```

## For Mac/Linux Users

```bash
# First time: Make scripts executable
chmod +x setup-all.sh start-all.sh

# First time setup
./setup-all.sh

# Daily startup
./start-all.sh
```

## What gets installed:
- Backend: Django, Django REST Framework, CORS headers
- Frontend: React, react-scripts
- Database migrations applied

## Servers:
- Backend (Django): http://localhost:8000
- Frontend (React): http://localhost:3000
- API Endpoint: http://localhost:8000/api/submit-ticket/
