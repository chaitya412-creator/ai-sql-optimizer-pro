# 🚀 AI SQL Optimizer Pro

A **Cross-Database AI-Powered SQL Optimization Engine** with **Proactive Monitoring** and **Stunning React UI**.

## ✨ Features

### 🎯 Core Capabilities

- **Multi-Database Support**: PostgreSQL, MySQL, Oracle, SQL Server
- **Proactive Monitoring Agent**: Automatically discovers slow queries from database performance views
- **AI-Powered Optimization**: Uses Ollama (sqlcoder:latest) with execution plan analysis
- **Rich Context**: Includes schema DDL and execution plans in LLM prompts
- **Beautiful Modern UI**: React + Vite + TailwindCSS + shadcn/ui
- **Real-time Dashboard**: Live monitoring statistics and performance charts

### 🔍 Monitoring Features

- **Automatic Query Discovery**: Polls databases every N minutes
- **Performance Metrics**: Execution time, I/O stats, call counts
- **Historical Tracking**: SQLite observability store
- **Connection Management**: Encrypted credential storage

### 🤖 AI Optimization

- **Execution Plan Analysis**: Identifies sequential scans, nested loops, high costs
- **Schema-Aware**: Fetches table DDL for context
- **Comprehensive Prompts**: Includes query, schema, and execution plan
- **Actionable Recommendations**: CREATE INDEX, ANALYZE TABLE, query rewrites

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Dashboard   │  │ Connections  │  │  Optimizer   │      │
│  │   - Stats    │  │  - Add/Edit  │  │  - Analyze   │      │
│  │   - Charts   │  │  - Test      │  │  - Results   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  API Endpoints                                        │   │
│  │  - /api/connections  - /api/monitoring               │   │
│  │  - /api/optimizer    - /api/dashboard                │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Core Services                                        │   │
│  │  - DatabaseManager   - OllamaClient                  │   │
│  │  - MonitoringAgent   - PlanAnalyzer                  │   │
│  │  - SecurityManager                                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
        ┌───────────────────┐  ┌──────────────────┐
        │ Observability DB  │  │  Ollama LLM      │
        │   (SQLite)        │  │  sqlcoder:latest │
        │ - Connections     │  │  @ 192.168.1.81  │
        │ - Queries         │  └──────────────────┘
        │ - Optimizations   │
        └───────────────────┘
                    │
                    ▼
        ┌───────────────────────────────┐
        │   Target Databases            │
        │  - PostgreSQL  - MySQL        │
        │  - Oracle      - SQL Server   │
        └───────────────────────────────┘
```

## 📋 Prerequisites

- **Docker** & **Docker Compose**
- **Ollama** running at `http://192.168.1.81:11434` with `sqlcoder:latest` model
- **Node.js** 18+ (for local frontend development)
- **Python** 3.11+ (for local backend development)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd ai-sql-optimizer-pro
cp .env.example .env
# Edit .env if needed (Ollama URL is pre-configured)
```

### 2. Start with Docker

```bash
docker-compose up --build -d
```

This will start:
- **Backend API**: http://localhost:8000
- **Frontend UI**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

### 3. Verify Services

```bash
# Check backend health
curl http://localhost:8000/health

# Check Ollama connection
curl http://192.168.1.81:11434/api/tags
```

## 📖 Usage Guide

### 1. Add Database Connection

1. Navigate to **Connections** page
2. Click **Add Connection**
3. Fill in details:
   - Name: `Production PostgreSQL`
   - Engine: `PostgreSQL`
   - Host, Port, Database, Username, Password
   - Enable Monitoring: ✅
4. Click **Test Connection**
5. Click **Save**

### 2. Monitor Queries

The monitoring agent automatically:
- Polls enabled connections every 60 minutes
- Discovers slow queries from performance views
- Stores metrics in observability database

**Manual Trigger**:
```bash
curl -X POST http://localhost:8000/api/monitoring/trigger
```

### 3. Optimize Query

**Option A: From Dashboard**
1. View **Top Bottlenecks** table
2. Click **Optimize** on any query
3. Review optimized SQL and recommendations

**Option B: Manual Analysis**
1. Go to **Optimizer** page
2. Select connection
3. Paste SQL query
4. Click **Analyze**
5. Review results

### 4. View Results

The optimization result includes:
- **Optimized SQL**: AI-rewritten query
- **Execution Plan**: Visual representation
- **Explanation**: Step-by-step analysis
- **Recommendations**: CREATE INDEX, ANALYZE TABLE, etc.

## 🔧 Configuration

### Environment Variables

```env
# Ollama Configuration
OLLAMA_BASE_URL=http://192.168.1.81:11434
OLLAMA_MODEL=sqlcoder:latest
OLLAMA_TIMEOUT=300

# Monitoring
MONITORING_ENABLED=true
MONITORING_INTERVAL_MINUTES=60
MAX_QUERIES_PER_POLL=100

