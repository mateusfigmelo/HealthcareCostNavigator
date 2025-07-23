"""Main FastAPI application for Healthcare Cost Navigator."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import ai_router, providers_router
from app.config import settings

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Healthcare Cost Navigator MVP - Search hospitals by MS-DRG procedures with AI assistant",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://frontend:3000",
        "*"  # Allow all origins for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(providers_router)
app.include_router(ai_router)


@app.get("/")
async def root() -> dict[str, str | dict[str, str]]:
    """Root endpoint with basic information."""
    return {
        "message": "Healthcare Cost Navigator API",
        "version": "0.1.0",
        "endpoints": {
            "providers": "/providers",
            "ai_assistant": "/ask",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "healthcare-cost-navigator"}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Custom exception handler for HTTP errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """General exception handler."""
    return JSONResponse(
        status_code=500, content={"detail": "Internal server error", "status_code": 500}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
