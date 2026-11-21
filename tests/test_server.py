import http.client, json, threading, unittest
from unittest.mock import patch
from cacheharbor.server import make_server

class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=make_server(0);cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def request(self,method,path,body=None,headers=None):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        try:
            c.request(method,path,body=body,headers=headers or {});r=c.getresponse();return r.status,r.read()
        finally:c.close()
    def post(self,data,headers=None):return self.request('POST','/api/run',json.dumps(data),{'Content-Type':'application/json',**(headers or {})})
    def test_metadata(self):
        code,body=self.request('GET','/api/meta');self.assertEqual(code,200);self.assertTrue(json.loads(body)['synthetic'])
    def test_simulation(self):
        code,body=self.post({'seed':17,'family':'balanced','capacity':16});self.assertEqual(code,200)
        r=json.loads(body);self.assertEqual(r['seed'],17);self.assertEqual(len(r['results']),4)
    def test_invalid_requests(self):
        for data in [[],{'seed':True},{'capacity':1000},{'family':'x'},{'extra':1}]:
            with self.subTest(data=data):self.assertEqual(self.post(data)[0],400)
        self.assertEqual(self.post({}, {'Origin':'https://elsewhere.example'})[0],403)
        self.assertEqual(self.request('POST','/api/run','{}')[0],415)
        self.assertEqual(self.request('GET','/../results/benchmark.json')[0],404)
    def test_busy(self):
        self.server.gate.acquire()
        try:self.assertEqual(self.post({})[0],429)
        finally:self.server.gate.release()
    def test_incomplete_body_times_out(self):
        from cacheharbor.server import Handler
        with patch.object(Handler,'timeout',.1):
            c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=2)
            try:
                c.putrequest('POST','/api/run');c.putheader('Content-Type','application/json');c.putheader('Content-Length','20');c.endheaders();c.send(b'{')
                r=c.getresponse();self.assertEqual(r.status,408);r.read()
            finally:c.close()
if __name__=='__main__':unittest.main()