# Database
DATABASE_URL=sqlite:///./app/db/observability.db

# Security
SECRET_KEY=your-secret-key-change-this
ENCRYPTION_KEY=your-encryption-key-change-this
```

## 📊 API Endpoints

### Connections
- `POST /api/connections` - Create connection
- `GET /api/connections` - List connections
- `GET /api/connections/{id}` - Get connection
- `PUT /api/connections/{id}` - Update connection
- `DELETE /api/connections/{id}` - Delete connection
- `POST /api/connections/{id}/test` - Test connection

### Monitoring
- `GET /api/monitoring/status` - Get agent status
- `POST /api/monitoring/start` - Start monitoring agent
- `POST /api/monitoring/stop` - Stop monitoring agent
- `POST /api/monitoring/trigger` - Trigger manual run
- `GET /api/monitoring/queries` - Get discovered queries

### Optimizer
- `POST /api/optimizer/optimize` - Optimize query
- `GET /api/optimizer/optimizations` - List optimizations
- `GET /api/optimizer/optimizations/{id}` - Get optimization
- `POST /api/optimizer/apply` - Apply optimization
- `DELETE /api/optimizer/optimizations/{id}` - Delete optimization

### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics
- `GET /api/dashboard/top-queries` - Get top slow queries
- `GET /api/dashboard/performance-trends` - Get performance trends
- `GET /api/dashboard/recent-activity` - Get recent activity

## 🎨 Frontend Features

### Dashboard Page
- **Stats Cards**: Total connections, queries, optimizations
- **Performance Charts**: Execution time trends
- **Top Bottlenecks Table**: Worst-performing queries
- **Recent Activity**: Latest optimizations

### Connections Page
- **Connection List**: All saved connections
- **Add/Edit Modal**: Connection form with validation
- **Test Connection**: Verify credentials
- **Enable/Disable Monitoring**: Toggle per connection

### Optimizer Page
- **Query Input**: SQL editor with syntax highlighting
- **Connection Selector**: Choose target database
- **Results Panel**: Optimized SQL, explanation, recommendations
- **Execution Plan Viewer**: Visual plan representation

### Monitoring Page
- **Agent Status**: Running, last run, next run
- **Discovered Queries**: List with filters
- **Manual Trigger**: Force monitoring cycle

## 🛠️ Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

## 🧪 Testing

### Quick Test Script

Run the included test script to verify all endpoints:

```bash
python test_endpoints.py
```

This will test all API endpoints including the newly added ones.

### Test Backend API Manually

```bash
# Health check
curl http://localhost:8000/health

# Test new dashboard endpoints
curl http://localhost:8000/api/dashboard/top-queries?limit=5
curl http://localhost:8000/api/dashboard/performance-trends?hours=24

# Test new monitoring endpoints
curl -X POST http://localhost:8000/api/monitoring/start
curl -X POST http://localhost:8000/api/monitoring/stop

# Create connection
curl -X POST http://localhost:8000/api/connections \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test PostgreSQL",
    "engine": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database": "testdb",
    "username": "user",
    "password": "pass",
    "ssl_enabled": false,
    "monitoring_enabled": true
  }'

# Optimize query
curl -X POST http://localhost:8000/api/optimizer/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "connection_id": 1,
    "sql_query": "SELECT * FROM users WHERE email = '\''test@example.com'\''",
    "include_execution_plan": true
  }'
```

## 🔒 Security

- **Credential Encryption**: Fernet encryption for database passwords
- **CORS Protection**: Configured allowed origins
- **Input Validation**: Pydantic schemas
- **SQL Injection Prevention**: Parameterized queries

## 📝 Project Structure

```
ai-sql-optimizer-pro/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── core/             # Core services
│   │   ├── models/           # Database models
│   │   └── db/               # SQLite database
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── services/         # API client
│   │   └── types/            # TypeScript types
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🤝 Contributing

This is a PoC (Proof of Concept). For production use:
1. Add authentication/authorization
2. Implement comprehensive error handling
3. Add extensive testing
4. Enhance security measures
5. Add more database engine support
6. Implement query execution validation

## 🐛 Recent Fixes

### 404 Error Fix (Latest)
Fixed missing API endpoints that were causing "Request failed with status code 404" errors:
- Added `GET /api/dashboard/top-queries` endpoint
- Added `GET /api/dashboard/performance-trends` endpoint  
- Added `POST /api/monitoring/start` endpoint
- Added `POST /api/monitoring/stop` endpoint

See [404_ERROR_FIX.md](404_ERROR_FIX.md) for detailed information.

## 📧 Support

For issues and questions, please open a GitHub issue.

---

**Built with ❤️ for Database Performance Optimization**

**Tech Stack**: FastAPI • React • Vite • TailwindCSS • Ollama • SQLAlchemy • PostgreSQL • MySQL • Oracle • SQL Server
