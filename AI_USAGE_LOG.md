# AI Usage Log & Agentic Artifacts Record

**Course**: Computer Networks – Transport Layer  
**Assignment**: Assignment 2: Dual-Panel Activity & Transport-Layer Protocol Visualizer (Extension of Assignment 1)  
**AI Platform**: Google Antigravity  
**Underlying Model**: Gemini 3.8 Flash (High)  
**Session Date**: October 2026  

---

## 1. Choice of Platform and Model

### Platform: **Google Antigravity**
- **Rationale**: Google Antigravity was selected as the agentic AI platform because it provides an autonomous, multi-tool coding environment capable of managing local processes, executing shell commands, reading and writing files across a large full-stack codebase, running background daemon servers, and performing automated unit tests in a single continuous session.
- **Agentic Capabilities Utilized**:
  - Proactive filesystem operations (`write_to_file`, `replace_file_content`, `view_file`, `list_dir`).
  - Terminal process management (`run_command` with daemon support for background Flask server execution).
  - Automated test orchestration (`python3 -m unittest tests/test_protocol_visualizer.py -v`).
  - Browser inspection and automation subagent execution (`browser_subagent`).

### Model: **Gemini 3.8 Flash (High)**
- **Rationale**: Gemini 3.8 Flash delivers low-latency code generation, exceptional adherence to complex RFC protocol specifications (RFC 793 for TCP, RFC 768 for UDP, RFC 3550 for RTP, RFC 9000 for QUIC), and high fidelity in maintaining strict architectural constraints (dual-panel layout, dual-layer synchronization, glassmorphism design tokens).

---

## 2. Prompt History & Agentic Interaction Stages

### Stage 1: Problem Ingestion & Assignment 2 Scope
- **User Prompt**:
  > *"Computer Networks – Transport Layer  
  > Assignment 2: Dual-Panel Activity & Transport-Layer Protocol Visualizer  
  > (Extension of Assignment 1 – Application Layer Dashboard)  
  > ... Extend the dual-panel web dashboard built in Assignment 1 so that, for the same three application-layer activities (Browsing, Mail, and Streaming), the user can also visualize the underlying Transport-layer protocol exchanges (primarily TCP, with optional UDP/QUIC where relevant) in real time ... Keep the exact dual-panel layout from Assignment 1 ... Right panel must now support two synchronized views (Application Layer and Transport Layer) ... Show exact TCP messages (SYN, SYN-ACK, ACK, PSH, FIN, etc.), sequence & acknowledgement numbers, window size, direction, timing, pause/next/prev/replay ..."*
- **Agent Analysis**:
  - Identified core requirements:
    1. Maintain strict side-by-side dual-panel layout from Assignment 1.
    2. Extend Right Panel to support two synchronized views (Application Layer & Transport Layer), plus a Dual View (Side-by-Side).
    3. Implement accurate Transport Layer behaviors:
       - **Browsing**: DNS over UDP port 53 ➔ TCP 3-way handshake (SYN, SYN-ACK, ACK) ➔ HTTP GET/200 data segments (`PSH, ACK`, MSS chunking, cumulative ACKs) ➔ 4-way connection teardown (`FIN-ACK`, `TIME_WAIT`) with Persistent (Keep-Alive) vs Non-Persistent options.
       - **Mail**: DNS MX over UDP ➔ TCP 3-way handshake to port 25 ➔ Conversational RFC 5321 stream over TCP segments ➔ Teardown.
       - **Streaming**: Primary TCP with Manifest & Segments, Flow Control (`Win`) and Congestion Control (`cwnd` Slow Start doubling); plus comparison modes for UDP (RTP datagrams) and QUIC (HTTP/3 1-RTT multiplexed streams).
    4. Provide controls: Play/Pause, Next, Prev, Replay, Speed, and Wireshark-style Packet Inspector.
    5. Deliverables: Source code, AI usage log, Reflection document, and automated test suite.

---

### Stage 2: Architecture & Modular Design

- **Transport Protocol Engines**:
  - `protocol_engine/tcp_engine.py`: Encapsulates RFC 793 TCP state machine, 32-bit ISN generation, byte-level sequence and acknowledgment tracking, TCP options (`MSS`, `WS`, `SACK`, `TS`), Flow Control (`Win`), Congestion Control (`cwnd`, `ssthresh`, Slow Start, Congestion Avoidance), and 4-way Teardown.
  - `protocol_engine/udp_engine.py`: Implements RFC 768 UDP header formatting and RFC 3550 RTP video streaming encapsulation.
  - `protocol_engine/quic_engine.py`: Implements RFC 9000 QUIC Initial and 1-RTT stream frame formatting.
- **Synchronized REST APIs (`app.py`)**:
  - Updated `/api/browse`, `/api/mail/send`, `/api/stream/init`, and `/api/stream/segment` to return both `app_steps` and `transport_steps` in parallel, with cross-layer references (`app_step_ref`).
