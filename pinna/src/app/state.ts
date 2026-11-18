import { batch, computed, signal } from "@preact/signals";
import { type Design, PRESETS, materialOf } from "../core/design.ts";
import { play, strikeAt } from "./audio.ts";
import type { Request, Response, Solution } from "./protocol.ts";

const STORAGE_KEY = "pinna.design.v1";

function loadDesign(): Design {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = parseDesign(stored);
      if (parsed) return parsed;
    }
  } catch {
    // Storage can be unavailable; fall through to the default.
  }
  return PRESETS[0];
}

/** Read a design from JSON, or null when it is not one. */
export function parseDesign(text: string): Design | null {
  try {
    const d = JSON.parse(text) as Design;
    const numbers = (v: unknown): v is number[] =>
      Array.isArray(v) && v.every((x) => typeof x === "number" && Number.isFinite(x));
    if (
      typeof d.name !== "string" ||
      typeof d.materialId !== "string" ||
      !(d.thickness > 0) ||
      typeof d.grainAngle !== "number"
    )
      return null;
    if (
      !d.profile ||
      !numbers(d.profile.depth) ||
      d.profile.depth.length < 2 ||
      (d.profile.axis !== "axial" && d.profile.axis !== "radial")
    )
      return null;
    if (
      !d.tuning ||
      !numbers(d.tuning.ratios) ||
      typeof d.tuning.fundamental !== "number" ||
      (d.tuning.family !== "bending" && d.tuning.family !== "all")
    )
      return null;
    const s = d.shape;
    const ok =
      (s.kind === "bar" && s.length > 0 && s.width > 0) ||
      (s.kind === "disc" && s.diameter > 0) ||
      (s.kind === "polygon" && s.sides >= 3 && s.diameter > 0) ||
      (s.kind === "free" &&
        Array.isArray(s.points) &&
        s.points.length >= 3 &&
        s.points.every((p) => numbers(p) && p.length === 2));
    if (!ok) return null;
    materialOf(d);
    return d;
  } catch {
    return null;
  }
}

export const design = signal<Design>(loadDesign());
export const solution = signal<Solution | null>(null);
export const busy = signal(false);
export const error = signal<string | null>(null);
/** The mode drawn on the piece; null shows the piece at rest or ringing from a strike. */
export const selectedMode = signal<number | null>(null);
export const hoveredMode = signal<number | null>(null);
export const shownMode = computed(() => hoveredMode.value ?? selectedMode.value);
/** Mallet contact time, seconds. Soft yarn is around 2 ms, hard plastic 0.2 ms. */
export const contactTime = signal(0.0009);
export const nodeBudget = signal(1400);
export const modeCount = signal(18);
export const showSand = signal(true);
export const showMesh = signal(false);

export interface TuneProgress {
  readonly running: boolean;
  readonly history: ReadonlyArray<ReadonlyArray<number>>;
  readonly converged?: boolean;
  readonly note?: string;
  readonly iterations?: number;
}
export const tuneProgress = signal<TuneProgress | null>(null);

export interface StrikeEvent {
  readonly node: number;
  readonly time: number;
}
export const lastStrike = signal<StrikeEvent | null>(null);

const worker = new Worker(new URL("./worker.ts", import.meta.url), { type: "module" });
let nextId = 1;
let latestSolve = 0;
let inFlight = false;
let queued: Request | null = null;

function send(request: Request) {
  // Only the newest request matters; anything waiting behind a running solve is replaced.
  if (inFlight) {
    queued = request;
    return;
  }
  inFlight = true;
  busy.value = true;
  worker.postMessage(request);
}

function done() {
  inFlight = false;
  if (queued) {
    const next = queued;
    queued = null;
    send(next);
  } else {
    busy.value = false;
  }
}

worker.onmessage = (event: MessageEvent<Response>) => {
  const message = event.data;
  if (message.type === "tuneStep") {
    const current = tuneProgress.value;
    tuneProgress.value = { running: true, history: [...(current?.history ?? []), message.cents] };
    return;
  }
  batch(() => {
    if (message.type === "solved") {
      if (message.id === latestSolve) {
        solution.value = message.solution;
        error.value = null;
      }
    } else if (message.type === "tuned") {
      const current = tuneProgress.value;
      tuneProgress.value = {
        running: false,
        history: current?.history ?? [],
        converged: message.converged,
        note: message.note,
        iterations: message.iterations,
      };
      solution.value = message.solution;
      designSilently(message.solution.design);
      error.value = null;
    } else {
      error.value = message.message;
      if (tuneProgress.value?.running) tuneProgress.value = null;
    }
  });
  done();
};

worker.onerror = (event) => {
  error.value = event.message;
  done();
};

let suppress = false;
function designSilently(next: Design) {
  suppress = true;
  design.value = next;
  suppress = false;
  persist(next);
}

function persist(d: Design) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(d));
  } catch {
    // Not being able to save is not worth interrupting the work.
  }
}

export function requestSolve() {
  latestSolve = nextId++;
  send({
    type: "solve",
    id: latestSolve,
    design: design.value,
    nodeBudget: nodeBudget.value,
    modeCount: modeCount.value,
  });
}

design.subscribe((d) => {
  if (suppress) return;
  persist(d);
  requestSolve();
});
nodeBudget.subscribe(() => solution.peek() && requestSolve());
modeCount.subscribe(() => solution.peek() && requestSolve());

export function update(patch: Partial<Design>) {
  design.value = { ...design.value, ...patch };
}

export function startTune() {
  tuneProgress.value = { running: true, history: [] };
  latestSolve = nextId++;
  send({
    type: "tune",
    id: latestSolve,
    design: design.value,
    nodeBudget: nodeBudget.value,
    modeCount: modeCount.value,
  });
}

export function strike(node: number, velocity = 1) {
  const s = solution.value;
  if (!s) return;
  play(strikeAt(s, materialOf(s.design), node, contactTime.value), velocity);
  batch(() => {
    selectedMode.value = null;
    lastStrike.value = { node, time: performance.now() };
  });
}

/** The node nearest a point, metres. */
export function nearestNode(s: Solution, x: number, y: number): number {
  let best = 0;
  let bestDistance = Infinity;
  for (let i = 0; i < s.nodes.length / 2; i++) {
    const d = (s.nodes[2 * i] - x) ** 2 + (s.nodes[2 * i + 1] - y) ** 2;
    if (d < bestDistance) {
      bestDistance = d;
      best = i;
    }
  }
  return best;
}
