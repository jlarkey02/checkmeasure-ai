from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
        
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if 'health' in path:
            response = {
                "status": "healthy",
                "deployment": "vercel-http-handler"
            }
        elif 'element-types' in path:
            response = {
                "element_types": [
                    {
                        "code": "J1",
                        "description": "Joist - Floor/Ceiling",
                        "category": "structural",
                        "calculator_type": "joist",
                        "active": True
                    }
                ]
            }
        else:
            response = {
                "message": "CheckMeasureAI API is running",
                "deployment": "vercel-http-handler",
                "status": "online"
            }
        
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
        
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if 'calculate' in path:
            response = {
                "element_code": "J1",
                "calculations": {"span_length": 4.0},
                "cutting_list": [{"element_code": "J1", "quantity": 1}],
                "formatted_output": "Basic calculation result",
                "deployment": "vercel-http-handler"
            }
        else:
            response = {
                "error": "POST endpoint not found",
                "deployment": "vercel-http-handler"
            }
        
        self.wfile.write(json.dumps(response).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()