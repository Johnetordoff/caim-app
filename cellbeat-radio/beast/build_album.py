"""bEAST — the soap faced killa: four original Cellbeat Mini patch performances.

NOT a human persona, voice clone, external sound library, artist imitation,
or sample of someone else's recording. The 'artist' is the generative aesthetic
and authored data: numbers, note events, synthesized instruments, and timing.
"""
from __future__ import annotations
import json
import math
import os
import subprocess
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
RATE=44100
BASE=[261.63,293.66,329.63,349.23,392.0,440.0,493.88,523.25,587.33,659.25,698.46,783.99]
PATCHES={
 "bubble-bass":(.67,.53),"soap-synth":(.92,.23),"clean-pluck":(.92,.24),
 "foam-lead":(1.06,.24),"rinse-pad":(2.66,.15),"glass-stab":(.74,.24),
 "killa-kick":(.49,.87),"killa-snare":(.38,.48),"killa-hat":(.16,.29)
}
CACHE={}
SONGS=[
 {"id":7,"slug":"bang-switch","title":"BANG SWITCH","bpm":152,"genre":"industrial bass pop","roots":[5,3,0,4],
  "chords":[[5,7,9],[3,5,7],[0,2,4],[4,6,8]],"hook":[9,9,7,5,8,9,10,9],
  "second":[9,11,10,9,7,5,7,8],"rhythm":"trap","mood":"Dirty low-end, chant-sized synth hook, detonating drops."},
 {"id":8,"slug":"plastic-heaven","title":"PLASTIC HEAVEN","bpm":128,"genre":"neon hyperpop","roots":[0,4,5,3],
  "chords":[[0,2,4],[4,6,8],[5,7,9],[3,5,7]],"hook":[7,9,11,9,8,7,9,11],
  "second":[9,8,7,5,7,9,8,7],"rhythm":"dance","mood":"Shimmering synthetic sweetness with a sharp club kick."},
 {"id":9,"slug":"killa-klean","title":"KILLA KLEAN","bpm":146,"genre":"industrial electro rock","roots":[2,0,4,1],
  "chords":[[2,4,6],[0,2,4],[4,6,8],[1,3,5]],"hook":[9,8,7,4,7,8,9,4],
  "second":[6,4,6,9,8,7,4,2],"rhythm":"stomp","mood":"Distorted synth riffs, hard snares, and machine-room swagger."},
 {"id":10,"slug":"heartdrive","title":"HEARTDRIVE","bpm":116,"genre":"dark synthpop anthem","roots":[3,0,4,5],
  "chords":[[3,5,7],[0,2,4],[4,6,8],[5,7,9]],"hook":[7,9,8,7,5,4,5,7],
  "second":[9,11,9,8,7,5,4,5],"rhythm":"retro","mood":"A towering cinematic chorus from nothing but oscillators."}
]

