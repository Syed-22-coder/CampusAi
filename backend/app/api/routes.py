from fastapi import APIRouter, status
from app.schemas.chat import (
    ChatRequest, ChatResponse, QueryRequest, QueryResponse,
    FeedbackRequest
)
from app.schemas.base import ResponseModel
from app.services.chat_service import ChatService
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Service instances
llm_service = LLMService()
rag_service = RAGService(llm_service=llm_service)
chat_service = ChatService()


@router.post("/chat", response_model=ResponseModel, status_code=status.HTTP_200_OK)
async def chat(request: ChatRequest):
    """
    Chat endpoint for conversational interactions

    Returns chat response with optional source citations
    """
    try:
        result = await chat_service.process_chat_message(
            message=request.message,
            conversation_id=request.conversation_id,
            rag_service=rag_service
        )

        return ResponseModel(
            success=True,
            data=result,
            message="Chat response generated successfully"
        )
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        return ResponseModel(
            success=False,
            message="Error processing chat message",
            error=str(e)
        )


@router.post("/query", response_model=ResponseModel, status_code=status.HTTP_200_OK)
async def query(request: QueryRequest):
    """
    Query endpoint for knowledge base searches

    Returns answer with confidence score and sources
    """
    try:
        result = await chat_service.process_query(
            query=request.query,
            context=request.context,
            rag_service=rag_service
        )

        return ResponseModel(
            success=True,
            data=result,
            message="Query processed successfully"
        )
    except Exception as e:
        logger.error(f"Query endpoint error: {str(e)}")
        return ResponseModel(
            success=False,
            message="Error processing query",
            error=str(e)
        )


@router.post("/feedback", response_model=ResponseModel, status_code=status.HTTP_200_OK)
async def feedback(request: FeedbackRequest):
    """
    Feedback endpoint for recording user ratings

    Used to track response quality and improve system
    """
    try:
        result = await chat_service.save_feedback(
            response_id=request.response_id,
            rating=request.rating,
            comment=request.comment
        )

        return ResponseModel(
            success=result.get("success", True),
            message=result.get("message", "Feedback saved")
        )
    except Exception as e:
        logger.error(f"Feedback endpoint error: {str(e)}")
        return ResponseModel(
            success=False,
            message="Error saving feedback",
            error=str(e)
        )


@router.get("/conversations/{conversation_id}", response_model=ResponseModel)
async def get_conversation_history(conversation_id: str):
    """
    Get conversation history for a specific conversation

    Used for multi-turn chat context
    """
    try:
        history = chat_service.get_conversation_history(conversation_id)

        return ResponseModel(
            success=True,
            data={"conversation_id": conversation_id, "messages": history},
            message="Conversation history retrieved"
        )
    except Exception as e:
        logger.error(f"Get conversation error: {str(e)}")
        return ResponseModel(
            success=False,
            message="Error retrieving conversation",
            error=str(e)
        )
