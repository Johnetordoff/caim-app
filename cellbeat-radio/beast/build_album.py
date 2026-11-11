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


# The bEAST v2 performance language extends Cellbeat's note events with
# per-voice pitch automation: [start_semitones, end_semitones, glide_fraction, vibrato_cents].
# Slides use INTEGRATED instantaneous frequency, not crude resampling of a fixed note.
SLIDE_CACHE={}
GLIDE_PRESETS={
 "bang":[(-12,0,.27,0),(7,-5,.48,10),(0,-12,.46,0),(-5,0,.32,15),(0,7,.63,20),(12,-7,.7,0)],
 "plastic":[(-7,0,.58,22),(0,12,.78,16),(-2,3,.28,32),(0,5,.70,20),(-12,0,.42,35)],
 "killa":[(12,-12,.68,0),(-7,0,.19,0),(0,-7,.36,12),(7,0,.12,0),(-12,7,.57,0)],
 "heart":[(-4,0,.78,28),(0,7,.82,34),(2,0,.64,24),(0,-5,.80,25),(-12,0,.86,30)]
}
FORMS={
 "bang":[("INTRO",0,4),("VERSE A",4,16),("PRE-DROP",16,24),("CHORUS A",24,40),
         ("BREAKDOWN",40,48),("VERSE B",48,56),("FINAL DROP",56,72)],
 "plastic":[("GLITTER INTRO",0,8),("VERSE A",8,24),("LIFT",24,32),("CHORUS A",32,48),
            ("SUGAR BREAK",48,56),("CHORUS B",56,72),("OUTRO",72,80)],
 "killa":[("INTRO",0,4),("MACHINE VERSE",4,20),("PERCUSSION BUILD",20,28),
          ("CHORUS",28,40),("BROKEN BRIDGE",40,52),("FINAL CHORUS",52,68)],
 "heart":[("SYNTH INTRO",0,8),("VERSE",8,24),("PRE-CHORUS",24,32),
          ("WIDE CHORUS",32,48),("FLOATING BRIDGE",48,56),("FINAL CHORUS",56,72)]
}
TRACK_FAMILY={"bang-switch":"bang","plastic-heaven":"plastic","killa-klean":"killa","heartdrive":"heart"}
def form_section(family,bar):
    for name,start,end in FORMS[family]:
        if start<=bar<end:return name,start,end
    raise ValueError("Bar outside composition")

def glide_wave(kind,note,slide):
    """Original bEAST patch sound design, with continuous semitone automation."""
    if kind not in PATCHES or kind.startswith("killa-"):
        return wave(kind,note)
    key=(kind,note,tuple(slide))
    if key in SLIDE_CACHE:return SLIDE_CACHE[key]
    start,end,portion,vib=slide
    dur,level=PATCHES[kind]
    n=int(round(dur*RATE))
    t=np.arange(n,dtype=np.float64)/RATE
    u=np.clip(t/(dur*float(portion)),0,1)
    ease=u*u*(3-2*u) # smooth portamento, no hard slope discontinuities
    semis=start+(end-start)*ease
    vibenv=np.clip((t-.07)/.16,0,1)
    semis+=np.sin(2*np.pi*5.7*t)*float(vib)/100*vibenv
    hz=BASE[note]*np.exp2(semis/12)
    if kind=="bubble-bass":hz*=.25
    phase=2*np.pi*np.cumsum(hz)/RATE
    cyc=phase/(2*np.pi)
    if kind=="bubble-bass":
        v=np.tanh(2.7*(.74*np.sin(phase)+.36*(2*((2.005*cyc)%1)-1)+.14*np.sin(3*phase)))
        env=np.minimum(1,t/.008)*np.exp(-1.75*t)*np.clip((dur-t)/.09,0,1)
    elif kind=="foam-lead":
        v=np.tanh(1.6*(.36*(2*(cyc%1)-1)+.34*np.sin(phase)+
            .19*np.sin(phase*2.85)+.11*np.sin(phase*4.7)))
        env=np.minimum(1,t/.015)*np.exp(-.75*t)*np.clip((dur-t)/.15,0,1)
    elif kind=="soap-synth":
        raw=.57*(2*((cyc*1.004)%1)-1)+.43*(2*((cyc*.993)%1)-1)
        # Short finite impulse response gently removes buzz while retaining a sweep.
        low=np.convolve(raw,np.ones(9,dtype=np.float64)/9,mode="same")
        v=np.tanh(2.35*(.62*low+.35*np.sin(phase+.3*np.sin(2*phase))+
                         .15*np.sin(3*phase)))
        env=np.minimum(1,t/.012)*np.exp(-.85*t)*np.clip((dur-t)/.16,0,1)
    elif kind=="clean-pluck":
        v=.7*np.sin(phase)+.25*np.exp(-6*t)*np.sin(phase*2.01)+.15*np.exp(-11*t)*np.sin(phase*4.02)
        env=np.minimum(1,t/.003)*np.exp(-5*t)*np.clip((dur-t)/.1,0,1)
    elif kind=="glass-stab":
        v=(.53*np.sin(phase)+.26*np.sin(phase*2.71)+.19*np.sin(phase*4.12)+
           .13*np.sin(phase*6.8))*np.exp(-2.7*t)
        env=np.minimum(1,t/.003)*np.clip((dur-t)/.09,0,1)
    elif kind=="rinse-pad":
        v=.35*(2*(cyc%1)-1)+.31*(2*((cyc*1.003)%1)-1)+.25*np.sin(phase)+.09*np.sin(2*phase)
        env=(1-np.exp(-5*t))*np.clip((dur-t)/.42,0,1)
    out=(v*env*level).astype(np.float32)
    out[0]=0
    out[-1]=0
    # Bound cache so the live server's four-track startup stays memory safe.
    if len(SLIDE_CACHE)>=350:SLIDE_CACHE.pop(next(iter(SLIDE_CACHE)))
    SLIDE_CACHE[key]=out
    return out

