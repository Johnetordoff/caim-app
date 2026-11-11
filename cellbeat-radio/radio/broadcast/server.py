"""Six UTC-synchronized Cellbeat online radio streams (standard-library server).

Endpoints:
  /                 Visible receiver with six playable live stations
  /live/1.mp3       Endless MP3 broadcast for station 1 (1..6)
  /hls/1/index.m3u8 Native Safari HLS live playlist
  /hls/1/N.mp3      Globally sequenced six-second MP3 HLS segment
  /clips/1.mp3      Finite file fallback for browsers that cannot play live MP3
  /api/stations     Public JSON station status, UTC on-air offsets
  /health           Health check
No third-party music, Node runtime, accounts, tracking or sensitive API.
"""
from __future__ import annotations
import json
import os
import re
import time
import http.client
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
BEAST = ROOT / "beast"
FROG = ROOT / "frog"
RATE = 44100
FRAME_SAMPLES = 1152
FRAME_TIME = FRAME_SAMPLES / RATE
SEG_FRAMES = 230
SEG_DURATION = SEG_FRAMES * FRAME_TIME
BITRATES = [0,32,40,48,56,64,80,96,112,128,160,192,224,256,320,0]
SAMPLERATES = [44100,48000,32000,0]
CLOCK_EPOCH = 0.0

def parse_frames(data: bytes) -> tuple[bytes, ...]:
    """Parse complete MPEG-1 Layer III frames; never split arbitrary MP3 bytes."""
    i, frames = 0, []
    if data[:3] == b"ID3" and len(data) >= 10:
        i = 10 + ((data[6] & 127)<<21) + ((data[7]&127)<<14) + ((data[8]&127)<<7) + (data[9]&127)
    while i + 4 <= len(data):
        h = int.from_bytes(data[i:i+4],"big")
        if h >> 21 != 0x7ff or (h>>19)&3 != 3 or (h>>17)&3 != 1:
            i += 1
            continue
        bitrate = BITRATES[(h>>12)&15]
        sr = SAMPLERATES[(h>>10)&3]
        if not bitrate or sr != RATE:
            i += 1
            continue
        length = (144000*bitrate)//sr + ((h>>9)&1)
        if i+length > len(data):
            break
        frames.append(data[i:i+length])
        i += length
    if len(frames) < 300:
        raise RuntimeError(f"Invalid or incomplete MP3: {len(frames)} frames")
    return tuple(frames)

def load():
    result={}
    if os.environ.get("BEAST_ONLY") != "1":
        for n in range(1,7):
            info=json.loads((BASE/"events"/f"station-{n}.json").read_text("utf-8"))
            filename=BASE/"tracks"/f"{n}.mp3"
            if not filename.is_file():
                raise RuntimeError(f"Missing generated audio: {filename}")
            raw=filename.read_bytes()
            frames=parse_frames(raw)
            result[n]={"id":n,"title":info["title"],"bpm":info["bpm"],
                       "raw":raw,"frames":frames,"duration":len(frames)*FRAME_TIME}
    # bEAST programs are original, fully synthesized Cellbeat artist tracks.
    catalog=json.loads((BEAST/"catalog.json").read_text("utf-8"))
    for item in catalog:
        n=int(item["id"])
        if n not in (7,8,9,10) or n in result:
            raise RuntimeError("Invalid bEAST channel number")
        filename=BEAST/"tracks"/(item["slug"]+".mp3")
        if not filename.is_file():
            raise RuntimeError(f"Missing generated bEAST music: {filename}")
        raw=filename.read_bytes()
        frames=parse_frames(raw)
        result[n]={"id":n,"title":"bEAST / "+item["title"],
                   "bpm":item["bpm"],"artist":"bEAST — the soap faced killa",
                   "page":"/beast/","genre":item["genre"],
                   "raw":raw,"frames":frames,"duration":len(frames)*FRAME_TIME}
    if os.environ.get("BEAST_ONLY") != "1":
        catalog=json.loads((FROG/"catalog.json").read_text("utf-8"))
        for item in catalog:
            n=int(item["id"])
            if n not in (11,12,13,14) or n in result:
                raise RuntimeError("Invalid LAI-Z FR0g station number")
            filename=FROG/"tracks"/(item["slug"]+".mp3")
            if not filename.is_file():
                raise RuntimeError(f"Missing generated FR0g audio: {filename}")
            raw=filename.read_bytes()
            frames=parse_frames(raw)
            result[n]={"id":n,"title":"LAI-Z FR0g / "+item["title"],
                       "bpm":item["bpm"],"artist":"LAI-Z FR0g",
                       "page":"/fr0g/","genre":item["genre"],
                       "raw":raw,"frames":frames,"duration":len(frames)*FRAME_TIME}
    if len(result)!=(4 if os.environ.get("BEAST_ONLY") == "1" else 14):
        raise RuntimeError("Unexpected Cellbeat station count")
    return result

