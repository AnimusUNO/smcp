#!/usr/bin/env python3
"""
Quick Mock Letta Server for Testing Puppetry Plugin
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
import time

class MockLettaHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "server": "mock-letta"}).encode())
            
        elif self.path == '/agents':
            self.send_response(200)
            self.send_header('Content-type', 'application/json') 
            self.end_headers()
            agents = {
                "agents": [
                    {"id": "demo-agent", "name": "Demo Agent", "created_at": "2024-01-01"},
                    {"id": "test-agent", "name": "Test Agent", "created_at": "2024-01-01"}
                ]
            }
            self.wfile.write(json.dumps(agents).encode())
            
        elif self.path.startswith('/agents/'):
            agent_id = self.path.split('/')[-1]
            if agent_id in ['demo-agent', 'test-agent']:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                agent = {
                    "id": agent_id,
                    "name": f"{agent_id.title()} Agent",
                    "created_at": "2024-01-01",
                    "persona": f"I am {agent_id}, a helpful AI assistant",
                    "human": "You are chatting with a human user"
                }
                self.wfile.write(json.dumps(agent).encode())
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path.startswith('/agents/') and self.path.endswith('/messages'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "messages": [
                    {
                        "id": "msg-123",
                        "role": "assistant", 
                        "text": "Hello! I'm responding from the mock server.",
                        "created_at": "2024-01-01"
                    }
                ]
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    server = HTTPServer(('localhost', 8283), MockLettaHandler)
    print("🚀 Mock Letta Server starting on http://localhost:8283")
    print("📊 Available test agents: demo-agent, test-agent")
    print("🔍 Health check: http://localhost:8283/health")
    print("📝 List agents: http://localhost:8283/agents")
    print("⚠️  Note: This is a MOCK server for testing only!")
    print("⏹️  Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Stopping mock server...")
        server.shutdown()