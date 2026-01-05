"""
AI SQL Optimizer Pro - Main Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from loguru import logger

from app.api import connections, monitoring, optimizer, dashboard, feedback, configuration, ml_performance, indexes, workload, patterns
from app.models.database import init_db
from app.core.monitoring_agent import MonitoringAgent

# Initialize monitoring agent
monitoring_agent = None


# Inject monitoring agent into monitoring API
def inject_monitoring_agent():
    """Inject monitoring agent into monitoring API module"""
    from app.api import monitoring as monitoring_api
    monitoring_api.set_monitoring_agent(monitoring_agent)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global monitoring_agent
    
    # Startup
    logger.info("🚀 Starting AI SQL Optimizer Pro...")
    
    # Initialize database
    init_db()
    logger.info("✅ Database initialized")
    
    # Start monitoring agent if enabled
    if os.getenv("MONITORING_ENABLED", "true").lower() == "true":
        monitoring_agent = MonitoringAgent()
        monitoring_agent.start()
        inject_monitoring_agent()
        logger.info("✅ Monitoring agent started")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down AI SQL Optimizer Pro...")
    if monitoring_agent:
        monitoring_agent.stop()
        logger.info("✅ Monitoring agent stopped")


# Create FastAPI app
app = FastAPI(
    title="AI SQL Optimizer Pro",
    description="Cross-Database AI-Powered SQL Optimization Engine with Proactive Monitoring",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS with enhanced settings
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
logger.info(f"Configuring CORS for origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "User-Agent",
        "DNT",
        "Cache-Control",
        "X-Requested-With",
    ],
    expose_headers=[
        "Content-Length",
        "Content-Type",
        "X-Request-ID",
    ],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Include routers
app.include_router(connections.router, prefix="/api/connections", tags=["Connections"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["Monitoring"])
app.include_router(optimizer.router, prefix="/api/optimizer", tags=["Optimizer"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(configuration.router, prefix="/api/config", tags=["Configuration"])
app.include_router(ml_performance.router, prefix="/api/ml", tags=["ML Performance"])
app.include_router(indexes.router, prefix="/api/indexes", tags=["Indexes"])
app.include_router(workload.router, prefix="/api/workload", tags=["Workload Analysis"])
app.include_router(patterns.router, prefix="/api/patterns", tags=["Patterns"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI SQL Optimizer Pro API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Ollama connection
        from app.core.ollama_client import OllamaClient
        ollama_client = OllamaClient()
        ollama_status = await ollama_client.check_health()
        
        return {
            "status": "healthy",
            "ollama": ollama_status,
            "monitoring_agent": monitoring_agent.is_running() if monitoring_agent else False
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("BACKEND_HOST", "0.0.0.0"),
        port=int(os.getenv("BACKEND_PORT", 8000)),
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )
