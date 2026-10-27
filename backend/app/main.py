
from fastapi import FastAPI

app = FastAPI(
    title="PhantomTrace API",
    description="AI-powered digital forensics investigation agent",
    version="0.1.0"
)

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
