# SQL Lab Platform - Python Backend

## Setup

### 1. Install Dependencies

```bash
cd backend_python
pip install -r requirements.txt
```

### 2. Update .env File

Edit `.env` with your database credentials:

```
DB_HOST=sql12.freesqldatabase.com
DB_PORT=3306
DB_USER=sql12823105
DB_PASSWORD=FbD7mfUYc6
DB_NAME=sql12823105
```

### 3. Run Backend

```bash
python app.py
```

Server will start on `http://localhost:5000`

---

## API Endpoints

### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/verify-otp` - OTP verification
- `POST /api/auth/login` - User login
- `GET /api/auth/profile` - Get user profile

### Query Execution
- `POST /api/query/execute` - Execute SQL query
- `GET /api/history` - Get query history
- `GET /api/history/stats` - Get query statistics

### Admin
- `GET /api/admin/dashboard` - Admin dashboard stats
- `GET /api/admin/otps` - View active OTPs

### Health
- `GET /api/health` - Health check

---

## Deployment on Render

1. Create new Web Service on Render
2. Connect GitHub repository
3. Set:
   - **Build Command:** `pip install -r backend_python/requirements.txt`
   - **Start Command:** `cd backend_python && python app.py`
4. Add Environment Variables from `.env`
5. Deploy!

---

## Features

- ✅ JWT Authentication
- ✅ OTP Email Verification
- ✅ SQL Query Execution
- ✅ Query History
- ✅ Admin Dashboard
- ✅ Query Security (blocks DROP, ALTER, etc.)
- ✅ Row limit enforcement
- ✅ Query logging
