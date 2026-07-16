"""M1推荐模块 - HTTP服务（纯Python，不依赖pydantic）"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

from models import StudentProfile, to_dict
from recommend import recommend


class RecommendHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        parsed = urlparse(self.path)
        
        if parsed.path == "/api/recommend":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            
            try:
                data = json.loads(body)
                student_data = data.get("student", data)
                
                # 提取timePreference（从请求或默认）
                time_preference = student_data.pop("timePreference", "上午")
                
                student = StudentProfile(**student_data)
                response = recommend(student, time_preference)
                result = to_dict(response)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                error = {"error": {"code": "INTERNAL_ERROR", "message": str(e), "trace_id": None}}
                self.wfile.write(json.dumps(error, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            result = {"status": "ok", "module": "M1-recommend", "version": "1.0.0"}
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def log_message(self, format, *args):
        print(f"[M1] {args[0]}")


def run_server(port=8001):
    server = HTTPServer(("0.0.0.0", port), RecommendHandler)
    print(f"M1推荐服务启动: http://localhost:{port}")
    print(f"健康检查: GET http://localhost:{port}/health")
    print(f"推荐接口: POST http://localhost:{port}/api/recommend")
    print("按 Ctrl+C 停止服务")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
