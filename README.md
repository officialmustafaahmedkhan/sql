# SQL Lab Platform - Deployment Guide

## Prerequisites

- Node.js 18+ installed
- MySQL 5.7+ or MySQL 8.0+ database
- Git account for version control
- Render account (for backend hosting)
- Vercel account (for frontend hosting)

---

## Part 1: Local Development Setup

### 1.1 Clone the Project

```bash
git clone <your-repo-url>
cd sql-lab-platform
```

### 1.2 Backend Setup

```bash
cd backend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
# - Set DB credentials
# - Configure JWT secret
# - Set up email credentials
```

### 1.3 Database Setup

```bash
# Login to MySQL
mysql -u root -p

# Create database and run schema
source ../schema.sql

# Exit MySQL
exit
```

### 1.4 Run Backend

```bash
npm run dev
```

The backend will run on `http://localhost:5000`

### 1.5 Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Edit .env
# Set REACT_APP_API_URL=http://localhost:5000/api
```

### 1.6 Run Frontend

```bash
npm start
```

The frontend will run on `http://localhost:3000`

---

## Part 2: Cloud Deployment

### 2.1 Database Setup (PlanetScale or MySQL Cloud)

#### Option A: PlanetScale (Free Tier)

1. Go to [PlanetScale](https://planetscale.com)
2. Create a free account
3. Create a new database
4. Get the connection string
5. Import the schema

```bash
# Install PlanetScale CLI
brew install planetscale/tap/pscale

# Connect to your database
pscale connect sql_lab

# In another terminal, run schema
mysql -h <host> -u <user> -p < schema.sql
```

#### Option B: MySQL on Render

1. Go to [Render](https://render.com)
2. Create a new MySQL instance
3. Select Free tier
4. Wait for provisioning
5. Get connection details

#### Option C: Free MySQL from FreeSQLDatabase

1. Go to [freesqldatabase.com](https://www.freesqldatabase.com)
2. Sign up for free account
3. Get connection credentials
4. Connect and run schema

### 2.2 Email Configuration

#### Gmail SMTP (Development)

1. Enable 2-Factor Authentication on your Google account
2. Go to Google Account > Security > App passwords
3. Generate a new app password for "Mail"
4. Use this password as `SMTP_PASS`

#### SendGrid (Production - Free Tier)

1. Sign up at [SendGrid](https://sendgrid.com)
2. Create a free account
3. Generate an API key
4. Use the API key as `SMTP_PASS`

### 2.3 Backend Deployment on Render

1. **Push code to GitHub**
   ```bash
   cd backend
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Deploy on Render**
   - Go to [render.com](https://render.com)
   - Sign up/Login
   - Click "New +" > "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: `sql-lab-api`
     - **Region**: Singapore (closest to you)
     - **Branch**: main
     - **Root Directory**: (leave empty)
     - **Runtime**: Node
     - **Build Command**: `npm install`
     - **Start Command**: `npm start`
     - **Plan**: Free

3. **Add Environment Variables**
   - `NODE_ENV`: production
   - `PORT`: 10000
   - `DB_HOST`: your-database-host
   - `DB_PORT`: 3306
   - `DB_USER`: your-database-user
   - `DB_PASSWORD`: your-database-password
   - `DB_NAME`: sql_lab
   - `JWT_SECRET`: generate-a-strong-random-string
   - `JWT_EXPIRES_IN`: 7d
   - `SMTP_HOST`: smtp.sendgrid.net
   - `SMTP_PORT`: 587
   - `SMTP_USER`: apikey
   - `SMTP_PASS`: your-sendgrid-api-key
   - `EMAIL_FROM`: your-verified-sender@domain.com
   - `ADMIN_EMAIL`: admin@iobm.edu.pk
   - `ADMIN_PASSWORD`: your-secure-admin-password
   - `QUERY_TIMEOUT_MS`: 3000
   - `MAX_ROWS`: 100

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete
   - Note your backend URL: `https://sql-lab-api.onrender.com`

### 2.4 Frontend Deployment on Vercel

1. **Push frontend to GitHub**
   ```bash
   cd frontend
   git init
   git add .
   git commit -m "Initial frontend commit"
   git remote add origin <your-frontend-github-repo-url>
   git push -u origin main
   ```

2. **Deploy on Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Sign up/Login with GitHub
   - Click "Add New Project"
   - Import your frontend repository
   - Configure:
     - **Framework Preset**: Create React App
     - **Root Directory**: ./ or frontend/
     - **Build Command**: npm run build
     - **Output Directory**: build

3. **Add Environment Variable**
   - `REACT_APP_API_URL`: `https://sql-lab-api.onrender.com/api`

4. **Deploy**
   - Click "Deploy"
   - Wait for deployment
   - Your app is live at: `https://your-project.vercel.app`

---

## Part 3: Post-Deployment Configuration

### 3.1 Update CORS

On Render, update your backend's CORS configuration in `server.js`:

```javascript
app.use(cors({
  origin: ['https://your-frontend.vercel.app', 'http://localhost:3000'],
  credentials: true
}));
```

### 3.2 Verify Admin Account

1. Access your deployed backend
2. Navigate to `/api/health` to verify it's running
3. Login with admin credentials to verify

### 3.3 Configure Domain (Optional)

#### On Vercel:
1. Go to Project Settings > Domains
2. Add your custom domain
3. Update DNS records as instructed

#### On Render:
1. Go to your web service > Settings
2. Add custom domain
3. Update DNS records

---

## Part 4: Security Checklist

- [ ] Change default admin password immediately
- [ ] Use strong JWT secret (32+ random characters)
- [ ] Enable HTTPS everywhere
- [ ] Set up rate limiting appropriately
- [ ] Regular database backups
- [ ] Monitor error logs on Render
- [ ] Use environment variables for all secrets

---

## Part 5: Troubleshooting

### Common Issues

#### 1. CORS Errors
- Verify CORS origin includes your frontend URL
- Check that backend is running

#### 2. Database Connection Failed
- Verify database credentials
- Check if database allows external connections
- Verify SSL/TLS settings

#### 3. Email Not Sending
- Check SMTP credentials
- Verify sender email is verified (SendGrid)
- Check app password for Gmail

#### 4. Query Timeout
- Increase `QUERY_TIMEOUT_MS` if needed
- Optimize complex queries

### Debug Mode

For local development debugging:
```bash
# In backend/.env
NODE_ENV=development
DEBUG=*
```

---

## Part 6: Free Tier Limitations

### Render Free Tier
- Web service sleeps after 15 minutes of inactivity
- First 750 hours/month free
- 512 MB RAM limit

### PlanetScale Free Tier
- 1 database
- 1 billion row reads/month
- 10 million row writes/month
- No branching on free tier

### Vercel Free Tier
- 100GB bandwidth/month
- 100 deployments
- Serverless functions

---

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review server logs on Render
3. Check browser console for frontend errors
4. Verify all environment variables are set correctly

---

## License

This project is for educational purposes. Modify and use as needed for your institution.
