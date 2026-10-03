"""
UDP Protocol Engine (RFC 768) & Real-Time Transport Protocol (RFC 3550)
Simulates connectionless Transport Layer datagrams:
- Fixed 8-byte UDP header (Source Port, Destination Port, Length, Checksum)
- Zero connection setup overhead (0-RTT)
- Unreliable, best-effort datagram delivery
- RTP encapsulation for real-time video/audio streaming (Payload Type 96 H.264)
"""
import random

def format_udp_header(src_port: int, dst_port: int, length: int, checksum: str = None) -> dict:
    """
    Constructs a parsed RFC 768 UDP header dict and raw representation.
    """
    cs = checksum or f"0x{random.randint(0x1000, 0xFFFF):04X}"
    return {
        "Source Port": f"{src_port}",
        "Destination Port": f"{dst_port}",
        "Length": f"{length} bytes (Header: 8 bytes, Data: {length - 8} bytes)",
        "Checksum": f"{cs} [unverified]",
        "Stream Type": "Datagram (Connectionless)"
    }

def format_rtp_header(seq_num: int, timestamp: int, ssrc: str, pt: int = 96) -> dict:
    """
    Constructs an RFC 3550 RTP header dict.
    """
    return {
        "Version": "2",
        "Padding": "0",
        "Extension": "0",
        "CSRC Count": "0",
        "Marker": "1 (Frame Boundary)",
        "Payload Type": f"{pt} (Dynamic H.264 Video)",
        "Sequence Number": f"{seq_num}",
        "Timestamp": f"{timestamp} (90 kHz clock)",
        "Synchronization Source (SSRC)": ssrc
    }
