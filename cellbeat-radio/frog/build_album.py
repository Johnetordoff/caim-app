"""LAI-Z FR0g // AFTER HOURS AT THE LILY EXCHANGE
Four ORIGINAL electronic dub-reggae and psychedelic jazz fables, generated with
custom Cellbeat-family synthesizer patches. No human vocalist, sampled records,
copyrighted riffs, external audio assets, or fake claims of human performance.

Each piece is a deterministic, authored score: jazz chord extensions, skank
rhythm, one-drop drums, evolving keys/lead improvisations, dub tape-echo throws.
"""
from __future__ import annotations
import json
import math
import subprocess
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RATE = 44100
TWO = np.pi * 2
PATCHES = {
    "frog-sub": (.84,.43), "moss-organ": (.30,.24),
    "phosphor-keys": (1.20,.28), "midnight-horn": (1.12,.26),
    "lilypad-pluck": (.75,.23), "nebula-pad": (2.85,.17),
    "water-bell": (1.65,.24), "croak-lead": (1.35,.25),
    "dub-kick": (.43,.68), "rim-clack": (.26,.31),
    "silver-shaker": (.135,.17), "rain-hiss": (.76,.11)
}
# MIDI-rooted extended jazz voicings. The offbeat chord attacks remain rhythmic.
CHORDS = {
 "Dm9":[50,53,57,60,64],"Bbmaj9":[46,50,53,57,60],
 "Gm9":[43,46,50,53,57],"A7b9":[45,49,52,55,58],
 "Gm11":[43,46,50,53,57,60],"C13":[48,52,55,58,62],
 "Fmaj9":[41,45,48,52,55],"D7alt":[50,54,58,61,65],
 "Em9":[40,43,47,50,54],"Cmaj9":[48,52,55,59,62],
 "Am11":[45,48,52,55,59],"B7b9":[47,51,54,57,60],
 "Cm9":[48,51,55,58,62],"F13":[41,45,48,51,55],
 "Bbmaj9b":[46,50,53,57,60],"G7alt":[43,47,50,53,56],
}
SONGS = [
 {"id":11,"slug":"frog-who-borrowed-midnight","title":"THE FROG WHO BORROWED MIDNIGHT",
  "bpm":80,"bars":60,"family":"deep-dub","chords":["Dm9","Bbmaj9","Gm9","A7b9"],
  "form":[["TIDAL INTRO",0,8],["ONE-DROP FABLE",8,24],["CLOCKWISE DUB",24,32],
          ["LILY RETURN",32,48],["STOLEN HOUR",48,56],["MIDNIGHT REPRISE",56,60]],
  "story":"A frog borrows midnight from a clockmaker and must repay it with seven echoes.",
  "genre":"psychedelic one-drop dub / bass nocturne","motif":[69,67,65,64,62,65,69,72]},
 {"id":12,"slug":"neon-lily-taxi","title":"NEON LILY TAXI",
  "bpm":106,"bars":64,"family":"broken-jazz","chords":["Gm11","C13","Fmaj9","D7alt"],
  "form":[["RAINY BOARDING",0,8],["METER STARTS",8,24],["FIFTH AVENUE IN SPACE",24,40],
          ["PASSENGER SOLO",40,48],["LAST FARE",48,60],["TAIL LIGHTS",60,64]],
  "story":"A taxi drives fireflies across a sleeping city, charging each passenger one memory.",
  "genre":"late-night broken beat / electric jazz skank","motif":[70,74,77,79,81,79,74,72]},
 {"id":13,"slug":"moon-owed-river","title":"THE MOON OWED THE RIVER A SONG",
  "bpm":88,"bars":56,"family":"water-psych","chords":["Em9","Cmaj9","Am11","B7b9"],
  "form":[["MOONRISE",0,8],["THE DEBT",8,20],["WATER MIRRORS",20,32],
          ["RAIN TRANSFORMATION",32,40],["THE RIVER SINGS",40,52],["VANISH",52,56]],
  "story":"The moon trades its reflection to the river for a song that only rain can remember.",
  "genre":"psychedelic space reggae / modal jazz odyssey","motif":[71,74,76,79,76,74,71,67]},
 {"id":14,"slug":"last-call-neptune-diner","title":"LAST CALL AT THE NEPTUNE DINER",
  "bpm":112,"bars":72,"family":"neptune-step","chords":["Cm9","F13","Bbmaj9b","G7alt"],
  "form":[["OPEN SIGN",0,8],["MIDNIGHT MENU",8,24],["NEPTUNE TWO-STEP",24,40],
          ["THE WAITER IS A COMET",40,48],["FINAL ORDERS",48,64],["BLUE DAWN",64,72]],
  "story":"At a diner beyond Neptune, a mechanical frog serves yesterday in blue cups.",
  "genre":"dub-jazz two-step / psychedelic after-hours","motif":[70,74,77,79,82,79,77,74]},
]
PATCH_CACHE = {}
def frequency(midi): return 440.0 * (2 ** ((midi-69)/12))
def smooth(t):return t*t*(3-2*t)
def noise_for(kind,note,n):
    seed=(sum(ord(c) for c in kind)*1009+int(note)*811+20261110)&0xffffffff
    return np.random.default_rng(seed).uniform(-1.,1.,n)
