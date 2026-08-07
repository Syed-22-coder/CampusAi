from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., min_length=1, max_length=1000)
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for multi-turn chat")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "What are the admissions requirements?",
                "conversation_id": "conv_123",
            }
        }
    )


class Source(BaseModel):
    """Source citation model"""

    title: str
    excerpt: str
    relevance: Optional[float] = Field(None, ge=0, le=1)
    url: Optional[str] = None
    section: Optional[str] = None
    source_path: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str
    sources: List[Source] = Field(default_factory=list, description="Source citations")
    conversation_id: str


class QueryRequest(BaseModel):
    """Request model for query endpoint"""
    query: str = Field(..., min_length=1, max_length=1000)
    context: Optional[str] = Field(None, description="Optional context for the query")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "Tell me about engineering programs",
                "context": "I'm interested in full-time programs",
            }
        }
    )


class QueryResponse(BaseModel):
    """Response model for query endpoint"""
    answer: str
    confidence: float = Field(..., ge=0, le=1)
    sources: List[Source] = Field(default_factory=list)


class FeedbackRequest(BaseModel):
    """Request model for feedback endpoint"""
    response_id: str
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    comment: Optional[str] = Field(None, max_length=500)
