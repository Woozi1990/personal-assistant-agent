import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field

from services.assistant_service import AssistantService

logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    session_id: str
    status: str
    message: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.assistant = AssistantService()
    yield
    del app.state.assistant


app = FastAPI(
    title="Personal Assistant",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request):
    assistant = http_request.app.state.assistant

    try:
        result = await assistant.chat(
            message=request.message,
            thread_id=request.session_id
        )

        return ChatResponse(
            session_id=request.session_id,
            status=result["status"],
            message=result["message"]
        )

    except Exception:
        logger.exception(
            "Chat request failed. session_id=%s",
            request.session_id,
        )

        raise HTTPException(
            status_code=500,
            detail="Internal server error",
        ) from None
