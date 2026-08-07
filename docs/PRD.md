**Project Name:** CampusAI – AI Virtual Receptionist
**Document Owner:** Mark (Documentation Lead)
**Approved By:** Abrar (Project Lead / Scrum Master)
**Status:** Draft

---

## 1. Project Overview

### 1.1 Problem Statement
Students spend significant time searching through multiple college websites or waiting for staff to answer repetitive questions regarding:
* Admissions
* Financial aid
* Registration
* IT support
* Campus services
* Academic advising

### 1.2 Proposed Solution
**CampusAI** is an AI-powered virtual receptionist designed to answer student questions. The system utilizes **Retrieval-Augmented Generation (RAG)** frameworks combined with an LLM (like ChatGPT or DeepSeek) to pull answers directly from verified college information. It transparently displays official sources for reliability and communicates responses using a virtual avatar equipped with text-to-speech capabilities.

---

## 2. Product Scope

### Minimum Viable Product (MVP) Scope

**Must Have (Required)**
* **AI chatbot:** To process user questions using AI.
* **RAG knowledge base:** So the information provided is strictly institution-specific.
* **Source citations:** So the information is reliable and can be verified by the user.
* **Department recommendations:** For further specification and escalation if the AI cannot fully resolve the issue.
* **Text-to-speech:** So the chatbot can speak its responses aloud.
* **Responsive web interface:** For a nice UI and better UX across desktop and mobile devices.

**Nice to Have**
* Voice input
* Animated avatar
* Conversation history
* Multiple languages

**Future Scope (Needs school authentication)**
* Student portal login
* Grades
* Tuition balances
* Appointment booking

---

## 3. Non-Functional Requirements & Risk Management

To ensure project success within the given timeframe, the following risks and mitigations are established as system constraints:

* **Accuracy (Zero Hallucinations):** The AI responses must be strictly restricted to verified official sources. 
* **Avatar Fallback:** If the TalkingHead avatar integration takes too long, the system must utilize an animated fallback or a voice-only option to ensure the MVP deadline is met.
* **API Reliability:** API connections (LLM, Speech, etc.) must be tested early. A backup demo must be prepared to mitigate potential live API failures.
* **Scope Management:** Due to strict time constraints, the team will focus solely on the "Must Have" MVP features. Any scope creep will be immediately deferred to the "Future Scope".

---

## 4. Technology Stack 

* **Frontend:** Next.js + TypeScript, Tailwind CSS
* **Backend:** FastAPI
* **AI & Database:** LangChain, Chroma (Vector Database), OpenAI-compatible API
* **Knowledge Base:** JSON / Markdown
* **Additional Integrations:** TalkingHead (Avatar), Browser Speech API (Text-to-Speech)
