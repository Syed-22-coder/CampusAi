# CampusAI Meeting 4 Deliverables and Execution Guide

**Meeting 4 Date**: August 2, 2026  
**Current Date**: Friday, July 31, 2026  
**Status**: In Progress  
**Theme**: Core AI integration goes live. CampusAI should answer real student questions by the end of this sprint.

---

## Deliverable Overview

| Team Member | Role | Deliverable | Priority |
|---|---|---|---|
| **Abrar** | Project Lead | LangChain + ChromaDB + Ollama RAG pipeline, `/api/chat` returns real answers | CRITICAL |
| **Mathew** | AI Research Lead | Finalize knowledge base accuracy, source metadata, retrieval QA | CRITICAL |
| **Syed** | UI/UX Lead | Real chat frontend connected to `/api/chat` | HIGH |
| **Mark** | Documentation Lead | Finalize PRD/SRS, create API.md, update board, start Final Report | HIGH |
| **Nairobi** | QA and Presentation Lead | Finalize Charter, 80% slides, Test Plan, demo script, start integration testing | HIGH |

**Dependency chain**: Mathew's knowledge quality -> Abrar's RAG backend -> Syed's frontend demo -> Nairobi's integration testing and demo rehearsal. Mark's docs run in parallel but must match what is actually built.

---

## Execution Contract

This section is the Meeting 4 source of truth for implementation details. If any task wording below is vague, use this section first.

### Current Backend State as of Friday, July 31, 2026

- Abrar's backend Meeting 4 work is already implemented locally and pushed.
- Live endpoints exist for:
  - `POST /api/chat`
  - `POST /api/query`
  - `POST /api/feedback`
  - `GET /api/conversations/{conversation_id}`
- Knowledge-base indexing command:
  - `python -m app.services.knowledge_loader --reset`
- Chroma persistence directory:
  - `backend/chromadb_data/`
- Default local runtime values now checked into the backend:
  - `OLLAMA_BASE_URL=http://localhost:11434`
  - `OLLAMA_MODEL=qwen2.5:3b-instruct`
  - `OLLAMA_TIMEOUT_SECONDS=180`
  - `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2`
  - `CHROMA_COLLECTION_NAME=centennial_knowledge_base`
- Acceptable stronger local model if someone already has it installed:
  - `qwen2.5:7b-instruct`

### Required Knowledge Metadata Format

Every `knowledge/**/*.md` file should use YAML frontmatter in this exact shape:

```markdown
---
title: Progress Campus
source_url: https://www.centennialcollege.ca/campuses/progress/
---

# Progress Campus

Content here...
```

Rules:

- `title` is required.
- `source_url` is optional.
- If `source_url` is present, it must be a real official source.
- If there is no single reliable source URL, omit `source_url`.
- Do not invent URLs.
- Keep file topics focused. Split overly broad files when retrieval quality suffers.
- Keep the first heading aligned with the file topic whenever possible.

### Live API Contract

All backend responses use this envelope:

```json
{
  "success": true,
  "data": {},
  "message": "Success",
  "error": null
}
```

#### `POST /api/chat`

Request:

```json
{
  "message": "Where is Progress Campus?",
  "conversation_id": "conv_123"
}
```

Response shape:

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

#### `POST /api/query`

Request:

```json
{
  "query": "Where is Progress Campus?",
  "context": "I am looking for business programs."
}
```

Response shape:

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

#### `POST /api/feedback`

Request:

```json
{
  "response_id": "resp_123",
  "rating": 5,
  "comment": "Very helpful."
}
```

#### `GET /api/conversations/{conversation_id}`

Response `data` shape:

```json
{
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
}
```

Frontend and QA note:

- `success: true` does not always mean the model answered normally.
- If Ollama is unavailable, the backend may still return `success: true` with a graceful fallback message and any retrieved citations.
- Treat that as a degraded state, not a UI crash.

### Required Proof of Done

Every owner should be able to show all of the following by Saturday, August 2, 2026:

- The exact files they changed.
- One concrete proof artifact:
  - screenshot, test run, API response, or demo output.
- A short summary of what is complete and what is still not complete.
- Work pushed to GitHub.

Recommended proof by role:

