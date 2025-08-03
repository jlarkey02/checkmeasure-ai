from http.server import BaseHTTPRequestHandler
import json
import urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse the path
        path = self.path
        
        # Set CORS headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
        
        # Route the request
        if path == '/health' or path == '/api/health':
            response = {
                "status": "healthy",
                "deployment": "vercel-python-handler"
            }
        elif path == '/api/calculations/element-types':
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
        elif path == '/' or path == '/api/':
            response = {
                "message": "CheckMeasureAI API is running",
                "deployment": "vercel-python-handler",
                "status": "online"
            }
        else:
            response = {
                "error": "Endpoint not found",
                "path": path,
                "deployment": "vercel-python-handler"
            }
        
        # Send the response
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def do_POST(self):
        # Set CORS headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
        
        # Parse the path
        path = self.path
        
        if path == '/api/calculations/calculate':
            response = {
                "element_code": "J1",
                "calculations": {"span_length": 4.0},
                "cutting_list": [{"element_code": "J1", "quantity": 1}],
                "formatted_output": "Basic calculation result",
                "deployment": "vercel-python-handler"
            }
        else:
            response = {
                "error": "POST endpoint not found",
                "path": path,
                "deployment": "vercel-python-handler"
            }
        
        # Send the response
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()