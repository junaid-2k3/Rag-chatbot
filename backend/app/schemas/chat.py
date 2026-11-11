from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .. import config


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    question: str = Field(max_length=config.MAX_QUESTION_CHARS)
    history: list[Message] = Field(default_factory=list, max_length=2 * config.MAX_HISTORY_TURNS)

    @field_validator("question")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("question must not be empty")
        return v


class Source(BaseModel):
    title: str
    heading: str
    url: str
    page: int | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    found: bool
