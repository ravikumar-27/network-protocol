# Transport Layer Protocol Visualizer: Architectural & AI Reflection

**Student**: Computer Networks Laboratory  
**Course**: Computer Networks – Transport Layer  
**Assignment**: Assignment 2: Dual-Panel Activity & Transport-Layer Protocol Visualizer  
**AI Platform**: Google Antigravity  
**Model Used**: Gemini 3.8 Flash (High)  
**Date**: October 2026  

---

## 1. Choice of AI Platform and Model

For Assignment 2, **Google Antigravity** paired with **Gemini 3.8 Flash (High)** was chosen as the agentic AI development environment.

### Why Google Antigravity?
Extending the application-layer dashboard from Assignment 1 to encompass full transport-layer mechanics required multi-file architectural refactoring, protocol state-machine design, byte-level mathematical accounting, and regression verification. Google Antigravity provided a true agentic coding loop:
- Native execution of shell tools and background daemons (`python app.py` running persistently while curl/unittest validations execute in parallel).
- Autonomous file system modifications (`write_to_file`, `replace_file_content`) across Python engines, Flask routes, HTML templates, CSS stylesheets, and client JavaScript.
- Direct invocation of unit test suites (`python3 -m unittest`) to verify sequence/ACK transitions and REST schemas immediately upon code changes.

### Why Gemini 3.8 Flash?
Gemini 3.8 Flash provided the ideal balance between high inference velocity and deep adherence to complex networking specifications:
- **Strict Protocol Compliance**: Accurately generated RFC 793 TCP header definitions, 32-bit sequence/acknowledgment progressions, RFC 768 UDP datagrams, RFC 3550 RTP video streaming headers, and RFC 9000 QUIC packet structures.
- **Large Context Retention**: Seamlessly reconciled existing Assignment 1 code with new Transport Layer engines without breaking legacy Application Layer behavior.
- **Full-Stack Competence**: Simultaneously produced robust Python network models and polished CSS/JavaScript UI components (layer tabs, glowing TCP state badges, real-time congestion telemetry, and responsive split-column layouts).

---

## 2. How the Application-Layer and Transport-Layer Views Stay Synchronized

A critical requirement of Assignment 2 is that actions triggered on the **Left Panel (Activity Panel)** must drive both the **Application Layer** and **Transport Layer** visualizations in parallel, while allowing users to inspect them either individually or side-by-side in real time.

We engineered a **Dual-Layer Reactive Pub/Sub & State Machine Architecture**:

```
[ User Interaction on Left Panel: Visit / Send / Stream ]
                           │
                           ▼
               [ Activity Controller (app.js) ]
                           │
                           ├──────────────────────────────┐
                           ▼                              ▼
               [ Left Panel UI Updates ]        [ REST API Request ]
               - Address bar / route dot        - POST /api/browse
               - HTML5 video element            - POST /api/mail/send
                           │                    - POST /api/stream/init
                           │                              │
                           │                              ▼
                           │                    [ Flask Backend Engine ]
                           │                    - Generates app_steps
                           │                    - Generates transport_steps
                           │                    - Attaches app_step_ref
                           │                              │
                           │                              ▼
                           │                    [ Parallel JSON Payload ]
                           │                              │
                           └──────────────────────────────┤
                                                          ▼
                                      [ Visualizer Engine (visualizer.js) ]
                                      - Stores appSteps & transportSteps
                                      - Drives Layer Tabs (App | Transport | Dual)
                                      - Governs single timer & step index
                                      - Synchronously updates:
                                        • Sequence diagrams & arrows
                                        • TCP State Machine Bar
                                        • Congestion Control Telemetry
                                        • Wireshark-Style Packet Inspector
```

### Key Synchronization Mechanics:
1. **Parallel Step Generation**: Backend endpoints (`/api/browse`, `/api/mail/send`, `/api/stream/init`, `/api/stream/segment`) generate both `app_steps` and `transport_steps` in a single transaction. Each transport step carries an `app_step_ref` metadata attribute linking it to its corresponding application-layer command.
2. **Unified State Pointer**: The visualizer maintains a single `currentStepIndex`. When the user plays, pauses, steps forward, or steps backward, both the transport timeline and the corresponding application timeline advance synchronously.
3. **Dual View (Side-by-Side Split)**: In Dual View mode, the visualizer renders a responsive two-column grid:
   - **Left Column**: Application Layer transaction (e.g. `HTTP GET /` or `SMTP DATA`).
   - **Right Column**: Underlying Transport Layer segments (e.g. `TCP 3-Way Handshake`, `PSH, ACK` payload segment, and server `ACK`).
   Advancing through transport steps automatically highlights the active transport card while concurrently highlighting the associated application layer card.
