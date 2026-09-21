# Application Layer Protocol Visualizer: Architectural & AI Reflection

**Student**: Computer Networks Laboratory  
**Course**: Computer Networks – Application Layer  
**AI Platform**: Google Antigravity  
**Model Used**: Gemini 3.8 Flash (High)  
**Date**: September 2026  

---

## 1. Choice of AI Platform and Model

For this assignment, **Google Antigravity** paired with **Gemini 3.8 Flash (High)** was chosen as the agentic AI platform. 

### Why Google Antigravity?
Google Antigravity operates as an agentic pair programmer rather than a passive code completion snippet tool. It has native access to the local development environment, shell tools, file systems, background task management, and structured planning workflows. Rather than manually copying code across multiple files, Antigravity was able to formulate an architectural design (`implementation_plan.md`), solicit user approval, execute directory scaffolding, configure Python virtual environments, generate modular codebases, and run automated regression test suites autonomously.

### Why Gemini 3.8 Flash?
Gemini 3.8 Flash provides a balanced combination of rapid inference speed, large multi-turn context capacity, and high fidelity in following structured network specifications (e.g., RFC 1035 for DNS, RFC 2616/9110 for HTTP, and RFC 5321 for SMTP). Its capability to write clean, standards-compliant Python network code while concurrently crafting modern CSS (glassmorphism, CSS grid, micro-animations) made it the ideal engine for this dual-panel full-stack application.

---

## 2. How the Two Panels Stay Synchronized

The assignment imposes a strict requirement: every action taken in the **Left Panel (Activity Panel)** must immediately and seamlessly trigger a corresponding animated exchange in the **Right Panel (Protocol Visualization Panel)**.

To achieve robust, deterministic synchronization without race conditions, we implemented an **Event-Driven Pub/Sub and State Machine Architecture**:

```
[ User Interaction: Visit / Send / Stream ]
                   │
                   ▼
       [ Activity Controller (app.js) ]
                   │
                   ├─────────────────────────────┐
                   ▼                             ▼
       [ Left Panel UI Updates ]       [ REST API Dispatch ]
       - Address bar update            - POST /api/browse
       - Route dot animation           - POST /api/mail/send
       - Video player mount            - POST /api/stream/init
                   │                             │
                   │                             ▼
                   │                   [ Flask Backend Engine ]
                   │                   - DNS / HTTP / SMTP / HLS
                   │                             │
                   │                             ▼
                   │                   [ Structured Protocol JSON ]
                   │                             │
                   └─────────────────────────────┤
                                                 ▼
                              [ Visualizer Engine (visualizer.js) ]
                              - Loads sequence into State Machine
                              - Computes directional arrows & badges
                              - Governs timer, play/pause, step pointer
                              - Synchronously updates timeline & packet cards
```

### Key Synchronization Mechanics:
1. **Normalized Protocol Exchange Schema**: The backend returns all protocol interactions as a standardized list of sequential steps containing `step_number`, `protocol` (`DNS`, `HTTP`, `SMTP`), `direction` (`client_to_server` vs `server_to_client`), `source`, `destination`, `transport` (`UDP` vs `TCP`), `title`, `summary`, `raw_text`, `fields`, and `timestamp_offset_ms`.
2. **Animation State Machine (`ProtocolVisualizer`)**: The right panel maintains a pointer `currentStepIndex`. When an activity begins, the visualizer resets the stage, loads the new sequence, and initiates an automatic playback timer governed by the user's selected playback speed (`0.5x`, `1.0x`, or `2.0x`).
3. **Dynamic Streaming Sync (`streaming.js`)**: Unlike static browsing and mail actions, video streaming produces ongoing network packets as playback progresses. The HTML5 `<video>` element emits `timeupdate` and `progress` events. Every 3.5 seconds of forward video playback, the client queries `/api/stream/segment`, fetching the next segment packet pair and dynamically appending it to the right panel timeline while recalculating the forward buffer capacity in real time.
4. **Bidirectional Control**: The user can pause, step forward, step backward, or replay the protocol sequence at any moment without disrupting left panel state.

---

## 3. What the AI Got Wrong and How It Was Corrected

During the iterative development session with the AI agent, several protocol nuances and integration challenges were identified and systematically resolved:

