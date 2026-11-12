import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .routes.chat import router

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logging.getLogger().setLevel(logging.INFO)  # Lambda pre-installs a handler, so basicConfig alone does not set the level
logging.getLogger("httpx").setLevel(logging.WARNING)

app = FastAPI(
    title="FAST Peshawar RAG chatbot",
    docs_url="/docs" if config.ENABLE_DOCS else None,
    redoc_url=None,
    openapi_url="/openapi.json" if config.ENABLE_DOCS else None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type"],
    allow_credentials=False,
)
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
