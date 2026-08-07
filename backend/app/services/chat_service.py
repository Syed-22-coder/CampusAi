import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence, Tuple

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ChatService:
    """Service for handling chat interactions"""

    def __init__(self, rag_service=None):
        self.conversations = {}  # Store conversation history in memory (temp)
        self.default_rag_service = rag_service
        self.logger = logger

    async def process_chat_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        rag_service=None
    ) -> Dict:
        """
        Process a chat message and return response with sources

        Args:
            message: User's chat message
            conversation_id: Optional conversation ID for context
            rag_service: RAG service instance for retrieving context

        Returns:
            Dict with response, sources, and conversation_id
        """
        try:
            # Generate or use provided conversation ID
            if not conversation_id:
                conversation_id = str(uuid.uuid4())

            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = []

            previous_messages = list(self.conversations[conversation_id])
            active_rag_service = rag_service or self.default_rag_service

            self.conversations[conversation_id].append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            sources = []
            response_text = ""

            if active_rag_service:
                try:
                    response_text, sources, _ = await active_rag_service.chat(
                        message=message,
                        chat_history=self._build_chat_history(previous_messages),
                    )
                except Exception as e:
                    self.logger.warning(f"RAG retrieval failed: {str(e)}")
                    sources = []
                    response_text = self._format_response(message, "")
            else:
                response_text = self._format_response(message, "")

            self.conversations[conversation_id].append({
                "role": "assistant",
                "content": response_text,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            self.logger.info(
                f"Chat message processed",
                extra={"extra_data": {
                    "conversation_id": conversation_id,
                    "message_length": len(message),
                    "sources_found": len(sources)
                }}
            )

            return {
                "response": response_text,
                "sources": sources,
                "conversation_id": conversation_id
            }

        except Exception as e:
            self.logger.error(f"Chat processing error: {str(e)}")
            raise

    async def process_query(
        self,
        query: str,
        context: Optional[str] = None,
        rag_service=None
    ) -> Dict:
        """
        Process a knowledge base query

        Args:
            query: Knowledge base query
            context: Optional context for the query
            rag_service: RAG service instance

        Returns:
            Dict with answer, confidence, and sources
        """
        try:
            sources = []
            answer = ""
            confidence = 0.0
            active_rag_service = rag_service or self.default_rag_service

            if active_rag_service:
                try:
                    answer, sources, confidence = await active_rag_service.query(query, context)
                except Exception as e:
                    self.logger.warning(f"Query processing failed: {str(e)}")
                    answer = "I couldn't find information about that. Please try rephrasing your question."
                    confidence = 0.0
            else:
                answer = "Query processing not available. RAG service not initialized."
                confidence = 0.0

            self.logger.info(
                f"Query processed",
                extra={"extra_data": {
                    "query_length": len(query),
                    "answer_length": len(answer),
                    "confidence": confidence,
                    "sources_found": len(sources)
                }}
            )

            return {
                "answer": answer,
                "confidence": confidence,
                "sources": sources
            }

        except Exception as e:
            self.logger.error(f"Query error: {str(e)}")
            raise

    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """Get conversation history"""
        return self.conversations.get(conversation_id, [])

    def _build_chat_history(self, messages: Sequence[Dict]) -> List[Tuple[str, str]]:
        chat_history: List[Tuple[str, str]] = []
        pending_user_message: Optional[str] = None

        for message in messages:
            role = message.get("role")
            content = message.get("content", "")
            if role == "user":
                pending_user_message = content
            elif role == "assistant" and pending_user_message is not None:
                chat_history.append((pending_user_message, content))
                pending_user_message = None

        return chat_history

    def _format_response(self, message: str, context: str) -> str:
        """Format response with context (placeholder)"""
        if context:
            return f"Based on the college information, I found relevant details about your question. Context: {context[:200]}..."
        else:
            return f"Thank you for your question: '{message}'. This feature is being set up."

    async def save_feedback(
        self,
        response_id: str,
        rating: int,
        comment: Optional[str] = None
    ) -> Dict:
        """Save user feedback on responses"""
        try:
            self.logger.info(
                "Feedback received",
                extra={"extra_data": {
                    "response_id": response_id,
                    "rating": rating,
                    "has_comment": comment is not None
                }}
            )

            return {
                "success": True,
                "message": "Feedback recorded successfully"
            }

        except Exception as e:
            self.logger.error(f"Feedback save error: {str(e)}")
            raise
