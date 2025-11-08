# Troubleshooting Signup Errors

## Common Issues and Solutions

### 1. "Network error: Could not connect to server"

**Problem**: Backend server is not running.

**Solution**:
```bash
# Terminal 1 - Start backend
cd /Users/jsmat/gaTech/AI@GT/Accenta
./start_backend.sh
```

Or manually:
```bash
cd /Users/jsmat/gaTech/AI@GT/Accenta
source venv/bin/activate
cd backend
uvicorn app:app --reload
```

Verify backend is running:
```bash
curl http://localhost:8000/health
```

### 2. CORS Errors

**Problem**: Frontend can't communicate with backend due to CORS.

**Solution**: Check that `backend/app.py` has CORS middleware configured:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. MongoDB Connection Issues

**Problem**: Backend can't connect to MongoDB Atlas.

**Solution**: 
- Check `.env` file has `MONGODB_URI` set
- Verify MongoDB connection string is correct
- Check network/firewall allows MongoDB Atlas connection

### 4. "User with this email already exists"

**Problem**: Trying to sign up with an email that's already registered.

**Solution**: Use a different email or login instead.

### 5. ESLint Warnings (Not Errors)

**Problem**: Console shows ESLint warnings but app still works.

**Solution**: These are just warnings, not errors. The app should still function. I've fixed most of them, but if you see warnings, they won't prevent signup.

## Debugging Steps

1. **Check Backend is Running**:
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"status":"healthy",...}`

2. **Check Frontend Console**:
   - Open browser DevTools (F12)
   - Look at Console tab for errors
   - Look at Network tab to see API requests

3. **Check Backend Logs**:
   - Look at the terminal where backend is running
   - Check for error messages

4. **Test API Directly**:
   ```bash
   curl -X POST http://localhost:8000/api/auth/signup \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","username":"testuser","password":"test123"}'
   ```

## Quick Fix Checklist

- [ ] Backend server is running on port 8000
- [ ] Frontend server is running on port 3000
- [ ] MongoDB connection is working
- [ ] `.env` file has all required variables
- [ ] No firewall blocking localhost connections
- [ ] Browser console shows no CORS errors

## Still Having Issues?

1. Check browser console for specific error messages
2. Check backend terminal for error logs
3. Verify both servers are running
4. Try clearing browser cache/localStorage
5. Check that API URL in frontend config matches backend