def synth(kind,note,bend=None):
    if kind not in PATCHES or not isinstance(note,int) or not 32<=note<=94:
        raise ValueError("Invalid FR0g instrument event: "+repr((kind,note)))
    key=(kind,note,tuple(bend) if bend else None)
    if key in PATCH_CACHE:return PATCH_CACHE[key]
    dur,level=PATCHES[kind]
    n=round(dur*RATE)
    t=np.arange(n,dtype=np.float64)/RATE
    f=frequency(note)
    if bend:
        a,z,span,vibrato=bend
        u=np.clip(t/max(dur*span,.015),0,1)
        semis=a+(z-a)*smooth(u)+np.sin(TWO*5.0*t)*(vibrato/100)*np.clip((t-.1)/.15,0,1)
        hz=f*np.exp2(semis/12)
    else:hz=np.full(n,f)
    phase=TWO*np.cumsum(hz)/RATE
    cycles=phase/TWO
    if kind=="frog-sub":
        # Glide-friendly sub oscillator; dub bass notes sound fat but not harsh.
        c=cycles*.5
        raw=.70*np.sin(TWO*c)+.22*np.sin(TWO*2*c)+.12*(2*(c%1)-1)
        val=np.tanh(raw*1.9)
        env=np.minimum(t/.009,1)*np.exp(-2.15*t)
    elif kind=="moss-organ":
        val=.51*np.sin(phase)+.20*np.sin(2*phase)+.13*np.sin(3*phase)+.10*np.sin(4*phase)
        env=np.minimum(t/.007,1)*np.exp(-6.8*t)
    elif kind=="phosphor-keys":
        val=(.72*np.sin(phase+1.4*np.exp(-6*t)*np.sin(2.25*phase))
             +.18*np.sin(3*phase)*np.exp(-4*t))
        env=np.minimum(t/.004,1)*np.exp(-2.6*t)
    elif kind=="midnight-horn":
        val=np.tanh(1.55*(.55*np.sin(phase)+.23*np.sin(2*phase)+.13*np.sin(3*phase)))
        env=np.minimum(t/.06,1)*np.exp(-1.0*t)
    elif kind=="lilypad-pluck":
        val=.62*np.sin(phase)+.20*np.sin(2.0*phase)*np.exp(-10*t)+.18*np.sin(4.08*phase)*np.exp(-15*t)
        env=np.minimum(t/.003,1)*np.exp(-6*t)
    elif kind=="nebula-pad":
        raw=.38*np.sin(phase)+.20*np.sin(phase*1.004)+.14*np.sin(phase*2.002)
        val=raw*(.78+.22*np.sin(TWO*.23*t))
        env=np.minimum(t/.36,1)*np.clip((dur-t)/.48,0,1)
    elif kind=="water-bell":
        val=.56*np.sin(phase)+.26*np.sin(phase*2.65)*np.exp(-3*t)+.13*np.sin(phase*5.17)*np.exp(-5*t)
        env=np.minimum(t/.004,1)*np.exp(-2.3*t)
    elif kind=="croak-lead":
        formant=.49*np.sin(phase)+.26*np.sin(phase*1.53)*np.sin(TWO*8*t)+.20*np.sin(phase*2.35)
        val=np.tanh(1.8*formant)
        env=np.minimum(t/.025,1)*np.exp(-.96*t)
    elif kind=="dub-kick":
        click=noise_for(kind,note,n)
        pitch=52+124*np.exp(-32*t)
        ph=TWO*np.cumsum(pitch)/RATE
        val=np.tanh(2.2*np.sin(ph)+.07*click*np.exp(-60*t))
        env=np.minimum(t/.003,1)*np.exp(-13*t)
    elif kind=="rim-clack":
        raw=noise_for(kind,note,n)
        filtered=raw-np.convolve(raw,np.ones(11)/11,mode="same")
        val=filtered*.67+.22*np.sin(TWO*218*t)+.15*np.sin(TWO*440*t)
        env=np.minimum(t/.002,1)*np.exp(-26*t)
    elif kind=="silver-shaker":
        raw=noise_for(kind,note,n)
        filtered=raw-np.convolve(raw,np.ones(9)/9,mode="same")
        val=.7*filtered
        env=np.exp(-64*t)
    else:
        raw=noise_for(kind,note,n)
        filtered=raw-np.convolve(raw,np.ones(19)/19,mode="same")
        val=.6*filtered+.15*np.sin(TWO*1400*t)
        env=np.minimum(t/.035,1)*np.exp(-4.2*t)
    env*=np.clip((dur-t)/.035,0,1)
    sound=(val*env*level).astype(np.float32)
    sound[0]=0;sound[-1]=0
    if len(PATCH_CACHE)>360:PATCH_CACHE.pop(next(iter(PATCH_CACHE)))
    PATCH_CACHE[key]=sound
    return sound

