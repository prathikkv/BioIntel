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
        """Handle all HTTP requests safely"""
        try:
            if not FASTAPI_AVAILABLE or not app:
                self._send_error_response(500, "FastAPI not available")
                return
            
            # Parse request
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            # Basic routing
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
                        "auth_register": "/api/auth/register",
                        "auth_login": "/api/auth/login"
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
                
            elif path == "/api/auth/register" and self.command == "POST":
                response_data = {
                    "message": "Registration endpoint ready",
                    "status": "service_initializing",
                    "timestamp": time.time()
                }
                self._send_json_response(200, response_data)
                
            elif path == "/api/auth/login" and self.command == "POST":
                response_data = {
                    "message": "Login endpoint ready", 
                    "status": "service_initializing",
                    "timestamp": time.time()
                }
                self._send_json_response(200, response_data)
                
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
                        "/api/auth/register",
                        "/api/auth/login"
                    ],
                    "timestamp": time.time()
                }
                self._send_json_response(404, response_data)
                
        except Exception as e:
            print(f"Request handling error: {e}")
            self._send_error_response(500, f"Internal server error: {str(e)}")
    
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