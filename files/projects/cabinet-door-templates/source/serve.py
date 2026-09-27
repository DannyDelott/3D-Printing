#!/usr/bin/env python3
"""Serve the organized project, redirecting existing bookmarked artifact URLs."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, unquote, quote
from project_paths import ROOT, CATALOG

class Handler(SimpleHTTPRequestHandler):
    def send_head(self):
        url=urlsplit(self.path)
        old=unquote(url.path).lstrip('/')
        target=CATALOG['legacy_urls'].get(old)
        if target and target!=old:
            self.send_response(308)
            self.send_header('Location','/'+quote(target,safe='/')+('?' + url.query if url.query else ''))
            self.send_header('Content-Length','0')
            self.end_headers()
            return None
        return super().send_head()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8767)
    args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(Handler,directory=str(ROOT)))
    print(f'Cabinet door templates: http://127.0.0.1:{args.port}/',flush=True)
    server.serve_forever()
