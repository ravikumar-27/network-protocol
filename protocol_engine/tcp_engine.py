"""
TCP Protocol Engine (RFC 793, RFC 7323, RFC 5681)
Simulates authentic Transport Layer TCP connections:
- Accurate 32-bit Sequence (Seq) and Acknowledgment (Ack) byte-level progression
- 3-Way Handshake: SYN -> SYN-ACK -> ACK (with TCP Options: MSS, WS, SACK, TS)
- Data transfer: PSH+ACK, cumulative ACKs, MSS chunking, Flow Control (Win)
- Congestion Control: cwnd, ssthresh, Slow Start, Congestion Avoidance
- Connection Teardown: 4-Way FIN-ACK handshake, TIME_WAIT state
- Persistent vs Non-Persistent TCP connection modes
"""
import random
import time

class TCPConnection:
    """
    Maintains client and server TCP connection state, sequence numbers,
    window sizes, and state transitions.
    """
    def __init__(self, client_port=None, server_port=80, client_ip="192.168.1.105", server_ip="93.184.215.14"):
        self.client_ip = client_ip
        self.server_ip = server_ip
        self.client_port = client_port or random.randint(49152, 65530)
        self.server_port = server_port
        
        # 32-bit Initial Sequence Numbers (RFC 793)
        self.client_isn = random.randint(1000000, 2000000000)
        self.server_isn = random.randint(2000000, 3000000000)
        
        self.client_seq = self.client_isn
        self.server_seq = self.server_isn
        self.client_ack = 0
        self.server_ack = 0
        
        # States (RFC 793 State Machine)
        self.client_state = "CLOSED"
        self.server_state = "LISTEN"
        
        # Flow & Congestion Control
        self.mss = 1460
        self.client_win = 65535
        self.server_win = 65535
        self.cwnd = 10 * self.mss  # Initial cwnd = 10 MSS (RFC 6928)
        self.ssthresh = 64 * 1024  # 64 KB
        self.congestion_phase = "Slow Start"
        self.rtt_ms = 24
        self.current_time_offset_ms = 0
        self.steps = []
        self.step_counter = 1

    def _format_raw_tcp_segment(self, src_port, dst_port, seq, ack, flags, win, data_offset=32, options=None, payload=""):
        """
        Formats a realistic Wireshark-style raw TCP packet header and hex/ASCII dump.
        """
        flags_str = ", ".join(flags)
        opt_str = ""
        if options:
            opt_str = f"\nOptions: ({len(options) * 4} bytes)\n" + "\n".join([f"  - {k}: {v}" for k, v in options.items()])
        
        checksum = f"0x{random.randint(0x1000, 0xFFFF):04X}"
        raw = (
            f"Transmission Control Protocol, Src Port: {src_port}, Dst Port: {dst_port}, Seq: {seq}, Ack: {ack}\n"
            f"Source Port: {src_port}\n"
            f"Destination Port: {dst_port}\n"
            f"Sequence Number: {seq} (relative: {seq - (self.client_isn if src_port == self.client_port else self.server_isn)})\n"
            f"Acknowledgment Number: {ack} (relative: {ack - (self.server_isn if src_port == self.client_port else self.client_isn) if ack > 0 else 0})\n"
            f"Header Length: {data_offset} bytes\n"
            f"Flags: 0x{self._flags_to_hex(flags):03X} [{flags_str}]\n"
            f"Window Size: {win} (Calculated Window: {win})\n"
            f"Checksum: {checksum} [correct]\n"
            f"Urgent Pointer: 0"
            f"{opt_str}"
        )
        if payload:
            raw += f"\n[Payload: {len(payload)} bytes]\n{payload[:300]}"
            if len(payload) > 300:
                raw += f"\n... [{len(payload) - 300} bytes omitted]"
        return raw

    def _flags_to_hex(self, flags):
        val = 0
        if "FIN" in flags: val |= 0x001
        if "SYN" in flags: val |= 0x002
        if "RST" in flags: val |= 0x004
        if "PSH" in flags: val |= 0x008
        if "ACK" in flags: val |= 0x010
        if "URG" in flags: val |= 0x020
        if "ECE" in flags: val |= 0x040
        if "CWR" in flags: val |= 0x080
        return val

    def add_handshake(self, base_time_ms=0):
        """
        Executes the classic TCP 3-Way Handshake:
        1. SYN (Client -> Server)
        2. SYN-ACK (Server -> Client)
        3. ACK (Client -> Server)
        """
        self.current_time_offset_ms = base_time_ms
        
        # 1. SYN
        self.client_state = "SYN_SENT"
        syn_options = {
            "Maximum Segment Size (MSS)": f"{self.mss} bytes",
            "TCP SACK Permitted": "True",
            "Window Scale (WS)": "7 (Multiply by 128)",
            "Timestamps (TS)": f"TSval={int(time.time()*1000)%10000000}, TSecr=0"
        }
        step_syn = {
            "step_number": self.step_counter,
            "transport": "TCP",
            "protocol": "TCP",
            "direction": "client_to_server",
            "source": f"Client ({self.client_ip}:{self.client_port})",
            "destination": f"Server ({self.server_ip}:{self.server_port})",
            "title": "TCP SYN [Handshake 1/3]",
            "summary": f"Client initiates connection with ISN={self.client_isn}, advertising MSS={self.mss} and Window Scale.",
            "flags": ["SYN"],
            "seq": self.client_seq,
            "ack": 0,
            "len": 0,
            "win": self.client_win,
            "client_state": "SYN_SENT",
            "server_state": "LISTEN",
            "cwnd": self.cwnd,
            "fields": {
                "TCP Flags": "[SYN]",
                "Sequence Number (Seq)": f"{self.client_seq} (ISN)",
                "Acknowledgment (Ack)": "0 (None)",
                "Window Size (Win)": f"{self.client_win} bytes",
                "Segment Length": "0 bytes",
                "TCP Options": "MSS=1460, SACK_PERM=1, WS=7",
                "Client State": "SYN_SENT",
                "Server State": "LISTEN"
            },
            "raw_text": self._format_raw_tcp_segment(
                self.client_port, self.server_port, self.client_seq, 0,
                ["SYN"], self.client_win, 32, syn_options
            ),
            "timestamp_offset_ms": self.current_time_offset_ms
        }
        self.steps.append(step_syn)
        self.step_counter += 1
        
        # SYN consumes 1 sequence number
        self.client_seq += 1
        self.server_ack = self.client_seq

        # 2. SYN-ACK
        self.current_time_offset_ms += int(self.rtt_ms / 2)
        self.server_state = "SYN_RCVD"
        synack_options = {
            "Maximum Segment Size (MSS)": f"{self.mss} bytes",
            "TCP SACK Permitted": "True",
            "Window Scale (WS)": "7 (Multiply by 128)",
            "Timestamps (TS)": f"TSval={int(time.time()*1000 + 12)%10000000}, TSecr={syn_options['Timestamps (TS)'].split(',')[0].split('=')[1]}"
        }
        step_synack = {
            "step_number": self.step_counter,
            "transport": "TCP",
            "protocol": "TCP",
            "direction": "server_to_client",
            "source": f"Server ({self.server_ip}:{self.server_port})",
            "destination": f"Client ({self.client_ip}:{self.client_port})",
            "title": "TCP SYN-ACK [Handshake 2/3]",
            "summary": f"Server agrees to connect with ISN={self.server_isn} and acknowledges client SYN (Ack={self.server_ack}).",
            "flags": ["SYN", "ACK"],
            "seq": self.server_seq,
            "ack": self.server_ack,
            "len": 0,
            "win": self.server_win,
            "client_state": "SYN_SENT",
            "server_state": "SYN_RCVD",
            "cwnd": self.cwnd,
            "fields": {
                "TCP Flags": "[SYN, ACK]",
                "Sequence Number (Seq)": f"{self.server_seq} (ISN)",
                "Acknowledgment (Ack)": f"{self.server_ack} (Client ISN + 1)",
                "Window Size (Win)": f"{self.server_win} bytes",
                "Segment Length": "0 bytes",
                "TCP Options": "MSS=1460, SACK_PERM=1, WS=7",
                "Client State": "SYN_SENT",
                "Server State": "SYN_RCVD"
            },
            "raw_text": self._format_raw_tcp_segment(
                self.server_port, self.client_port, self.server_seq, self.server_ack,
                ["SYN", "ACK"], self.server_win, 32, synack_options
            ),
            "timestamp_offset_ms": self.current_time_offset_ms
        }
        self.steps.append(step_synack)
        self.step_counter += 1
        
        # SYN-ACK consumes 1 sequence number
        self.server_seq += 1
        self.client_ack = self.server_seq

        # 3. ACK
        self.current_time_offset_ms += int(self.rtt_ms / 2)
        self.client_state = "ESTABLISHED"
        self.server_state = "ESTABLISHED"
        step_ack = {
            "step_number": self.step_counter,
            "transport": "TCP",
            "protocol": "TCP",
            "direction": "client_to_server",
            "source": f"Client ({self.client_ip}:{self.client_port})",
            "destination": f"Server ({self.server_ip}:{self.server_port})",
            "title": "TCP ACK [Handshake 3/3 - ESTABLISHED]",
            "summary": f"Client completes 3-way handshake. Connection is now ESTABLISHED on both endpoints.",
            "flags": ["ACK"],
            "seq": self.client_seq,
            "ack": self.client_ack,
            "len": 0,
            "win": self.client_win,
            "client_state": "ESTABLISHED",
            "server_state": "ESTABLISHED",
            "cwnd": self.cwnd,
            "fields": {
                "TCP Flags": "[ACK]",
                "Sequence Number (Seq)": f"{self.client_seq}",
                "Acknowledgment (Ack)": f"{self.client_ack} (Server ISN + 1)",
                "Window Size (Win)": f"{self.client_win} bytes",
                "Segment Length": "0 bytes",
                "Connection State": "ESTABLISHED ➔ ESTABLISHED",
                "Client State": "ESTABLISHED",
                "Server State": "ESTABLISHED"
            },
            "raw_text": self._format_raw_tcp_segment(
                self.client_port, self.server_port, self.client_seq, self.client_ack,
                ["ACK"], self.client_win, 20
            ),
            "timestamp_offset_ms": self.current_time_offset_ms
        }
        self.steps.append(step_ack)
        self.step_counter += 1

    def send_client_data(self, payload: str, title="TCP Data Segment [PSH, ACK]", summary="", app_step_ref=None):
        """
        Sends application data from client to server (e.g. HTTP GET, SMTP command).
        Sets PSH and ACK flags, advances client sequence number.
        """
        self.current_time_offset_ms += 4
        payload_bytes = len(payload.encode("utf-8"))
        
        step = {
            "step_number": self.step_counter,
            "transport": "TCP",
            "protocol": "TCP",
            "direction": "client_to_server",
            "source": f"Client ({self.client_ip}:{self.client_port})",
            "destination": f"Server ({self.server_ip}:{self.server_port})",
            "title": title,
            "summary": summary or f"Client sends {payload_bytes} bytes of application payload with PSH flag set.",
            "flags": ["PSH", "ACK"],
            "seq": self.client_seq,
            "ack": self.client_ack,
            "len": payload_bytes,
            "win": self.client_win,
            "client_state": self.client_state,
            "server_state": self.server_state,
            "cwnd": self.cwnd,
            "app_step_ref": app_step_ref,
            "fields": {
                "TCP Flags": "[PSH, ACK]",
                "Sequence Number (Seq)": f"{self.client_seq}",
                "Acknowledgment (Ack)": f"{self.client_ack}",
                "Payload Length (Len)": f"{payload_bytes} bytes",
                "Window Size (Win)": f"{self.client_win} bytes",
                "Next Expected Seq": f"{self.client_seq + payload_bytes}",
                "Client State": self.client_state,
                "Server State": self.server_state
            },
            "raw_text": self._format_raw_tcp_segment(
                self.client_port, self.server_port, self.client_seq, self.client_ack,
                ["PSH", "ACK"], self.client_win, 20, payload=payload
            ),
            "timestamp_offset_ms": self.current_time_offset_ms
        }
        self.steps.append(step)
        self.step_counter += 1
        
        # Advance sequence and server's expected ack
        self.client_seq += payload_bytes
        self.server_ack = self.client_seq

    def send_server_ack(self, summary="", app_step_ref=None):
        """
        Server sends pure ACK acknowledging received client bytes.
        """
        self.current_time_offset_ms += int(self.rtt_ms / 2)
        step = {
            "step_number": self.step_counter,
            "transport": "TCP",
            "protocol": "TCP",
            "direction": "server_to_client",
            "source": f"Server ({self.server_ip}:{self.server_port})",
            "destination": f"Client ({self.client_ip}:{self.client_port})",
            "title": "TCP ACK [Payload Acknowledgment]",
            "summary": summary or f"Server acknowledges client bytes up to Ack={self.server_ack}.",
            "flags": ["ACK"],
            "seq": self.server_seq,
            "ack": self.server_ack,
            "len": 0,
            "win": self.server_win,
            "client_state": self.client_state,
            "server_state": self.server_state,
            "cwnd": self.cwnd,
            "app_step_ref": app_step_ref,
            "fields": {
                "TCP Flags": "[ACK]",
                "Sequence Number (Seq)": f"{self.server_seq}",
                "Acknowledgment (Ack)": f"{self.server_ack}",
                "Window Size (Win)": f"{self.server_win} bytes",
                "Segment Length": "0 bytes",
                "Client State": self.client_state,
                "Server State": self.server_state
            },
            "raw_text": self._format_raw_tcp_segment(
                self.server_port, self.client_port, self.server_seq, self.server_ack,
                ["ACK"], self.server_win, 20
            ),
            "timestamp_offset_ms": self.current_time_offset_ms
        }
        self.steps.append(step)
        self.step_counter += 1

    def send_server_data(self, payload: str, title="TCP Data Segment [PSH, ACK]", summary="", app_step_ref=None, chunk_mss=False):
        """
        Sends application data from server to client.
        If chunk_mss is True and payload > MSS, splits into multiple segments to illustrate
        MSS segmenting, sliding window, and cumulative ACK.
        """
        payload_bytes = len(payload.encode("utf-8"))
        
        if chunk_mss and payload_bytes > self.mss:
            # Multi-segment transmission
            chunk1_len = self.mss
            chunk2_len = payload_bytes - self.mss
            
            # Segment 1
            self.current_time_offset_ms += 6
            step1 = {
                "step_number": self.step_counter,
                "transport": "TCP",
                "protocol": "TCP",
                "direction": "server_to_client",
                "source": f"Server ({self.server_ip}:{self.server_port})",
                "destination": f"Client ({self.client_ip}:{self.client_port})",
                "title": f"{title} (Part 1/2, MSS Chunk)",
                "summary": f"Server sends first data fragment of {chunk1_len} bytes (MSS limit).",
                "flags": ["ACK"],
                "seq": self.server_seq,
                "ack": self.server_ack,
                "len": chunk1_len,
                "win": self.server_win,
                "client_state": self.client_state,
                "server_state": self.server_state,
                "cwnd": self.cwnd,
                "app_step_ref": app_step_ref,
                "fields": {
                    "TCP Flags": "[ACK]",
                    "Sequence Number (Seq)": f"{self.server_seq}",
                    "Acknowledgment (Ack)": f"{self.server_ack}",
                    "Payload Length (Len)": f"{chunk1_len} bytes (MSS)",
                    "Window Size (Win)": f"{self.server_win} bytes",
                    "Next Expected Seq": f"{self.server_seq + chunk1_len}",
                    "Client State": self.client_state,
                    "Server State": self.server_state
                },
                "raw_text": self._format_raw_tcp_segment(
                    self.server_port, self.client_port, self.server_seq, self.server_ack,
                    ["ACK"], self.server_win, 20, payload=payload[:chunk1_len]
                ),
                "timestamp_offset_ms": self.current_time_offset_ms
            }
            self.steps.append(step1)
            self.step_counter += 1
            self.server_seq += chunk1_len
            
            # Segment 2
            self.current_time_offset_ms += 4
            step2 = {
                "step_number": self.step_counter,
                "transport": "TCP",
                "protocol": "TCP",
                "direction": "server_to_client",
                "source": f"Server ({self.server_ip}:{self.server_port})",
                "destination": f"Client ({self.client_ip}:{self.client_port})",
                "title": f"{title} (Part 2/2, Final Chunk)",
                "summary": f"Server sends remaining {chunk2_len} bytes with PSH flag set to flush to application.",
                "flags": ["PSH", "ACK"],
                "seq": self.server_seq,
                "ack": self.server_ack,
                "len": chunk2_len,
                "win": self.server_win,
                "client_state": self.client_state,
                "server_state": self.server_state,
                "cwnd": self.cwnd,
                "app_step_ref": app_step_ref,
                "fields": {
                    "TCP Flags": "[PSH, ACK]",
                    "Sequence Number (Seq)": f"{self.server_seq}",
                    "Acknowledgment (Ack)": f"{self.server_ack}",
                    "Payload Length (Len)": f"{chunk2_len} bytes",
                    "Window Size (Win)": f"{self.server_win} bytes",
                    "Next Expected Seq": f"{self.server_seq + chunk2_len}",
                    "Client State": self.client_state,
                    "Server State": self.server_state
                },
                "raw_text": self._format_raw_tcp_segment(
                    self.server_port, self.client_port, self.server_seq, self.server_ack,
                    ["PSH", "ACK"], self.server_win, 20, payload=payload[chunk1_len:]
                ),
                "timestamp_offset_ms": self.current_time_offset_ms
            }
            self.steps.append(step2)
            self.step_counter += 1
            self.server_seq += chunk2_len
            self.client_ack = self.server_seq
            
            # Client Cumulative ACK
            self.current_time_offset_ms += int(self.rtt_ms / 2)
            self.send_client_ack(summary=f"Client cumulatively acknowledges both segments up to Ack={self.client_ack}.", app_step_ref=app_step_ref)
        else:
            # Single segment
            self.current_time_offset_ms += int(self.rtt_ms / 2)
            step = {
                "step_number": self.step_counter,
                "transport": "TCP",
                "protocol": "TCP",
                "direction": "server_to_client",
                "source": f"Server ({self.server_ip}:{self.server_port})",
                "destination": f"Client ({self.client_ip}:{self.client_port})",
                "title": title,
                "summary": summary or f"Server sends {payload_bytes} bytes of application response data.",
                "flags": ["PSH", "ACK"],
                "seq": self.server_seq,
                "ack": self.server_ack,
                "len": payload_bytes,
                "win": self.server_win,
                "client_state": self.client_state,
                "server_state": self.server_state,
                "cwnd": self.cwnd,
                "app_step_ref": app_step_ref,
                "fields": {
                    "TCP Flags": "[PSH, ACK]",
                    "Sequence Number (Seq)": f"{self.server_seq}",
                    "Acknowledgment (Ack)": f"{self.server_ack}",
                    "Payload Length (Len)": f"{payload_bytes} bytes",
                    "Window Size (Win)": f"{self.server_win} bytes",
                    "Next Expected Seq": f"{self.server_seq + payload_bytes}",
                    "Client State": self.client_state,
                    "Server State": self.server_state
                },
                "raw_text": self._format_raw_tcp_segment(
                    self.server_port, self.client_port, self.server_seq, self.server_ack,
                    ["PSH", "ACK"], self.server_win, 20, payload=payload
                ),
                "timestamp_offset_ms": self.current_time_offset_ms
            }
            self.steps.append(step)
            self.step_counter += 1
            
            self.server_seq += payload_bytes
            self.client_ack = self.server_seq
            
            # Client ACK
            self.current_time_offset_ms += int(self.rtt_ms / 2)
            self.send_client_ack(summary=f"Client acknowledges server data up to Ack={self.client_ack}.", app_step_ref=app_step_ref)

    def send_client_ack(self, summary="", app_step_ref=None):
        """
        Client sends pure ACK acknowledging received server bytes.
        """
        step = {
            "step_number": self.step_counter,
            "transport": "TCP",
            "protocol": "TCP",
            "direction": "client_to_server",
            "source": f"Client ({self.client_ip}:{self.client_port})",
            "destination": f"Server ({self.server_ip}:{self.server_port})",
            "title": "TCP ACK [Receiver Acknowledgment]",
            "summary": summary or f"Client sends cumulative ACK up to Ack={self.client_ack}.",
            "flags": ["ACK"],
            "seq": self.client_seq,
            "ack": self.client_ack,
            "len": 0,
            "win": self.client_win,
            "client_state": self.client_state,
            "server_state": self.server_state,
            "cwnd": self.cwnd,
            "app_step_ref": app_step_ref,
            "fields": {
                "TCP Flags": "[ACK]",
                "Sequence Number (Seq)": f"{self.client_seq}",
                "Acknowledgment (Ack)": f"{self.client_ack}",
                "Window Size (Win)": f"{self.client_win} bytes",
                "Segment Length": "0 bytes",
                "Client State": self.client_state,
                "Server State": self.server_state
            },
            "raw_text": self._format_raw_tcp_segment(
                self.client_port, self.server_port, self.client_seq, self.client_ack,
                ["ACK"], self.client_win, 20
            ),
            "timestamp_offset_ms": self.current_time_offset_ms
        }
        self.steps.append(step)
        self.step_counter += 1

    def add_teardown(self, initiator="client"):
        """
        Executes standard 4-Way TCP Teardown (RFC 793):
        1. FIN-ACK (Initiator -> Responder)
        2. ACK (Responder -> Initiator)
        3. FIN-ACK (Responder -> Initiator)
        4. ACK (Initiator -> Responder)
        Transitions client to TIME_WAIT (2*MSL) and server to CLOSED.
        """
        self.current_time_offset_ms += 10
        
        if initiator == "client":
            # 1. Client FIN-ACK
            self.client_state = "FIN_WAIT_1"
            step1 = {
                "step_number": self.step_counter,
                "transport": "TCP",
                "protocol": "TCP",
                "direction": "client_to_server",
                "source": f"Client ({self.client_ip}:{self.client_port})",
                "destination": f"Server ({self.server_ip}:{self.server_port})",
                "title": "TCP FIN-ACK [Teardown 1/4 - Close Initiate]",
                "summary": f"Client initiates connection termination (FIN flag set). Transitions to FIN_WAIT_1.",
                "flags": ["FIN", "ACK"],
                "seq": self.client_seq,
                "ack": self.client_ack,
                "len": 0,
                "win": self.client_win,
                "client_state": "FIN_WAIT_1",
                "server_state": "ESTABLISHED",
                "cwnd": self.cwnd,
                "fields": {
                    "TCP Flags": "[FIN, ACK]",
                    "Sequence Number (Seq)": f"{self.client_seq}",
                    "Acknowledgment (Ack)": f"{self.client_ack}",
                    "Window Size (Win)": f"{self.client_win} bytes",
                    "Segment Length": "0 bytes (FIN consumes 1 Seq)",
                    "Client State": "FIN_WAIT_1",
                    "Server State": "ESTABLISHED"
                },
                "raw_text": self._format_raw_tcp_segment(
                    self.client_port, self.server_port, self.client_seq, self.client_ack,
                    ["FIN", "ACK"], self.client_win, 20
                ),
                "timestamp_offset_ms": self.current_time_offset_ms
            }
            self.steps.append(step1)
            self.step_counter += 1
            # FIN consumes 1 sequence number
            self.client_seq += 1
            self.server_ack = self.client_seq
            
            # 2. Server ACK
            self.current_time_offset_ms += int(self.rtt_ms / 2)
            self.server_state = "CLOSE_WAIT"
            self.client_state = "FIN_WAIT_2"
            step2 = {
                "step_number": self.step_counter,
                "transport": "TCP",
                "protocol": "TCP",
                "direction": "server_to_client",
                "source": f"Server ({self.server_ip}:{self.server_port})",
                "destination": f"Client ({self.client_ip}:{self.client_port})",
                "title": "TCP ACK [Teardown 2/4 - Close Wait]",
                "summary": f"Server acknowledges client FIN. Client enters FIN_WAIT_2; Server enters CLOSE_WAIT.",
                "flags": ["ACK"],
                "seq": self.server_seq,
                "ack": self.server_ack,
                "len": 0,
                "win": self.server_win,
                "client_state": "FIN_WAIT_2",
                "server_state": "CLOSE_WAIT",
                "cwnd": self.cwnd,
                "fields": {
                    "TCP Flags": "[ACK]",
                    "Sequence Number (Seq)": f"{self.server_seq}",
                    "Acknowledgment (Ack)": f"{self.server_ack} (Client FIN + 1)",
                    "Window Size (Win)": f"{self.server_win} bytes",
                    "Client State": "FIN_WAIT_2",
                    "Server State": "CLOSE_WAIT"
                },
                "raw_text": self._format_raw_tcp_segment(
                    self.server_port, self.client_port, self.server_seq, self.server_ack,
                    ["ACK"], self.server_win, 20
                ),
                "timestamp_offset_ms": self.current_time_offset_ms
            }
            self.steps.append(step2)
            self.step_counter += 1
            
            # 3. Server FIN-ACK
            self.current_time_offset_ms += 8
            self.server_state = "LAST_ACK"
            step3 = {
                "step_number": self.step_counter,
                "transport": "TCP",
                "protocol": "TCP",
                "direction": "server_to_client",
                "source": f"Server ({self.server_ip}:{self.server_port})",
                "destination": f"Client ({self.client_ip}:{self.client_port})",
                "title": "TCP FIN-ACK [Teardown 3/4 - Server Close]",
                "summary": f"Server finishes outstanding operations and closes its end. Transitions to LAST_ACK.",
                "flags": ["FIN", "ACK"],
                "seq": self.server_seq,
                "ack": self.server_ack,
                "len": 0,
                "win": self.server_win,
                "client_state": "FIN_WAIT_2",
                "server_state": "LAST_ACK",
                "cwnd": self.cwnd,
                "fields": {
                    "TCP Flags": "[FIN, ACK]",
                    "Sequence Number (Seq)": f"{self.server_seq}",
                    "Acknowledgment (Ack)": f"{self.server_ack}",
                    "Window Size (Win)": f"{self.server_win} bytes",
                    "Segment Length": "0 bytes (FIN consumes 1 Seq)",
                    "Client State": "FIN_WAIT_2",
                    "Server State": "LAST_ACK"
                },
                "raw_text": self._format_raw_tcp_segment(
                    self.server_port, self.client_port, self.server_seq, self.server_ack,
                    ["FIN", "ACK"], self.server_win, 20
                ),
                "timestamp_offset_ms": self.current_time_offset_ms
            }
            self.steps.append(step3)
            self.step_counter += 1
            # FIN consumes 1 sequence number
            self.server_seq += 1
            self.client_ack = self.server_seq
            
            # 4. Client final ACK
            self.current_time_offset_ms += int(self.rtt_ms / 2)
            self.client_state = "TIME_WAIT"
            self.server_state = "CLOSED"
            step4 = {
                "step_number": self.step_counter,
                "transport": "TCP",
                "protocol": "TCP",
                "direction": "client_to_server",
                "source": f"Client ({self.client_ip}:{self.client_port})",
                "destination": f"Server ({self.server_ip}:{self.server_port})",
                "title": "TCP ACK [Teardown 4/4 - TIME_WAIT]",
                "summary": f"Client acknowledges server FIN. Server enters CLOSED; Client enters TIME_WAIT (2*MSL timer) before closing.",
                "flags": ["ACK"],
                "seq": self.client_seq,
                "ack": self.client_ack,
                "len": 0,
                "win": self.client_win,
                "client_state": "TIME_WAIT (2*MSL)",
                "server_state": "CLOSED",
                "cwnd": self.cwnd,
                "fields": {
                    "TCP Flags": "[ACK]",
                    "Sequence Number (Seq)": f"{self.client_seq}",
                    "Acknowledgment (Ack)": f"{self.client_ack} (Server FIN + 1)",
                    "Window Size (Win)": f"{self.client_win} bytes",
                    "Client State": "TIME_WAIT (2*MSL)",
                    "Server State": "CLOSED"
                },
                "raw_text": self._format_raw_tcp_segment(
                    self.client_port, self.server_port, self.client_seq, self.client_ack,
                    ["ACK"], self.client_win, 20
                ),
                "timestamp_offset_ms": self.current_time_offset_ms
            }
            self.steps.append(step4)
            self.step_counter += 1
        else:
            # Server-initiated teardown
            self.server_state = "FIN_WAIT_1"
            step1 = {
                "step_number": self.step_counter,
                "transport": "TCP",
                "protocol": "TCP",
                "direction": "server_to_client",
                "source": f"Server ({self.server_ip}:{self.server_port})",
                "destination": f"Client ({self.client_ip}:{self.client_port})",
                "title": "TCP FIN-ACK [Teardown 1/4 - Server Initiates Close]",
                "summary": f"Server closes connection (FIN flag set).",
                "flags": ["FIN", "ACK"],
                "seq": self.server_seq,
                "ack": self.server_ack,
                "len": 0,
                "win": self.server_win,
                "client_state": "ESTABLISHED",
                "server_state": "FIN_WAIT_1",
                "cwnd": self.cwnd,
                "fields": {
                    "TCP Flags": "[FIN, ACK]",
                    "Sequence Number (Seq)": f"{self.server_seq}",
                    "Acknowledgment (Ack)": f"{self.server_ack}",
                    "Window Size (Win)": f"{self.server_win} bytes",
                    "Client State": "ESTABLISHED",
                    "Server State": "FIN_WAIT_1"
                },
                "raw_text": self._format_raw_tcp_segment(
                    self.server_port, self.client_port, self.server_seq, self.server_ack,
                    ["FIN", "ACK"], self.server_win, 20
                ),
                "timestamp_offset_ms": self.current_time_offset_ms
            }
            self.steps.append(step1)
            self.step_counter += 1
            self.server_seq += 1
            self.client_ack = self.server_seq
            
            # Client ACK
            self.current_time_offset_ms += int(self.rtt_ms / 2)
            self.client_state = "CLOSE_WAIT"
            self.server_state = "FIN_WAIT_2"
            step2 = {
                "step_number": self.step_counter,
                "transport": "TCP",
                "protocol": "TCP",
                "direction": "client_to_server",
                "source": f"Client ({self.client_ip}:{self.client_port})",
                "destination": f"Server ({self.server_ip}:{self.server_port})",
                "title": "TCP ACK [Teardown 2/4 - Client Acknowledges]",
                "summary": f"Client acknowledges server FIN.",
                "flags": ["ACK"],
                "seq": self.client_seq,
                "ack": self.client_ack,
                "len": 0,
                "win": self.client_win,
                "client_state": "CLOSE_WAIT",
                "server_state": "FIN_WAIT_2",
                "cwnd": self.cwnd,
                "fields": {
                    "TCP Flags": "[ACK]",
                    "Sequence Number (Seq)": f"{self.client_seq}",
                    "Acknowledgment (Ack)": f"{self.client_ack}",
                    "Client State": "CLOSE_WAIT",
                    "Server State": "FIN_WAIT_2"
                },
                "raw_text": self._format_raw_tcp_segment(
                    self.client_port, self.server_port, self.client_seq, self.client_ack,
                    ["ACK"], self.client_win, 20
                ),
                "timestamp_offset_ms": self.current_time_offset_ms
            }
            self.steps.append(step2)
            self.step_counter += 1
            
            # Client FIN-ACK
            self.current_time_offset_ms += 6
            self.client_state = "LAST_ACK"
            step3 = {
                "step_number": self.step_counter,
                "transport": "TCP",
                "protocol": "TCP",
                "direction": "client_to_server",
                "source": f"Client ({self.client_ip}:{self.client_port})",
                "destination": f"Server ({self.server_ip}:{self.server_port})",
                "title": "TCP FIN-ACK [Teardown 3/4 - Client Close]",
                "summary": f"Client finishes closing and sends FIN.",
                "flags": ["FIN", "ACK"],
                "seq": self.client_seq,
                "ack": self.client_ack,
                "len": 0,
                "win": self.client_win,
                "client_state": "LAST_ACK",
                "server_state": "FIN_WAIT_2",
                "cwnd": self.cwnd,
                "fields": {
                    "TCP Flags": "[FIN, ACK]",
                    "Sequence Number (Seq)": f"{self.client_seq}",
                    "Acknowledgment (Ack)": f"{self.client_ack}",
                    "Client State": "LAST_ACK",
                    "Server State": "FIN_WAIT_2"
                },
                "raw_text": self._format_raw_tcp_segment(
                    self.client_port, self.server_port, self.client_seq, self.client_ack,
                    ["FIN", "ACK"], self.client_win, 20
                ),
                "timestamp_offset_ms": self.current_time_offset_ms
            }
            self.steps.append(step3)
            self.step_counter += 1
            self.client_seq += 1
            self.server_ack = self.client_seq
            
            # Server ACK
            self.current_time_offset_ms += int(self.rtt_ms / 2)
            self.server_state = "TIME_WAIT (2*MSL)"
            self.client_state = "CLOSED"
            step4 = {
                "step_number": self.step_counter,
                "transport": "TCP",
                "protocol": "TCP",
                "direction": "server_to_client",
                "source": f"Server ({self.server_ip}:{self.server_port})",
                "destination": f"Client ({self.client_ip}:{self.client_port})",
                "title": "TCP ACK [Teardown 4/4 - Connection Closed]",
                "summary": f"Server acknowledges client FIN. Client CLOSED; Server enters TIME_WAIT.",
                "flags": ["ACK"],
                "seq": self.server_seq,
                "ack": self.server_ack,
                "len": 0,
                "win": self.server_win,
                "client_state": "CLOSED",
                "server_state": "TIME_WAIT",
                "cwnd": self.cwnd,
                "fields": {
                    "TCP Flags": "[ACK]",
                    "Sequence Number (Seq)": f"{self.server_seq}",
                    "Acknowledgment (Ack)": f"{self.server_ack}",
                    "Client State": "CLOSED",
                    "Server State": "TIME_WAIT (2*MSL)"
                },
                "raw_text": self._format_raw_tcp_segment(
                    self.server_port, self.client_port, self.server_seq, self.server_ack,
                    ["ACK"], self.server_win, 20
                ),
                "timestamp_offset_ms": self.current_time_offset_ms
            }
            self.steps.append(step4)
            self.step_counter += 1