STATIONS = load()
STATIC_ALLOW={
    "/simulation.js":ROOT/"simulation.js",
    "/composer.js":ROOT/"composer.js",
    "/samples.js":ROOT/"samples.js",
    "/audio.js":ROOT/"audio.js",
    "/instruments.js":ROOT/"instruments.js",
    "/standard-instruments.js":ROOT/"standard-instruments.js",
    "/radio/index.html":ROOT/"radio/index.html",
    "/radio/streams.html":ROOT/"radio/streams.html",
    "/radio/channels.js":ROOT/"radio/channels.js",
    "/radio/stream-engine.js":ROOT/"radio/stream-engine.js",
}
for name in ["beyond-beyond-redline.js","beyond-beyond-redline-night-drive.js",
             "beyond-beyond-redline-meter.js","signal-no-masters.json",
             "neon-interceptor.json","neon-interceptor-v2.json"]:
    STATIC_ALLOW["/songs/"+name]=ROOT/"songs"/name

def headers(handler,code,content_type,length=None,extra=None):
    handler.send_response(code)
    handler.send_header("Content-Type",content_type)
    handler.send_header("Cache-Control","no-cache, no-store, must-revalidate")
    handler.send_header("X-Content-Type-Options","nosniff")
    handler.send_header("Access-Control-Allow-Origin","*")
    if length is not None:
        handler.send_header("Content-Length",str(length))
    if extra:
        for key,value in extra.items():
            handler.send_header(key,str(value))
    handler.end_headers()

