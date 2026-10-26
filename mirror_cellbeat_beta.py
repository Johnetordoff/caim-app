from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
import re, shutil, time

BASE='https://cellbeat-mini-beta.onrender.com/'
OUT=Path('cellbeat-beta-static-output')
OVR=Path('cellbeat-beta-overrides')
ORIGIN=urlparse(BASE).netloc
SOURCE='573bc87be8ac896087c7ce7ac81bc26cd0158638'
if OUT.exists():shutil.rmtree(OUT)
seen=set();queue=[BASE]

class Links(HTMLParser):
    def __init__(self):super().__init__();self.urls=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        for k in ('src','href'):
            if k in d:self.urls.append(d[k])

def fetch(url):
    last=None
    for i in range(4):
        try:
            with urlopen(Request(url,headers={'User-Agent':'CellbeatBetaDirect/4.0'}),timeout=120) as r:return r.read(),r.headers.get_content_type()
        except Exception as e:last=e;time.sleep(2*(i+1))
    raise last

def dst(url):
    p=urlparse(url).path
    if p.endswith('/'):p+='index.html'
    return OUT/(p or '/index.html').lstrip('/')

while queue:
    url=queue.pop(0)
    if url in seen:continue
    seen.add(url);u=urlparse(url)
    if u.scheme not in ('http','https') or u.netloc!=ORIGIN or u.path.startswith('/api/'):continue
    body,ctype=fetch(url);p=dst(url);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
    text=None
    if ctype.startswith('text/') or ctype in ('application/javascript','application/json'):
        try:text=body.decode()
        except UnicodeDecodeError:pass
    refs=[]
    if text and ctype=='text/html':x=Links();x.feed(text);refs=x.urls
    elif text and ctype=='text/css':refs=re.findall(r'url\(["\']?([^"\')]+)',text)
    for ref in refs:
        if not ref or ref.startswith(('data:','mailto:','tel:','#','javascript:')):continue
        nxt=urljoin(url,ref)
        if urlparse(nxt).netloc==ORIGIN:queue.append(nxt)

mini=OUT/'mini'
if not (mini/'index.html').is_file():raise SystemExit('missing mirrored tracker index')
tracker=(mini/'index.html').read_text()
for src in mini.rglob('*'):
    if src.is_file():
        target=OUT/src.relative_to(mini);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
for name in ('audio.js','instruments.js','tracker-contrast.css','bleak.js','beta-behavior.js'):
    if not (OVR/name).is_file():raise SystemExit('missing current beta override '+name)
    shutil.copy2(OVR/name,OUT/name)

style=r'''.beta-sharing{max-width:1000px;margin:3px auto;padding:0 4px}.beta-sharing .song{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:3px;align-items:center;overflow-wrap:anywhere;padding:2px 0}.beta-sharing .song small{display:block;font-size:9px}.beta-sharing .actions{display:flex;flex-wrap:wrap;gap:2px}.beta-sharing .panel{padding:3px;margin-bottom:3px}.beta-sharing .sharing-row{display:flex;gap:3px;margin:2px 0}.beta-sharing .sharing-row input{flex:1;min-width:0;min-height:36px;height:36px;padding:4px 6px}.beta-sharing .sharing-row .btn,.beta-sharing .actions .btn{min-height:36px;padding:4px 6px}.bleak-feedback{display:flex;justify-content:flex-end;gap:4px}.bleak-feedback[hidden]{display:none}.bleak-feedback .btn{width:44px;height:44px;padding:0;font-size:20px;background:#555!important;color:#aaa!important;filter:grayscale(1);opacity:.55}.bleak-feedback .btn[aria-pressed="true"]{filter:none;opacity:1;color:#fff!important}#bleakUp[aria-pressed="true"]{background:#27813a!important}#bleakDown[aria-pressed="true"]{background:#a83232!important}.transport{grid-template-columns:repeat(4,minmax(0,1fr))!important}#quickSaveSongBtn{background:#4a5d3c!important;color:#f0ffe7!important}.beta-recordings{padding:0!important}.beta-recordings summary{display:flex;align-items:center;justify-content:space-between;gap:8px;min-height:40px;margin:0!important;padding:6px 8px;background:#1b1b1b;border:0;list-style:none}.beta-recordings summary::-webkit-details-marker{display:none}.beta-recordings summary::before{content:"▸"}.beta-recordings[open] summary::before{content:"▾"}.beta-recording-body{padding:5px}.beta-recording-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:5px;align-items:end}.beta-recording-row label,.beta-recording-name{display:flex;flex-direction:column;gap:3px;font-size:10px}.beta-recording-row select{width:100%}.beta-recording-row .btn{min-width:120px}.beta-recording-name{margin-top:5px}.beta-recording-help{margin:5px 0 0;color:var(--muted);font-size:10px;line-height:1.35}@media(max-width:760px){.beta-sharing .song{grid-template-columns:1fr}.transport{grid-template-columns:repeat(2,minmax(0,1fr))!important}}'''
share=r'''<section class="beta-sharing"><section class="panel"><div class="sharing-row"><input id="titleInput" aria-label="Optional song name" placeholder="Song name (optional)" type="text" maxlength="80"><button id="saveCurrentBtn" class="btn primary" type="button">Save</button></div><div id="sharedNow"></div><div id="myMessage" class="message"></div><div id="mySongs" class="songs"></div></section><div hidden aria-hidden="true"><input id="searchInput" type="search"><button id="searchBtn" type="button">Find</button><div id="searchMessage"></div><div id="searchResults"></div></div></section><span id="trackerFrame" hidden></span>'''
record=r'''<details class="panel beta-recordings"><summary><span>Recordings</span><span id="recordStatus" class="rec">idle</span></summary><div class="beta-recording-body"><div class="beta-recording-row"><label>Take<select id="takeSelect" disabled><option>No takes yet</option></select></label><button id="saveWavBtn" class="btn" type="button" disabled>Create WAV</button></div><label class="beta-recording-name">WAV name<input id="songName" type="text" maxlength="60" value="Cellbeat-Mini-song"></label><a id="wavDownload" class="download" hidden>Download WAV</a><p class="beta-recording-help">REC starts recording. END or Stop finishes. Choose a take, then Create WAV.</p></div></details>'''
feedback=r'''<div id="bleakFeedback" class="bleak-feedback" hidden><button id="bleakUp" class="btn" type="button" aria-label="Thumbs up" aria-pressed="false">👍</button><button id="bleakDown" class="btn" type="button" aria-label="Thumbs down" aria-pressed="false">👎</button></div>'''
bridge=r'''<script>(function(){var h=document.getElementById("trackerFrame");Object.defineProperty(h,"contentWindow",{value:window});Object.defineProperty(h,"contentDocument",{value:document});h.scrollIntoView=function(){window.scrollTo(0,0)};window.addEventListener("load",function(){h.dispatchEvent(new Event("load"))})}());</script>'''
quick=r'''<script>(function(){var q=document.getElementById("quickSaveSongBtn"),s=document.getElementById("saveCurrentBtn");if(q&&s)q.addEventListener("click",function(){s.click();});}());</script>'''