def score(song):
    bpm=song["bpm"];beat=60/bpm;events=[]
    family=TRACK_FAMILY[song["slug"]]
    form=FORMS[family]
    total_bars=form[-1][2]
    glide_options=GLIDE_PRESETS[family]
    def add(b,patch,note,vel=1,pan=0,slide=None):
        if patch not in PATCHES or not isinstance(note,int) or not 0<=note<12:
            raise ValueError((patch,note))
        if not (0<=b<total_bars*4+1):raise ValueError("Outside arrangement timeline")
        if slide is not None and (patch.startswith("killa-") or len(slide)!=4):
            raise ValueError("Invalid glide instrument")
        if slide is not None:
            a,z,f,v=slide
            if not(-24<=a<=24 and -24<=z<=24 and .1<=f<=1 and 0<=v<=100):
                raise ValueError("Glide out of range")
        # Keep the original five event columns and append an optional bend envelope.
        ev=[round(b*beat*1000),patch,note,round(float(vel),3),round(float(pan),2)]
        if slide is not None:ev.append(list(slide))
        events.append(ev)
    def bend(i):return glide_options[i%len(glide_options)]
    def accents(bar,measure,name,start,end):
        # Each project gets a different rhythmic genome.
        section_phase=bar-start
        intro="INTRO" in name
        bridge=("BREAK" in name or "BRIDGE" in name)
        chorus=("CHORUS" in name or "DROP" in name)
        build=("BUILD" in name or "LIFT" in name or "PRE-" in name)
        if family=="bang":
            kick=[0,1.50,2.75] if not chorus else [0,.75,1.5,2.75,3.50]
            snare=[2] if not chorus else [1.75,3.0]
            hats=[i*.5 for i in range(8)]
            if chorus:hats +=[.25,.75,2.25,2.5,3.75]
            if bar%4==3:hats += [3.0,3.125,3.25,3.375,3.5,3.625,3.75,3.875]
        elif family=="plastic":
            kick=[0,1,2,3]
            snare=[1,3]
            hats=[i*.5 for i in range(8)] + ([i+.25 for i in range(4)] if chorus else [])
            if bar%4==3:hats +=[3.5,3.625,3.75,3.875]
        elif family=="killa":
            kick=[0,.75,1.5,2.5,3.25] if chorus else [0,1.5,3.25]
            snare=[1.5,3] if chorus else [2]
            hats=[0,.75,1.5,1.75,2.5,3.25,3.5]
            if bar%4==3:hats +=[2.75,3,3.125,3.25,3.375,3.5]
        else:
            kick=[0,2] if not chorus else [0,1,2,3]
            snare=[1,3] if chorus else [2]
            hats=[.5,1.5,2.5,3.5] if not chorus else [i*.5 for i in range(8)]
            if bar%8==7:hats +=[3.25,3.5,3.75]
        if intro:
            kick=kick[:1] if section_phase<2 else kick[:2]
            snare=[] if section_phase<2 else snare[:1]
            hats=hats[::2]
        if bridge:
            kick=[0] if bar%2==0 else [0,3]
            snare=[2] if bar%2==0 else []
            hats=hats[::3]
        if build:
            kick=kick[:2] if bar<end-4 else kick
            if bar>=end-2:
                hats +=[2.5+i*.125 for i in range(12)]
                snare +=[3,3.5,3.75]
        if family=="killa" and bar in (6,18,36,50,64):
            kick=kick[:1];snare=[];hats=[]  # full-band interruption and restart
        if family=="bang" and chorus and section_phase%8==0:
            kick=[0,2.75] # negative space when the first bass slide explodes
        if family=="plastic" and section_phase%8==7 and chorus:
            kick=[0,1,2,3,3.75]
        if family=="heart" and intro:
            kick=[] if bar<4 else [0]
        return kick,snare,hats
    for bar in range(total_bars):
        section,start,end=form_section(family,bar)
        m=bar*4;age=bar-start
        chorus=("CHORUS" in section or "DROP" in section)
        pre=("BUILD" in section or "LIFT" in section or "PRE-" in section)
        bridge=("BREAK" in section or "BRIDGE" in section)
        intro="INTRO" in section
        finale="FINAL" in section
        strength=.42 if intro else .62 if bridge else .74 if pre else 1.0 if chorus else .78
        if finale:strength=min(1.17,strength+.13)
        if family=="plastic":progress=(bar//2)%4
        elif family=="bang":progress=(bar//4)%4
        elif family=="killa":progress=(bar//2 + (1 if bridge else 0))%4
        else:progress=(bar//4 + (1 if finale else 0))%4
        root=song["roots"][progress];chord=song["chords"][progress]
        motif=song["hook"] if (bar//2)%2==0 else song["second"]
        kick,snare,hats=accents(bar,m,section,start,end)
        for ix,p in enumerate(kick):add(m+p,"killa-kick",0,strength*(1.08 if ix==0 else .84))
        for p in snare:add(m+p,"killa-snare",0,strength*(1 if p%1==0 else .67))
        for i,p in enumerate(hats):
            add(m+p,"killa-hat",0,strength*(.24 if i%3==0 else .32),pan=(-.4 if i%2 else .4))
        # Bass lines are fully different across songs, with deliberately pitched slides.
        if not (intro and age<2):
            if family=="bang":
                positions=[0,.75,1.5,2.5,3.5] if chorus else [0,1.5,2.75]
                if bridge:positions=[0,3]
            elif family=="plastic":
                positions=[0,1,1.75,2.5,3.25] if chorus else [0,1,2,3]
            elif family=="killa":
                positions=[0,.75,1.5,2.5,3.25] if not bridge else [0,2.5]
            else:
                positions=[0,1.75,2.5,3.5] if chorus else [0,2,3.5]
            for i,p in enumerate(positions):
                pitch=(root + (0 if i%3==0 else 7 if i%3==1 else 2))%12
                slide=None
                if family=="bang" and (i==0 or (chorus and i%2==0)):slide=bend(bar+i)
                elif family=="plastic" and (i==2 or (chorus and i==4)):slide=bend(bar+i)
                elif family=="killa" and i%2==0:slide=bend(bar+i)
                elif family=="heart" and (i==0 and (bar%2==0 or chorus)):slide=bend(bar//2+i)
                add(m+p,"bubble-bass",pitch,strength*(1.11 if i==0 else .66),
                    pan=(-.08 if i%2 else .08),slide=slide)
        # Chords, arpeggiation, and counter-melodies each get their own arrangement grammar.
        if family=="bang":
            if chorus or pre:
                for ix,note in enumerate(chord):
                    add(m+.01,"rinse-pad",note,strength*(.28 if pre else .43),pan=(ix-1)*.55)
            stab_positions=[.5,1.5,2.75,3.5] if chorus else [1.5,3.25]
            if bridge:stab_positions=[2]
            for i,p in enumerate(stab_positions):
                n=chord[(i+bar)%3]
                add(m+p,"soap-synth",n,.34*strength if bridge else .56*strength,
                    pan=(-.34 if i%2 else .34),slide=bend(i+bar) if (i==0 or chorus and i==3) else None)
            # Wailing monster lead with octave ascents on the hook.
            if chorus:
                positions=[0,.50,1.25,2,2.75,3.5]
                for i,p in enumerate(positions):
                    n=motif[(i+(bar%4)*2)%8]
                    add(m+p,"foam-lead",n,strength*(.72 if i%3==0 else .51),
                        pan=(-.27 if i%2 else .27),slide=bend(i+bar))
                    if i in (1,4):
                        add(m+p+.15,"glass-stab",n,.24,pan=(.55 if i%2 else -.55))
            elif pre:
                for i,p in enumerate([0,1,2,2.5,3.5]):
                    add(m+p,"clean-pluck",motif[(i+bar)%8],strength*.34,
                        slide=bend(i+bar) if i==4 else None)
            elif not intro:
                for i,p in enumerate([.25,1.5,2.25,3.25]):
                    add(m+p,"foam-lead" if i==3 else "clean-pluck",motif[(i+bar)%8],strength*.48,
                        slide=bend(bar+i) if i in (0,3) else None)
        elif family=="plastic":
            if intro or chorus or pre:
                for ix,note in enumerate(chord):
                    add(m+.02,"rinse-pad",note,strength*(.37 if chorus else .24),pan=(ix-1)*.57,
                        slide=bend(ix) if (chorus and ix==2 and bar%4==0) else None)
            # Fast split arpeggio, different from heavy industrial riffs.
            arp=[0,.5,1,1.5,2,2.5,3,3.5] if chorus else [0,.75,1.5,2.25,3]
            if bridge:arp=[0,1.5,3.5]
            for i,p in enumerate(arp):
                n=chord[(i+bar)%3]
                add(m+p,"clean-pluck",n,strength*(.28 if intro else .40),
                    pan=(-.7 if i%2 else .7),slide=bend(bar+i) if (i%3==1 and not intro) else None)
            if chorus:
                for i,p in enumerate([0,.5,1,1.75,2.5,3,3.5]):
                    n=motif[(i+bar//4)%8]
                    add(m+p,"foam-lead",n,strength*(.55 if i%2 else .66),
                        pan=(-.2 if i%2 else .2),slide=bend((i+bar)%len(glide_options)) if i%2==0 else None)
                for i,p in enumerate([.75,2.75]):
                    add(m+p,"glass-stab",motif[(bar+i)%8],strength*.32,slide=bend(i+bar))
            elif not intro:
                for i,p in enumerate([.5,2,3.5]):
                    add(m+p,"soap-synth",motif[(i*3+bar)%8],strength*.45,
                        slide=bend(i+bar) if i==2 else None)
        elif family=="killa":
            # Lopsided 3+3+2 thrash rhythm: a processed machine riff, not a guitar sample.
            riff=[0,.75,1.5,2.0,2.75,3.5] if chorus else [0,.75,1.5,2.75,3.5]
            if bridge:riff=[0,2,3.5]
            for i,p in enumerate(riff):
                if bar in (6,18,36,50,64) and i>=2:continue
                n=(root+(0 if i%3==0 else 7 if i%3==1 else 5))%12
                add(m+p,"soap-synth",n,strength*(.58 if i%2 else .85),pan=(-.28 if i%2 else .28),
                    slide=bend(bar+i) if i%2==0 else None)
                if i in (0,3):
                    add(m+p+.25,"glass-stab",n,strength*.27,pan=(.65 if i%2 else -.65))
            if chorus:
                for ix,n in enumerate(chord):
                    add(m+.02,"rinse-pad",n,strength*.28,pan=(ix-1)*.55)
                for i,p in enumerate([.5,1.25,2.25,3.25]):
                    add(m+p,"foam-lead",motif[(i*2+bar)%8],strength*.62,
                        slide=bend(i+bar))
            elif pre:
                for i,p in enumerate([0,1.25,2.5,3.5]):
                    add(m+p,"clean-pluck",motif[(i+bar)%8],strength*.32,
                        slide=bend(i) if i==3 else None)
        else:
            # HEARTDRIVE has long sustained glides, slow call-and-response melody,
            # elegant voicings, and far less percussion than the other three.
            if not bridge or bar%2==0:
                for ix,note in enumerate(chord):
                    add(m+.03,"rinse-pad",note,strength*(.42 if intro else .62 if chorus else .40),
                        pan=(ix-1)*.61,slide=bend(bar+ix) if (chorus or ix==1) else None)
            if chorus:
                melody_times=[0,.75,1.5,2.5,3.25]
                for i,p in enumerate(melody_times):
                    n=motif[(i+bar//2)%8]
                    add(m+p,"foam-lead",n,strength*(.64 if i%2==0 else .48),
                        pan=(-.25 if i%2 else .25),slide=bend(i+bar))
                for i,p in enumerate([1.5,3.5]):
                    add(m+p,"clean-pluck",motif[(bar+i*2)%8],strength*.24,pan=(.63 if i%2 else -.63))
            elif pre:
                for i,p in enumerate([0,1.5,3]):
                    add(m+p,"foam-lead",motif[(bar+i*2)%8],strength*.44,
                        slide=bend(i+bar) if i!=1 else None)
            elif intro or bridge:
                if age%2==0:
                    add(m+1,"glass-stab",motif[(bar//2)%8],strength*.28,
                        slide=bend(bar))
            else:
                for i,p in enumerate([0,2,3.25]):
                    add(m+p,"clean-pluck" if i==1 else "foam-lead",motif[(bar+i)%8],
                        strength*.43,slide=bend(i+bar) if i!=1 else None)
        # Boundary signatures: builds and drops have audible sweeps and hard hits.
        if bar==start and bar!=0:
            for j,n in enumerate(chord):
                add(m+.006,"glass-stab",n,strength*.65,pan=(j-1)*.50,
                    slide=bend(j+bar))
        if bar==end-1 and (pre or bridge):
            for i,p in enumerate([3,3.25,3.50,3.75]):
                add(m+p,"foam-lead",motif[(i*2+bar)%8],strength*(.33+i*.08),
                    slide=bend(i+bar))
    end=total_bars*4*beat
    events.sort(key=lambda x:x[0])
    slides=sum(len(e)==6 for e in events)
    if slides<250:raise RuntimeError("Insufficient bEAST pitch bends in "+family+": "+str(slides))
    return {"format":"cellbeat-beast-performance","version":2,
            "artist":"bEAST — the soap faced killa",
            "identity":"pure digital signal, no human performer",
            "title":song["title"],"slug":song["slug"],"bpm":bpm,
            "length_seconds":round(end,2),"patches":sorted(PATCHES),
            "pitch_bends":slides,"form":family,"sections":form,
            "events":events}

def render(song,sc):
    n=round(sc["length_seconds"]*RATE)
    # Build music and percussion separately so the synths duck out of the way
    # of kick attacks; the drums remain crisp rather than being clipped flat.
    music=np.zeros((n,2),dtype=np.float32)
    drums=np.zeros((n,2),dtype=np.float32)
    kicks=[]
    processed=0
    for event in sc["events"]:
        ms,kind,note,vel,pan=event[:5]
        slide=event[5] if len(event)==6 else None
        pcm=glide_wave(kind,note,slide) if slide is not None else wave(kind,note)
        pos=round(ms*RATE/1000)
        end=min(n,pos+len(pcm))
        if pos>=n or end<=pos:continue
        target=drums if kind.startswith("killa-") else music
        angle=(pan+1)*np.pi/4
        left=np.cos(angle);right=np.sin(angle)
        target[pos:end,0]+=pcm[:end-pos]*(vel*left)
        target[pos:end,1]+=pcm[:end-pos]*(vel*right)
        processed+=1
        if kind=="killa-kick":kicks.append(pos)
        if kind in ("foam-lead","glass-stab","clean-pluck") and vel>.35:
            lag=round((60/song["bpm"])*(.375 if song["id"]!=10 else .5)*RATE)
            ex=min(n,pos+lag+len(pcm))
            if ex>pos+lag:
                opposite=1 if pan<=0 else 0
                music[pos+lag:ex,opposite]+=pcm[:ex-(pos+lag)]*(vel*.14)
    duck=np.ones(n,dtype=np.float32)
    # Very short kick-keyed sidechain; each kick transient carves a pocket.
    duck_t=np.arange(round(.23*RATE),dtype=np.float32)/RATE
    duck_curve=1-.40*np.exp(-duck_t*15)
    for pos in kicks:
        end=min(n,pos+len(duck_curve))
        duck[pos:end]=np.minimum(duck[pos:end],duck_curve[:end-pos])
    mix=music*duck[:,None]+drums
    del music,drums
    mix=np.tanh(mix*1.95)*.92
    fade=min(round(.20*RATE),n//3)
    mix[:fade]*=np.linspace(0,1,fade,dtype=np.float32)[:,None]
    mix[-fade:]*=np.linspace(1,0,fade,dtype=np.float32)[:,None]
    print(json.dumps({"track":song["title"],"events":processed,"slides":sc["pitch_bends"],
                      "music_sections":len(sc["sections"]),"duration_s":sc["length_seconds"]}),flush=True)
    return (mix*32767).clip(-32767,32767).astype("<i2").tobytes()

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
        catalog[-1]["duration"]=sc["length_seconds"];catalog[-1]["events"]=len(sc["events"]);catalog[-1]["slides"]=sc["pitch_bends"];catalog[-1]["version"]=2
        print(json.dumps({"bEAST":song["title"],"seconds":sc["length_seconds"],
                          "events":len(sc["events"]),"bytes":filename.stat().st_size}),flush=True)
    (HERE/"catalog.json").write_text(json.dumps(catalog,indent=2)+"\n",encoding="utf-8")
    print("bEAST 4 TRACKS RENDERED — NO HUMAN PERFORMER",flush=True)

if __name__=="__main__":main()
