"""Run from repository root: python -m campus.server. Loopback only."""
import io
import json
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
import zipfile
from campus.core import terms, translate, LibreEngine, render_template

ROOT = Path(__file__).resolve().parent.parent
ENGINE = LibreEngine(os.getenv('CAMPUS_LT_URL', 'http://127.0.0.1:5000'), os.getenv('CAMPUS_LT_API_KEY', ''))

def source_archive():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
        # The release manifest lists only distributed source and build materials.
        for name in json.loads((ROOT/'campus'/'source-manifest.json').read_text(encoding='utf-8')):
            p = (ROOT/name).resolve()
            if ROOT not in p.parents or not p.is_file():
                raise RuntimeError('源码清单无效，请重新生成发布包')
            z.write(p, name)
    return buffer.getvalue()

class Handler(BaseHTTPRequestHandler):
    def valid_host(self):
        return self.headers.get('Host') in {
            f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}

    def log_message(self, *args):
        pass

    def send(self, status, data, content_type='application/json; charset=utf-8'):
        if not isinstance(data, bytes): data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if not self.valid_host(): return self.send(403, {'error':'仅允许本机地址访问'})
        path = urlsplit(self.path).path
        if path == '/api/terms': return self.send(200, terms())
        if path == '/api/health':
            try:
                languages = ENGINE.request('/languages', timeout=2)
                codes = [x['code'] for x in languages]
                ready = 'zh' in codes and 'ru' in codes
                return self.send(200, {'ready': ready, 'languages': codes, 'message': '引擎已连接；实际翻译仍需验证语言路径' if ready else '缺少中俄模型'})
            except RuntimeError as exc:
                return self.send(200, {'ready': False, 'message': str(exc)})
        if path == '/source.zip': return self.send(200, source_archive(), 'application/zip')
        assets = {'/':'index.html', '/app.js':'app.js', '/style.css':'style.css'}
        if path in assets:
            mime = {'/':'text/html', '/app.js':'text/javascript', '/style.css':'text/css'}[path]
            return self.send(200, (ROOT/'campus'/'static'/assets[path]).read_bytes(), mime+'; charset=utf-8')
        return self.send(404, {'error':'未找到资源'})

    def do_POST(self):
        if not self.valid_host(): return self.send(403, {'error':'仅允许本机地址访问'})
        # Reject cross-site browser requests even when the service runs on localhost.
        origin = self.headers.get('Origin')
        if origin and origin != 'http://' + self.headers.get('Host', ''):
            return self.send(403, {'error':'不允许跨站请求'})
        if self.headers.get('Content-Type','').split(';')[0] != 'application/json':
            return self.send(415, {'error':'请求必须为 JSON'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 65536: raise ValueError('请求过大或为空')
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict): raise ValueError('请求必须为对象')
            if self.path == '/api/translate':
                result = translate(data.get('text'), data.get('source'), data.get('target'), ENGINE,
                                   data.get('preserve', []), data.get('glossary', True))
            elif self.path == '/api/template':
                result = render_template(data.get('kind'), data.get('fields'))
            else: return self.send(404, {'error':'未找到接口'})
            self.send(200, result)
        except (ValueError, TypeError) as exc:
            self.send(400, {'error':str(exc)})
        except RuntimeError as exc:
            self.send(503, {'error':str(exc)})

def main():
    port = int(os.getenv('CAMPUS_PORT', '8765'))
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    print(f'CampusBridge: http://127.0.0.1:{port} (Ctrl+C to stop)', flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__ == '__main__': main()
