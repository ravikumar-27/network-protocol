"""
Unit and Integration Tests for Dual-Panel Activity & Protocol Visualizer
Assignment 2: Application Layer + Transport Layer Visualizer
"""
import unittest
import json
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from protocol_engine import (
    resolve_dns,
    execute_http_request,
    simulate_smtp_transaction,
    generate_streaming_init_steps,
    generate_segment_step,
    TCPConnection,
    generate_browsing_transport_steps,
    generate_mail_transport_steps,
    generate_streaming_transport_steps,
    generate_streaming_segment_transport_steps,
    STREAM_PRESETS
)

class TestProtocolEngines(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_dns_engine(self):
        result = resolve_dns("example.com", "A")
        self.assertEqual(result["record_type"], "A")
        self.assertGreaterEqual(len(result["steps"]), 2)
        step1, step2 = result["steps"][0], result["steps"][1]
        self.assertEqual(step1["direction"], "client_to_server")
        self.assertEqual(step2["direction"], "server_to_client")
        self.assertEqual(step1["protocol"], "DNS")
        self.assertEqual(step2["protocol"], "DNS")

    def test_http_engine(self):
        result = execute_http_request("http://example.com", "93.184.215.14")
        self.assertEqual(result["status_code"], 200)
        self.assertEqual(len(result["steps"]), 2)
        req_step, resp_step = result["steps"][0], result["steps"][1]
        self.assertEqual(req_step["protocol"], "HTTP")
        self.assertEqual(req_step["direction"], "client_to_server")
        self.assertEqual(resp_step["direction"], "server_to_client")
        self.assertIn("GET", req_step["raw_text"])

    def test_smtp_engine(self):
        result = simulate_smtp_transaction(
            "student@university.edu",
            "prof@university.edu",
            "Assignment",
            "Here is the submission."
        )
        self.assertEqual(result["total_steps"], 15)
        commands = [s["raw_text"] for s in result["steps"]]
        self.assertTrue(any("EHLO" in c for c in commands))
        self.assertTrue(any("MAIL FROM" in c for c in commands))
        self.assertTrue(any("RCPT TO" in c for c in commands))
        self.assertTrue(any("DATA" in c for c in commands))
        self.assertTrue(any("250 2.0.0 Ok: queued" in c for c in commands))
        self.assertTrue(any("QUIT" in c for c in commands))
        self.assertTrue(any("221" in c for c in commands))

    def test_tcp_state_machine_and_seq_ack(self):
        """Tests RFC 793 byte-accurate TCP handshake, data transfer, and teardown."""
        tcp = TCPConnection(client_port=54000, server_port=80)
        self.assertEqual(tcp.client_state, "CLOSED")
        self.assertEqual(tcp.server_state, "LISTEN")
        
        # 1. Handshake
        tcp.add_handshake(base_time_ms=0)
        self.assertEqual(tcp.client_state, "ESTABLISHED")
        self.assertEqual(tcp.server_state, "ESTABLISHED")
        self.assertEqual(len(tcp.steps), 3)
        
        # Check SYN consumed 1 sequence number
        syn_step = tcp.steps[0]
        synack_step = tcp.steps[1]
        ack_step = tcp.steps[2]
        self.assertIn("SYN", syn_step["flags"])
        self.assertEqual(synack_step["ack"], syn_step["seq"] + 1)
        self.assertEqual(ack_step["ack"], synack_step["seq"] + 1)
        
        # 2. Data Transfer (PSH, ACK)
        old_client_seq = tcp.client_seq
        payload = "GET /index.html HTTP/1.1\r\nHost: example.com\r\n\r\n"
        payload_len = len(payload)
        tcp.send_client_data(payload)
        self.assertEqual(tcp.client_seq, old_client_seq + payload_len)
        self.assertEqual(tcp.server_ack, old_client_seq + payload_len)
        
        # 3. Teardown
        tcp.add_teardown(initiator="client")
        self.assertEqual(tcp.client_state, "TIME_WAIT")
        self.assertEqual(tcp.server_state, "CLOSED")

    def test_browsing_transport_steps(self):
        dns_res = resolve_dns("example.com", "A")
        http_res = execute_http_request("http://example.com", dns_res["primary_ip"])
        
        # Non-persistent
        steps = generate_browsing_transport_steps(dns_res["steps"], http_res["steps"], "example.com", dns_res["primary_ip"], persistent=False)
        self.assertGreaterEqual(len(steps), 8)
        # First 2 steps are UDP DNS
        self.assertEqual(steps[0]["transport"], "UDP")
        self.assertEqual(steps[1]["transport"], "UDP")
        # Step 3 is TCP SYN
        self.assertEqual(steps[2]["transport"], "TCP")
        self.assertIn("SYN", steps[2]["flags"])
        # Contains Teardown FIN
        self.assertTrue(any("FIN" in s.get("flags", []) for s in steps))

        # Persistent
        steps_p = generate_browsing_transport_steps(dns_res["steps"], http_res["steps"], "example.com", dns_res["primary_ip"], persistent=True)
        self.assertTrue(any("Keep-Alive" in s.get("title", "") for s in steps_p))

    def test_mail_transport_steps(self):
        smtp_res = simulate_smtp_transaction("alice@lab.edu", "bob@lab.edu", "Test", "Msg")
        steps = generate_mail_transport_steps("alice@lab.edu", "bob@lab.edu", "Test", "Msg", smtp_res)
        # Should have UDP DNS, TCP handshake, multi-turn SMTP over TCP, and teardown
        self.assertGreaterEqual(len(steps), 15)
        protocols = [s["transport"] for s in steps]
        self.assertIn("UDP", protocols)
        self.assertIn("TCP", protocols)
        # Verify EHLO, DATA, QUIT are sent as TCP segments
        summaries = " ".join([s["summary"] for s in steps])
        self.assertIn("EHLO", summaries)
        self.assertIn("DATA", summaries)
        self.assertIn("QUIT", summaries)

    def test_streaming_modes(self):
        video = STREAM_PRESETS["bbb"]
        init_res = generate_streaming_init_steps("bbb", "720p")
        
        # TCP mode
        tcp_steps = generate_streaming_transport_steps(video, "720p", init_res, mode="tcp")
        self.assertGreaterEqual(len(tcp_steps), 8)
        self.assertTrue(any("SYN" in s.get("flags", []) for s in tcp_steps))
        
        # UDP (RTP) mode
        udp_steps = generate_streaming_transport_steps(video, "720p", init_res, mode="udp")
        self.assertGreaterEqual(len(udp_steps), 5)
        self.assertTrue(any("RTP" in s.get("flags", []) for s in udp_steps))
        
        # QUIC mode
        quic_steps = generate_streaming_transport_steps(video, "720p", init_res, mode="quic")
        self.assertGreaterEqual(len(quic_steps), 4)
        self.assertTrue(any(s.get("transport") == "QUIC" for s in quic_steps))

    def test_flask_endpoints_dual_layer(self):
        # Health
        res = self.app.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json["status"], "healthy")
        self.assertIn("Transport Layer", res.json["layers_supported"])

        # Browse - Returns both app_steps and transport_steps
        res = self.app.post("/api/browse", json={"url": "example.com", "persistent": False})
        self.assertEqual(res.status_code, 200)
        data = res.json
        self.assertIn("app_steps", data)
        self.assertIn("transport_steps", data)
        self.assertGreaterEqual(len(data["app_steps"]), 4)
        self.assertGreaterEqual(len(data["transport_steps"]), 8)

        # Mail - Returns both app_steps and transport_steps
        res = self.app.post("/api/mail/send", json={
            "from": "student@college.edu",
            "to": "prof@college.edu",
            "subject": "Hi",
            "body": "Test body"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json
        self.assertIn("app_steps", data)
        self.assertIn("transport_steps", data)
        self.assertEqual(len(data["app_steps"]), 15)
        self.assertGreaterEqual(len(data["transport_steps"]), 15)

        # Stream Init - TCP
        res = self.app.post("/api/stream/init", json={"video_id": "bbb", "quality": "720p", "transport_mode": "tcp"})
        self.assertEqual(res.status_code, 200)
        data = res.json
        self.assertIn("app_steps", data)
        self.assertIn("transport_steps", data)

        # Stream Init - UDP
        res_udp = self.app.post("/api/stream/init", json={"video_id": "bbb", "quality": "720p", "transport_mode": "udp"})
        self.assertEqual(res_udp.status_code, 200)
        self.assertEqual(res_udp.json["transport_mode"], "udp")

        # Stream Segment
        res_seg = self.app.post("/api/stream/segment", json={
            "video_id": "bbb",
            "quality": "720p",
            "segment_num": 1,
            "start_step_num": 9,
            "transport_mode": "tcp"
        })
        self.assertEqual(res_seg.status_code, 200)
        self.assertIn("request_step", res_seg.json)
        self.assertIn("response_step", res_seg.json)
        self.assertIn("transport_steps", res_seg.json)

    def test_static_and_templates(self):
        # Index
        res = self.app.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Dual-Panel Activity", res.data)

        with self.app.get("/static/css/style.css") as res:
            self.assertEqual(res.status_code, 200)

        with self.app.get("/static/js/app.js") as res:
            self.assertEqual(res.status_code, 200)

        with self.app.get("/static/js/visualizer.js") as res:
            self.assertEqual(res.status_code, 200)

        with self.app.get("/static/js/streaming.js") as res:
            self.assertEqual(res.status_code, 200)

if __name__ == "__main__":
    unittest.main()