- Abrar: `pytest` output and one working `/api/chat` or `/api/query` example.
- Mathew: `knowledge/RETRIEVAL_TEST_LOG.md` with at least 20 questions.
- Syed: screenshot or local demo of the chat UI hitting the real backend.
- Mark: committed docs files that match live backend behavior.
- Nairobi: committed test plan, demo script, and first-round integration notes.

---

## Abrar - Project Lead / Backend Integration

### Goal

Make CampusAI actually answer questions.

### Task 1: Integrate LangChain into the Backend

**What to do**

1. Wire LangChain into `backend/app/services/rag_service.py`.
2. Replace placeholder logic with real LangChain components:
   - `RecursiveCharacterTextSplitter`
   - `HuggingFaceEmbeddings` using `all-MiniLM-L6-v2`
   - `Chroma` vectorstore wrapper
   - retrieval chain logic for query answering
3. Keep prompt templates in a dedicated file such as `backend/app/services/prompts.py`.

**Deliverable**: `rag_service.py` no longer returns placeholder retrieval behavior.

### Task 2: Load the Knowledge Base into ChromaDB

**What to do**

1. Implement `backend/app/services/knowledge_loader.py`.
2. Walk the `knowledge/` directory and index all `.md` and relevant `.json` knowledge sources.
3. Chunk documents, generate embeddings, and upsert them into the `centennial_knowledge_base` collection.
4. Attach chunk metadata for citations:
   - `title`
   - `section`
   - `source_path`
   - `source_url` when available
5. Support rerunning indexing with:
   - `python -m app.services.knowledge_loader --reset`

**Deliverable**: Running the loader populates ChromaDB with the current knowledge base.

### Task 3: Connect Ollama to the RAG Pipeline

**What to do**

1. Implement real Ollama calls in `backend/app/services/llm_service.py`.
2. Use the OpenAI-compatible endpoint at `OLLAMA_BASE_URL`.
3. Use the checked-in default model `qwen2.5:3b-instruct` unless there is a documented reason to switch.
4. Keep `is_available()` meaningful and graceful when Ollama is not running.
5. Do not add an OpenAI fallback.

**Deliverable**: `LLMService.generate_response()` returns real model output.

### Task 4: `/api/chat` Returns Real AI Responses

**What to do**

1. Pass a real `RAGService` instance into `ChatService`.
2. Instantiate `RAGService` and `LLMService` once and inject them in `backend/app/api/routes.py`.
3. Verify multi-turn conversation history still works.

**Deliverable**: A real student question to `/api/chat` returns a grounded answer.

### Task 5: Return Source Citations with Each Response

**What to do**

1. Populate `sources` in chat and query responses from indexed metadata.
2. Each source should include at least:
   - `title`
   - `excerpt`
3. Include these when available:
   - `url`
   - `section`
   - `source_path`
   - `relevance`

**Deliverable**: Responses include traceable citations instead of placeholders.

### Task 6: Basic Integration Tests

**What to do**

1. Extend `backend/tests/test_api.py` or add `backend/tests/test_rag_pipeline.py`.
2. Cover:
   - knowledge base loads successfully
   - known question returns non-empty answer with at least one source
   - Ollama-unavailable case degrades gracefully
3. Keep existing API contract tests passing.

**Deliverable**: Test suite covers the real RAG path.

### Success Criteria for Abrar

- Backend answers real knowledge-based questions.
- Swagger UI at `/docs` can demo a grounded answer.
- Integration tests pass.
- Code is pushed to GitHub.

### Files to Create or Modify

- `backend/app/services/rag_service.py`
- `backend/app/services/llm_service.py`
- `backend/app/services/knowledge_loader.py`
- `backend/app/services/prompts.py`
- `backend/app/api/routes.py`
- `backend/tests/test_rag_pipeline.py`

---

## Mathew - AI Research Lead

### Goal

Ensure the knowledge base produces accurate answers.

### Task 1: Finish Official Centennial Knowledge Files

**What to do**

1. Complete the department, program, facility, and policy files.
2. Make sure the major student-facing topics exist:
   - admissions
   - tuition and financial aid
   - programs by school
   - campus locations and hours
   - key student services
   - important dates
