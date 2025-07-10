"""
BioIntel.AI - Ultra-Safe Vercel Handler
Minimal FastAPI application for Vercel deployment without heavy dependencies
"""
import os
import sys
import json
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from io import StringIO

# Add project root to path
current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Safe FastAPI import with comprehensive error handling
try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
    print("✅ FastAPI imported successfully")
except ImportError as e:
    FASTAPI_AVAILABLE = False
    print(f"❌ FastAPI import failed: {e}")

# Create minimal FastAPI app
if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="BioIntel.AI",
        description="Free AI-powered bioinformatics platform",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Welcome to BioIntel.AI",
            "description": "Free AI-powered bioinformatics platform",
            "version": "1.0.0",
            "status": "running",
            "timestamp": time.time(),
            "environment": os.getenv("ENVIRONMENT", "production"),
            "endpoints": {
                "health": "/health",
                "docs": "/docs",
                "redoc": "/redoc"
            }
        }
    
    # Health check
    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0"
        }
    
    # Safe authentication endpoints (without heavy imports)
    class UserRegister(BaseModel):
        email: str
        password: str
        full_name: str = None
    
    class UserLogin(BaseModel):
        email: str
        password: str
    
    @app.post("/api/auth/register")
    async def register(user: UserRegister):
        """Safe registration endpoint"""
        return {
            "message": "Registration endpoint available",
            "email": user.email,
            "status": "authentication_service_initializing"
        }
    
    @app.post("/api/auth/login") 
    async def login(user: UserLogin):
        """Safe login endpoint"""
        return {
            "message": "Login endpoint available",
            "email": user.email,
            "status": "authentication_service_initializing"
        }
    
    @app.get("/api/auth/me")
    async def get_me():
        """Safe user info endpoint"""
        return {
            "message": "User endpoint available",
            "status": "authentication_service_initializing"
        }
    
    print("✅ FastAPI app created successfully")
    
else:
    app = None
    print("❌ FastAPI app creation failed")