4. **Live TCP State Machine & Telemetry Tracking**: As the visualizer advances, it continuously updates client and server state badges (`CLOSED` ➔ `SYN_SENT` ➔ `ESTABLISHED` ➔ `FIN_WAIT_1` ➔ `TIME_WAIT`), current sequence/acknowledgment numbers, receive window sizes (`Win`), congestion window capacity (`cwnd`), and estimated round-trip time (`RTT`).

---

## 3. What the AI Got Wrong and How It Was Corrected

During the development of the transport-layer protocol engine, several non-trivial protocol subtleties were initially miscalculated by the AI and required targeted algorithmic corrections:

### Issue 1: Sequence Number Consumption for SYN and FIN Flags
- **Initial AI Output**: The AI initially treated TCP sequence numbers as strictly equal to the count of payload bytes transmitted. Consequently, after the initial `SYN` packet (which has 0 payload bytes), the client sequence number remained unchanged, and the server's `SYN-ACK` packet set `Ack = Client_ISN` instead of `Client_ISN + 1`.
- **Why It Was Wrong**: Per RFC 793 Section 3.3, control flags that establish or terminate a connection (`SYN` and `FIN`) occupy exactly **one byte of sequence number space** in the logical byte stream (often called a "phantom byte"), even though they carry no application data.
- **Correction**: We modified `protocol_engine/tcp_engine.py` so that `SYN` explicitly advances `client_seq += 1`, the server acknowledges `Ack = client_seq`, `SYN-ACK` advances `server_seq += 1`, and `FIN` advances the sequence number by 1 during connection teardown.

### Issue 2: Zero-Length Pure ACKs Advancing Sequence Numbers
- **Initial AI Output**: When the client or server transmitted a pure `ACK` segment (e.g. step 3 of the 3-way handshake or a receiver payload acknowledgment), the AI incremented the sender's sequence number by 1.
- **Why It Was Wrong**: A pure `ACK` packet with `Len = 0` carries neither application payload nor sequence-consuming flags (`SYN`/`FIN`). Incrementing the sequence number on a pure ACK violates RFC 793 and causes subsequent data packets to display sequence number gaps, triggering false out-of-order retransmission alerts in network inspectors.
- **Correction**: We enforced the rule:
  $$\text{Next Seq} = \text{Current Seq} + \text{Payload Bytes} + (1 \text{ if SYN or FIN else } 0)$$
  Pure `ACK` packets retain their sequence number without incrementing.

### Issue 3: Connection Teardown Half-Close vs. Immediate Termination
- **Initial AI Output**: The AI initially collapsed TCP teardown into a single two-way packet exchange (`FIN` from client, `ACK` from server) and immediately set both endpoints to `CLOSED`.
- **Why It Was Wrong**: TCP supports **half-closed** connections. A client sending `FIN-ACK` transitions to `FIN_WAIT_1` and then `FIN_WAIT_2` upon receiving the server's `ACK`. It can still receive incoming data until the server independently issues its own `FIN-ACK` (transitioning the server from `CLOSE_WAIT` to `LAST_ACK`). Finally, upon acknowledging the server's FIN, the client must enter `TIME_WAIT` for `2 * MSL` (Maximum Segment Lifetime) to ensure that the final ACK was delivered and old duplicate segments flush from the network.
- **Correction**: We implemented the complete 4-way teardown state machine in `tcp_engine.py`:
  1. Client `FIN-ACK` (Client: `ESTABLISHED` ➔ `FIN_WAIT_1`)
  2. Server `ACK` (Server: `ESTABLISHED` ➔ `CLOSE_WAIT`; Client: `FIN_WAIT_1` ➔ `FIN_WAIT_2`)
  3. Server `FIN-ACK` (Server: `CLOSE_WAIT` ➔ `LAST_ACK`)
  4. Client `ACK` (Client: `FIN_WAIT_2` ➔ `TIME_WAIT`; Server: `LAST_ACK` ➔ `CLOSED`)

