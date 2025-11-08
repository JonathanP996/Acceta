# MongoDB Atlas Setup Guide - For Database Host

This guide is for the person hosting the MongoDB Atlas database to allow access for other users.

## Step 1: Network Access (IP Whitelist)

This is the **most important step** - without this, connections will be blocked.

1. **Log in to MongoDB Atlas**: https://cloud.mongodb.com/
2. **Select your cluster** (Cluster0)
3. **Click "Network Access"** in the left sidebar
4. **Click "Add IP Address"** button
5. **Choose one of these options**:
   
   **Option A: Allow from Anywhere (Easiest for Development)**
   - Click **"Allow Access from Anywhere"**
   - This adds `0.0.0.0/0` which allows all IP addresses
   - ⚠️ **Warning**: Only use this for development/testing, not production!
   
   **Option B: Add Specific IP Address (More Secure)**
   - Click **"Add Current IP Address"** (if you're on the same network)
   - Or manually enter the IP address of the person who needs access
   - To find someone's IP: Ask them to visit https://whatismyipaddress.com/
   - Click **"Confirm"**

6. **Wait 1-2 minutes** for changes to take effect

## Step 2: Verify Database User

Make sure the database user exists and has the correct password:

1. **Click "Database Access"** in the left sidebar
2. **Find the user**: `jonathanpattassery10_db_user`
3. **Verify permissions**: Should have "Read and write to any database" or at least access to the `accenta` database
4. **If user doesn't exist or password is wrong**:
   - Click "Add New Database User"
   - Choose "Password" authentication
   - Username: `jonathanpattassery10_db_user`
   - Password: `0KCauQFn1KZPrql4` (or create a new one)
   - Set privileges to "Read and write to any database"
   - Click "Add User"

## Step 3: Get Connection String

To share the connection string:

1. **Click "Connect"** on your cluster
2. **Choose "Connect your application"**
3. **Select**:
   - Driver: **Python**
   - Version: **3.6 or later**
4. **Copy the connection string** - it looks like:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
5. **Replace `<username>` and `<password>`** with the actual database user credentials
6. **Share this connection string** with the person who needs access

## Step 4: Verify Connection String Format

The connection string should be in this format:
```
mongodb+srv://username:password@cluster0.trnux1p.mongodb.net/?retryWrites=true&w=majority
```

**Current connection string being used:**
```
mongodb+srv://jonathanpattassery10_db_user:0KCauQFn1KZPrql4@cluster0.trnux1p.mongodb.net/?retryWrites=true&w=majority
```

## Step 5: Test Connection

After making changes, wait 1-2 minutes, then test:

1. The person using the database should restart their backend server
2. Check the server logs for connection messages
3. Visit: `http://localhost:8000/health` and check if `database: "connected"`

## Common Issues

### "IP not whitelisted" Error
- **Solution**: Add IP address in Network Access (Step 1)
- Wait 1-2 minutes after adding

### "Authentication failed" Error
- **Solution**: Check username/password in Database Access (Step 2)
- Verify the connection string has correct credentials

### "Connection timeout" Error
- **Solution**: Check if cluster is running (should be green in Atlas)
- Verify network access settings

## Security Best Practices

For **development/testing**:
- ✅ Allow access from anywhere (`0.0.0.0/0`) is okay
- ✅ Use strong passwords
- ✅ Don't share connection strings publicly

For **production**:
- ❌ Never use `0.0.0.0/0` (allow from anywhere)
- ✅ Whitelist only specific IP addresses
- ✅ Use database-specific users with limited permissions
- ✅ Enable additional security features (MFA, etc.)

## Quick Checklist

- [ ] Network Access configured (IP whitelist)
- [ ] Database user exists with correct password
- [ ] User has "Read and write" permissions
- [ ] Connection string is correct and shared
- [ ] Waited 1-2 minutes for changes to propagate
- [ ] Tested connection from the application

## Need Help?

If connection still fails after following these steps:
1. Check MongoDB Atlas dashboard for any error messages
2. Verify the cluster is running (not paused)
3. Check the connection string format
4. Review MongoDB Atlas logs for connection attempts

