import logging

from fastapi import APIRouter, HTTPException

from ..schemas.chat import ChatRequest, ChatResponse
from ..services import llm, rag

router = APIRouter()
log = logging.getLogger("chat")


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:  # sync def: FastAPI runs it in a worker thread
    history = [m.model_dump() for m in req.history]
    try:
        result = rag.answer(req.question, history)
    except llm.LLMUnavailable as e:
        log.warning("llm unavailable: %s", e)  # no question text in logs
        raise HTTPException(status_code=503, detail="The assistant is busy right now. Please try again in a minute.")
    log.info("chat found=%s sources=%d history=%d", result["found"], len(result["sources"]), len(history))
    return ChatResponse(answer=result["answer"], sources=result["sources"], found=result["found"])
