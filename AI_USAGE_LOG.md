# AI Usage Log & Agentic Artifacts Record

**Course**: Computer Networks – Application Layer  
**Assignment**: Dual-Panel Activity & Protocol Visualizer  
**AI Platform**: Google Antigravity  
**Underlying Model**: Gemini 3.8 Flash (High)  
**Session Date**: September 2026  

---

## 1. Choice of Platform and Model
- **Platform**: **Google Antigravity**
  - **Rationale**: Google Antigravity provides an integrated agentic coding environment with proactive terminal execution, file system orchestration, MCP (Model Context Protocol) tool integration, and planning modes. This enables end-to-end architecture design, code generation, testing, and verification in a single continuous session.
- **Model**: **Gemini 3.8 Flash (High)**
  - **Rationale**: Gemini 3.8 Flash delivers fast inference latency, large context window processing, and high instruction-following accuracy across Python networking code and modern CSS/JavaScript user interfaces.

---

## 2. Prompt History & Agentic Interaction Stages

### Stage 1: Problem Ingestion & Requirement Analysis
- **User Prompt**:
  > *"this is the assignment i was given help me with the code, use python+flask for backend and html/js for the frontend, now complete the code, the streaming page should be able to play videos online and show the responses, and for the rest follow the instructions in the pdf"*
- **Agent Analysis**:
  - Parsed the multi-page assignment PDF specification.
  - Identified the core requirements:
    1. Strict side-by-side dual-panel layout (Activity Panel on left, Protocol Visualizer on right).
    2. Three application layer activities: Browsing, Mail, and Streaming.
    3. Parallel visualization of protocols:
       - Browsing: DNS (A) ➔ HTTP/1.1 (Request + Response)
       - Mail: DNS (MX) ➔ RFC 5321 SMTP conversation (EHLO, MAIL FROM, RCPT TO, DATA, QUIT)
       - Streaming: DNS ➔ HTTP HLS (Manifest / Playlist + Segments)
    4. Exact messages, direction indicators, timing, key fields, animations, and playback controls (Pause, Next, Prev, Replay, Speed).
    5. Real online video playback in the streaming page with telemetry.
    6. Four student deliverables: Code, AI Usage Log, Screenshots/Video demo, Reflection Document.

### Stage 2: Architecture Planning & Plan Approval
- **Artifact Generated**: `implementation_plan.md`
- **Design Proposal**:
  - Clean separation into modular protocol engines (`dns_engine.py`, `http_engine.py`, `smtp_engine.py`, `streaming_engine.py`).
  - Flask application server with REST endpoints (`/api/browse`, `/api/mail/send`, `/api/stream/init`, `/api/stream/segment`).
  - Frontend built with clean vanilla HTML5/CSS3/JavaScript, leveraging CSS variables, glassmorphism, and responsive CSS grid.
  - Step-by-step visualizer engine (`visualizer.js`) equipped with a state machine supporting step navigation, auto-play, pause, speed control, and Wireshark-style packet inspector.
- **User Approval**: Approved by user.

### Stage 3: Implementation & Agent Execution
- **Step 1**: Created project structure under `protocol-visualizer/`.
- **Step 2**: Generated virtual environment and installed `flask` and `requests`.
- **Step 3**: Implemented `protocol_engine/dns_engine.py`:
  - RFC 1035 packet schema generation (Header ID, Flags `0x0100`/`0x8180`, Questions, Answers with TTL).
  - Real socket fallback with simulated IP caching.
- **Step 4**: Implemented `protocol_engine/http_engine.py`:
  - Request headers (`Host`, `User-Agent`, `Accept`, `Connection`), HTTP status line, response headers, and body snippets.
- **Step 5**: Implemented `protocol_engine/smtp_engine.py`:
  - RFC 5321 state machine: `220 Greeting` ➔ `EHLO` ➔ `250-Capabilities` ➔ `MAIL FROM` ➔ `250 OK` ➔ `RCPT TO` ➔ `250 OK` ➔ `DATA` ➔ `354` ➔ RFC 5322 payload with terminating dot `\r\n.\r\n` ➔ `250 Queued` ➔ `QUIT` ➔ `221 Bye`.
- **Step 6**: Implemented `protocol_engine/streaming_engine.py`:
  - Online video presets (`Big Buck Bunny`, `Tears of Steel`, `Sintel`).
  - HLS Master Manifest generation with adaptive bitrate stream tags (`#EXT-X-STREAM-INF`).
  - Chunked segment request/response generator with `Range: bytes=...` and `HTTP 206 Partial Content`.
- **Step 7**: Implemented Flask server (`app.py`) and single-command startup script (`run.sh`).
- **Step 8**: Implemented responsive UI:
  - `templates/index.html`: Strict dual-panel layout, tabbed activities, browser mockup, email envelope tracker, and HTML5 video player.
  - `static/css/style.css`: Modern dark glassmorphic styling, sequence diagram actor pillars, directional arrows with gradient pulses, packet inspection tables.
  - `static/js/app.js`: Tab orchestration, activity logger, and API dispatchers.
  - `static/js/visualizer.js`: Step-by-step timeline renderer, playback controller, and keyboard shortcuts.
  - `static/js/streaming.js`: Online video streaming controller, buffer capacity calculation, and dynamic segment packet injection.

### Stage 4: Verification & Automated Testing
- **Step 1**: Created `tests/test_protocol_visualizer.py` containing 6 comprehensive unit and integration tests.
- **Step 2**: Executed test suite with Python `unittest`: All 6 tests passed (0.389s).
- **Step 3**: Verified live Flask endpoints via `curl`:
  - `GET /api/health` ➔ `200 OK`
  - `POST /api/browse` ➔ `200 OK` (retrieved example.com with 4 protocol steps)
  - `POST /api/mail/send` ➔ `200 OK` (retrieved full 15-step SMTP conversation)
  - `POST /api/stream/init` & `POST /api/stream/segment` ➔ `200 OK` (retrieved HLS manifest and 206 Partial Content segment)

---

## 3. Summary of Agentic Artifacts
1. `implementation_plan.md`: Technical specification and architectural design document.
2. `app.py` & `protocol_engine/`: Complete Python backend.
3. `templates/index.html` & `static/`: Full frontend application.
4. `tests/test_protocol_visualizer.py`: Automated verification suite.
5. `README.md`: Setup, execution, and architectural guide.
6. `AI_USAGE_LOG.md`: Prompt history and platform evidence.
7. `REFLECTION.md`: Academic reflection document.