3. Cross-check facts against official Centennial sources.
4. Flag time-sensitive facts with wording such as "verify before stating" when appropriate.

**Deliverable**: Knowledge base is broad enough to answer common student questions.

### Task 2: Add Source Metadata

**What to do**

1. Add YAML frontmatter to each knowledge markdown file.
2. Use this exact minimum format:

```markdown
---
title: Admissions Requirements
source_url: https://www.centennialcollege.ca/admissions/
---
```

3. `title` is required.
4. Omit `source_url` when no single official source URL exists.
5. Do not fabricate links.

**Deliverable**: Every knowledge file has usable title/source metadata.

### Task 3: Test at Least 20 Sample Questions

**What to do**

1. Once indexing is ready, run at least 20 realistic student questions through `/api/query` or `/api/chat`.
2. Record:
   - question
   - expected answer summary
   - actual answer summary
   - source file(s) returned
   - pass/fail
   - notes

**Deliverable**: A retrieval test log with 20 or more questions.

**Suggested file**: `knowledge/RETRIEVAL_TEST_LOG.md`

### Task 4: Fix Missing or Inaccurate Knowledge

**What to do**

1. Identify gaps and inaccuracies from the retrieval log.
2. Correct the relevant files.
3. Re-run failed questions after the fix.

**Deliverable**: Known gaps are closed and retrieval quality improves.

### Task 5: Improve Chunking if Retrieval Quality Is Poor

**What to do**

1. If retrieval quality is weak, work with Abrar on chunk size and overlap tuning.
2. Prefer smaller, focused files and sections over long mixed-topic documents.

**Deliverable**: Retrieval returns relevant chunks for most test questions.

### Success Criteria for Mathew

- Most common student questions return relevant, accurate content.
- Every knowledge file has source metadata.
- 20 or more questions are tested and logged.
- Files are pushed to GitHub.

### Files to Create or Modify

- `knowledge/**/*.md`
- `knowledge/RETRIEVAL_TEST_LOG.md`

---

## Syed - UI/UX Lead

### Goal

Build the real frontend.

### Task 1: Chat Interface, Message Bubbles, Input Box, Loading Indicator

**What to do**

1. Implement the components described in `frontend/Next.js Frontend Layout Components.md`.
2. Build:
   - `ChatMessage.tsx`
   - `ChatInput.tsx`
   - loading or typing indicator
3. Assemble them into a real chat page such as `frontend/app/chat/page.tsx`.

**Deliverable**: Styled chat UI runs locally with `npm run dev`.

### Task 2: Connect to `/api/chat`

**What to do**

1. Implement `frontend/lib/api.ts`.
2. Call the live backend using `NEXT_PUBLIC_API_URL`.
3. Send:

```json
{
  "message": "Where is Progress Campus?",
  "conversation_id": "conv_123"
}
```

4. Handle the `ResponseModel` envelope:
   - `success`
   - `data`
   - `message`
   - `error`
5. Persist and reuse `data.conversation_id` across follow-up turns.
6. Render `data.response` and `data.sources` exactly as returned.
7. Handle:
   - network failures
   - `success: false`
   - degraded `success: true` fallback messages when Ollama is unavailable

**Deliverable**: Typing a question in the browser returns a real backend response.

### Task 3: Display Citations

**What to do**

1. Implement `SourceCitation.tsx` using the citation data from the backend.
2. Show at least:
   - title
   - excerpt
3. Optionally show:
   - section
   - source file path
   - source URL

**Deliverable**: Every AI response visibly shows where the answer came from.

### Task 4: Responsive Layout

**What to do**

1. Test mobile, tablet, and desktop layouts.
2. Verify message scrolling.
3. Verify the input box remains usable on small screens.

**Deliverable**: Chat UI is usable across screen sizes.

### Success Criteria for Syed

- User can ask a question in the browser and receive a real AI response.
- Citations render in the UI.
- Layout is responsive.
- Code is pushed to GitHub.

### Files to Create or Modify

- `frontend/components/ChatMessage.tsx`
- `frontend/components/ChatInput.tsx`
- `frontend/components/SourceCitation.tsx`
- `frontend/components/ConversationList.tsx` if time permits
- `frontend/app/chat/page.tsx`
- `frontend/lib/api.ts`
- `frontend/types/chat.ts`