- **Frontend Architecture (`templates/index.html`, `style.css`, `visualizer.js`, `app.js`, `streaming.js`)**:
  - Layer Switcher: `Application Layer` | `Transport Layer` | `Dual View (Side-by-Side)`.
  - Live TCP State Machine Bar: Real-time client state (`CLOSED` ➔ `SYN_SENT` ➔ `ESTABLISHED` ➔ `FIN_WAIT_1` ➔ `TIME_WAIT`) and server state (`LISTEN` ➔ `SYN_RCVD` ➔ `ESTABLISHED` ➔ `CLOSE_WAIT` ➔ `CLOSED`).
  - Live Congestion & Flow Control Bar: `Seq`, `Ack`, `Win`, `cwnd`, `ssthresh`, `Phase`, `RTT`.
  - Browsing Option: Persistent TCP (Keep-Alive) toggle.
  - Streaming Option: Transport Protocol segmented selector (`TCP`, `UDP`, `QUIC`).

---

### Stage 3: Implementation Steps & Iteration

- **Step 1**: Created `protocol_engine/tcp_engine.py` with `TCPConnection` class enforcing exact byte accounting:
  - Initial `SYN` consumes 1 sequence number.
  - Initial `SYN-ACK` consumes 1 sequence number.
  - Pure `ACK` segments (0 payload bytes) do not consume sequence numbers.
  - Data segments (`PSH, ACK`) consume exactly `len(payload.encode('utf-8'))` bytes.
  - Server ACK acknowledges `Ack = Seq + Len`.
  - Final `FIN` consumes 1 sequence number.
- **Step 2**: Created `protocol_engine/udp_engine.py` and `protocol_engine/quic_engine.py` and re-exported via `protocol_engine/__init__.py`.
- **Step 3**: Updated Flask server `app.py` with multi-protocol support and parallel step generation.
- **Step 4**: Enhanced `static/css/style.css` with styles for layer tabs, glowing TCP state badges, congestion telemetry pills, TCP flag chips, and responsive dual-view split columns.
- **Step 5**: Rewrote `static/js/visualizer.js` to manage dual step arrays (`appSteps` and `transportSteps`), dual-column rendering, step synchronization, and TCP state machine updates.
- **Step 6**: Updated `static/js/app.js` and `static/js/streaming.js` to dispatch options and dynamically update both timelines.
- **Step 7**: Built comprehensive test suite in `tests/test_protocol_visualizer.py` with 9 unit and integration tests.

---

### Stage 4: Testing & Verification

- **Automated Tests**:
  Executed `python3 -m unittest tests/test_protocol_visualizer.py -v`. All 9 tests passed in 0.529 seconds:
  1. `test_dns_engine`: Verified RFC 1035 query/response structure.
  2. `test_http_engine`: Verified HTTP GET request and 200 OK headers.
  3. `test_smtp_engine`: Verified 15-step RFC 5321 conversation.
  4. `test_tcp_state_machine_and_seq_ack`: Verified RFC 793 byte-accurate handshake, payload increment, and teardown.
  5. `test_browsing_transport_steps`: Verified UDP DNS, TCP handshake, data transfer, and persistent vs non-persistent modes.
  6. `test_mail_transport_steps`: Verified SMTP mapping onto TCP byte stream on port 25.
  7. `test_streaming_modes`: Verified TCP, UDP (RTP), and QUIC transport modes.
  8. `test_flask_endpoints_dual_layer`: Verified REST API responses contain both `app_steps` and `transport_steps`.
  9. `test_static_and_templates`: Verified HTML templates and CSS/JS static delivery.
- **Live Endpoint Verification**:
  Launched background Flask daemon and verified via `curl`:
  - `GET /api/health` ➔ `200 OK` (Application Layer & Transport Layer healthy).
  - `POST /api/browse` ➔ `200 OK` (Returns `app_steps` and `transport_steps`).
  - `POST /api/mail/send` ➔ `200 OK` (Returns full SMTP conversation and TCP segments).
  - `POST /api/stream/init` ➔ `200 OK` (Returns HLS/RTP/QUIC steps).

---

## 3. Summary of Agentic Artifacts

1. `protocol_engine/tcp_engine.py`: RFC 793 TCP state machine, byte-level Seq/Ack logic, congestion control.
2. `protocol_engine/udp_engine.py`: RFC 768 UDP and RFC 3550 RTP video engine.
3. `protocol_engine/quic_engine.py`: RFC 9000 QUIC 1-RTT stream multiplexing engine.
4. `protocol_engine/__init__.py`: Package exports for both Application and Transport layer engines.
5. `app.py`: Flask application server with dual-layer REST endpoints.
6. `templates/index.html`: Dual-panel HTML template with Layer Switcher, TCP State bar, and Telemetry bar.
7. `static/css/style.css`: Modern glassmorphic styling, state badges, flag tags, and dual-column layout.
8. `static/js/visualizer.js`: State machine visualizer driving synchronized App, Transport, and Dual views.
9. `static/js/app.js`: Tab controller, activity logger, and API dispatchers.
10. `static/js/streaming.js`: HTML5 video controller, telemetry, and segment packet streaming.
11. `tests/test_protocol_visualizer.py`: Automated 9-test unit and integration test suite.
12. `README.md`: Architectural documentation and quick start guide.
13. `AI_USAGE_LOG.md`: Complete AI usage log, prompt history, and evidence.
14. `REFLECTION.md`: Comprehensive 1-2 page academic reflection document.
