
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from openai import OpenAIError

from app.services.meta_ai import investigate_with_ai

app = FastAPI(
    title="PhantomTrace API",
    description="AI-powered digital forensics investigation agent",
    version="0.2.0"
)

class InvestigationRequest(BaseModel):
    logs: str = Field(min_length=1, max_length=20000)

@app.get("/")
def root():
    return {
        "project": "PhantomTrace",
        "status": "running",
        "ai_model": "Meta Muse Spark"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/api/investigate")
def investigate(request: InvestigationRequest):
    try:
        analysis = investigate_with_ai(request.logs)
        return {
            "status": "completed",
            "model": "Meta Muse Spark",
            "analysis": analysis
        }
    except (OpenAIError, RuntimeError):
        raise HTTPException(
            status_code=502,
            detail="AI analysis failed. Check server logs and Meta API configuration."
        )