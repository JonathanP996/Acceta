# Users Created Successfully! ✅

## Created Users

### 1. Demo User
- **User ID**: `user_1e22d98b0e88`
- **Email**: `demo@accenta.com`
- **Username**: `demo_user`
- **Password**: `demo123`

### 2. John Doe
- **User ID**: `user_d4c74594d841`
- **Email**: `john@example.com`
- **Username**: `john_doe`
- **Password**: `securepass123`

### 3. Test User
- **User ID**: `user_7b6cfb77576b`
- **Email**: `demo@test.com`
- **Username**: `demouser`
- **Password**: `testpass123`

## Available Endpoints

### Signup
```bash
POST /api/auth/signup
{
  "email": "user@example.com",
  "username": "username",
  "password": "password"
}
```

### Login
```bash
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "password"
}
```

### Get User
```bash
GET /api/auth/user/{user_id}
```

## Test Commands

### Create a new user:
```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "username": "newuser",
    "password": "password123"
  }'
```

### Login:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@accenta.com",
    "password": "demo123"
  }'
```

### Get user info:
```bash
curl http://localhost:8000/api/auth/user/user_1e22d98b0e88
```

## Next Steps

Users are now stored in MongoDB and can:
1. Login to the system
2. Create accent profiles
3. Submit audio for analysis
4. Track their progress

All users are ready to use the Accenta platform! 🎉