def generate_browsing_transport_steps(dns_steps, http_steps, domain="example.com", server_ip="93.184.215.14", persistent=False):
    """
    Generates synchronized Transport Layer steps for the Web Browsing activity:
    - UDP Datagrams for DNS query & response (port 53)
    - TCP 3-way Handshake on port 80/443 (SYN, SYN-ACK, ACK)
    - TCP Data segments carrying HTTP GET and HTTP 200 response with MSS segmentation
    - TCP 4-way Teardown (or kept ESTABLISHED if persistent=True)
    """
    transport_steps = []
    step_num = 1
    
    # 1. DNS over UDP Port 53
    client_dns_port = random.randint(49152, 59999)
    if dns_steps and len(dns_steps) >= 2:
        # Step 1: DNS Query Datagram
        q_step = dns_steps[0]
        q_len = 38
        transport_steps.append({
            "step_number": step_num,
            "transport": "UDP",
            "protocol": "UDP",
            "direction": "client_to_server",
            "source": f"Client (192.168.1.105:{client_dns_port})",
            "destination": "DNS Resolver (8.8.8.8:53)",
            "title": "UDP Datagram (DNS Query)",
            "summary": f"Client sends {q_len}-byte UDP datagram to port 53. Connectionless, zero-RTT delivery.",
            "flags": ["UDP"],
            "seq": 0,
            "ack": 0,
            "len": q_len,
            "win": 0,
            "client_state": "N/A (Connectionless)",
            "server_state": "N/A (Connectionless)",
            "app_step_ref": 1,
            "fields": {
                "Transport": "UDP (User Datagram Protocol)",
                "Source Port": f"{client_dns_port}",
                "Destination Port": "53 (Domain Name System)",
                "UDP Length": f"{q_len + 8} bytes (Header: 8B, Data: {q_len}B)",
                "Checksum": f"0x{random.randint(0x1000, 0xFFFF):04X}",
                "Delivery Model": "Unreliable Datagram (No Handshake)"
            },
            "raw_text": f"User Datagram Protocol, Src Port: {client_dns_port}, Dst Port: 53\nSource Port: {client_dns_port}\nDestination Port: 53\nLength: {q_len + 8}\nChecksum: 0x48a1 [unverified]\n[Payload: DNS Query for {domain}]",
            "timestamp_offset_ms": q_step.get("timestamp_offset_ms", 0)
        })
        step_num += 1
        
        # Step 2: DNS Response Datagram
        r_step = dns_steps[1]
        r_len = 54
        transport_steps.append({
            "step_number": step_num,
            "transport": "UDP",
            "protocol": "UDP",
            "direction": "server_to_client",
            "source": "DNS Resolver (8.8.8.8:53)",
            "destination": f"Client (192.168.1.105:{client_dns_port})",
            "title": "UDP Datagram (DNS Response)",
            "summary": f"DNS Resolver returns A-record for '{domain}' in a {r_len}-byte datagram.",
            "flags": ["UDP"],
            "seq": 0,
            "ack": 0,
            "len": r_len,
            "win": 0,
            "client_state": "N/A (Connectionless)",
            "server_state": "N/A (Connectionless)",
            "app_step_ref": 2,
            "fields": {
                "Transport": "UDP (User Datagram Protocol)",
                "Source Port": "53",
                "Destination Port": f"{client_dns_port}",
                "UDP Length": f"{r_len + 8} bytes",
                "Checksum": f"0x{random.randint(0x1000, 0xFFFF):04X}",
                "Resolved IP": server_ip
            },
            "raw_text": f"User Datagram Protocol, Src Port: 53, Dst Port: {client_dns_port}\nSource Port: 53\nDestination Port: {client_dns_port}\nLength: {r_len + 8}\nChecksum: 0x82b9 [unverified]\n[Payload: DNS A-Record -> {server_ip}]",
            "timestamp_offset_ms": r_step.get("timestamp_offset_ms", 15)
        })
        step_num += 1

    # 2. TCP Connection for HTTP
    tcp = TCPConnection(server_port=80, server_ip=server_ip)
    tcp.step_counter = step_num
    base_tcp_time = transport_steps[-1]["timestamp_offset_ms"] + 5 if transport_steps else 20
    
    # 3-Way Handshake
    tcp.add_handshake(base_time_ms=base_tcp_time)
    
    # HTTP Request over TCP
    http_req_text = "GET / HTTP/1.1\r\nHost: " + domain + "\r\nUser-Agent: Mozilla/5.0\r\nAccept: text/html\r\nConnection: " + ("keep-alive" if persistent else "close") + "\r\n\r\n"
    if http_steps and len(http_steps) >= 1:
        http_req_text = http_steps[0].get("raw_text", http_req_text)
        
    tcp.send_client_data(
        payload=http_req_text,
        title="TCP PSH+ACK [HTTP GET Request]",
        summary=f"Client transmits HTTP GET request ({len(http_req_text)} bytes) over established TCP byte-stream.",
        app_step_ref=3
    )
    
    # Server ACK for request
    tcp.send_server_ack(
        summary=f"Server acknowledges reception of HTTP request bytes (Ack={tcp.server_ack}).",
        app_step_ref=3
    )
    
    # HTTP Response over TCP
    http_resp_text = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: 1256\r\n\r\n<!DOCTYPE html><html><body><h1>Example Domain</h1></body></html>"
    if http_steps and len(http_steps) >= 2:
        http_resp_text = http_steps[1].get("raw_text", http_resp_text)
        
    tcp.send_server_data(
        payload=http_resp_text,
        title="TCP PSH+ACK [HTTP 200 OK Response]",
        summary=f"Server sends HTTP 200 OK payload ({len(http_resp_text)} bytes) to client.",
        app_step_ref=4,
        chunk_mss=True
    )
    
    # Teardown (if non-persistent) or Keep-Alive notification
    if not persistent:
        tcp.add_teardown(initiator="client")
    else:
        # Kept ESTABLISHED
        tcp.current_time_offset_ms += 10
        step_keepalive = {
            "step_number": tcp.step_counter,
            "transport": "TCP",
            "protocol": "TCP",
            "direction": "client_to_server",
            "source": f"Client ({tcp.client_ip}:{tcp.client_port})",
            "destination": f"Server ({tcp.server_ip}:{tcp.server_port})",
            "title": "TCP Connection Retained [Keep-Alive Mode]",
            "summary": "Connection: keep-alive enabled. TCP socket remains in ESTABLISHED state for subsequent HTTP requests (saves 1-RTT handshake).",
            "flags": ["ACK"],
            "seq": tcp.client_seq,
            "ack": tcp.client_ack,
            "len": 0,
            "win": tcp.client_win,
            "client_state": "ESTABLISHED",
            "server_state": "ESTABLISHED",
            "cwnd": tcp.cwnd,
            "fields": {
                "TCP Flags": "[ACK]",
                "Connection Mode": "Persistent (HTTP/1.1 Keep-Alive)",
                "Client State": "ESTABLISHED",
                "Server State": "ESTABLISHED",
                "Sockets Open": "Active (Reusable for next GET)"
            },
            "raw_text": tcp._format_raw_tcp_segment(tcp.client_port, tcp.server_port, tcp.client_seq, tcp.client_ack, ["ACK"], tcp.client_win, 20),
            "timestamp_offset_ms": tcp.current_time_offset_ms
        }
        tcp.steps.append(step_keepalive)
        tcp.step_counter += 1

    transport_steps.extend(tcp.steps)
    return transport_steps