---

## Mark - Documentation Lead

### Goal

Finalize project documentation against the actual implementation.

### Task 1: Finish PRD

**What to do**

1. Finalize `docs/PRD.md` against the real Meeting 4 scope.
2. Make sure the MVP list matches what is actually implemented.

**Deliverable**: Finalized `docs/PRD.md`.

### Task 2: Finish SRS

**What to do**

1. Finalize `docs/SRS.md`.
2. Cross-check requirements against the actual backend behavior for:
   - `/api/chat`
   - `/api/query`
   - `/api/feedback`

**Deliverable**: Finalized `docs/SRS.md`.

### Task 3: Create API.md

**What to do**

1. Document all live endpoints in `docs/API.md`.
2. Use the exact live API contract from the "Execution Contract" section above.
3. Include request and response examples.
4. Document the standard response envelope:
   - `{ success, data, message, error }`
5. Document the degraded-response case where `success` may still be `true`.
6. Link to Swagger at `/docs`.

**Deliverable**: `docs/API.md` matches the real integrated backend.

### Task 4: Update GitHub Project Board

**What to do**

1. Move Meeting 3 items to Done.
2. Add or update Meeting 4 tasks with owners and due date of August 2, 2026.
3. Keep board status current.

**Deliverable**: Board reflects real sprint status.

### Task 5: Start Final Report

**What to do**

1. Create `docs/FINAL_REPORT.md` or the agreed shared equivalent.
2. Start sections for:
   - project summary
   - objectives
   - what was built
   - tech stack
   - team contributions
   - challenges
   - results
   - future work

**Deliverable**: Final Report skeleton exists and is partially filled in.

### Success Criteria for Mark

- Documentation matches the real implementation.
- Project board is current.
- Final Report has started.
- Files are pushed to GitHub.

### Files to Create or Modify

- `docs/PRD.md`
- `docs/SRS.md`
- `docs/API.md`
- `docs/FINAL_REPORT.md`
- GitHub Projects board

---

## Nairobi - QA and Presentation Lead

### Goal

Prepare for demo day and start integration testing.

### Task 1: Project Charter Finalized

**What to do**

1. Finalize `docs/PROJECT_CHARTER.md`.
2. Confirm scope, constraints, stakeholders, and objectives still match reality.
3. Get team sign-off.

**Deliverable**: Final Project Charter.

### Task 2: Presentation Slides 80% Complete

**What to do**

1. Continue the deck from Meeting 3.
2. Include:
   - problem
   - solution
   - features
   - stack
   - architecture
   - demo
   - challenges
   - roadmap
3. Coordinate with Abrar and Syed so the demo slides match the actual system.

**Deliverable**: Slide deck is structurally complete and about 80% done.

### Task 3: Test Plan

**What to do**

1. Create `docs/TEST_PLAN.md`.
2. Cover:
   - Abrar's backend tests
   - RAG pipeline integration tests
   - frontend-backend integration tests
   - end-to-end workflow tests
   - empty input
   - very long input
   - Ollama down
3. Include degraded-state testing:
   - backend reachable, Ollama unavailable
   - frontend cannot reach backend
   - citations returned but answer quality is weak
4. Include a manual QA checklist for demo readiness.

**Deliverable**: `docs/TEST_PLAN.md` is complete and actionable.

### Task 4: Demo Script

**What to do**

1. Create `docs/DEMO_SCRIPT.md`.
2. Include at least:
   - one campus-location question
   - one admissions or program question
   - one student-services question
   - one fallback note if Ollama is slow or unavailable
3. For each demo step, note what should be highlighted.

**Deliverable**: Demo script is ready for rehearsal.

### Task 5: Begin Integration Testing

**What to do**

1. Once Syed's frontend is connected, test the full browser-to-backend flow.
2. Verify:
   - answers appear
   - citations appear
   - error states are understandable
   - degraded Ollama behavior is not confusing
3. Log bugs and send findings back to the team.

**Deliverable**: First-pass integration testing is underway and findings are recorded.

### Success Criteria for Nairobi