### Issue 4: Cumulative ACKs and MSS Segmentation
- **Initial AI Output**: For large HTTP responses (such as a 4 KB web page or a 700 KB video chunk), the AI generated a single massive TCP segment with `Len = 700,000 bytes`.
- **Why It Was Wrong**: The Maximum Segment Size (MSS) for standard Ethernet is 1,460 bytes ($1500 - 20\text{ IP} - 20\text{ TCP}$). Large application payloads cannot traverse the IP layer in a single TCP segment without IP fragmentation or TCP-level segmentation.
- **Correction**: We added MSS segment chunking to `tcp_engine.py`. Large responses are split into standard MSS chunks (e.g. 1,440-byte first fragment followed by final chunk with `PSH` flag set), followed by cumulative client acknowledgments (`Ack = Server_ISN + Total_Bytes`).

---

## 4. Key Differences Observed Between Transport Flows (Browsing, Mail, Streaming)

Comparing the transport-layer exchanges across the three activities reveals profound differences in connection lifecycles, throughput dynamics, and delivery guarantees:

| Dimension | Web Browsing (HTTP/1.1 over TCP) | Sending Mail (SMTP over TCP) | Video Streaming (HLS over TCP vs UDP vs QUIC) |
| :--- | :--- | :--- | :--- |
| **Connection Setup** | 1-RTT Handshake: Client `SYN` ➔ Server `SYN-ACK` ➔ Client `ACK`. | 1-RTT Handshake on Port 25 before MTA banner. | **TCP**: 1-RTT Handshake.<br>**UDP**: 0-RTT (No Handshake).<br>**QUIC**: 1-RTT Handshake with TLS 1.3. |
| **Interaction Pattern** | **Short Request-Response**: Client sends `GET`, server returns `200 OK`. | **Conversational Lockstep**: Multi-turn command-reply dialogue (`EHLO`, `MAIL FROM`, `RCPT TO`, `DATA`). | **Pipelined Segment Bursts**: Continuous chunk downloads (`segment_000.ts`, `segment_001.ts`) matching media buffer consumption. |
| **Byte-Stream Progression** | Single burst: Client sends ~300 B, server sends ~1.5 KB, connection finishes. | Linear incremental stream: Each command appends tens of bytes; Seq and Ack advance incrementally on each turn. | High-throughput bulk stream: Hundreds of kilobytes per chunk; rapid sequence progression in tens of thousands of bytes. |
| **Connection Lifecycle** | **Non-Persistent**: Teardown per request (`Connection: close`).<br>**Persistent**: Kept `ESTABLISHED` (`Connection: keep-alive`) to avoid repeat handshakes. | **Long-Lived Session**: Single TCP connection carries entire email transaction and terminates only after `QUIT` / `221 Bye`. | **Persistent Pipeline**: Reuses TCP socket to stream continuous media chunks while adjusting bitrates (ABR). |
| **Flow & Congestion Control** | Stays in **Slow Start** (`cwnd = 10 MSS`) because payload is too small to trigger Congestion Avoidance. | Stays in **Slow Start**; limited by application turn-taking rather than network bandwidth. | Expands `cwnd` exponentially during Slow Start, transitions to **Congestion Avoidance**, advertises Receive Window (`Win`), and estimates RTT. |
| **UDP / QUIC Contrast** | N/A (Web browsing requires reliable byte stream). | N/A (Mail delivery mandates guaranteed lossless transport). | **UDP (RTP)**: Sacrifices reliability for low latency; zero handshakes, no ACKs, loss-tolerant.<br>**QUIC (HTTP/3)**: Multiplexes independent streams over UDP without Head-of-Line blocking. |

---

## 5. Educational Takeaways & Conclusion

1. **User Actions Map Directly to Transport Guarantees**: A simple button click on the left panel (visiting a URL, sending an email, or playing a video) triggers radically different transport layer lifecycles. Web browsing is short and bursty, email is structured and conversational, and video streaming is high-bandwidth and buffer-driven.
2. **The "Reliable Byte-Stream" Abstraction**: While the Application Layer perceives HTTP and SMTP as sending whole messages, the Transport Layer deconstructs these into individual numbered octets, sequence windows, acknowledgment counters, and retransmission timers.
3. **TCP Overhead vs. UDP Speed**: Visualizing UDP and QUIC side-by-side with TCP clearly illustrates why modern real-time applications (WebRTC, live stadium sports, HTTP/3) avoid TCP's 3-way handshake and head-of-line blocking delays in favor of datagram delivery and multiplexed streams.
4. **Efficacy of Agentic AI in Systems Engineering**: Utilizing Google Antigravity paired with Gemini 3.8 Flash demonstrated the power of agentic workflows in building educational software. The agent did not merely write snippets; it designed the dual-layer architecture, modeled the RFC 793 state machine, maintained strict sequence/ACK math, ran regression test suites, and created an engaging interactive platform for computer networking students.