# Vercel handler class
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._handle_request()
    
    def do_POST(self):
        self._handle_request()
    
    def do_PUT(self):
        self._handle_request()
    
    def do_DELETE(self):
        self._handle_request()
    
    def do_PATCH(self):
        self._handle_request()
    
    def do_OPTIONS(self):
        self._send_cors_headers()
        self.end_headers()
    
    def _handle_request(self):
        """Handle all HTTP requests by delegating to FastAPI"""
        try:
            if not FASTAPI_AVAILABLE or not app:
                self._send_error_response(500, "FastAPI not available")
                return
            
            # Create ASGI scope for FastAPI
            from io import BytesIO
            import asyncio
            
            # Read request body for POST requests
            content_length = int(self.headers.get('content-length', 0))
            request_body = b''
            if content_length > 0:
                request_body = self.rfile.read(content_length)
            
            # Parse URL
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_string = parsed_url.query.encode() if parsed_url.query else b''
            
            # Create ASGI scope
            scope = {
                "type": "http",
                "method": self.command,
                "path": path,
                "query_string": query_string,
                "headers": [
                    (name.lower().encode(), value.encode()) 
                    for name, value in self.headers.items()
                ],
                "server": ("localhost", 8000),
                "client": (self.client_address[0], self.client_address[1])
            }
            
            # Async receive callable
            async def receive():
                return {
                    "type": "http.request",
                    "body": request_body,
                    "more_body": False
                }
            
            # Response data
            response_data = {
                "status": 200,
                "headers": [],
                "body": b""
            }
            
            # Async send callable  
            async def send(message):
                if message["type"] == "http.response.start":
                    response_data["status"] = message["status"]
                    response_data["headers"] = message.get("headers", [])
                elif message["type"] == "http.response.body":
                    response_data["body"] += message.get("body", b"")
            
            # Run FastAPI app
            async def run_app():
                await app(scope, receive, send)
            
            # Execute async
            try:
                asyncio.run(run_app())
                
                # Send response
                self.send_response(response_data["status"])
                self._send_cors_headers()
                
                # Send headers
                for header_name, header_value in response_data["headers"]:
                    self.send_header(header_name.decode(), header_value.decode())
                
                self.end_headers()
                
                # Send body
                if response_data["body"]:
                    self.wfile.write(response_data["body"])
                    
            except Exception as fastapi_error:
                print(f"FastAPI execution error: {fastapi_error}")
                # Fallback to simple routing for critical endpoints
                self._handle_fallback_routing()
                
        except Exception as e:
            print(f"Request handling error: {e}")
            self._send_error_response(500, f"Internal server error: {str(e)}")
    
    def _handle_fallback_routing(self):
        """Fallback routing when FastAPI delegation fails"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == "/" or path == "":
            response_data = {
                "message": "Welcome to BioIntel.AI",
                "description": "Free AI-powered bioinformatics platform", 
                "version": "1.0.0",
                "status": "running",
                "timestamp": time.time(),
                "endpoints": {
                    "health": "/health",
                    "docs": "/docs",
                    "auth_register": "/api/auth/register (POST)",
                    "auth_login": "/api/auth/login (POST)"
                }
            }
            self._send_json_response(200, response_data)
            
        elif path == "/health":
            response_data = {
                "status": "healthy",
                "timestamp": time.time(),
                "version": "1.0.0",
                "environment": os.getenv("ENVIRONMENT", "production")
            }
            self._send_json_response(200, response_data)
            
        elif path in ["/api/auth/register", "/api/auth/registration"] and self.command == "POST":
            # Handle both register and registration paths
            response_data = {
                "message": "Registration endpoint ready",
                "note": "Use POST /api/auth/register with JSON body: {\"email\": \"user@example.com\", \"password\": \"pass123\", \"full_name\": \"Name\"}",
                "status": "service_initializing",
                "timestamp": time.time()
            }
            self._send_json_response(200, response_data)
            
        elif path == "/api/auth/login" and self.command == "POST":
            response_data = {
                "message": "Login endpoint ready",
                "note": "Use POST /api/auth/login with JSON body: {\"email\": \"user@example.com\", \"password\": \"pass123\"}",
                "status": "service_initializing", 
                "timestamp": time.time()
            }
            self._send_json_response(200, response_data)
            
        elif path in ["/api/auth/register", "/api/auth/registration", "/api/auth/login"] and self.command == "GET":
            # Helpful error for wrong HTTP method
            response_data = {
                "error": "Method Not Allowed",
                "message": f"Endpoint {path} requires POST request, not GET",
                "correct_usage": f"POST {path}",
                "content_type": "application/json",
                "example_body": {
                    "email": "user@example.com",
                    "password": "your_password",
                    "full_name": "Your Name" if "register" in path else None
                },
                "timestamp": time.time()
            }
            # Remove None values
            response_data["example_body"] = {k: v for k, v in response_data["example_body"].items() if v is not None}
            self._send_json_response(405, response_data)
            
        else:
            # 404 for unknown paths
            response_data = {
                "error": "Not Found",
                "path": path,
                "method": self.command,
                "available_endpoints": [
                    "/",
                    "/health", 
                    "/docs",
                    "POST /api/auth/register",
                    "POST /api/auth/login"
                ],
                "note": "Authentication endpoints require POST requests",
                "timestamp": time.time()
            }
            self._send_json_response(404, response_data)
    
    def _send_json_response(self, status_code, data):
        """Send JSON response"""
        try:
            response_json = json.dumps(data, indent=2)
            self.send_response(status_code)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response_json)))
            self.end_headers()
            self.wfile.write(response_json.encode('utf-8'))
        except Exception as e:
            print(f"JSON response error: {e}")
            self._send_error_response(500, "Response generation failed")
    
    def _send_error_response(self, status_code, message):
        """Send error response"""
        try:
            error_data = {
                "error": message,
                "status_code": status_code,
                "timestamp": time.time()
            }
            response_json = json.dumps(error_data)
            self.send_response(status_code)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(response_json.encode('utf-8'))
        except Exception as e:
            print(f"Error response failed: {e}")
    
    def _send_cors_headers(self):
        """Send CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')
    
    def log_message(self, format, *args):
        """Override to prevent log spam"""
        pass

# For local testing
if __name__ == "__main__":
    print("🚀 Starting BioIntel.AI Safe Handler")
    print(f"FastAPI Available: {FASTAPI_AVAILABLE}")
    if FASTAPI_AVAILABLE and app:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        print("❌ Cannot start - FastAPI not available")