- Team can rehearse the presentation.
- Test plan and demo script exist and are usable.
- Integration testing has started with recorded findings.
- Files are pushed to GitHub.

### Files to Create or Modify

- `docs/PROJECT_CHARTER.md`
- `docs/PRESENTATION_SLIDES`
- `docs/TEST_PLAN.md`
- `docs/DEMO_SCRIPT.md`

---

## Coordination Notes

### Critical Path

Mathew's metadata format must match Abrar's loader expectations. Use the YAML frontmatter format in this document and do not invent alternatives during Meeting 4.

### Blockers to Watch

- Abrar's backend is ready enough for the rest of the team to work against now.
- Mathew should improve metadata and retrieval quality before final QA.
- Syed should build against the live `/api/chat` contract in this document.
- Nairobi's meaningful integration testing depends on Syed connecting the frontend.
- Mark should document what is live, not what was originally planned.

### GitHub

All work should follow the team's normal GitHub flow:

- feature branch when practical
- clear commits
- PR
- review
- merge to `master`

If time is too tight, keep changes small and still make sure the final pushed work is reviewable.

---

## Final Checklist for Saturday, August 2, 2026

### Abrar

- [x] LangChain integrated into backend
- [x] Knowledge base loaded into ChromaDB
- [x] Ollama connected to the RAG pipeline
- [x] `/api/chat` returns real AI responses
- [x] Source citations returned with each response
- [x] Basic integration tests passing

### Mathew

- [ ] Official Centennial knowledge files finished
  - `knowledge/college_info.json` is still a placeholder and needs real data populated
  - Check for missing or incomplete content in: `knowledge/departments/centennial_departments.md`, `knowledge/facilities/centennial_facilities.md`, `knowledge/policies/centennial_policies.md`, `knowledge/programs/centennial_programs (1).md`
  - Ensure all major student-facing topics are covered: admissions, tuition and financial aid, programs by school, campus locations and hours, key student services, important dates
- [ ] Source metadata added to knowledge files
  - None of the current `.md` files have YAML frontmatter; every file needs a block like the following added at the very top:
    ```
    ---
    title: ...
    source_url: ...
    ---
    ```
  - `title` is required; `source_url` is optional — only include a real official Centennial URL, never a fabricated one
  - Files to update: `knowledge/departments/centennial_departments.md`, `knowledge/facilities/centennial_facilities.md`, `knowledge/policies/centennial_policies.md`, `knowledge/programs/centennial_programs (1).md`, and any other `.md` files under `knowledge/`
- [ ] 20 or more sample questions tested and logged
  - Create `knowledge/RETRIEVAL_TEST_LOG.md` and record each question with: question text, expected answer summary, actual answer summary, source file(s) returned, pass/fail, and notes
  - Run questions through `POST /api/query` or `POST /api/chat` once the knowledge base is indexed with `python -m app.services.knowledge_loader --reset`
- [ ] Missing or inaccurate knowledge fixed
  - Depends on results in `knowledge/RETRIEVAL_TEST_LOG.md` — edit the relevant `.md` files under `knowledge/` for each failed or inaccurate result
  - Re-run failed questions after each fix to confirm retrieval quality has improved
- [ ] Chunking improved if retrieval quality was poor
  - Edit `backend/config.py` — tune the `CHUNK_SIZE` and `CHUNK_OVERLAP` values if retrieval is returning irrelevant or truncated content
  - Coordinate with Abrar before changing chunking parameters; re-run the knowledge loader (`python -m app.services.knowledge_loader --reset`) after any change to rebuild the index

### Syed

- [ ] Chat interface, input, and loading indicator built
  - Create `frontend/components/ChatMessage.tsx` — renders individual user and assistant message bubbles
  - Create `frontend/components/ChatInput.tsx` — text input box and send button
  - Create `frontend/components/LoadingIndicator.tsx` — typing/loading indicator shown while awaiting the backend response
  - Create `frontend/app/chat/page.tsx` — assembles the above components into the main chat page