class Receiver(BaseHTTPRequestHandler):
    protocol_version="HTTP/1.1"
    server_version="CellbeatRadio/1.0"
    def log_message(self,fmt,*args):
        if not self.path.startswith("/live/"):
            print('%s %s' %(self.address_string(),fmt%args),flush=True)
    def do_HEAD(self): self.handle_request(head=True)
    def do_GET(self): self.handle_request(head=False)
    def send_bytes(self,body,kind="application/octet-stream",head=False,extra=None):
        headers(self,200,kind,len(body),extra)
        if not head:
            self.wfile.write(body)
    def handle_request(self,head=False):
        parsed=urlparse(self.path)
        path=unquote(parsed.path)
        if path in ("/","/listen","/index.html") and os.environ.get("BEAST_ONLY") == "1":
            return self.send_bytes((BEAST/"index.html").read_bytes(),"text/html; charset=utf-8",head)
        if path in ("/","/listen","/index.html"):
            return self.send_bytes((BASE/"receiver.html").read_bytes(),"text/html; charset=utf-8",head)
        if path in ("/beast","/beast/","/beast/index.html"):
            return self.send_bytes((BEAST/"index.html").read_bytes(),"text/html; charset=utf-8",head)
        if path in ("/fr0g","/fr0g/","/fr0g/index.html") and os.environ.get("BEAST_ONLY") != "1":
            return self.send_bytes((FROG/"index.html").read_bytes(),"text/html; charset=utf-8",head)
        if path=="/health":
            return self.send_bytes(b"ok\n","text/plain; charset=utf-8",head)
        if path=="/api/stations":
            now=time.time()
            data={"service":"Cellbeat Radio","clock":"UTC-synchronized",
                  "utc":datetime.fromtimestamp(now,timezone.utc).isoformat(),
                  "on_air":[{"id":n,"title":s["title"],"bpm":s["bpm"],
                             "artist":s.get("artist","Cellbeat Mini"),"page":s.get("page","/"),
                             "direct_mp3":f"/live/{n}.mp3",
                             "hls":f"/hls/{n}/index.m3u8",
                             "clip":f"/clips/{n}.mp3",
                             "position_s":round((now-CLOCK_EPOCH)%s["duration"],2),
                             "program_duration_s":round(s["duration"],2)}
                            for n,s in STATIONS.items()]}
            return self.send_bytes(json.dumps(data).encode(),"application/json; charset=utf-8",head)
        m=re.fullmatch(r"/clips/((?:[1-9]|1[0-4]))\.mp3",path)
        if m:
            s=STATIONS[int(m.group(1))]
            data=s["raw"]
            # Static playable fallback and byte-range requests (especially Safari).
            byte_range=self.headers.get("Range","")
            rng=re.fullmatch(r"bytes=(\d*)-(\d*)",byte_range)
            if rng:
                start=int(rng.group(1)) if rng.group(1) else 0
                end=int(rng.group(2)) if rng.group(2) else len(data)-1
                if start>=len(data) or end<start:
                    headers(self,416,"audio/mpeg",0,{"Content-Range":f"bytes */{len(data)}"})
                    return
                end=min(end,len(data)-1)
                chunk=data[start:end+1]
                headers(self,206,"audio/mpeg",len(chunk),{"Accept-Ranges":"bytes","Content-Range":f"bytes {start}-{end}/{len(data)}"})
                if not head:self.wfile.write(chunk)
                return
            return self.send_bytes(data,"audio/mpeg",head,{"Accept-Ranges":"bytes"})
        m=re.fullmatch(r"/live/((?:[1-9]|1[0-4]))\.mp3",path)
        if m:
            return self.send_live(int(m.group(1)),head)
        m=re.fullmatch(r"/hls/((?:[1-9]|1[0-4]))/index\.m3u8",path)
        if m:
            n=int(m.group(1))
            seq=int((time.time()-CLOCK_EPOCH)//SEG_DURATION)
            first=max(0,seq-4)
            parts=["#EXTM3U","#EXT-X-VERSION:3",
                   "#EXT-X-TARGETDURATION:7",f"#EXT-X-MEDIA-SEQUENCE:{first}",
                   "#EXT-X-ALLOW-CACHE:NO"]
            for i in range(first,seq+1):
                parts += [f"#EXTINF:{SEG_DURATION:.6f},",f"{i}.mp3"]
            return self.send_bytes(("\n".join(parts)+"\n").encode(),
                                   "application/vnd.apple.mpegurl",head)
        m=re.fullmatch(r"/hls/((?:[1-9]|1[0-4]))/(\d+)\.mp3",path)
        if m:
            n,seq=int(m.group(1)),int(m.group(2))
            now_seq=int((time.time()-CLOCK_EPOCH)//SEG_DURATION)
            if seq>now_seq+1 or seq<now_seq-240:
                headers(self,404,"text/plain",0)
                return
            frames=STATIONS[n]["frames"];total=len(frames)
            start=(seq*SEG_FRAMES)%total
            chunk=b"".join(frames[(start+j)%total] for j in range(SEG_FRAMES))
            return self.send_bytes(chunk,"audio/mpeg",head)
        static=STATIC_ALLOW.get(path)
        if static and static.is_file():
            kind="text/javascript; charset=utf-8" if static.suffix==".js" else (
                 "application/json" if static.suffix==".json" else "text/html; charset=utf-8")
            return self.send_bytes(static.read_bytes(),kind,head)
        headers(self,404,"text/plain; charset=utf-8",9)
        if not head:
            self.wfile.write(b"Not found")
    def send_live(self,n,head):
        frames=STATIONS[n]["frames"]
        headers(self,200,"audio/mpeg",None,{
            "Transfer-Encoding":"chunked",
            "X-Cellbeat-Station":str(n),
            "X-Cellbeat-Live":"UTC synchronized",
            "Connection":"keep-alive"})
        if head:return
        # A listener joins the globally-running program in progress.
        # Send 8 MP3 frames every 8*1152/44100 seconds.
        batch=8
        index=int((time.time()-CLOCK_EPOCH)/FRAME_TIME)%len(frames)
        deadline=time.monotonic()
        try:
            while True:
                payload=b"".join(frames[(index+j)%len(frames)] for j in range(batch))
                self.wfile.write(("%X\r\n"%len(payload)).encode()+payload+b"\r\n")
                self.wfile.flush()
                index=(index+batch)%len(frames)
                deadline+=batch*FRAME_TIME
                delay=deadline-time.monotonic()
                if delay>0:time.sleep(delay)
                elif delay < -1:
                    # Correct for significant network pauses instead of drifting.
                    index=int((time.time()-CLOCK_EPOCH)/FRAME_TIME)%len(frames)
                    deadline=time.monotonic()
        except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError,TimeoutError):
            pass

def self_test(port):
    """Exercise every live MP3, HLS and API route through the actual HTTP server."""
    time.sleep(.4)
    def request(path, count=None, extra=None):
        c=http.client.HTTPConnection("127.0.0.1",port,timeout=7)
        try:
            c.request("GET",path,headers=extra or {})
            r=c.getresponse()
            data=r.read(count) if count is not None else r.read()
            status=r.status
            mime=r.getheader("Content-Type","")
            return status,mime,data
        finally:
            c.close()
    try:
        routes=["/","/beast/","/health","/api/stations"]
        if os.environ.get("BEAST_ONLY") != "1":routes.append("/fr0g/")
        for p in routes:
            status,mime,data=request(p)
            if status!=200:raise ValueError(p+" returned "+str(status))
            if p=="/api/stations" and len(json.loads(data)["on_air"])!=len(STATIONS):raise ValueError("Station count mismatch")
            print("SELFTEST OK",p,status,len(data),flush=True)
        for n in sorted(STATIONS):
            status,mime,data=request(f"/live/{n}.mp3",2048)
            if status!=200 or not mime.startswith("audio/mpeg") or len(data)!=2048:
                raise ValueError(f"Broken live MP3 endpoint {n}: {status} {mime} {len(data)}")
            print(f"SELFTEST OK /live/{n}.mp3 2048 audio bytes",flush=True)
            status,mime,data=request(f"/hls/{n}/index.m3u8")
            if status!=200 or not data.startswith(b"#EXTM3U"):
                raise ValueError(f"Broken HLS playlist {n}")
            seq=int(re.search(rb"(\d+)\.mp3",data).group(1))
            status,mime,seg=request(f"/hls/{n}/{seq}.mp3")
            if status!=200 or not mime.startswith("audio/mpeg") or len(seg)<20000:
                raise ValueError(f"Broken HLS audio segment {n}")
            status,mime,clip=request(f"/clips/{n}.mp3",100,{"Range":"bytes=0-99"})
            if status!=206 or len(clip)!=100:
                raise ValueError(f"Broken clip byte-range support {n}")
            print(f"SELFTEST OK /hls/{n}/... and range /clips/{n}.mp3",flush=True)
        print("CELLBEAT BROADCAST SELFTEST: ALL STATIONS PASS",flush=True)
    except Exception as exc:
        print("CELLBEAT BROADCAST SELFTEST FAILED:",repr(exc),flush=True)

if __name__=="__main__":
    port=int(os.environ.get("PORT","10000"))
    class Server(ThreadingHTTPServer):daemon_threads=True
    app=Server(("0.0.0.0",port),Receiver)
    print(f"Cellbeat Radio serving {len(STATIONS)} real MP3 channels on port {port}",flush=True)
    threading.Thread(target=self_test,args=(port,),daemon=True).start()
    app.serve_forever(poll_interval=.2)