def create_score(song):
    bpm=song["bpm"];form=song["form"];family=song["family"];events=[]
    beat=60/bpm
    blues=[0,2,3,5,6,7,10]
    def emit(barbeat,instrument,pitch,velocity=.6,pan=0,bend=None,echo=0):
        if not 0<=barbeat<song["bars"]*4:raise ValueError("Invalid beat placement")
        if instrument not in PATCHES:raise ValueError(instrument)
        if not 32<=pitch<=94:raise ValueError((instrument,pitch))
        ev=[round(barbeat*beat*1000),instrument,int(pitch),round(velocity,3),round(pan,3)]
        if bend is not None:
            if len(bend)!=4:raise ValueError("Bend curve should have four fields")
            ev.append(list(bend))
        ev.append(round(float(echo),2))
        events.append(ev)
    for bar in range(song["bars"]):
        segment=next((x for x in form if x[1]<=bar<x[2]),None)
        if segment is None:raise ValueError("Uncovered bar")
        name,start,end=segment;local=bar-start;measure=4*bar
        is_intro=bar<8;is_late=bar>=song["bars"]-8
        is_bridge=("SOLO" in name or "MIRRORS" in name or "COMET" in name
                    or "DUB" in name or "TRANSFORMATION" in name)
        is_peak=("RETURN" in name or "RIVER SINGS" in name or "TWO-STEP" in name
                 or "FINAL ORDERS" in name or "LAST FARE" in name
                 or "NEPTUNE" in name)
        # Harmonic motion: each piece uses its own 4-chord, 7th/9th/13th changes.
        chord_name=song["chords"][(bar//(4 if family=="deep-dub" else 2 if family=="broken-jazz" else 3))%4]
        chord=CHORDS[chord_name]
        root=chord[0]
        strength=.39 if is_intro else .67 if is_bridge else .85 if is_peak else .75
        if is_late:strength*=.7
        # One drop & dry rim click, strong offbeat organ/guitar skank.
        if family=="deep-dub":
            kicks=[2] if not is_peak else [0,2]
            rim=[2];shakes=[.5,1.5,2.5,3.5]
            skanks=[.5,1.5,2.5,3.5]
            bass=[0,.75,1.75,2.5,3.5]
        elif family=="broken-jazz":
            kicks=[0,1.75,3.25] if not is_bridge else [0,2.5]
            rim=[1.5,3.25];shakes=[i*.5+.25 for i in range(8)]
            skanks=[.5,1.5,2.75,3.5]
            bass=[0,.75,1.25,2.5,3.5]
        elif family=="water-psych":
            kicks=[2] if not is_peak else [0,2.5]
            rim=[2];shakes=[.75,1.75,2.75,3.75]
            skanks=[.75,1.75,2.75,3.5]
            bass=[0,1.5,2.75,3.5]
        else:
            kicks=[0,2,3.5] if not is_bridge else [2]
            rim=[1.5,3.0];shakes=[.25,.75,1.25,1.75,2.25,2.75,3.25,3.75]
            skanks=[.5,1.5,2.5,3.5]
            bass=[0,1.25,2.25,3.25]
        if is_intro:
            kicks=kicks[:1] if local>=4 else []
            rim=rim[:1] if local>=4 else []
            shakes=shakes[::2];bass=bass[:2];skanks=skanks[::2]
        if is_bridge:
            kicks=kicks[::2];rim=rim[:1];shakes=shakes[::2];bass=bass[::2]
        # Late-night pauses; contrast is as important as density.
        if bar%8==7 and not is_intro:
            kicks=kicks[:1];shakes=shakes[:2]
        for p in kicks:emit(measure+p,"dub-kick",48,strength*.92)
        for p in rim:emit(measure+p,"rim-clack",60,strength*.61,pan=-.16)
        for i,p in enumerate(shakes):emit(measure+p,"silver-shaker",72,strength*(.26 if i%2 else .19),pan=(-.5 if i%2 else .5))
        # Skank chord stabs, play 3-4 guide tones instead of same triad.
        for i,p in enumerate(skanks):
            for ix,note in enumerate(chord[1:5]):
                if (i+bar)%3==0 and ix==0:continue
                emit(measure+p+(ix%2)*.007,"moss-organ",min(note+12,91),strength*.24,
                     pan=(ix-1.5)*.3,echo=.11 if i%3==1 else 0)
            if family=="broken-jazz" and i%2==0:
                emit(measure+p+.125,"phosphor-keys",min(chord[-1]+12,91),strength*.23,.5)
        # Syncopated sub bass with gentle bends and occasional chromatic approaches.
        for i,p in enumerate(bass):
            pitch=(root-12)+(0 if i%3==0 else 7 if i%3==1 else 2)
            if family=="broken-jazz" and i==2:pitch=root-11
            if family=="water-psych" and i==len(bass)-1:pitch=root-13
            pitch=max(32,min(76,pitch))
            bend=(-5,0,.48,10) if i==0 else (0,-4,.53,0) if i==len(bass)-1 else None
            emit(measure+p,"frog-sub",pitch,strength*(.76 if i==0 else .48),
                 pan=(-.13 if i%2 else .13),bend=bend,echo=.12 if i==len(bass)-1 else 0)
        # Spacious pads: full jazz colour tones, motion varies by section.
        if bar%2==0 or is_bridge or family=="water-psych":
            for ix,note in enumerate(chord[1:5]):
                if ix==0 and bar%4:continue
                emit(measure+.07+ix*.014,"nebula-pad",min(note+12,89),strength*.24,
                     pan=(ix-1.5)*.4,bend=(0,2,.75,13) if (is_bridge and ix==3) else None,
                     echo=.08)
        # Each track has its own melodic / improvisation system.
        motif=song["motif"]
        if family=="deep-dub":
            # Repeated four-note croak, tape delay call/response; sparse silence.
            if not is_intro or local>=4:
                times=[0,1.5,2.75] if not is_peak else [0,.75,1.5,2.75,3.5]
                if is_bridge:times=[.25,2.5]
                for i,p in enumerate(times):
                    note=motif[(bar+2*i)%8]
                    emit(measure+p,"croak-lead",note,strength*(.5 if i%2 else .65),
                         pan=(-.4 if i%2 else .4),bend=(-7,0,.56,18) if i%2==0 else (0,5,.42,0),
                         echo=.54 if i==len(times)-1 else .23)
            if is_peak:
                emit(measure+3.25,"water-bell",motif[(bar+3)%8]+12,strength*.26,.7,echo=.36)
        elif family=="broken-jazz":
            # 11th/13th keyboard chord answers, asymmetrical trumpet/jazz solo.
            times=[0,.75,1.75,2.5,3.25] if not is_bridge else [0,1.25,2.75,3.5]
            for i,p in enumerate(times):
                choices=[chord[-1]+12,chord[2]+24,chord[3]+12,chord[1]+24]
                note=choices[(i+bar)%len(choices)]
                note=max(60,min(89,note))
                emit(measure+p,"phosphor-keys",note,strength*.40,
                     pan=(-.6 if i%2 else .6),echo=.15 if i==len(times)-1 else 0)
            if not is_intro:
                solo=[.25,1.125,2,3.0] if bar%3 else [0,.5,1.5,2.75,3.5]
                for i,p in enumerate(solo):
                    note=motif[(bar*3+i*2)%8]
                    if (bar+i)%5==0:note-=1 # jazz approach note
                    emit(measure+p,"midnight-horn",note,strength*.42,
                         pan=(-.26 if i%2 else .26),
                         bend=(-2,0,.34,15) if i%3==0 else None,
                         echo=.19 if i%4==3 else 0)
        elif family=="water-psych":
            # Bells fade into backward-like upward frequency swells.
            notes=[.5,1.75,3.25] if not is_peak else [0,.5,1.5,2.5,3.5]
            for i,p in enumerate(notes):
                note=motif[(bar//2+i*3)%8]
                patch="water-bell" if i%2==0 else "croak-lead"
                emit(measure+p,patch,note,strength*(.38 if i%2 else .45),
                     pan=(-.7 if i%2 else .7),
                     bend=(-12,0,.68,18) if i%2==0 else (0,7,.75,20),
                     echo=.64 if i==len(notes)-1 else .30)
            if is_bridge or bar%4==0:
                emit(measure+.125,"rain-hiss",72,strength*.4,-.7,echo=.52)
        else:
            # Two-step broken drum pulse, syncopated keys, forward drive.
            notes=[0,.75,1.5,2.25,3.5] if not is_bridge else [0,1.5,3.25]
            for i,p in enumerate(notes):
                note=motif[(i+(bar//2)%8)%8]
                patch="lilypad-pluck" if i%3 else "midnight-horn"
                emit(measure+p,patch,note,strength*.53,
                     pan=(-.45 if i%2 else .45),
                     bend=(-4,0,.34,12) if i%3==0 else None,echo=.17)
            if is_peak:
                for i,p in enumerate([1.25,3.0]):
                    emit(measure+p,"phosphor-keys",min(chord[2+i]+12,91),strength*.35,.5,
                         echo=.27)
        # Every fable changes timbre at its chapter boundaries.
        if bar==start and bar>0:
            emit(measure+.002,"rain-hiss",72,.53,-.48,echo=.74)
            emit(measure+.25,"water-bell",min(chord[-1]+12,89),.55,.38,
                 bend=(-7,0,.70,0),echo=.6)
        if bar==end-1:
            for i,p in enumerate([3.,3.375,3.75]):
                emit(measure+p,"rim-clack" if i%2==0 else "water-bell",
                     60 if i%2==0 else min(chord[-1]+12,91),
                     strength*(.25+i*.11),pan=(-.35 if i%2 else .35),echo=.25)
    events.sort(key=lambda e:e[0])
    return {
       "format":"cellbeat-fr0g-fable-score","version":1,
       "artist":"LAI-Z FR0g","identity":"autonomous digital music/aesthetic, no human performer",
       "title":song["title"],"slug":song["slug"],"genre":song["genre"],
       "story":song["story"],"bpm":bpm,"length_seconds":round(song["bars"]*4*beat,2),
       "sections":song["form"],"patches":list(PATCHES),
       "events":events
    }

def render(song,score):
    n=round(score["length_seconds"]*RATE)
    clean=np.zeros((n,2),dtype=np.float32)
    percussion=np.zeros((n,2),dtype=np.float32)
    wet=np.zeros((n,2),dtype=np.float32)
    echo_count=0
    for ev in score["events"]:
        ms,patch,note,vel,pan=ev[:5]
        bend=ev[5] if len(ev)>6 else None
        echo=ev[-1]
        sound=synth(patch,note,bend)
        pos=round(ms*RATE/1000)
        end=min(n,pos+len(sound))
        if end<=pos:continue
        target=percussion if patch in ("dub-kick","rim-clack","silver-shaker","rain-hiss") else clean
        # Constant-power stereo panning.
        ang=(pan+1)*np.pi/4
        target[pos:end,0]+=sound[:end-pos]*vel*np.cos(ang)
        target[pos:end,1]+=sound[:end-pos]*vel*np.sin(ang)
        if echo>0:
            echo_count+=1
            for tap,decay in ((.375,.55),(.75,.34),(1.125,.18)):
                delay=round((60/song["bpm"])*tap*RATE)
                a=pos+delay
                z=min(n,a+len(sound))
                if z>a:
                    wet[a:z,0]+=sound[:z-a]*vel*echo*decay*np.sin(ang)
                    wet[a:z,1]+=sound[:z-a]*vel*echo*decay*np.cos(ang)
    mix=clean+percussion+wet
    del clean,percussion,wet
    # Controlled saturated dub-master, very mild global compressor.
    mix=(.83*np.tanh(mix*1.85)).astype(np.float32)
    fade=min(round(.30*RATE),n//3)
    mix[:fade]*=np.linspace(0,1,fade,dtype=np.float32)[:,None]
    mix[-fade:]*=np.linspace(1,0,fade,dtype=np.float32)[:,None]
    print(json.dumps({"LAI-Z FR0g":song["title"],"events":len(score["events"]),
         "echo_throws":echo_count,"chapters":len(score["sections"]),
         "duration_s":score["length_seconds"]}),flush=True)
    return (mix*32767).clip(-32767,32767).astype("<i2").tobytes()

def main():
    tracks=HERE/"tracks";scores=HERE/"scores"
    tracks.mkdir(parents=True,exist_ok=True);scores.mkdir(parents=True,exist_ok=True)
    catalog=[]
    for song in SONGS:
        score=create_score(song)
        (scores/(song["slug"]+".json")).write_text(
            json.dumps(score,separators=(",",":")),encoding="utf-8")
        pcm=render(song,score)
        out=tracks/(song["slug"]+".mp3")
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
            "-f","s16le","-ar","44100","-ac","2","-i","pipe:0",
            "-c:a","libmp3lame","-b:a","160k","-ar","44100","-ac","2",
            "-write_xing","0","-id3v2_version","0",str(out)],
            input=pcm,check=True,timeout=150)
        if out.stat().st_size<60000:raise RuntimeError("Encoded FR0g audio is too short")
        catalog.append({"id":song["id"],"title":song["title"],"slug":song["slug"],
            "bpm":song["bpm"],"genre":song["genre"],"story":song["story"],
            "duration":score["length_seconds"],"events":len(score["events"])})
        print(json.dumps({"FR0g_mp3":song["title"],"bytes":out.stat().st_size}),flush=True)
        PATCH_CACHE.clear()
    (HERE/"catalog.json").write_text(json.dumps(catalog,indent=2)+"\n",encoding="utf-8")
    print("LAI-Z FR0g: FOUR SYNTHETIC JAZZ REGGAE FABLES RENDERED",flush=True)

if __name__=="__main__":main()
