import json

def handler(request, context):
    """Vercel serverless function handler"""
    try:
        # Get request method and path
        method = request.get('method', 'GET')
        path = request.get('path', '/')
        
        # Set CORS headers
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': '*'
        }
        
        # Handle OPTIONS (CORS preflight)
        if method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': ''
            }
        
        # Route the request
        if method == 'GET':
            if path.endswith('/health'):
                response_data = {
                    "status": "healthy",
                    "deployment": "vercel-function"
                }
            elif path.endswith('/element-types'):
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
                    "deployment": "vercel-function",
                    "status": "online",
                    "path": path,
                    "method": method
                }
                
        elif method == 'POST':
            if path.endswith('/calculate'):
                response_data = {
                    "element_code": "J1",
                    "calculations": {"span_length": 4.0},
                    "cutting_list": [{"element_code": "J1", "quantity": 1}],
                    "formatted_output": "Basic calculation result",
                    "deployment": "vercel-function"
                }
            else:
                response_data = {
                    "error": "POST endpoint not found",
                    "path": path,
                    "deployment": "vercel-function"
                }
        else:
            response_data = {
                "error": "Method not allowed",
                "method": method,
                "deployment": "vercel-function"
            }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                "error": "Internal server error",
                "details": str(e),
                "deployment": "vercel-function"
            })
        }