- [ ] Connected to `/api/chat`
  - Create `frontend/lib/api.ts` — implement a function that POSTs to `/api/chat` using `NEXT_PUBLIC_API_URL`, sends `{ message, conversation_id }`, and returns the full `ResponseModel` envelope
  - Handle `success: false` and degraded `success: true` (Ollama unavailable) states — do not crash the UI in either case
  - Persist and reuse `data.conversation_id` for follow-up turns within the same session
- [ ] Citations displayed
  - Create `frontend/components/SourceCitation.tsx` — renders the `sources` array from `data.sources`; show at minimum `title` and `excerpt`; optionally show `section`, `source_path`, and `url` when present
- [ ] Responsive layout confirmed
  - Apply Tailwind CSS breakpoints (`sm:`, `md:`, `lg:`) in `frontend/components/ChatMessage.tsx`, `frontend/components/ChatInput.tsx`, and `frontend/app/chat/page.tsx`
  - Verify the input box remains accessible and the message list scrolls correctly on small screens

### Mark

- [ ] PRD finished
  - Update `docs/PRD.md` — file is currently marked "Draft" with a Meeting 3 note; remove the draft marker, align the MVP feature list with what is actually implemented in the backend, and ensure the stated scope matches Meeting 4 reality
- [ ] SRS finished
  - Update `docs/SRS.md` — same issue as PRD; still marked "Draft"; cross-check all requirements against the live endpoints (`/api/chat`, `/api/query`, `/api/feedback`) and finalize
- [ ] API.md created
  - Create `docs/API.md` — document all 4 live endpoints: `POST /api/chat`, `POST /api/query`, `POST /api/feedback`, `GET /api/conversations/{id}`
  - Refer to `backend/app/api/routes.py` for route definitions and `backend/app/schemas/chat.py` for exact request/response shapes
  - Include the standard response envelope `{ success, data, message, error }`, request/response JSON examples (use the examples in the Execution Contract section of this document), and the degraded-state note where `success: true` does not guarantee a full model answer
  - Link to the live Swagger docs at `/docs`
- [ ] GitHub Project Board updated
  - No file needed — update the board directly on GitHub: move Meeting 3 items to Done, add or update Meeting 4 tasks with owner names and due date August 2, 2026
- [ ] Final Report started
  - Create `docs/FINAL_REPORT.md` with skeleton sections: project summary, objectives, what was built, tech stack, team contributions, challenges, results, future work

### Nairobi

- [ ] Project Charter finalized
  - Create `docs/PROJECT_CHARTER.md` — confirm scope, constraints, stakeholders, and objectives still match the actual project; get team sign-off before Meeting 4
- [ ] Presentation slides about 80% complete
  - Create `docs/PRESENTATION_OUTLINE.md` as a written outline/placeholder if the slides live in Google Slides or another external tool — include slide titles and bullet-point content for: problem, solution, features, stack, architecture, demo walkthrough, challenges, and roadmap
- [ ] Test Plan written
  - Create `docs/TEST_PLAN.md` — cover backend unit tests, RAG pipeline integration tests, frontend-backend integration tests, end-to-end workflow tests, edge cases (empty input, very long input, Ollama down), and a manual QA checklist for demo readiness; include degraded-state scenarios (backend reachable but Ollama unavailable; frontend cannot reach backend)
- [ ] Demo script written
  - Create `docs/DEMO_SCRIPT.md` — include at least one campus-location question, one admissions or program question, one student-services question, and a fallback note for when Ollama is slow or unavailable; annotate each step with what should be highlighted to the audience
- [ ] Integration testing begun
  - Run the existing test suite first: `pytest backend/tests/test_api.py` and `pytest backend/tests/test_rag_pipeline.py`
  - Once Syed's frontend is connected, test the full browser-to-backend flow: verify answers and citations appear, error states are understandable, and degraded Ollama behavior does not cause confusing UI states
  - Log bugs and send findings back to the team

---

## Key Success Factors

1. Talk before making format changes. Mathew and Abrar must not diverge on metadata shape.
2. Build against the live system as soon as possible. Do not wait until the last day to switch off placeholders.
3. Log what you test. Retrieval notes and QA findings are part of the deliverable, not optional extras.
4. Docs should follow reality. Mark should document the real backend and real frontend once connected.

CampusAI should be demo-ready by the end of this sprint, not just architecturally planned.
