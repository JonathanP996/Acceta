# Quick Start Guide - Accenta Backend

## 🚀 Start the Server

### Option 1: Using the Start Script (Easiest)

```bash
cd /Users/jsmat/gaTech/AI@GT/Accenta
./start_backend.sh
```

### Option 2: Manual Start

```bash
cd /Users/jsmat/gaTech/AI@GT/Accenta/backend
source ../venv/bin/activate
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## 📍 Server URLs

Once started, the server will be available at:

- **API Base**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc

## ✅ Verify It's Running

1. Open your browser and go to: http://localhost:8000/docs
2. You should see the Swagger UI with all available endpoints
3. Try the `/health` endpoint to verify everything is working

## 🛑 Stop the Server

Press `Ctrl+C` in the terminal where the server is running.

## 🔧 Troubleshooting

### Port Already in Use

If port 8000 is already in use:

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn app:app --reload --port 8001
```

### Virtual Environment Not Activated

Make sure you activate the virtual environment:

```bash
source venv/bin/activate
```

### Missing Dependencies

If you get import errors:

```bash
cd backend
source ../venv/bin/activate
pip install -r requirements.txt
```

## 📝 Next Steps

1. Test the `/health` endpoint
2. Try uploading an audio file to `/api/analyze_accent`
3. Check the API docs at `/docs` for all available endpoints