def generate_mail_transport_steps(from_email, to_email, subject, body, smtp_result):
    """
    Generates synchronized Transport Layer steps for the Mail (SMTP) activity:
    - DNS MX lookup datagrams over UDP port 53
    - TCP 3-Way Handshake with MTA on port 25
    - Exact TCP segment exchanges for each RFC 5321 command and reply:
      220 Greeting, EHLO, 250, MAIL FROM, 250, RCPT TO, 250, DATA, 354, Payload, 250 Queued, QUIT, 221 Bye
    - TCP 4-Way Teardown (Server-initiated or client-initiated)
    """
    transport_steps = []
    step_num = 1
    
    server_host = smtp_result.get("server_host", "mail.university.edu")
    server_ip = "198.51.100.25"
    client_dns_port = random.randint(49152, 59999)
    
    # 1. DNS MX UDP exchange
    q_len = 42
    transport_steps.append({
        "step_number": step_num,
        "transport": "UDP",
        "protocol": "UDP",
        "direction": "client_to_server",
        "source": f"Client MUA (192.168.1.105:{client_dns_port})",
        "destination": "DNS Resolver (8.8.8.8:53)",
        "title": "UDP Datagram (DNS MX Query)",
        "summary": f"Resolves Mail Exchange MX records for recipient domain over UDP port 53.",
        "flags": ["UDP"],
        "seq": 0, "ack": 0, "len": q_len, "win": 0,
        "client_state": "N/A", "server_state": "N/A",
        "app_step_ref": 1,
        "fields": {
            "Transport": "UDP Port 53",
            "Query": f"MX for {to_email.split('@')[-1] if '@' in to_email else 'domain'}",
            "Delivery": "Connectionless"
        },
        "raw_text": f"User Datagram Protocol, Src Port: {client_dns_port}, Dst Port: 53\nLength: {q_len + 8}\n[DNS MX Query]",
        "timestamp_offset_ms": 0
    })
    step_num += 1
    
    r_len = 68
    transport_steps.append({
        "step_number": step_num,
        "transport": "UDP",
        "protocol": "UDP",
        "direction": "server_to_client",
        "source": "DNS Resolver (8.8.8.8:53)",
        "destination": f"Client MUA (192.168.1.105:{client_dns_port})",
        "title": "UDP Datagram (DNS MX Response)",
        "summary": f"DNS returns MX record: preference 10, {server_host} ({server_ip}).",
        "flags": ["UDP"],
        "seq": 0, "ack": 0, "len": r_len, "win": 0,
        "client_state": "N/A", "server_state": "N/A",
        "app_step_ref": 2,
        "fields": {
            "Transport": "UDP Port 53",
            "Answer": f"MX 10 {server_host} -> {server_ip}"
        },
        "raw_text": f"User Datagram Protocol, Src Port: 53, Dst Port: {client_dns_port}\nLength: {r_len + 8}\n[DNS MX Answer -> {server_host}]",
        "timestamp_offset_ms": 15
    })
    step_num += 1

    # 2. TCP Handshake on Port 25
    tcp = TCPConnection(server_port=25, server_ip=server_ip)
    tcp.step_counter = step_num
    tcp.add_handshake(base_time_ms=25)
    
    # 3. Conversational SMTP stream over TCP
    app_steps = smtp_result.get("steps", [])
    
    # Mapping app steps to transport:
    # App steps:
    # 3: Server 220 Greeting
    # 4: Client EHLO
    # 5: Server 250 Capabilities
    # 6: Client MAIL FROM
    # 7: Server 250 OK
    # 8: Client RCPT TO
    # 9: Server 250 OK
    # 10: Client DATA
    # 11: Server 354 Start mail input
    # 12: Client Message payload
    # 13: Server 250 Queued
    # 14: Client QUIT
    # 15: Server 221 Bye
    
    for s in app_steps[2:]:
        direction = s.get("direction")
        raw_cmd = s.get("raw_text", "")
        title = s.get("title", "")
        app_num = s.get("step_number")
        
        if direction == "server_to_client":
            tcp.send_server_data(
                payload=raw_cmd,
                title=f"TCP PSH+ACK [SMTP: {title}]",
                summary=f"Server sends SMTP response: '{raw_cmd.splitlines()[0] if raw_cmd else title}' over TCP stream.",
                app_step_ref=app_num
            )
        else:
            tcp.send_client_data(
                payload=raw_cmd,
                title=f"TCP PSH+ACK [SMTP: {title}]",
                summary=f"Client transmits SMTP command: '{raw_cmd.splitlines()[0] if raw_cmd else title}' over TCP stream.",
                app_step_ref=app_num
            )
            # Add server ACK acknowledging command
            tcp.send_server_ack(
                summary=f"Server acknowledges client SMTP command bytes.",
                app_step_ref=app_num
            )
            
    # 4. TCP Teardown after QUIT / 221
    tcp.add_teardown(initiator="client")
    
    transport_steps.extend(tcp.steps)
    return transport_steps