### Issue 1: Over-Simplification of the SMTP Handshake
- **Initial AI Output**: In the initial draft of the SMTP engine, the AI generated a single combined step for the EHLO exchange and collapsed the multi-line `250` capability response into a single `250 OK` line.
- **Correction**: Real SMTP servers conforming to RFC 5321 emit multi-line responses prefixed with hyphens (e.g., `250-mail.domain.com`, `250-PIPELINING`, `250-SIZE 10485760`) and conclude with a space (`250 DSN`). Furthermore, the AI omitted the intermediate `354 Start mail input` reply code that is mandatory before the client transmits email headers and body. We updated `smtp_engine.py` to enforce the full 15-step conversational lockstep: `220 Greeting` ➔ `EHLO` ➔ `250-Capabilities` ➔ `MAIL FROM` ➔ `250 OK` ➔ `RCPT TO` ➔ `250 OK` ➔ `DATA` ➔ `354` ➔ Message Body with `\r\n.\r\n` ➔ `250 Queued` ➔ `QUIT` ➔ `221 Bye`.

### Issue 2: Static vs. Real Online Video Streaming
- **Initial AI Output**: The AI initially proposed displaying a simulated progress bar or static mockup placeholder for the video player rather than an actual playable online video stream.
- **Correction**: The user specifically requested: *"the streaming page should be able to play videos online and show the responses"*. We corrected this by integrating open-access CDN video sources (Big Buck Bunny, Tears of Steel, Sintel) into an HTML5 `<video>` element with full media controls, while synchronizing the real playback time and buffer telemetry with simulated chunked transport segment requests (`HTTP 206 Partial Content`).

### Issue 3: DNS Query/Response Flag Accuracy
- **Initial AI Output**: The DNS response step displayed generic string labels without realistic 16-bit flag bitmasks.
- **Correction**: We modified `dns_engine.py` to explicitly model standard query flags (`0x0100`, Recursion Desired `RD=1`) and standard response flags (`0x8180`, Query/Response `QR=1`, Recursion Available `RA=1`, Response Code `RCODE=0 No error`), as well as transaction IDs and TTL values.

---

## 4. Key Differences Observed Between DNS+HTTP, SMTP, and Streaming HTTP Flows

Comparing the three application-layer flows highlights fundamental distinctions in protocol design, connection management, and state models:

| Dimension | DNS (RFC 1035) + HTTP/1.1 (RFC 9110) | SMTP (RFC 5321) | Video Streaming (HLS / DASH over HTTP) |
| :--- | :--- | :--- | :--- |
| **Primary Transport** | UDP Port 53 (DNS) + TCP Port 80/443 (HTTP) | TCP Port 25 (or 587) | TCP Port 80/443 (or QUIC/UDP HTTP/3) |
| **Session State** | **Stateless**: Each HTTP request is independent; DNS is atomic. | **Stateful**: Strict multi-turn conversational state machine. | **Pipeline / Chunked**: Progressive manifest polling + continuous chunk fetching. |
| **Interaction Pattern** | Request-Response: Client asks, server returns, transaction complete. | Turn-by-Turn Dialog: Client sends command, awaits numeric code (220, 250, 354, 221), then sends next. | Pull-based Pipeline: Client requests manifest, estimates bandwidth, and pulls media chunks. |
| **Directionality** | Pull (Client requests content). | Push (Sender pushes mail to receiver MTA). | Pull (Client adapts bitrate based on buffer capacity). |
| **Payload Delivery** | Single atomic transfer (`Content-Length` or chunked transfer). | End-of-Data delimiter: `<CR><LF>.<CR><LF>`. | Fragmented media segments (`.ts` / `.m4s`) using `Range: bytes=...` (`206 Partial Content`). |
| **Error Recovery** | Fast retry (DNS UDP timeout) or HTTP status codes (`4xx`/`5xx`). | Intermediate status codes (`4xx` temporary deferral vs `5xx` permanent failure). | Dynamic bitrate downshifting to lower resolution (e.g. 1080p ➔ 480p) to avoid buffer starvation. |

### Educational Takeaways:
1. **DNS is the Common Denominator**: All three activities begin with DNS resolution (A-record lookup for web servers and CDN edge nodes, and MX-record lookup for mail transfer agents).
2. **Stateless vs. Conversational**: While HTTP treats each interaction as an isolated transaction, SMTP cannot accept message content without first traversing strict pre-condition states (`EHLO` ➔ `MAIL FROM` ➔ `RCPT TO` ➔ `DATA`).
3. **Adaptive Media vs. Web Pages**: In conventional web browsing, the entire HTML payload is rendered once received. In video streaming, the client continuously negotiates quality and buffers chunks ahead of the playhead, transforming HTTP from a document transfer protocol into a real-time streaming pipeline.

---

## 5. Conclusion

Developing the **Dual-Panel Activity & Protocol Visualizer** in collaboration with Google Antigravity demonstrated the effectiveness of modern agentic workflows in educational software engineering. The resulting dashboard provides students with an intuitive bridge between surface-level user interactions and the underlying packet exchanges of the Internet application layer.