source=tracker.replace('<title>Cellbeat Mini // Tracker</title>','<title>Cellbeat Mini Beta // Tracker</title>',1)
source=source.replace('</head>','<style id="cellbeatBetaDirect">'+style+'</style></head>',1)
source=source.replace('</nav>','<button id="quickSaveSongBtn" class="btn" type="button" aria-label="Save current song pattern">Save Song</button></nav>',1)
follower='<label class="check"><input type="checkbox" id="followRobot" checked>Follow robot across grids <span id="posText"></span></label>'
if follower in source:source=source.replace(follower,'<input type="checkbox" id="followRobot" checked hidden><span id="posText" hidden></span>',1)
pat=re.compile(r'<div class="panel"><h2>Song takes / <span id="recordStatus" class="rec">idle</span></h2>.*?<p class="message">The robot starts/stops recording on REC/END cells\. Stop also finishes a take\. Save before closing; up to 16 takes stay here for this visit\. Two-minute limit per take\.</p></div>',re.S)
source,n=pat.subn(record,source,count=1)
if n!=1:raise SystemExit('recordings panel marker changed')
source=re.sub(r'(<(?:nav|div|section) class="transport")',lambda m:feedback+m.group(1),source,count=1)
extras=share+bridge+'<script src="sharing.js"></script>'+quick+'<script src="random_seeds.js"></script><script src="bleak.js"></script><script src="beta-behavior.js"></script>'
source=source.replace('</body>',extras+'</body>',1)
if '<iframe' in source.lower():raise SystemExit('direct beta unexpectedly contains iframe')
for required in ('id="grid"','id="playBtn"','id="quickSaveSongBtn"','id="bleakFeedback"','id="trackerFrame"'):
    if required not in source:raise SystemExit('missing direct beta control '+required)
(OUT/'index.html').write_text(source)

sharing=(OUT/'sharing.js').read_text()
sharing=sharing.replace('if(!name)return msg(mineMsg,"Give the song a title first.",true);','if(!name)name="Untitled song";')
sharing=sharing.replace('msg(mineMsg,"Saved and backed up across browser storage.");','msg(mineMsg,"Saved.");')
(OUT/'sharing.js').write_text(sharing)
app=(OUT/'app.js').read_text().replace('message("? Program selected. Tap a rotator or other occupied cell to open its visit rules.");','').replace('Take finished. Render WAV, then tap Save song .wav.','Take ready. Open Recordings to create a WAV.').replace('WAV ready. Tap Save song .wav to download this take.','WAV ready. Tap Download WAV.')
(OUT/'app.js').write_text(app)
(OUT/'beta-source.txt').write_text(SOURCE+'\n')
(OUT/'health.txt').write_text('cellbeat-beta-direct-ok\n')
print('built direct beta',SOURCE,'from',len(seen),'mirrored resources; no legacy wrapper dependency')
