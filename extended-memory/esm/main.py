"""ESM FastAPI Application Entry Point"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
from logging.handlers import RotatingFileHandler
import time
from sqlalchemy import text
from contextlib import asynccontextmanager

from esm.config import get_settings
from esm.database import engine, Base
from esm.api import memories, search, assistants, shared, analytics, export, websocket
from esm.utils.exceptions import ESMException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler("logs/esm.log", maxBytes=10 * 1024 * 1024, backupCount=5),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting ESM application...")
    # Create database tables (handled by migrations)
    # Base.metadata.create_all(bind=engine)
    # logger.info("📊 Database tables created")

    # Initialize search indices
    from esm.services.search_service import SearchService
    search_service = SearchService()
    await search_service.initialize_indices()
    logger.info("🔍 Search indices initialized")

    yield

    logger.info("🛑 Shutting down ESM application...")

# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title="Extended Sienna Memory (ESM)",
    description="AI Memory System with Multi-Assistant Support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    return response

# Exception handlers
@app.exception_handler(ESMException)
async def esm_exception_handler(request: Request, exc: ESMException):
    logger.error(f"ESM Exception: {exc.message} - Detail: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "detail": exc.detail}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP Error", "detail": "An error occurred"}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": db_ok,
        "version": "1.0.0",
        "timestamp": time.time()
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Extended Sienna Memory (ESM) API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Include routers
app.include_router(memories.router, prefix="/api/v1/memories", tags=["memories"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(assistants.router, prefix="/api/v1/assistants", tags=["assistants"])
app.include_router(shared.router, prefix="/api/v1/shared", tags=["shared"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(export.router, prefix="/api/v1/export", tags=["export"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "esm.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
