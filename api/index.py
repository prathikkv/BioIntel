from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = '{"message": "BioIntel.AI is working on Vercel!", "status": "healthy", "success": true}'
        self.wfile.write(response.encode('utf-8'))
        return

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = '{"message": "POST request received", "status": "healthy"}'
        self.wfile.write(response.encode('utf-8'))
        return