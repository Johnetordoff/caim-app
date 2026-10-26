from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
import re, time

BASE='https://cellbeat-mini-beta.onrender.com/'
OUT=Path('cellbeat-beta-static-output')
ORIGIN=urlparse(BASE).netloc
seen=set(); queue=[BASE]

class Links(HTMLParser):
    def __init__(self): super().__init__(); self.urls=[]
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        for k in ('src','href'):
            if k in d: self.urls.append(d[k])

def fetch(url):
    last=None
    for i in range(4):
        try:
            req=Request(url,headers={'User-Agent':'CellbeatBetaMirror/1.0'})
            with urlopen(req,timeout=120) as r: return r.read(), r.headers.get_content_type()
        except Exception as e:
            last=e; time.sleep(2*(i+1))
    raise last

def target(url):
    p=urlparse(url).path
    if p.endswith('/'): p += 'index.html'
    if p=='': p='/index.html'
    return OUT / p.lstrip('/')

while queue:
    url=queue.pop(0)
    if url in seen: continue
    seen.add(url)
    u=urlparse(url)
    if u.scheme not in ('http','https') or u.netloc!=ORIGIN or u.path.startswith('/api/'): continue
    body, ctype=fetch(url)
    dst=target(url); dst.parent.mkdir(parents=True,exist_ok=True); dst.write_bytes(body)
    text=None
    if ctype.startswith('text/') or ctype in ('application/javascript','application/json'):
        try: text=body.decode('utf-8')
        except UnicodeDecodeError: pass
    links=[]
    if text and ctype=='text/html':
        p=Links(); p.feed(text); links=p.urls
    elif text and ctype=='text/css':
        links=re.findall(r'url\(["\']?([^"\')]+)',text)
    for ref in links:
        if not ref or ref.startswith(('data:','mailto:','tel:','#','javascript:')): continue
        nxt=urljoin(url,ref)
        if urlparse(nxt).netloc==ORIGIN: queue.append(nxt)

print('mirrored',len(seen),'resources')
