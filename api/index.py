from urllib.parse import parse_qs
import json

def handler(environ, start_response):
    """WSGI-compatible handler for Vercel"""
    
    # Extract request info
    method = environ.get('REQUEST_METHOD', 'GET')
    path_info = environ.get('PATH_INFO', '/')
    query_string = environ.get('QUERY_STRING', '')
    
    # CORS headers
    headers = [
        ('Content-Type', 'application/json'),
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
        ('Access-Control-Allow-Headers', '*')
    ]
    
    try:
        # Handle OPTIONS request
        if method == 'OPTIONS':
            start_response('200 OK', headers)
            return [b'']
        
        # Route the request
        if method == 'GET':
            if 'health' in path_info:
                response_data = {
                    "status": "healthy",
                    "deployment": "vercel-wsgi",
                    "path": path_info
                }
            elif 'element-types' in path_info:
                response_data = {
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
                response_data = {
                    "message": "CheckMeasureAI API is running",
                    "deployment": "vercel-wsgi",
                    "status": "online",
                    "path": path_info,
                    "method": method
                }
                
        elif method == 'POST':
            if 'calculate' in path_info:
                response_data = {
                    "element_code": "J1",
                    "calculations": {"span_length": 4.0},
                    "cutting_list": [{"element_code": "J1", "quantity": 1}],
                    "formatted_output": "Basic calculation result",
                    "deployment": "vercel-wsgi"
                }
            else:
                response_data = {
                    "error": "POST endpoint not found",
                    "path": path_info,
                    "deployment": "vercel-wsgi"
                }
        else:
            response_data = {
                "error": "Method not allowed", 
                "method": method,
                "deployment": "vercel-wsgi"
            }
        
        # Return successful response
        start_response('200 OK', headers)
        return [json.dumps(response_data).encode('utf-8')]
        
    except Exception as e:
        # Return error response
        error_response = {
            "error": "Internal server error",
            "details": str(e),
            "deployment": "vercel-wsgi"
        }
        start_response('500 Internal Server Error', headers)
        return [json.dumps(error_response).encode('utf-8')]