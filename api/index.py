"""
Vercel-compatible entry point for BioIntel.AI
Ultra-minimal version designed specifically for Vercel Python runtime
"""
import json
import os
import time

# Vercel Python function handler
def handler(request, context=None):
    """
    Main Vercel function handler
    This function will be called by Vercel's Python runtime
    """
    try:
        # Create a successful response
        response_data = {
            'message': 'BioIntel.AI is running on Vercel!',
            'status': 'healthy',
            'version': '1.0.0',
            'timestamp': time.time(),
            'environment': os.getenv('ENVIRONMENT', 'production'),
            'success': True,
            'vercel_runtime': 'python',
            'function_invocation': 'successful'
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            },
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        # If anything fails, return detailed error information
        error_response = {
            'error': 'Function execution failed',
            'details': str(e),
            'type': type(e).__name__,
            'timestamp': time.time(),
            'environment': os.getenv('ENVIRONMENT', 'unknown')
        }
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(error_response)
        }

# Alternative entry points for different Vercel configurations
app = handler  # For direct function calls
main = handler  # Alternative entry point

# Test the function locally
if __name__ == "__main__":
    print("Testing Vercel function handler...")
    result = handler({})
    print("Result:")
    print(json.dumps(result, indent=2))