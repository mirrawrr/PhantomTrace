
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from openai import OpenAIError
from app.tools.log_parser import parse_security_logs
from app.tools.event_correlator import correlate_events
from app.tools.evidence_verifier import verify_evidence

from app.services.meta_ai import investigate_with_ai
from app.services.investigation_agent import investigate_agent, InvalidLogs
from app.services.adaptive_agent import AdaptiveRequest, investigate_adaptive

app = FastAPI(
    title="PhantomTrace API",
    description="AI-powered digital forensics investigation agent",
    version="0.3.0"
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

@app.post("/api/evidence/analyze")
def analyze_evidence(request: InvestigationRequest):
    parsed = parse_security_logs(request.logs)

    if parsed["errors"]:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Security log validation failed.",
                "errors": parsed["errors"],
            },
        )

    events = parsed["events"]
    correlation = correlate_events(events)

    verification = verify_evidence(
        events,
        correlation["findings"],
    )

    return {
        "status": "completed",
        "total_events": parsed["total_events"],
        "events": events,
        "correlation": correlation,
        "verification": verification,
    }


@app.post("/api/investigate/agent")
def agent_investigate(request: InvestigationRequest):
    try:
        return investigate_agent(request.logs)
    except InvalidLogs as exc:
        raise HTTPException(status_code=422, detail={"message": str(exc), "errors": exc.errors}) from exc
    except (OpenAIError, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail="Agent investigation failed. Check Meta API configuration or retry.") from exc


@app.post("/api/investigate/adaptive")
def adaptive_investigate(request: AdaptiveRequest):
    try:
        return investigate_adaptive(request)
    except InvalidLogs as exc:
        raise HTTPException(status_code=422, detail={"message": str(exc), "errors": exc.errors}) from exc
    except (OpenAIError, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail="Adaptive investigation failed. Check configuration or retry.") from exc
