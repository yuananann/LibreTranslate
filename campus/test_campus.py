import io
import json
import threading
import unittest
import zipfile
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from campus.core import translate, render_template, terms, LibreEngine
from campus.server import Handler, source_archive

def fail_engine(*args): raise RuntimeError('no engine')

class CoreTests(unittest.TestCase):
    def test_glossary_offline(self):
        r=translate('数据结构\n线性代数','zh','ru',fail_engine)
        self.assertEqual(r['translatedText'],'структуры данных\nлинейная алгебра')
    def test_reverse(self): self.assertEqual(translate('структуры данных','ru','zh',fail_engine)['translatedText'],'数据结构')
    def test_longest_match(self): self.assertEqual(len(translate('计算机网络','zh','ru',fail_engine)['hits']),1)
    def test_protected_name(self): self.assertEqual(translate('Ivan Petrov CS101','zh','ru',fail_engine,['Ivan Petrov'])['translatedText'],'Ivan Petrov CS101')
    def test_engine_called(self):
        received=[]
        class Stub(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def do_POST(self):
                received.append((self.path,json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
                result=json.dumps({'translatedText':'Здравствуйте'}).encode()
                self.send_response(200);self.send_header('Content-Length',str(len(result)));self.end_headers();self.wfile.write(result)
        srv=ThreadingHTTPServer(('127.0.0.1',0),Stub)
        thread=threading.Thread(target=srv.serve_forever,daemon=True);thread.start()
        try:
            engine=LibreEngine('http://127.0.0.1:'+str(srv.server_port),'test-key')
            self.assertEqual(translate('你好','zh','ru',engine)['translatedText'],'Здравствуйте')
            self.assertEqual(received,[('/translate',dict(q='你好',source='zh',target='ru',format='text',api_key='test-key'))])
        finally: srv.shutdown();srv.server_close();thread.join()
    def test_disabled_glossary(self): self.assertEqual(translate('数据结构','zh','ru',lambda *a:'whole sentence',glossary=False)['translatedText'],'whole sentence')
    def test_word_boundary(self): self.assertEqual(translate('алгоритмы','ru','zh',lambda *a:'算法复数')['hits'],[])
    def test_empty(self):
        with self.assertRaises(ValueError): translate('','zh','ru',fail_engine)
    def test_length(self):
        with self.assertRaises(ValueError): translate('a'*5001,'zh','ru',fail_engine)
    def test_language(self):
        with self.assertRaises(ValueError): translate('hello','en','ru',fail_engine)
    def test_unavailable(self):
        with self.assertRaises(RuntimeError): translate('你好','zh','ru',fail_engine)
    def test_template(self):
        r=render_template('notice',dict(course_zh='数据结构',course_ru='Структуры данных',date='2026-10-20',time='14:00',room='A301'))
        self.assertIn('14:00',r['translatedText'])
        self.assertIn('数据结构',r['sourceText'])
    def test_template_missing(self):
        with self.assertRaises(ValueError): render_template('notice',{})
    def test_bad_preserve(self):
        with self.assertRaises(ValueError): translate('hi','zh','ru',fail_engine,'hi')
    def test_seed_integrity(self):
        data=terms();self.assertEqual(len(data),36);self.assertEqual(len({x['id'] for x in data}),36)
    def test_source(self):
        z=zipfile.ZipFile(io.BytesIO(source_archive()));self.assertIn('campus/core.py',z.namelist());self.assertIn('LICENSE',z.namelist())
        self.assertFalse(any('.env' in x or '__pycache__' in x for x in z.namelist()))

class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.url='http://127.0.0.1:'+str(cls.server.server_port)
    @classmethod
    def tearDownClass(cls): cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def request(self,path,body,origin=None):
        headers={'Content-Type':'application/json'}
        if origin: headers['Origin']=origin
        return urlopen(Request(self.url+path,json.dumps(body).encode(),headers))
    def test_home(self):
        with urlopen(self.url) as r:self.assertIn('校园译桥',r.read().decode())
    def test_api_translation(self):
        with self.request('/api/translate',dict(text='数据结构',source='zh',target='ru')) as r:self.assertIn('структуры',json.load(r)['translatedText'])
    def test_cross_origin(self):
        with self.assertRaises(HTTPError) as e:self.request('/api/translate',{},'https://evil.example')
        self.assertEqual(e.exception.code,403)
        with self.assertRaises(HTTPError) as e:urlopen(Request(self.url,headers={'Host':'evil.example'}))
        self.assertEqual(e.exception.code,403)
    def test_traversal(self):
        with self.assertRaises(HTTPError) as e:urlopen(self.url+'/../pyproject.toml')
        self.assertEqual(e.exception.code,404)
    def test_invalid_payload(self):
        with self.assertRaises(HTTPError) as e:self.request('/api/translate',[])
        self.assertEqual(e.exception.code,400)

if __name__=='__main__':unittest.main(verbosity=2)
