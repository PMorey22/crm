from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent import RealEstateAgent


app = FastAPI(
    title="AI Real Estate Lead Agent",
    description="Agentic AI workflow integration POC",
    version="1.0.0"
)

agent = RealEstateAgent()


class LeadRequest(BaseModel):
    session_id: str
    message: str


@app.get("/")
def health_check():
    return {
        "status": "running",
        "service": "AI Real Estate Lead Agent"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/agent/process")
def process_lead(request: LeadRequest):
    try:
        return agent.process(
            session_id=request.session_id,
            message=request.message
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )