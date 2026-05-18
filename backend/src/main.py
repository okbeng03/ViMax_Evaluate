"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.db.database import init_db, close_db
from src.utils.logger import setup_logging, logger
from src.utils.exceptions import AppException


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Agent图像评估系统...")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down...")
    await close_db()
    logger.info("Database connections closed")


app = FastAPI(
    title=settings.app_name,
    description="Agent图像评估系统 - 提供CLIP和LLM驱动的图像质量评估能力",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle application exceptions."""
    status_codes = {
        "VALIDATION_ERROR": 400,
        "TASK_NOT_FOUND": 404,
        "PROJECT_NOT_FOUND": 404,
        "TASK_NOT_COMPLETED": 202,
        "IMAGE_FORMAT_UNSUPPORTED": 422,
        "IMAGE_LOAD_FAILED": 422,
    }
    status_code = status_codes.get(exc.code, 500)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Agent图像评估系统", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


logger.info("FastAPI application created")
