**Project Name:** CampusAI – AI Virtual Receptionist
**Document Owner:** Mark (Documentation Lead)
**Approved By:** Abrar (Project Lead / Scrum Master)
**Status:** Draft

---

## 1. Introduction

### 1.1 Purpose
This document specifies the software requirements for the CampusAI Virtual Receptionist. It outlines the system architecture, functional requirements, and non-functional requirements to guide the development team (Frontend, Backend, and AI integration) in building the Minimum Viable Product (MVP).

### 1.2 Scope
CampusAI is a web-based, AI-powered chatbot designed to answer student queries using an institution-specific Knowledge Base. It utilizes a Retrieval-Augmented Generation (RAG) architecture to ensure accuracy, alongside Text-to-Speech (TTS) and virtual avatar capabilities for an interactive user experience.

---

## 2. System Architecture & Technology Stack

The system follows a decoupled client-server architecture.

### 2.1 Core Technologies
*   **Frontend Client:** Next.js with TypeScript for robust UI development.
*   **Styling:** Tailwind CSS for a highly responsive web interface.
*   **Backend API:** FastAPI (Python) for handling asynchronous requests and AI orchestration.
*   **AI Integration Framework:** LangChain.
*   **Vector Database:** Chroma DB (for storing and retrieving institutional knowledge).
*   **Large Language Model (LLM):** OpenAI-compatible API.
*   **Knowledge Base Format:** JSON / Markdown documents.

### 2.2 Third-Party APIs & Libraries
*   **Text-to-Speech (TTS):** Browser Speech API.
*   **Avatar Integration:** TalkingHead (with animated/voice-only fallback).

---

## 3. Functional Requirements (FR)

These define what the system *must do* to satisfy the MVP scope.

*   **FR-1: Chat Interface**
    *   The frontend must provide a text input field and a chat log for users to converse with the AI.
*   **FR-2: RAG Processing Pipeline**
    *   Upon receiving a user query, the FastAPI backend must use LangChain to query the Chroma vector database for relevant institutional context before passing the prompt to the LLM.
*   **FR-3: Source Citation Generation**
    *   The backend response object must include the specific source (e.g., document name or URL) from the Knowledge Base used to generate the answer.
    *   The frontend must display these source citations clearly within the chat UI.
*   **FR-4: Department Escalation**
    *   If the AI cannot find a relevant answer in the Chroma DB, it must output a standardized fallback message recommending the appropriate human department for further assistance.
*   **FR-5: Text-to-Speech (TTS) Execution**
    *   The system must convert the AI's generated text response into spoken audio using the Browser Speech API.
*   **FR-6: Avatar Synchronization (Optional/Fallback)**
    *   The frontend must trigger the TalkingHead avatar to animate synchronously with the TTS audio. If the avatar fails to load, the system must degrade gracefully to a static UI with voice-only output.

---

## 4. Non-Functional Requirements (NFR)

These define system attributes such as performance, security, and usability.

*   **NFR-1: System Accuracy (Zero Hallucinations)**
    *   The LLM prompt engineering must strictly forbid generating answers outside of the provided context retrieved from Chroma DB. 
*   **NFR-2: Performance & Latency**
    *   The web interface must be responsive (mobile and desktop).
    *   The backend should aim to return the AI's text response within acceptable chat latency (e.g., < 3-5 seconds), excluding TTS generation time.
*   **NFR-3: High Availability / Error Handling**
    *   If the LLM API experiences downtime, the FastAPI backend must return a graceful error message to the frontend, preventing the application from crashing.
*   **NFR-4: Version Control & Collaboration**
    *   All code must be maintained on GitHub.
    *   Documentation (PRD, SRS) must be kept up-to-date in the repository.

---

## 5. High-Level Data Flow

1.  **User Input:** User types a question on the Next.js frontend.
2.  **API Request:** Frontend sends a POST request with the query to the FastAPI backend.
3.  **Context Retrieval:** FastAPI (via LangChain) searches the Chroma Database for similar vectors (institutional data).
4.  **LLM Generation:** LangChain sends the user query + retrieved context to the OpenAI-compatible LLM.
5.  **API Response:** FastAPI receives the answer and formats it into a JSON response (including `answer_text` and `source_citations`) and sends it back to the frontend.
6.  **UI Update & TTS:** The Next.js frontend displays the text and sources, while triggering the Browser Speech API to read the text aloud through the Avatar.
