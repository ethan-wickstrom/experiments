import type { Material } from "../core/materials.ts";
import type { Solution } from "./protocol.ts";

/**
 * Sound of a strike, by modal synthesis.
 *
 * A mallet delivers a half-sine force pulse of contact time τ at one point.
 * Mode i, of unit modal mass, then rings as
 *   q_i(t) = φ_i(p) · F(f_i) / ω_i · e^(−α_i t) · sin(ω_i t),
 * where F is the spectrum of the pulse. The radiated pressure follows the
 * surface acceleration, which multiplies each term by ω_i². The decay rate is
 * α_i = π f_i η from the material's loss factor, plus a small constant for the
 * air and the suspension.
 */

export interface Strike {
  readonly amplitudes: Float64Array;
  readonly decays: Float64Array;
  readonly frequencies: Float64Array;
}

/** Magnitude spectrum of a unit half-sine pulse lasting `tau` seconds. */
export function pulseSpectrum(frequency: number, tau: number): number {
  const x = 2 * frequency * tau;
  if (Math.abs(x - 1) < 1e-6) return tau / 2;
  return (
    Math.abs(((2 * tau) / Math.PI) * Math.cos(Math.PI * frequency * tau)) / Math.abs(1 - x * x)
  );
}

/** Decay per second from support and air, independent of frequency. */
const SUPPORT_DECAY = 0.6;

export function strikeAt(
  solution: Solution,
  material: Material,
  node: number,
  contactTime: number,
): Strike {
  const n = solution.modes.length;
  const amplitudes = new Float64Array(n);
  const decays = new Float64Array(n);
  const frequencies = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    const mode = solution.modes[i];
    const omega = 2 * Math.PI * mode.frequency;
    frequencies[i] = mode.frequency;
    amplitudes[i] = mode.shape[node] * pulseSpectrum(mode.frequency, contactTime) * omega;
    decays[i] = Math.PI * mode.frequency * material.eta + SUPPORT_DECAY;
  }
  return { amplitudes, decays, frequencies };
}

let context: AudioContext | undefined;
let master: GainNode | undefined;
let analyser: AnalyserNode | undefined;

export function audio(): { context: AudioContext; master: GainNode; analyser: AnalyserNode } {
  if (!context) {
    context = new AudioContext({ latencyHint: "interactive" });
    master = context.createGain();
    master.gain.value = 0.8;
    const limiter = context.createDynamicsCompressor();
    limiter.threshold.value = -6;
    limiter.ratio.value = 12;
    limiter.attack.value = 0.002;
    analyser = context.createAnalyser();
    analyser.fftSize = 8192;
    analyser.smoothingTimeConstant = 0.5;
    master.connect(limiter).connect(analyser).connect(context.destination);
  }
  if (context.state === "suspended") void context.resume();
  return { context, master: master!, analyser: analyser! };
}

export function render(strike: Strike, sampleRate: number, seconds: number): Float32Array {
  const length = Math.floor(seconds * sampleRate);
  const out = new Float32Array(length);
  const nyquist = sampleRate / 2;
  for (let i = 0; i < strike.frequencies.length; i++) {
    const f = strike.frequencies[i];
    const a = strike.amplitudes[i];
    if (f >= nyquist || f < 20 || a === 0) continue;
    // Recurrence for a damped sinusoid: y[n] = 2r cos(θ) y[n−1] − r² y[n−2].
    const r = Math.exp(-strike.decays[i] / sampleRate);
    const theta = (2 * Math.PI * f) / sampleRate;
    const c1 = 2 * r * Math.cos(theta);
    const c2 = r * r;
    let y1 = 0;
    let y2 = (-a * Math.sin(theta)) / r;
    const samples = Math.min(length, Math.ceil((Math.log(1e4) / strike.decays[i]) * sampleRate));
    for (let n = 0; n < samples; n++) {
      const y = c1 * y1 - c2 * y2;
      out[n] += y;
      y2 = y1;
      y1 = y;
    }
  }
  let peak = 0;
  for (let n = 0; n < length; n++) peak = Math.max(peak, Math.abs(out[n]));
  if (peak > 0) for (let n = 0; n < length; n++) out[n] /= peak;
  return out;
}

export function longestRing(strike: Strike): number {
  let slowest = Infinity;
  for (let i = 0; i < strike.decays.length; i++)
    if (strike.amplitudes[i] !== 0) slowest = Math.min(slowest, strike.decays[i]);
  return Math.min(8, Math.max(0.6, Math.log(1e3) / slowest));
}

export function play(strike: Strike, velocity = 1): void {
  const { context, master } = audio();
  const samples = render(strike, context.sampleRate, longestRing(strike));
  const buffer = context.createBuffer(1, samples.length, context.sampleRate);
  buffer.copyToChannel(samples as Float32Array<ArrayBuffer>, 0);
  const source = context.createBufferSource();
  source.buffer = buffer;
  const gain = context.createGain();
  gain.gain.value = 0.7 * velocity;
  source.connect(gain).connect(master);
  source.start();
}

/** A plain sine at the target pitch, to compare the piece against by ear. */
export function playReference(frequency: number, seconds = 1.6): void {
  const { context, master } = audio();
  const osc = context.createOscillator();
  const gain = context.createGain();
  osc.frequency.value = frequency;
  const t = context.currentTime;
  gain.gain.setValueAtTime(0, t);
  gain.gain.linearRampToValueAtTime(0.18, t + 0.02);
  gain.gain.exponentialRampToValueAtTime(0.0005, t + seconds);
  osc.connect(gain).connect(master);
  osc.start(t);
  osc.stop(t + seconds);
}

export function wavBlob(samples: Float32Array, sampleRate: number): Blob {
  const data = new DataView(new ArrayBuffer(44 + samples.length * 2));
  const text = (offset: number, s: string) => {
    for (let i = 0; i < s.length; i++) data.setUint8(offset + i, s.charCodeAt(i));
  };
  text(0, "RIFF");
  data.setUint32(4, 36 + samples.length * 2, true);
  text(8, "WAVEfmt ");
  data.setUint32(16, 16, true);
  data.setUint16(20, 1, true);
  data.setUint16(22, 1, true);
  data.setUint32(24, sampleRate, true);
  data.setUint32(28, sampleRate * 2, true);
  data.setUint16(32, 2, true);
  data.setUint16(34, 16, true);
  text(36, "data");
  data.setUint32(40, samples.length * 2, true);
  for (let i = 0; i < samples.length; i++)
    data.setInt16(
      44 + 2 * i,
      Math.round(Math.max(-1, Math.min(1, samples[i] * 0.89)) * 32767),
      true,
    );
  return new Blob([data], { type: "audio/wav" });
}