def wave(kind,note):
    key=kind,note
    if key in CACHE:return CACHE[key]
    dur,level=PATCHES[kind]
    f=BASE[note]
    n=round(dur*RATE)
    t=np.arange(n,dtype=np.float64)/RATE
    ph=2*np.pi*f*t
    release=np.clip((dur-t)/(.36 if kind=="rinse-pad" else .05),0,1)
    if kind=="bubble-bass":
        ff=f/4
        tmod=t+.012/(2*np.pi*7.1)*(1-np.cos(2*np.pi*7.1*t))
        cycles=ff*tmod
        saw=2*((2.005*cycles)%1)-1
        v=np.tanh(2.7*(.74*np.sin(2*np.pi*cycles)+.36*saw+.14*np.sin(6*np.pi*cycles)))
        env=np.minimum(1,t/.008)*np.exp(-1.75*t)*np.clip((dur-t)/.09,0,1)
    elif kind=="soap-synth":
        a=2*((f*t*1.004)%1)-1
        b=2*((f*t*.993)%1)-1
        raw=.57*a+.43*b
        # Native-inspired low-pass, stable one-pole equivalent.
        low=np.empty(n,np.float64);hold=0.
        for i in range(n):
            hold+=.075*(raw[i]-hold);low[i]=hold
        v=np.tanh(2.35*(.62*low+.35*np.sin(ph+.3*np.sin(ph*2))+.15*np.sin(ph*3)))
        env=np.minimum(1,t/.012)*np.exp(-.85*t)*np.clip((dur-t)/.16,0,1)
    elif kind=="clean-pluck":
        v=.7*np.sin(ph)+.25*np.exp(-6*t)*np.sin(ph*2.01)+.15*np.exp(-11*t)*np.sin(ph*4.02)
        env=np.minimum(1,t/.003)*np.exp(-5*t)*np.clip((dur-t)/.1,0,1)
    elif kind=="foam-lead":
        vibr=t + .005/(2*np.pi*5.2)*(1-np.cos(2*np.pi*5.2*t))
        cycle=f*vibr
        saw=2*(cycle%1)-1
        v=np.tanh(1.6*(.36*saw+.34*np.sin(2*np.pi*cycle)+.19*np.sin(2*np.pi*2.85*cycle)+.11*np.sin(2*np.pi*4.7*cycle)))
        env=np.minimum(1,t/.015)*np.exp(-.75*t)*np.clip((dur-t)/.15,0,1)
    elif kind=="rinse-pad":
        tt=t + .003/(2*np.pi*.34)*(1-np.cos(2*np.pi*.34*t))
        c=f*tt
        v=.35*(2*(c%1)-1)+.31*(2*((c*1.003)%1)-1)+.25*np.sin(2*np.pi*c)+.09*np.sin(4*np.pi*c)
        env=(1-np.exp(-5*t))*np.clip((dur-t)/.42,0,1)
    elif kind=="glass-stab":
        v=(.53*np.sin(ph)+.26*np.sin(ph*2.71)+.19*np.sin(ph*4.12)+.13*np.sin(ph*6.8))*np.exp(-2.7*t)
        env=np.minimum(1,t/.003)*np.clip((dur-t)/.09,0,1)
    elif kind=="killa-kick":
        # Genuine pitch-swept synthetic kick, with a deterministic transient.
        phase=2*np.pi*(47*t+150*(1-np.exp(-33*t))/33)
        noise=np.random.default_rng(20261110+note).uniform(-1,1,n)
        v=np.tanh(2.6*np.sin(phase)+noise*.09*np.exp(-42*t))
        env=np.minimum(1,t/.002)*np.exp(-11*t)*np.clip((dur-t)/.025,0,1)
    elif kind=="killa-snare":
        rng=np.random.default_rng(20261111+note)
        noise=rng.uniform(-1,1,n)
        # A snare's broadband snap plus a pitched 180-Hz body.
        smooth=np.convolve(noise,np.ones(17)/17,mode="same")
        v=(noise-smooth)*.85+.23*np.sin(2*np.pi*180*t)+.1*np.sin(2*np.pi*335*t)
        env=np.minimum(1,t/.001)*np.exp(-18*t)*np.clip((dur-t)/.03,0,1)
    else:
        rng=np.random.default_rng(20261112+note)
        noise=rng.uniform(-1,1,n)
        smooth=np.convolve(noise,np.ones(7)/7,mode="same")
        v=(noise-smooth)*.85+.12*np.sin(2*np.pi*5600*t)
        env=np.exp(-50*t)*np.clip((dur-t)/.02,0,1)
    result=(v*env*level).astype(np.float32)
    result[0]=0;result[-1]=0;CACHE[key]=result
    return result

