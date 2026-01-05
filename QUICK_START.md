# 🚀 Quick Start Guide

Get **AI SQL Optimizer Pro** running in 5 minutes!

## Prerequisites Check

Before starting, ensure you have:

- ✅ **Docker** installed and running
- ✅ **Docker Compose** v2.0+
- ✅ **Ollama** running at `http://192.168.1.81:11434`
- ✅ **sqlcoder:latest** model pulled in Ollama

### Verify Ollama

```bash
# Check if Ollama is accessible
curl http://192.168.1.81:11434/api/tags

# Should return a list of models including sqlcoder
```

If `sqlcoder:latest` is not installed:
```bash
# On the machine running Ollama
ollama pull sqlcoder:latest
```

## 🎯 Step-by-Step Setup

### Step 1: Clone/Navigate to Project

```bash
cd ai-sql-optimizer-pro
```

### Step 2: Configure Environment (Optional)

The default configuration works out of the box with your Ollama setup:

```bash
# Optional: Copy and customize .env
cp .env.example .env

# The default .env already has:
# OLLAMA_BASE_URL=http://192.168.1.81:11434
# OLLAMA_MODEL=sqlcoder:latest
```

### Step 3: Start Services

```bash
# Build and start all services
docker-compose up --build -d

# This will start:
# - Backend API (port 8000)
# - Frontend UI (port 3000)
```

### Step 4: Verify Services

```bash
# Check if services are running
docker-compose ps

# Should show:
# sql-optimizer-backend   running   0.0.0.0:8000->8000/tcp
# sql-optimizer-frontend  running   0.0.0.0:3000->3000/tcp
```

### Step 5: Health Check

```bash
# Check backend health
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "ollama": {
#     "status": "healthy",
#     "model_available": true
#   },
#   "monitoring_agent": true
# }
```

### Step 6: Access the Application

Open your browser and navigate to:

- **Frontend UI**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health

## 🎨 First Steps in the UI

### 1. Add Your First Database Connection

1. Click on **"Connections"** in the sidebar
2. Click **"Add Connection"** button
3. Fill in the form:
   ```
   Name: My PostgreSQL DB
   Engine: PostgreSQL
   Host: your-db-host
   Port: 5432
   Database: your-database
   Username: your-username
   Password: your-password
   Enable Monitoring: ✅
   ```
4. Click **"Test Connection"**
5. If successful, click **"Save"**

### 2. View Dashboard

1. Click on **"Dashboard"** in the sidebar
2. You'll see:
   - Total connections
   - Queries discovered
   - Optimizations created
   - Top bottlenecks table

### 3. Optimize a Query

**Option A: From Discovered Queries**
1. Go to **"Monitoring"** page
2. View discovered slow queries
3. Click **"Optimize"** on any query

**Option B: Manual Analysis**
1. Go to **"Optimizer"** page
2. Select a connection
3. Paste your SQL query
4. Click **"Analyze Query"**
5. Review the results:
   - Optimized SQL
   - Explanation
   - Recommendations

### 4. Monitor Agent Status

1. Go to **"Monitoring"** page
2. View agent status:
   - Running: ✅
   - Last Run: timestamp
   - Next Run: timestamp
3. Click **"Trigger Now"** to manually run monitoring

## 🧪 Test with Sample Data

### Create a Test PostgreSQL Database

```bash
# Run a test PostgreSQL container
docker run --name test-postgres -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres

# Connect and create sample data
docker exec -it test-postgres psql -U postgres -c "
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255),
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO users (email, name)
SELECT 
    'user' || i || '@example.com',
    'User ' || i
FROM generate_series(1, 10000) i;
"
```

### Add Connection in UI

```
Name: Test PostgreSQL
Engine: PostgreSQL
Host: localhost (or host.docker.internal on Mac/Windows)
Port: 5432
Database: postgres
Username: postgres
Password: password
Enable Monitoring: ✅
```

### Test Query to Optimize

```sql
SELECT * FROM users WHERE email = 'user5000@example.com';
```

This query will likely show:
- Sequential scan issue
- Recommendation to add index on email column

## 📊 View Results

After optimization, you'll see:

**Optimized SQL:**
```sql
-- May suggest adding index first
CREATE INDEX idx_users_email ON users(email);

-- Then the optimized query
SELECT id, email, name, created_at 
FROM users 
WHERE email = 'user5000@example.com';
```

**Explanation:**
- Why the original query was slow
- What the execution plan showed
- How the optimization improves performance

**Recommendations:**
- CREATE INDEX statements
- ANALYZE TABLE commands
- Query pattern improvements

## 🛠️ Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker-compose logs backend

# Common issues:
# 1. Port 8000 already in use
# 2. Ollama not accessible
# 3. Database initialization failed
```

### Frontend Won't Start

```bash
# Check logs
docker-compose logs frontend

# Common issues:
# 1. Port 3000 already in use
# 2. Backend not accessible
# 3. Node modules not installed
```

### Ollama Connection Failed

```bash
# Verify Ollama is running
curl http://192.168.1.81:11434/api/tags

# Check if sqlcoder model exists
# If not, pull it:
ollama pull sqlcoder:latest
```

### Database Connection Failed

1. Verify database is accessible from Docker container
2. Check credentials
3. For localhost databases, use `host.docker.internal` (Mac/Windows) or `172.17.0.1` (Linux)
4. Ensure firewall allows connections

## 🔄 Restart Services

```bash
# Stop services
docker-compose down

# Start services
docker-compose up -d

# Rebuild and start (if code changed)
docker-compose up --build -d
```

## 📝 View Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend
```

## 🧹 Clean Up

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (deletes observability database)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

## 🎉 Success!

You should now have:
- ✅ Backend API running on port 8000
- ✅ Frontend UI running on port 3000
- ✅ Monitoring agent discovering queries
- ✅ AI optimization working with Ollama

## 📚 Next Steps

1. **Add more connections** - Connect to your production databases
2. **Enable monitoring** - Let the agent discover slow queries
3. **Review optimizations** - Check the dashboard for recommendations
4. **Apply fixes** - Implement suggested indexes and query improvements

## 💡 Tips

- **Monitoring Interval**: Default is 60 minutes. Adjust in `.env` if needed
- **Query Limit**: Default discovers top 100 queries. Adjust `MAX_QUERIES_PER_POLL`
- **Safety**: DDL execution is disabled by default. Enable with caution
- **Performance**: The observability database grows over time. Clean periodically

## 🆘 Need Help?

- Check the **README.md** for detailed documentation
- Review **BACKEND_COMPLETE.md** for backend details
- Check API docs at http://localhost:8000/docs
- Review logs with `docker-compose logs`

---

**Happy Optimizing! 🚀**