def generate_streaming_transport_steps(video, quality, stream_init_result, mode="tcp"):
    """
    Generates synchronized Transport Layer steps for Video Streaming:
    - Mode 'tcp': TCP 3-way handshake with CDN edge, Manifest GET/200, Segment GET/206 with
      Flow Control (Receive Window), Congestion Control (cwnd doubling in Slow Start), and cumulative ACKs.
    - Mode 'udp': RTP over UDP live stream simulation (0-RTT, datagrams, no ACKs, packet loss resilience).
    - Mode 'quic': QUIC / HTTP/3 over UDP simulation (0-RTT/1-RTT handshake, Stream IDs, no HOL blocking).
    """
    transport_steps = []
    step_num = 1
    cdn_host = video.get("cdn_host", "cdn.videostream.net")
    cdn_ip = video.get("cdn_ip", "104.21.64.18")
    
    # 1. CDN DNS UDP
    client_dns_port = random.randint(49152, 59999)
    transport_steps.append({
        "step_number": step_num,
        "transport": "UDP",
        "protocol": "UDP",
        "direction": "client_to_server",
        "source": f"Client (192.168.1.105:{client_dns_port})",
        "destination": "DNS Resolver (8.8.8.8:53)",
        "title": "UDP Datagram (CDN Edge DNS Query)",
        "summary": f"Resolves CDN edge hostname '{cdn_host}' via UDP port 53.",
        "flags": ["UDP"],
        "seq": 0, "ack": 0, "len": 44, "win": 0,
        "client_state": "N/A", "server_state": "N/A",
        "app_step_ref": 1,
        "fields": {
            "Transport": "UDP Port 53",
            "Hostname": cdn_host,
            "Mode": "Connectionless"
        },
        "raw_text": f"User Datagram Protocol, Src Port: {client_dns_port}, Dst Port: 53\nLength: 52\n[DNS Query for {cdn_host}]",
        "timestamp_offset_ms": 0
    })
    step_num += 1
    
    transport_steps.append({
        "step_number": step_num,
        "transport": "UDP",
        "protocol": "UDP",
        "direction": "server_to_client",
        "source": "DNS Resolver (8.8.8.8:53)",
        "destination": f"Client (192.168.1.105:{client_dns_port})",
        "title": "UDP Datagram (CDN Edge IP Answer)",
        "summary": f"DNS Resolver returns closest Anycast CDN IP: {cdn_ip}.",
        "flags": ["UDP"],
        "seq": 0, "ack": 0, "len": 60, "win": 0,
        "client_state": "N/A", "server_state": "N/A",
        "app_step_ref": 2,
        "fields": {
            "Transport": "UDP Port 53",
            "Anycast IP": cdn_ip,
            "TTL": "300s"
        },
        "raw_text": f"User Datagram Protocol, Src Port: 53, Dst Port: {client_dns_port}\nLength: 68\n[DNS A-Record: {cdn_ip}]",
        "timestamp_offset_ms": 12
    })
    step_num += 1

    if mode == "udp":
        # UDP / RTP Datagram comparison mode
        client_rtp_port = 5004
        server_rtp_port = 5004
        current_time = 25
        
        # RTP stream initiation
        transport_steps.append({
            "step_number": step_num,
            "transport": "UDP",
            "protocol": "RTP/UDP",
            "direction": "client_to_server",
            "source": f"Player (192.168.1.105:{client_rtp_port})",
            "destination": f"Media Server ({cdn_ip}:{server_rtp_port})",
            "title": "RTSP/UDP Setup [Direct Datagram Channel]",
            "summary": "Player requests UDP media stream. NO TCP 3-way handshake needed; socket bound immediately.",
            "flags": ["UDP"],
            "seq": 0, "ack": 0, "len": 120, "win": 0,
            "client_state": "OPEN (Datagram)", "server_state": "OPEN (Datagram)",
            "app_step_ref": 3,
            "fields": {
                "Protocol": "UDP / RTSP Setup",
                "Client Port": f"{client_rtp_port}",
                "Server Port": f"{server_rtp_port}",
                "Handshake Overhead": "0 RTT (Zero Connection Latency)"
            },
            "raw_text": f"User Datagram Protocol, Src Port: {client_rtp_port}, Dst Port: {server_rtp_port}\nLength: 128\n[RTSP SETUP Request: Transport: RTP/AVP/UDP]",
            "timestamp_offset_ms": current_time
        })
        step_num += 1
        
        # Multiple continuous RTP datagrams
        ssrc = f"0x{random.randint(0x10000000, 0xFFFFFFFF):08X}"
        for i in range(1, 6):
            current_time += 15
            rtp_seq = 1000 + i
            rtp_ts = 90000 * i
            transport_steps.append({
                "step_number": step_num,
                "transport": "UDP",
                "protocol": "RTP/UDP",
                "direction": "server_to_client",
                "source": f"Media Server ({cdn_ip}:{server_rtp_port})",
                "destination": f"Player (192.168.1.105:{client_rtp_port})",
                "title": f"RTP Packet #{rtp_seq} over UDP (H.264 Video)",
                "summary": f"Server streams 1400-byte video datagram. Unacknowledged fire-and-forget delivery.",
                "flags": ["UDP", "RTP"],
                "seq": rtp_seq, "ack": 0, "len": 1400, "win": 0,
                "client_state": "STREAMING", "server_state": "STREAMING",
                "app_step_ref": 4 + (i % 4),
                "fields": {
                    "Transport": "UDP (8-byte Header)",
                    "RTP Version": "2",
                    "Payload Type": "96 (Dynamic H.264 Video)",
                    "RTP Sequence Number": f"{rtp_seq}",
                    "RTP Timestamp": f"{rtp_ts} (90 kHz clock)",
                    "SSRC Identifier": ssrc,
                    "Reliability Model": "Best-Effort (Loss Tolerant, No Retransmit Delays)"
                },
                "raw_text": f"Real-Time Transport Protocol\n  [Payload Type: H264 (96), SSeq: {rtp_seq}, Timestamp: {rtp_ts}]\n  Synchronization Source: {ssrc}\nUser Datagram Protocol, Src Port: {server_rtp_port}, Dst Port: {client_rtp_port}\nLength: 1408\n[H.264 NAL Unit Slice Data]",
                "timestamp_offset_ms": current_time
            })
            step_num += 1
            
        return transport_steps

    elif mode == "quic":
        # QUIC / HTTP/3 over UDP comparison mode
        current_time = 25
        cid_client = f"0x{random.randint(0x10000000, 0xFFFFFFFF):08X}"
        cid_server = f"0x{random.randint(0x10000000, 0xFFFFFFFF):08X}"
        
        # 1. QUIC Initial (Client -> Server)
        transport_steps.append({
            "step_number": step_num,
            "transport": "QUIC",
            "protocol": "QUIC",
            "direction": "client_to_server",
            "source": f"Player (192.168.1.105:52180)",
            "destination": f"CDN Edge ({cdn_ip}:443)",
            "title": "QUIC Initial [1-RTT Handshake Initiate]",
            "summary": "Client sends QUIC Initial packet containing TLS 1.3 ClientHello inside UDP datagram.",
            "flags": ["Initial", "CRYPTO"],
            "seq": 0, "ack": 0, "len": 1200, "win": 0,
            "client_state": "HANDSHAKE", "server_state": "LISTEN",
            "app_step_ref": 3,
            "fields": {
                "Transport": "QUIC over UDP Port 443",
                "Packet Type": "Initial (Long Header)",
                "Destination Connection ID": cid_server,
                "Source Connection ID": cid_client,
                "Frames": "CRYPTO (TLS 1.3 ClientHello), PADDING",
                "Multiplexing": "Stream-based (No Head-of-Line Blocking)"
            },
            "raw_text": f"QUIC Protocol (RFC 9000)\n  Header: Long Header, Type: Initial\n  DCID: {cid_server}, SCID: {cid_client}\n  Frame: CRYPTO (Offset: 0, Length: 256)\n  TLS 1.3 Handshake: ClientHello",
            "timestamp_offset_ms": current_time
        })
        step_num += 1
        
        # 2. QUIC Handshake Response (Server -> Client)
        current_time += 14
        transport_steps.append({
            "step_number": step_num,
            "transport": "QUIC",
            "protocol": "QUIC",
            "direction": "server_to_client",
            "source": f"CDN Edge ({cdn_ip}:443)",
            "destination": f"Player (192.168.1.105:52180)",
            "title": "QUIC Handshake [ServerHello + EncryptedExtensions]",
            "summary": "Server replies with TLS 1.3 ServerHello and Handshake Finished. Handshake completes in 1-RTT.",
            "flags": ["Handshake", "ACK"],
            "seq": 0, "ack": 0, "len": 1280, "win": 0,
            "client_state": "1-RTT Connected", "server_state": "1-RTT Connected",
            "app_step_ref": 4,
            "fields": {
                "Transport": "QUIC over UDP",
                "Packet Type": "Handshake",
                "Connection Established": "1-RTT (Ready for HTTP/3 Streams)",
                "Encryption": "1-RTT Application Keys Active"
            },
            "raw_text": f"QUIC Protocol (RFC 9000)\n  Header: Long Header, Type: Handshake\n  Frame: CRYPTO (TLS 1.3 ServerHello, Finished)\n  Frame: ACK (Largest Acknowledged: 0)",
            "timestamp_offset_ms": current_time
        })
        step_num += 1
        
        # 3. QUIC HTTP/3 Stream Data
        current_time += 10
        transport_steps.append({
            "step_number": step_num,
            "transport": "QUIC",
            "protocol": "HTTP/3",
            "direction": "client_to_server",
            "source": f"Player (192.168.1.105:52180)",
            "destination": f"CDN Edge ({cdn_ip}:443)",
            "title": "QUIC 1-RTT [HTTP/3 GET master.m3u8]",
            "summary": "Client fetches manifest on Stream ID 0. Independent streams prevent head-of-line blocking.",
            "flags": ["1-RTT", "STREAM"],
            "seq": 1, "ack": 0, "len": 180, "win": 0,
            "client_state": "ACTIVE", "server_state": "ACTIVE",
            "app_step_ref": 5,
            "fields": {
                "Packet Type": "Short Header (1-RTT)",
                "Stream ID": "0 (Client-Initiated, Bidirectional)",
                "HTTP/3 Frame": "HEADERS (GET /master.m3u8)",
                "Multiplexing Advantage": "Lost segment packet won't stall manifest stream"
            },
            "raw_text": f"QUIC Protocol\n  Header: Short Header (1-RTT)\n  Frame: STREAM (Stream ID: 0, Offset: 0, Length: 180, Fin: 1)\n  HTTP/3 HEADERS: :method=GET, :path=/master.m3u8",
            "timestamp_offset_ms": current_time
        })
        step_num += 1
        
        return transport_steps

    # Default Mode: TCP (HLS over TCP)
    tcp = TCPConnection(server_port=443, server_ip=cdn_ip)
    tcp.step_counter = step_num
    tcp.add_handshake(base_time_ms=25)
    
    # 1. Master manifest GET
    tcp.send_client_data(
        payload="GET /master.m3u8 HTTP/1.1\r\nHost: " + cdn_host + "\r\nAccept: application/x-mpegURL\r\nConnection: keep-alive\r\n\r\n",
        title="TCP PSH+ACK [HTTP GET master.m3u8]",
        summary=f"Player requests HLS master manifest to inspect available bitrates.",
        app_step_ref=3
    )
    tcp.send_server_ack(summary="CDN Edge acknowledges manifest GET request.", app_step_ref=3)
    
    # 2. Master manifest 200 OK
    manifest_body = "#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-STREAM-INF:BANDWIDTH=5200000,RESOLUTION=1920x1080\n1080p/index.m3u8\n#EXT-X-STREAM-INF:BANDWIDTH=2800000,RESOLUTION=1280x720\n720p/index.m3u8"
    tcp.send_server_data(
        payload=f"HTTP/1.1 200 OK\r\nContent-Type: application/vnd.apple.mpegurl\r\nContent-Length: {len(manifest_body)}\r\n\r\n{manifest_body}",
        title="TCP PSH+ACK [HTTP 200 Master Manifest]",
        summary=f"CDN returns master manifest playlist ({len(manifest_body)} bytes).",
        app_step_ref=4
    )
    
    # 3. Media Playlist GET
    tcp.send_client_data(
        payload=f"GET /{quality}/index.m3u8 HTTP/1.1\r\nHost: {cdn_host}\r\nConnection: keep-alive\r\n\r\n",
        title=f"TCP PSH+ACK [HTTP GET {quality}/index.m3u8]",
        summary=f"Player requests media segment playlist for {quality} quality tier.",
        app_step_ref=5
    )
    tcp.send_server_ack(summary="CDN Edge acknowledges media playlist request.", app_step_ref=5)
    
    # 4. Media Playlist 200 OK
    playlist_body = f"#EXTM3U\n#EXT-X-TARGETDURATION:4\n#EXTINF:4.000,\nsegment_000.ts\n#EXTINF:4.000,\nsegment_001.ts"
    tcp.send_server_data(
        payload=f"HTTP/1.1 200 OK\r\nContent-Type: application/vnd.apple.mpegurl\r\nContent-Length: {len(playlist_body)}\r\n\r\n{playlist_body}",
        title=f"TCP PSH+ACK [HTTP 200 {quality} Playlist]",
        summary=f"CDN delivers media chunk index list for {quality}.",
        app_step_ref=6
    )
    
    # 5. First Segment GET (segment_000.ts)
    tcp.send_client_data(
        payload=f"GET /{quality}/segment_000.ts HTTP/1.1\r\nHost: {cdn_host}\r\nRange: bytes=0-716799\r\nConnection: keep-alive\r\n\r\n",
        title="TCP PSH+ACK [HTTP GET segment_000.ts]",
        summary=f"Player requests initial video transport chunk with byte-range header.",
        app_step_ref=7
    )
    tcp.send_server_ack(summary="CDN Edge acknowledges segment_000.ts request.", app_step_ref=7)
    
    # 6. Segment Download with Slow Start / Flow Control Demonstration
    tcp.cwnd = 20 * tcp.mss  # Doubled in slow start
    tcp.congestion_phase = "Slow Start (cwnd = 20 MSS)"
    seg_resp_headers = f"HTTP/1.1 206 Partial Content\r\nContent-Type: video/mp2t\r\nContent-Range: bytes 0-716799/716800\r\nContent-Length: 716800\r\n\r\n[MPEG-2 Transport Stream Binary Data]"
    tcp.send_server_data(
        payload=seg_resp_headers,
        title="TCP PSH+ACK [HTTP 206 Video Segment Chunk]",
        summary=f"CDN delivers 700 KB video chunk. TCP congestion window expanded to {tcp.cwnd} bytes (Slow Start).",
        app_step_ref=8,
        chunk_mss=True
    )
    
    transport_steps.extend(tcp.steps)
    return transport_steps


