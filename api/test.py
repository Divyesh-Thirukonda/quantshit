"""
Minimal Vercel deployment test for Quantshit
"""
import json
from datetime import datetime

def handler(event, context):
    """Simple HTTP handler for Vercel"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps({
            'message': 'Quantshit Arbitrage Engine API',
            'version': '2.0.0',
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'note': 'Minimal deployment test - imports disabled for now'
        })
    }

# For FastAPI compatibility, create an app-like interface
class SimpleApp:
    def __call__(self, scope, receive, send):
        # ASGI app interface
        return handler(scope, None)

app = SimpleApp()

# For direct Vercel calling
def lambda_handler(event, context):
    return handler(event, context)