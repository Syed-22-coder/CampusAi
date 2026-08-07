# CampusAI API Documentation

**Base URL:** `http://localhost:8000`  
**Authentication:** None required for MVP.

## Overview
This document outlines the REST API endpoints for the CampusAI backend. It includes core features like the AI-powered chat, Retrieval-Augmented Generation (RAG) queries, user feedback, and conversation history.

### Standard Response Envelope
All API endpoints return data using the following standard JSON envelope format:

```json
{
  "success": true,
  "data": {},
  "message": "String message",
  "error": null
}
```

*Note: A `success: true` status does not always guarantee the LLM generated a complete answer. If the local model (Ollama) is unavailable, the backend may still return a degraded `success: true` response with a graceful fallback message alongside any retrieved citations.*

---

## 1. Chat Interaction
Send a chat message to the AI assistant within an active conversation session.

* **URL:** `/api/chat`
* **Method:** `POST`

**Request Body:**
```json
{
  "message": "Where is Progress Campus?",
  "conversation_id": "conv_123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "response": "Progress Campus is located at 941 Progress Ave., Scarborough, ON M1G 3T8.",
    "sources": [
      {
        "title": "Centennial College: Campuses and Facilities",
        "excerpt": "## Progress Campus **Address:** 941 Progress Ave., Scarborough, ON M1G 3T8 ...",
        "url": null,
        "section": "Progress Campus",
        "source_path": "facilities/centennial_facilities.md",
        "relevance": 0.57
      }
    ],
    "conversation_id": "conv_123"
  },
  "message": "Chat response generated successfully",
  "error": null
}
```

---

## 2. Knowledge Base Query
Perform a direct RAG query against the knowledge base (does not require or persist conversation state).

* **URL:** `/api/query`
* **Method:** `POST`

**Request Body:**
```json
{
  "query": "Where is Progress Campus?",
  "context": "I am looking for business programs."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "answer": "Progress Campus is located at 941 Progress Ave., Scarborough, ON M1G 3T8.",
    "confidence": 0.75,
    "sources": [
      {
        "title": "Centennial College: Campuses and Facilities",
        "excerpt": "## Progress Campus **Address:** 941 Progress Ave., Scarborough, ON M1G 3T8 ...",
        "url": null,
        "section": "Progress Campus",
        "source_path": "facilities/centennial_facilities.md",
        "relevance": 0.57
      }
    ]
  },
  "message": "Query processed successfully",
  "error": null
}
```

---

## 3. Submit Feedback
Submit user feedback on a specific AI response.

* **URL:** `/api/feedback`
* **Method:** `POST`

**Request Body:**
```json
{
  "response_id": "resp_123",
  "rating": 5,
  "comment": "Very helpful."
}
```

---

## 4. Get Conversation History
Retrieve the message history for a specific conversation ID.

* **URL:** `/api/conversations/{conversation_id}`
* **Method:** `GET`

**Response:**
```json
{
  "success": true,
  "data": {
    "conversation_id": "conv_123",
    "messages": [
      {
        "role": "user",
        "content": "Where is Progress Campus?",
        "timestamp": "2026-07-31T18:00:00+00:00"
      },
      {
        "role": "assistant",
        "content": "Progress Campus is located at 941 Progress Ave., Scarborough, ON M1G 3T8.",
        "timestamp": "2026-07-31T18:00:05+00:00"
      }
    ]
  },
  "message": "Success",
  "error": null
}
```