def generate_streaming_segment_transport_steps(video, quality, segment_num, start_step_num=9, mode="tcp"):
    """
    Generates dynamic Transport Layer steps when a subsequent video segment is fetched:
    - Simulates ongoing TCP byte transfers, window scaling, and cumulative ACKs.
    - Or RTP/UDP datagrams if in UDP mode.
    """
    cdn_host = video.get("cdn_host", "cdn.videostream.net")
    cdn_ip = video.get("cdn_ip", "104.21.64.18")
    
    if mode == "udp":
        client_rtp_port = 5004
        server_rtp_port = 5004
        rtp_seq = 2000 + segment_num
        rtp_ts = 90000 * (segment_num + 1)
        
        step_datagram = {
            "step_number": start_step_num,
            "transport": "UDP",
            "protocol": "RTP/UDP",
            "direction": "server_to_client",
            "source": f"Media Server ({cdn_ip}:{server_rtp_port})",
            "destination": f"Player (192.168.1.105:{client_rtp_port})",
            "title": f"RTP Packet #{rtp_seq} [Segment #{segment_num} Datagram]",
            "summary": f"Live media server streams RTP video datagram over UDP (no ACK, low latency).",
            "flags": ["UDP", "RTP"],
            "seq": rtp_seq, "ack": 0, "len": 1400, "win": 0,
            "client_state": "STREAMING", "server_state": "STREAMING",
            "fields": {
                "Transport": "UDP Port 5004",
                "RTP Sequence": f"{rtp_seq}",
                "RTP Timestamp": f"{rtp_ts}",
                "Bandwidth Control": "Bitrate-Governed (No TCP backoff)"
            },
            "raw_text": f"Real-Time Transport Protocol, Seq: {rtp_seq}, Timestamp: {rtp_ts}\nUser Datagram Protocol, Src Port: {server_rtp_port}, Dst Port: {client_rtp_port}\nLength: 1408",
            "timestamp_offset_ms": 20
        }
        return [step_datagram]

    # TCP Segment
    tcp = TCPConnection(server_port=443, server_ip=cdn_ip)
    tcp.step_counter = start_step_num
    tcp.client_seq = 1000000 + (segment_num * 50000)
    tcp.server_seq = 2000000 + (segment_num * 800000)
    tcp.client_ack = tcp.server_seq
    tcp.server_ack = tcp.client_seq
    tcp.client_state = "ESTABLISHED"
    tcp.server_state = "ESTABLISHED"
    tcp.cwnd = min(64 * tcp.mss, 10 * tcp.mss * (segment_num + 1))
    
    # 1. Segment Request
    req_payload = f"GET /{quality}/segment_{segment_num:03d}.ts HTTP/1.1\r\nHost: {cdn_host}\r\nConnection: keep-alive\r\n\r\n"
    tcp.send_client_data(
        payload=req_payload,
        title=f"TCP PSH+ACK [HTTP GET segment_{segment_num:03d}.ts]",
        summary=f"Player requests next video segment #{segment_num} ({quality}) over existing persistent TCP connection."
    )
    
    # 2. Server ACK
    tcp.send_server_ack(summary="CDN Edge acknowledges segment GET request.")
    
    # 3. Server Response
    resp_payload = f"HTTP/1.1 206 Partial Content\r\nContent-Type: video/mp2t\r\nContent-Length: 720000\r\n\r\n[MPEG-2 Transport Stream Data]"
    tcp.send_server_data(
        payload=resp_payload,
        title=f"TCP PSH+ACK [HTTP 206 Segment #{segment_num} Stream]",
        summary=f"CDN delivers video chunk data. Window size: {tcp.server_win}, cwnd: {tcp.cwnd} bytes.",
        chunk_mss=True
    )
    
    return tcp.steps
