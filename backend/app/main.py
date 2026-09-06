"""
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_evaluation import router as evaluation_router

app = FastAPI(
    title="Intelligent Programming Assessment",
    description="Multi-language, multi-agent programming assessment framework.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(evaluation_router)


@app.get("/")
def root() -> dict:
    return {"status": "ok", "message": "Intelligent Programming Assessment API is running."}