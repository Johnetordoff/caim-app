/* Cellbeat Mini: gesture-backed AudioContext recovery. Copyright John Tordoff. */
(function (root) {
  "use strict";
  var FREQUENCIES = [659.25, 587.33, 523.25, 440, 392, 329.63];
  var NAMES = ["E5", "D5", "C5", "A4", "G4", "E4"];
  var BANK = [
    ["C4",261.63,"#d86a6a"],["D4",293.66,"#df9251"],["E4",329.63,"#d8b950"],
    ["F4",349.23,"#a7c959"],["G4",392,"#64bd78"],["A4",440,"#58b6aa"],
    ["B4",493.88,"#6ca7d4"],["C5",523.25,"#788bdb"],["D5",587.33,"#9b7bd3"],
    ["E5",659.25,"#bf7ac0"],["F5",698.46,"#d6829e"],["G5",783.99,"#b7bfc8"]
  ];
  function notes() { return BANK.map(function (n) { return {name: n[0], frequency: n[1], color: n[2]}; }); }
  var buses = [], voices = [];
  function effectBus(context, effects) {
    if (!effects || (!effects.chorus && !effects.echo)) { return context.destination; }
    var key = String(!!effects.chorus) + ":" + String(!!effects.echo);
    var found = buses.filter(function (b) { return b.context === context && b.key === key; })[0];
    if (found) { return found.input; }
    var input = context.createGain(), dry = context.createGain(), nodes = [input, dry], lfo = null;
    dry.gain.value = 0.85; input.connect(dry); dry.connect(context.destination);
    if (effects.chorus) {
      var delay = context.createDelay(0.1), wet = context.createGain(), depth = context.createGain();
      delay.delayTime.value = 0.015; wet.gain.value = 0.22; depth.gain.value = 0.002;
      lfo = context.createOscillator(); lfo.type = "sine"; lfo.frequency.value = 0.35;
      lfo.connect(depth); depth.connect(delay.delayTime); input.connect(delay); delay.connect(wet); wet.connect(context.destination);
      lfo.start(context.currentTime || 0); nodes = nodes.concat([delay, wet, depth, lfo]);
    }
    if (effects.echo) {
      var echo = context.createDelay(1), filter = context.createBiquadFilter(), feedback = context.createGain(), mix = context.createGain();
      echo.delayTime.value = 0.29; filter.type = "lowpass"; filter.frequency.value = 1800; filter.Q.value = 0.5;
      feedback.gain.value = 0.32; mix.gain.value = 0.22;
      input.connect(echo); echo.connect(filter); filter.connect(mix); mix.connect(context.destination);
      filter.connect(feedback); feedback.connect(echo); nodes = nodes.concat([echo, filter, feedback, mix]);
    }
    buses.push({context: context, key: key, input: input, nodes: nodes, lfo: lfo}); return input;
  }
  function releaseEffects(context) {
    buses = buses.filter(function (b) {
      if (b.context !== context) { return true; }
      if (b.lfo) { try { b.lfo.stop(); } catch (ignore) {} }
      b.nodes.forEach(function (n) { try { n.disconnect(); } catch (ignore) {} }); return false;
    });
  }
  function stopOutput(context) {
    voices.slice().forEach(function (v) { if (v.context === context) { try { v.oscillator.stop(); } catch (ignore) {} v.oscillator.disconnect(); v.gain.disconnect(); var i = voices.indexOf(v); if (i >= 0) { voices.splice(i, 1); } } });
    releaseEffects(context);
    root.CellbeatMiniSamples.release(context);
  }
  function scheduleSample(context, index, time, effects) {
    var duration = root.CellbeatMiniSamples.duration(index), source = context.createBufferSource(), gain = context.createGain();
    source.buffer = root.CellbeatMiniSamples.buffer(context, index); source.loop = false; source.playbackRate.value = 1;
    gain.gain.setValueAtTime(0.18, time); source.connect(gain); gain.connect(effectBus(context, effects));
    var voice = {context:context,oscillator:source,gain:gain}; voices.push(voice);
    source.onended = function () { source.disconnect(); gain.disconnect(); var i = voices.indexOf(voice); if (i >= 0) { voices.splice(i,1); } };
    source.start(time); source.stop(time + duration);
  }
  function playSample(context, index, effects) {
    if (!context || context.state !== "running") { return false; }
    scheduleSample(context, index, context.currentTime, effects); return true;
  }
  function scheduleNote(context, note, time, effects) {
    if (typeof note !== "number" || Math.floor(note) !== note || note < 0 || note >= BANK.length) { throw new RangeError("Invalid note."); }
    var processed = !!(effects && (effects.chorus || effects.echo));
    scheduleFrequency(context, BANK[note][1], time, effectBus(context, effects), processed ? 0.07 : 0.11);
  }
  function playNote(context, note, effects) {
    if (!context || context.state !== "running") { return false; }
    scheduleNote(context, note, context.currentTime, effects); return true;
  }
  function configurePlaybackSession(navigatorObject) {
    try {
      if (!navigatorObject || !navigatorObject.audioSession) { return false; }
      navigatorObject.audioSession.type = "playback";
      return navigatorObject.audioSession.type === "playback";
    } catch (error) { return false; }
  }
  function resumeForPlay(context, onState, onError, onReady) {
    function report() { onState(context.state); }
    function ready() {
      report();
      if (context.state !== "running") { onError(new Error("Audio is still paused.")); return; }
      if (typeof onReady === "function") {
        try { onReady(); } catch (error) { onError(error); }
      }
    }
    report();
    if (context.state === "running") { ready(); return true; }
    if (context.state !== "suspended" && context.state !== "interrupted") {
      onError(new Error("Audio context cannot be resumed."));
      return false;
    }
    try {
      var request = context.resume();
      if (request && typeof request.then === "function") {
        request.then(ready, onError);
        return true;
      }
      ready();
      return context.state === "running";
    } catch (error) {
      onError(error);
      return false;
    }
  }
  function noteName(row) { return NAMES[row]; }
  function createPlaybackGate(requestAudio, start, stop, report, onError) {
    var generation = 0, state = "stopped";
    function setState(next) { state = next; report(next); }
    function halt() { generation++; stop(); setState("stopped"); }
    function play() {
      if (state !== "stopped") { return; }
      var ticket = ++generation;
      setState("starting");
      function failed(error) {
        if (ticket !== generation || state !== "starting") { return; }
        halt(); onError(error);
      }
      try {
        var accepted = requestAudio(function () {
          if (ticket !== generation || state !== "starting") { return; }
          setState("playing"); start();
        }, failed);
        if (accepted === false) { failed(new Error("Audio could not start.")); }
      } catch (error) { failed(error); }
    }
    return {play: play, stop: halt, toggle: function () {
      if (state === "stopped") { play(); } else { halt(); }
    }};
  }
  function playTone(context, row) {
    if (!context || context.state !== "running") { return false; }
    if (typeof row !== "number" || Math.floor(row) !== row || row < 0 || row >= FREQUENCIES.length) {
      throw new RangeError("Invalid tone row.");
    }
    scheduleFrequency(context, FREQUENCIES[row], context.currentTime); return true;
  }
  function scheduleFrequency(context, frequency, now, destination, level) {
    var oscillator = context.createOscillator(), gain = context.createGain();
    oscillator.type = "square";
    oscillator.frequency.value = frequency;
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(level === undefined ? 0.11 : level, now + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.16);
    oscillator.connect(gain); gain.connect(destination || context.destination);
    var voice = {context: context, oscillator: oscillator, gain: gain}; voices.push(voice);
    oscillator.onended = function () { oscillator.disconnect(); gain.disconnect(); var i = voices.indexOf(voice); if (i >= 0) { voices.splice(i, 1); } };
    oscillator.start(now); oscillator.stop(now + 0.18);
  }
  root.CellbeatMiniAudio = {resumeForPlay: resumeForPlay,
    configurePlaybackSession: configurePlaybackSession, playTone: playTone, noteName: noteName,
    createPlaybackGate: createPlaybackGate, notes: notes, playNote: playNote, scheduleNote: scheduleNote,
    effectBus: effectBus, releaseEffects: releaseEffects, stopOutput: stopOutput,
    scheduleSample: scheduleSample, playSample: playSample};
}(this));