def score(song):
    bpm=song["bpm"];beat=60/bpm;events=[]
    def add(b,patch,note,vel=1,pan=0):
        if patch not in PATCHES or not isinstance(note,int) or not 0<=note<12:raise ValueError((patch,note))
        events.append([round(b*beat*1000),patch,note,round(vel,3),round(pan,2)])
    # 64 bars = intro 4, verse 16, build 8, hook chorus 16, switch-up 8, final hook 12.
    # Each section is intentionally different: not a repeated random-note loop.
    for bar in range(64):
        root=song["roots"][(bar//2)%4]
        chord=song["chords"][(bar//2)%4]
        measure=bar*4
        intro=bar<4
        verse=4<=bar<20
        build=20<=bar<28
        chorus=28<=bar<44 or bar>=52
        breakbeat=44<=bar<52
        power=.45 if intro else .70 if verse else .75 if build else 1.0 if chorus else .54
        if bar>=56:power*=1.05
        # Low-end: half-time cross-rhythm and octave-relative bubble bass.
        if not intro or bar>=2:
            bass_pattern=[0,1.5,2.5,3.5] if song["rhythm"]=="trap" else [0,1,2.5,3.25]
            if song["rhythm"]=="stomp":bass_pattern=[0,.75,1.5,2.5,3.25]
            if song["rhythm"]=="retro":bass_pattern=[0,2,3.5]
            for j,p in enumerate(bass_pattern):
                if breakbeat and j%2:continue
                pitch=root if j%4<2 else (root+7)%12
                add(measure+p,"bubble-bass",pitch,power*(.91 if j else 1.14))
        # Kicks and hard snare signatures.
        if song["rhythm"]=="dance" or (chorus and song["rhythm"]=="retro"):
            kicks=[0,1,2,3]
        elif song["rhythm"]=="stomp":
            kicks=[0,1.5,2.5,3.25]
        elif song["rhythm"]=="trap":
            kicks=[0,1.5,2.75]
        else:kicks=[0,2,3.5]
        if verse and song["rhythm"]!="dance":kicks=kicks[:-1]
        if breakbeat:kicks=[0,2.5]
        if intro:kicks=[0,2] if bar>=2 else [0]
        for j,p in enumerate(kicks):
            add(measure+p,"killa-kick",0,power*(1.1 if j==0 else .92))
        snares=[1,3] if song["rhythm"] in ("dance","retro") or chorus else [2]
        if intro:snares=[2] if bar>=2 else []
        if build:snares=[1,2,3]
        if breakbeat:snares=[2]
        for p in snares:
            add(measure+p,"killa-snare",0,power*(.97 if p==2 else .88))
            if chorus and bar%4==3 and p==3:
                add(measure+3.75,"killa-snare",0,.30)
        # High hats/rolls change rhythmic density around the drop.
        hatstep=.25 if (chorus and song["rhythm"] in ("trap","stomp")) or (build and bar>=24) else .5
        if intro:hatstep=1.
        for i in range(round(4/hatstep)):
            p=i*hatstep
            if breakbeat and i%3==0:continue
            vel=.24 if i%2==0 else .40
            if song["rhythm"]=="trap" and i%4==3:vel=.51
            add(measure+p,"killa-hat",0,power*vel,pan=(-.3 if i%2 else .3))
        if bar%4==3 and (build or chorus):
            for ix in range(4):
                add(measure+3+ix*.25,"killa-snare" if ix%2==0 else "killa-hat",0,.24+ix*.09)
        # Chord progression — rinse pads expand in the hooks.
        if intro or build or chorus or song["slug"]=="heartdrive":
            for ix,note in enumerate(chord):
                add(measure+.01,"rinse-pad",note,power*(.35 if intro else .54 if chorus else .42),
                    pan=(-.63+ix*.63))
        # Syncopated chord stabs build harmony without vocals.
        if verse or chorus:
            stabs=[.5,1.75,3.0] if song["slug"]=="killa-klean" else [.75,2.5,3.5]
            for ix,p in enumerate(stabs):
                if verse and ix==1:continue
                add(measure+p,"soap-synth",chord[ix%3],power*(.55 if verse else .76),
                    pan=(-.38 if ix%2 else .38))
        # A recognizable two-bar melodic hook.
        motif=song["hook"] if bar%4<2 else song["second"]
        if chorus:
            for i,n in enumerate(motif):
                # eight 8th-note hits: repeating refrain, per-bar variation.
                p=i*.5
                if (bar%8)==7 and i==7:n=song["hook"][0]
                add(measure+p,"foam-lead",n,power*(.56 if i%4 else .77),
                    pan=(-.13 if i%2 else .13))
                if i in (0,3,6):
                    add(measure+p+.24,"clean-pluck",n,.28*power,pan=(.55 if i%2 else -.55))
        elif build:
            for i in range(4):
                n=motif[(i+bar)%8]
                add(measure+i,"clean-pluck",n,power*(.28+.1*i),pan=(-.45 if i%2 else .45))
            if bar>=24:
                add(measure+3.5,"glass-stab",motif[0],.45)
        elif verse:
            riff=[0,.75,1.5,2.75,3.5] if song["slug"]=="killa-klean" else [0,1.5,2.5,3.5]
            for i,p in enumerate(riff):
                n=motif[(i*2+bar//4)%8]
                add(measure+p,"clean-pluck" if i%2 else "soap-synth",n,
                    power*(.43 if i%2 else .52),pan=(-.34 if i%2 else .34))
        elif intro:
            if bar>=1:
                for i,n in enumerate(motif[::2][:4]):
                    add(measure+i,"glass-stab",n,.29,pan=(-.5 if i%2 else .5))
        else:
            for i in range(3):
                add(measure+[0,1.5,3.][i],"glass-stab",motif[(i*3+bar)%8],.32,
                    pan=(-.5 if i%2 else .5))
        # Sweeping impact on every big section edge.
        if bar in (4,20,28,44,52,60):
            for ix,n in enumerate(chord):
                add(measure+.005,"glass-stab",n,.85 if bar in (28,52) else .47,
                    pan=(ix-1)*.25)
    end=64*4*beat
    events.sort(key=lambda e:e[0])
    return {"format":"cellbeat-beast-performance","version":1,"artist":"bEAST — the soap faced killa",
            "identity":"pure digital signal, no human performer",
            "title":song["title"],"slug":song["slug"],"bpm":bpm,
            "length_seconds":round(end,2),"patches":sorted(PATCHES),
            "sections":[[0,"INTRO"],[4,"VERSE"],[20,"BUILD"],[28,"CHORUS"],[44,"BREAK"],
                        [52,"FINAL CHORUS"],[64,"END"]],
            "events":events}

def render(song,sc):
    n=round(sc["length_seconds"]*RATE)
    mix=np.zeros((n,2),dtype=np.float32)
    for ms,kind,note,vel,pan in sc["events"]:
        pcm=wave(kind,note)
        pos=round(ms*RATE/1000)
        end=min(n,pos+len(pcm))
        if pos>=n or end<=pos:continue
        angle=(pan+1)*np.pi/4
        left=np.cos(angle);right=np.sin(angle)
        mix[pos:end,0]+=pcm[:end-pos]*(vel*left)
        mix[pos:end,1]+=pcm[:end-pos]*(vel*right)
        # Timed stereo echoes for melody and glass hits.
        if kind in ("foam-lead","glass-stab") and vel>.37:
            lag=round((60/song["bpm"])*.375*RATE)
            ex=min(n,pos+lag+len(pcm))
            if ex>pos+lag:
                opposite=1 if pan<=0 else 0
                mix[pos+lag:ex,opposite]+=pcm[:ex-(pos+lag)]*(vel*.18)
    # Glue compression, keeping transient bass and kick punch intact.
    mix=np.tanh(mix*2.2)*.94
    fade=min(round(.22*RATE),n//3)
    mix[:fade]*=np.linspace(0,1,fade,dtype=np.float32)[:,None]
    mix[-fade:]*=np.linspace(1,0,fade,dtype=np.float32)[:,None]
    output=(mix*32767).clip(-32767,32767).astype("<i2").tobytes()
    return output

def main():
    output=HERE/"tracks";scores=HERE/"scores"
    output.mkdir(parents=True,exist_ok=True);scores.mkdir(parents=True,exist_ok=True)
    catalog=[]
    for song in SONGS:
        sc=score(song)
        (scores/(song["slug"]+".json")).write_text(json.dumps(sc,separators=(",",":")),encoding="utf-8")
        raw=render(song,sc)
        filename=output/(song["slug"]+".mp3")
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
                        "-f","s16le","-ar","44100","-ac","2","-i","pipe:0",
                        "-c:a","libmp3lame","-b:a","192k","-ar","44100","-ac","2",
                        "-write_xing","0","-id3v2_version","0",str(filename)],
                        input=raw,check=True,timeout=150)
        if filename.stat().st_size<80000:raise RuntimeError("MP3 unexpectedly small")
        catalog.append({k:song[k] for k in ("id","slug","title","bpm","genre","mood")})
        catalog[-1]["duration"]=sc["length_seconds"];catalog[-1]["events"]=len(sc["events"])
        print(json.dumps({"bEAST":song["title"],"seconds":sc["length_seconds"],
                          "events":len(sc["events"]),"bytes":filename.stat().st_size}),flush=True)
    (HERE/"catalog.json").write_text(json.dumps(catalog,indent=2)+"\n",encoding="utf-8")
    print("bEAST 4 TRACKS RENDERED — NO HUMAN PERFORMER",flush=True)

if __name__=="__main__":main()
