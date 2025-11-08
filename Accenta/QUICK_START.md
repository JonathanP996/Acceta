# Accenta - Quick Start Guide

## 🚀 Fastest Way to Start

### Option 1: Use the Start Scripts (Easiest)

**Terminal 1 - Backend:**
```bash
cd /Users/jsmat/gaTech/AI@GT/Accenta
./start_backend.sh
```

**Terminal 2 - Frontend:**
```bash
cd /Users/jsmat/gaTech/AI@GT/Accenta
./start_frontend.sh
```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd /Users/jsmat/gaTech/AI@GT/Accenta
source venv/bin/activate
cd backend
uvicorn app:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd /Users/jsmat/gaTech/AI@GT/Accenta/frontend
npm start
```

## 📍 Important Paths

- **Project Root**: `/Users/jsmat/gaTech/AI@GT/Accenta`
- **Backend**: `/Users/jsmat/gaTech/AI@GT/Accenta/backend`
- **Frontend**: `/Users/jsmat/gaTech/AI@GT/Accenta/frontend`
- **Virtual Env**: `/Users/jsmat/gaTech/AI@GT/Accenta/venv`

## ⚠️ Common Issues

### "No such file or directory: Accenta/backend"
- Make sure you're in the right directory: `/Users/jsmat/gaTech/AI@GT/Accenta`
- Use absolute path: `cd /Users/jsmat/gaTech/AI@GT/Accenta/backend`

### "Virtual environment not found"
- The venv should be in `/Users/jsmat/gaTech/AI@GT/Accenta/venv`
- If missing, create it: `python3 -m venv venv` (from Accenta directory)

### "uvicorn: command not found"
- Activate venv first: `source venv/bin/activate`
- Install: `pip install uvicorn`

## ✅ Verify Setup

```bash
# Check you're in the right place
cd /Users/jsmat/gaTech/AI@GT/Accenta
pwd  # Should show: /Users/jsmat/gaTech/AI@GT/Accenta

# Check backend
ls backend/app.py  # Should exist

# Check frontend
ls frontend/package.json  # Should exist

# Check venv
ls venv/bin/activate  # Should exist
```

## 🎯 URLs

- **Backend API**: http://localhost:8000
- **Frontend App**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

## 📝 First Time Setup

If you haven't set up yet:

```bash
cd /Users/jsmat/gaTech/AI@GT/Accenta

# Backend setup
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Frontend setup
cd frontend
npm install
cd ..
```

Then use the start scripts above!

