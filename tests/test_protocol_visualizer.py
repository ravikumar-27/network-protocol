"""
Unit and Integration Tests for Dual-Panel Activity & Protocol Visualizer
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
    generate_segment_step
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
        # Verify complete RFC 5321 commands exist
        commands = [s["raw_text"] for s in result["steps"]]
        self.assertTrue(any("EHLO" in c for c in commands))
        self.assertTrue(any("MAIL FROM" in c for c in commands))
        self.assertTrue(any("RCPT TO" in c for c in commands))
        self.assertTrue(any("DATA" in c for c in commands))
        self.assertTrue(any("250 2.0.0 Ok: queued" in c for c in commands))
        self.assertTrue(any("QUIT" in c for c in commands))
        self.assertTrue(any("221" in c for c in commands))

    def test_streaming_engine(self):
        result = generate_streaming_init_steps("bbb", "720p")
        self.assertEqual(result["total_steps"], 8)
        # Check manifest and segment steps
        protocols = [s["protocol"] for s in result["steps"]]
        self.assertIn("DNS", protocols)
        self.assertIn("HTTP", protocols)
        
        # Test subsequent segment fetch
        seg_pair = generate_segment_step("bbb", "720p", 2, 9)
        self.assertEqual(seg_pair["request_step"]["protocol"], "HTTP")
        self.assertEqual(seg_pair["response_step"]["fields"]["Status Line"], "HTTP/1.1 206 Partial Content")

    def test_flask_endpoints(self):
        # Health
        res = self.app.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json["status"], "healthy")

        # Browse
        res = self.app.post("/api/browse", json={"url": "example.com"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json["status"], "success")
        self.assertEqual(res.json["domain"], "example.com")
        self.assertGreaterEqual(len(res.json["steps"]), 4)

        # Mail
        res = self.app.post("/api/mail/send", json={
            "from": "student@college.edu",
            "to": "prof@college.edu",
            "subject": "Hi",
            "body": "Test body"
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json["status"], "success")
        self.assertEqual(len(res.json["steps"]), 15)

        # Stream Init
        res = self.app.post("/api/stream/init", json={"video_id": "bbb", "quality": "720p"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json["status"], "success")
        self.assertEqual(len(res.json["steps"]), 8)

        # Stream Segment
        res = self.app.post("/api/stream/segment", json={
            "video_id": "bbb",
            "quality": "720p",
            "segment_num": 1,
            "start_step_num": 9
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json["status"], "success")
        self.assertIn("request_step", res.json)
        self.assertIn("response_step", res.json)

    def test_static_and_templates(self):
        # Index
        res = self.app.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Dual-Panel Activity &amp; Protocol Visualizer", res.data)
        self.assertIn(b"Activity Panel", res.data)
        self.assertIn(b"Protocol Visualization Panel", res.data)

        # CSS
        res = self.app.get("/static/css/style.css")
        self.assertEqual(res.status_code, 200)

        # JS
        res = self.app.get("/static/js/app.js")
        self.assertEqual(res.status_code, 200)

        res = self.app.get("/static/js/visualizer.js")
        self.assertEqual(res.status_code, 200)

        res = self.app.get("/static/js/streaming.js")
        self.assertEqual(res.status_code, 200)

if __name__ == "__main__":
    unittest.main()
