from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import os
from dotenv import load_dotenv
from app.utils.logger import get_logger
from app.api.routes import router as api_router

load_dotenv()

logger = get_logger(__name__)

app = FastAPI(
    title="CampusAI API",
    description="AI-powered virtual receptionist for Centennial College",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS configuration
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    os.getenv("FRONTEND_URL", "http://localhost:3000"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Error handling middleware
@app.middleware("http")
async def error_handler_middleware(request: Request, call_next):
    """Global error handling middleware"""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}", extra={"extra_data": {
            "path": request.url.path,
            "method": request.method
        }})
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal Server Error",
                "message": "An unexpected error occurred"
            }
        )


# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation Error",
            "message": "Invalid request parameters",
            "details": jsonable_encoder(exc.errors())
        }
    )


# Register API routes
app.include_router(api_router, prefix="/api", tags=["chat"])


@app.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "name": "CampusAI API",
        "version": "0.1.0",
        "status": "healthy",
        "docs": "/docs",
        "description": "AI-powered virtual receptionist for Centennial College"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "0.1.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
