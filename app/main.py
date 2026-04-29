"""
JSR-Payment-Agent — FastAPI Application Entry Point.

This is the main module that bootstraps the FastAPI app, configures
CORS middleware, and registers all API routers.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.chat import router as chat_router

# ──────────────────────────────────────────────
# Load environment variables
# ──────────────────────────────────────────────
load_dotenv()

# ──────────────────────────────────────────────
# Application factory
# ──────────────────────────────────────────────
app = FastAPI(
    title="JSR Payment Agent",
    description=(
        "مساعد جسر الذكي — واجهة برمجة تطبيقات لوكيل الذكاء الاصطناعي "
        "المتخصص في إدارة الرواتب والتأمينات الاجتماعية ونظام مُدد.\n\n"
        "Jisr AI Assistant — API for the AI agent specialized in "
        "payroll management, GOSI, and Mudad systems."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ──────────────────────────────────────────────
# CORS configuration
# ──────────────────────────────────────────────
_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# Register routers
# ──────────────────────────────────────────────
app.include_router(chat_router, prefix="/api/v1")


# ──────────────────────────────────────────────
# Health check
# ──────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "JSR Payment Agent",
            "version": "1.0.0",
            "message": "مرحبًا بك في واجهة جسر الذكية 🚀",
        }
    )


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}


# ──────────────────────────────────────────────
# Uvicorn runner (for `python -m app.main`)
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("DEBUG", "true").lower() == "true",
    )
