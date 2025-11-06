"""
Simplest possible API endpoint for Vercel
"""

def handler(request, context):
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/plain',
        },
        'body': 'Hello World'
    }
