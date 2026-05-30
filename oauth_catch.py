import http.server, socketserver, urllib.parse, json
OUT='/Users/twinpeakstownie/reach_forward_agent/oauth_code.json'
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        params=dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
        open(OUT,'w').write(json.dumps(params))
        self.send_response(200); self.send_header('Content-Type','text/html'); self.end_headers()
        self.wfile.write(b'<html><body style="font-family:sans-serif;text-align:center;padding-top:80px"><h1>Code captured. You can close this tab.</h1></body></html>')
    def log_message(self,*a): pass
with socketserver.TCPServer(('127.0.0.1',8899),H) as s:
    s.handle_request()
print("captured")
