# SQL Lab Platform - Deployment Guide

## Quick Deploy

### Backend: Render.com (Free)

1. **Go to:** https://render.com
2. **Sign up/Login** with GitHub
3. **New → Web Service**
4. **Connect your repo** or upload `backend_python` folder
5. **Settings:**
   - Name: `sql-lab-backend`
   - Region: Singapore
   - Branch: `main`
   - Root Directory: `backend_python`
   - Runtime: `Python`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`

6. **Environment Variables (Add these):**
   ```
   DB_HOST=sql12.freesqldatabase.com
   DB_PORT=3306
   DB_USER=sql12823105
   DB_PASSWORD=FbD7mfUYc6
   DB_NAME=sql12823105
   JWT_SECRET=your-secure-random-key-here
   RESEND_API_KEY=re_5b2wxgWh_Ng1neUWvp7ziVfsThD1hYE2L
   EMAIL_FROM=onboarding@resend.dev
   ALLOWED_DOMAIN=
   ADMIN_EMAIL=admin@iobm.edu.pk
   MAX_ROWS=100
   ```

7. **Deploy!** (~2-3 minutes)

### Frontend: Vercel (Free)

1. **Go to:** https://vercel.com
2. **Sign up/Login** with GitHub
3. **Add New Project**
4. **Import** your frontend repo
5. **Framework Preset:** Vite
6. **Build Command:** `npm run build`
7. **Environment Variables:**
   ```
   REACT_APP_API_URL=https://your-backend-url.onrender.com/api
   ```
8. **Deploy!**

## After Deploy

1. **Update Frontend .env:**
   ```
   REACT_APP_API_URL=https://sql-lab-backend.onrender.com/api
   ```

2. **Test Everything:**
   - Signup works
   - OTP sends to email
   - SQL queries execute
   - Multiple queries work

## Domain Verification (For Real Emails)

To send emails to @iobm.edu.pk students:

1. Go to https://resend.com/domains
2. Add your domain (e.g., `your-domain.com`)
3. Add DNS records shown by Resend
4. Update `EMAIL_FROM` to `noreply@your-domain.com`

## Admin Login

- Email: `admin@iobm.edu.pk`
- Password: `admin123`

**Change admin password after first login!**
