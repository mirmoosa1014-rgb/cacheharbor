"""Bounded loopback demo; no uploads or external services."""
import argparse, json, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from .engine import compare, integer, FAMILIES
from .experiment import ROOT

class Handler(SimpleHTTPRequestHandler):
    timeout=5
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT/'web'),**kwargs)
    def reply(self,status,data):
        body=json.dumps(data,allow_nan=False).encode();self.send_response(status)
        self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/api/meta':return self.reply(200,self.server.benchmark)
        if path not in ('/','/index.html','/app.js','/style.css'):return self.reply(404,{'error':'not found'})
        super().do_GET()
    def do_POST(self):
        if self.path!='/api/run':return self.reply(404,{'error':'not found'})
        origin=self.headers.get('Origin');allowed={f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'}
        if origin and origin not in allowed:return self.reply(403,{'error':'same-origin requests only'})
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.reply(415,{'error':'application/json required'})
        try:
            n=int(self.headers.get('Content-Length','0'))
            if not 0<n<=512:raise ValueError('request must contain 1–512 bytes')
            raw_body=self.rfile.read(n)
            if len(raw_body)!=n:raise ValueError('incomplete request body')
            data=json.loads(raw_body)
            if not isinstance(data,dict) or set(data)-{'seed','family','capacity'}:raise ValueError('provide seed, family and capacity only')
            seed=integer(data.get('seed',3001),0,100000,'seed');capacity=integer(data.get('capacity',32),4,64,'capacity')
            family=data.get('family','phase_swap')
            if family not in FAMILIES:raise ValueError('unknown workload family')
            if not self.server.gate.acquire(False):return self.reply(429,{'error':'simulation busy; retry shortly'})
            try:
                config=self.server.benchmark['config']
                result=compare(seed,family,capacity,config['interval'],config['fixed_fraction'])
            finally:self.server.gate.release()
            self.reply(200,result)
        except TimeoutError:self.reply(408,{'error':'request body timed out'})
        except (ValueError,TypeError) as exc:self.reply(400,{'error':str(exc)})

def make_server(port=8767):
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.benchmark=json.loads((ROOT/'results/benchmark.json').read_text())
    server.gate=threading.BoundedSemaphore(1);return server
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8767);a=p.parse_args()
    with make_server(a.port) as server:
        print(f'CacheHarbor: http://127.0.0.1:{server.server_port}',flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
