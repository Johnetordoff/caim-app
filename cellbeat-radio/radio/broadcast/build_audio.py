"""Build six broadcast MP3 loops from private Cellbeat music event data.

Event data is delivered through an encrypted Render environment variable,
not committed to the public deployment repository. No Node or GitHub Actions.
"""
import base64
import json
import math
import os
import subprocess
from pathlib import Path
import numpy as np

BASE=Path(__file__).resolve().parent
EVENTS=BASE/"events"
OUT=BASE/"tracks"
RATE=44100
PITCH=[261.63,293.66,329.63,349.23,392,440,493.88,523.25,587.33,659.25,698.46,783.99]
INSTRUMENTS=["tone","sample","synth","piano","organ","pluck","bell"]
CHANNELS=[
 ("Signal / No Masters",96),
 ("Beyond Beyond Redline",148),
 ("Beyond Beyond Redline / Night Drive",124),
 ("Beyond Beyond Redline / Meter",146),
 ("Neon Interceptor",138),
 ("Neon Interceptor / Pursuit Mix",132),
]
CACHE={}
NATIVE=None

def decode_private_events():
    packed=os.environ.get("CELLBEAT_EVENTS_PACK","")
    if not packed:
        raise RuntimeError("CELLBEAT_EVENTS_PACK is not configured: refusing to broadcast invented music")
    raw=base64.b64decode(packed,validate=True)
    if len(raw)<12:
        raise RuntimeError("Cellbeat station data incomplete")
    pos=0
    EVENTS.mkdir(parents=True,exist_ok=True)
    for i,(title,bpm) in enumerate(CHANNELS,1):
        if pos+2>len(raw):raise ValueError("Missing station event count")
        count=int.from_bytes(raw[pos:pos+2],"big");pos+=2
        rows=[]
        for _ in range(count):
            if pos+4>len(raw):raise ValueError("Truncated original Cellbeat event")
            tick=int.from_bytes(raw[pos:pos+2],"big");inst=raw[pos+2];note=raw[pos+3];pos+=4
            if tick>=480 or inst>=len(INSTRUMENTS) or note>11:
                raise ValueError("Invalid original Cellbeat event")
            rows.append([round(tick*15000/bpm),INSTRUMENTS[inst],note])
        target=EVENTS/f"station-{i}.json"
        target.write_text(json.dumps({"id":i,"title":title,"bpm":bpm,"ticks":480,
            "duration_ms":round(480*15000/bpm),"events":rows},
            separators=(",",":")),encoding="utf-8")
        print(f"Recovered original Cellbeat channel {i} ({count} events)",flush=True)
    if pos!=len(raw):raise ValueError("Unexpected trailer in Cellbeat program data")

def samples():
    """Temporary synthesized kit percussion, not the proprietary raw native PCM."""
    global NATIVE
    if NATIVE is not None:return NATIVE
    rng=np.random.default_rng(19198)
    t=np.arange(round(.48*RATE),dtype=np.float64)/RATE
    # Kick: swooping sub-bass oscillator
    phase=2*np.pi*(48*t+125*(1-np.exp(-t*19))/19)
    kick=(np.sin(phase)*np.exp(-t*12)*.96).astype(np.float32)
    # Snare, hat, low bass, with fixed seeds for deterministic deploys
    noise=rng.uniform(-1,1,len(t))
    snare=((noise*.75+np.sin(2*np.pi*185*t)*.22)*np.exp(-t*18)).astype(np.float32)
    hat=(rng.uniform(-1,1,len(t))*np.exp(-t*56)*.56).astype(np.float32)
    bass=(np.sin(2*np.pi*130.81*t)*np.exp(-t*6.5)*.85).astype(np.float32)
    NATIVE=[kick,snare,hat,bass]
    return NATIVE

def synth(kind,note):
    key=(kind,note)
    if key in CACHE:return CACHE[key]
    if not 0<=note<12:return np.zeros(0,np.float32)
    f=PITCH[note]
    dur={"tone":.20,"synth":.65,"piano":1.1,"organ":.65,"pluck":.8,"bell":1.6}.get(kind)
    if dur is None:return np.zeros(0,np.float32)
    t=np.arange(round(dur*RATE),dtype=np.float64)/RATE
    a=2*np.pi*f*t
    if kind=="tone":
        shape=np.where(np.sin(a)>=0,1.,-1.)
        env=np.where(t<.01,.0001+.1*t/.01,.1*np.exp(-35*(t-.01)))
    elif kind=="synth":
        shape=.5*((2*((f*.997*t)%1)-1)+(2*((f*1.003*t)%1)-1))
        env=np.minimum(1,t/.018)*np.exp(-4*t)*.13
    elif kind=="piano":
        shape=(np.sin(a+.9*np.exp(-9*t)*np.sin(2*a))+.25*np.exp(-5*t)*np.sin(3*a))/1.25
        env=np.minimum(1,t/.004)*np.exp(-4*t)*.15
    elif kind=="organ":
        shape=(np.sin(a)+.45*np.sin(2*a)+.25*np.sin(3*a)+.12*np.sin(4*a))/1.82
        env=np.minimum(1,t/.012)*np.minimum(1,np.maximum(0,(dur-t)/.2))*.10
    elif kind=="pluck":
        shape=(np.sin(a)+.4*np.exp(-12*t)*np.sin(2*a)+.2*np.exp(-18*t)*np.sin(3*a))/1.6
        env=np.minimum(1,t/.002)*np.exp(-8*t)*.16
    else:
        shape=(np.sin(a)*np.exp(-2.8*t)+.4*np.sin(2.76*a)*np.exp(-4*t)+
               .2*np.sin(5.4*a)*np.exp(-6*t))/1.6
        env=np.minimum(1,t/.002)*.17
    env*=np.maximum(0,np.minimum(1,(dur-t)/.03))
    CACHE[key]=(shape*env).astype(np.float32)
    return CACHE[key]

def render_one(i):
    obj=json.loads((EVENTS/f"station-{i}.json").read_text("utf-8"))
    length=math.ceil(obj["duration_ms"]/1000*RATE)
    mix=np.zeros(length,dtype=np.float32)
    native=samples()
    for ms,kind,note in obj["events"]:
        pos=round(ms*RATE/1000)
        if pos<0 or pos>=length:continue
        wave=native[note]*.18 if kind=="sample" else synth(kind,note)
        end=min(length,pos+len(wave))
        if end>pos:mix[pos:end]+=wave[:end-pos]
    mix=np.tanh(mix*2.4)*.83
    fade=min(round(.035*RATE),length//4)
    mix[:fade]*=np.linspace(0,1,fade,dtype=np.float32)
    mix[-fade:]*=np.linspace(1,0,fade,dtype=np.float32)
    OUT.mkdir(parents=True,exist_ok=True)
    out=OUT/f"{i}.mp3"
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","s16le",
        "-ar",str(RATE),"-ac","1","-i","pipe:0","-c:a","libmp3lame",
        "-b:a","128k","-ar",str(RATE),"-ac","1",
        "-write_xing","0","-id3v2_version","0",str(out)]
    pcm=(np.clip(mix,-1,1)*32767).astype("<i2").tobytes()
    subprocess.run(cmd,input=pcm,check=True,timeout=120)
    if out.stat().st_size<25000:raise RuntimeError("MP3 output too short")
    print(f"Station {i}: {obj['title']} ({len(obj['events'])} events, {out.stat().st_size} bytes)",flush=True)

def main():
    decode_private_events()
    for i in range(1,7):render_one(i)

if __name__=="__main__":main()
