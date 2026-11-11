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
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
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
    for n in range(1,7):
        info=json.loads((BASE/"events"/f"station-{n}.json").read_text("utf-8"))
        filename=BASE/"tracks"/f"{n}.mp3"
        if not filename.is_file():
            raise RuntimeError(f"Missing generated audio: {filename}")
        raw=filename.read_bytes()
        frames=parse_frames(raw)
        result[n]={"id":n,"title":info["title"],"bpm":info["bpm"],
                   "raw":raw,"frames":frames,"duration":len(frames)*FRAME_TIME}
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
        if path in ("/","/listen","/index.html"):
            return self.send_bytes((BASE/"receiver.html").read_bytes(),"text/html; charset=utf-8",head)
        if path=="/health":
            return self.send_bytes(b"ok\n","text/plain; charset=utf-8",head)
        if path=="/api/stations":
            now=time.time()
            data={"service":"Cellbeat Radio","clock":"UTC-synchronized",
                  "utc":datetime.fromtimestamp(now,timezone.utc).isoformat(),
                  "on_air":[{"id":n,"title":s["title"],"bpm":s["bpm"],
                             "direct_mp3":f"/live/{n}.mp3",
                             "hls":f"/hls/{n}/index.m3u8",
                             "clip":f"/clips/{n}.mp3",
                             "position_s":round((now-CLOCK_EPOCH)%s["duration"],2),
                             "program_duration_s":round(s["duration"],2)}
                            for n,s in STATIONS.items()]}
            return self.send_bytes(json.dumps(data).encode(),"application/json; charset=utf-8",head)
        m=re.fullmatch(r"/clips/([1-6])\.mp3",path)
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
        m=re.fullmatch(r"/live/([1-6])\.mp3",path)
        if m:
            return self.send_live(int(m.group(1)),head)
        m=re.fullmatch(r"/hls/([1-6])/index\.m3u8",path)
        if m:
            n=int(m.group(1))
            seq=int((time.time()-CLOCK_EPOCH)//SEG_DURATION)
            first=max(0,seq-4)
            parts=["#EXTM3U","#EXT-X-VERSION:3",
                   "#EXT-X-TARGETDURATION:7",f"#EXT-X-MEDIA-SEQUENCE:{first}",
                   "#EXT-X-INDEPENDENT-SEGMENTS"]
            for i in range(first,seq+1):
                parts += [f"#EXTINF:{SEG_DURATION:.6f},",f"{i}.mp3"]
            return self.send_bytes(("\n".join(parts)+"\n").encode(),
                                   "application/vnd.apple.mpegurl",head)
        m=re.fullmatch(r"/hls/([1-6])/(\d+)\.mp3",path)
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

if __name__=="__main__":
    port=int(os.environ.get("PORT","10000"))
    class Server(ThreadingHTTPServer):daemon_threads=True
    app=Server(("0.0.0.0",port),Receiver)
    print(f"Cellbeat Radio serving six real MP3 channels on port {port}",flush=True)
    app.serve_forever(poll_interval=.2)
