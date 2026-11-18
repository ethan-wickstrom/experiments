import { useEffect, useRef, useState } from "preact/hooks";
import {
  type Design,
  PRESETS,
  type Shape,
  centred,
  depthAt,
  extentOf,
  materialOf,
  outlineOf,
} from "../core/design.ts";
import { MATERIALS } from "../core/materials.ts";
import { longestRing, playReference, render as renderStrike, strikeAt, wavBlob } from "./audio.ts";
import { OutlineEditor } from "./OutlineEditor.tsx";
import { centsBetween, midiFrequency, midiName, pitchOf, signed } from "./pitch.ts";
import { ProfileEditor } from "./ProfileEditor.tsx";
import { Spectrum } from "./Spectrum.tsx";
import * as state from "./state.ts";
import { View } from "./view.ts";

const mm = (metres: number) => metres * 1000;

function NumberField(props: {
  label: string;
  value: number;
  unit?: string;
  min: number;
  max: number;
  step?: number;
  digits?: number;
  onChange: (value: number) => void;
}) {
  const digits = props.digits ?? 1;
  const [text, setText] = useState<string | null>(null);
  const shown = text ?? String(Number(props.value.toFixed(digits)));
  const commit = (raw: string) => {
    const value = Number(raw);
    if (raw.trim() !== "" && Number.isFinite(value))
      props.onChange(Math.min(props.max, Math.max(props.min, value)));
    setText(null);
  };
  return (
    <label class="field">
      <span>{props.label}</span>
      <span class="input">
        <input
          type="number"
          value={shown}
          min={props.min}
          max={props.max}
          step={props.step ?? 1}
          onInput={(e) => {
            const raw = e.currentTarget.value;
            setText(raw);
            const value = Number(raw);
            if (
              raw.trim() !== "" &&
              Number.isFinite(value) &&
              value >= props.min &&
              value <= props.max
            )
              props.onChange(value);
          }}
          onBlur={(e) => commit(e.currentTarget.value)}
          onKeyDown={(e) => e.key === "Enter" && e.currentTarget.blur()}
        />
        {props.unit && <em>{props.unit}</em>}
      </span>
    </label>
  );
}

function Segmented<T extends string>(props: {
  value: T;
  options: ReadonlyArray<{ value: T; label: string }>;
  onChange: (value: T) => void;
  label: string;
}) {
  return (
    <div class="segmented" role="radiogroup" aria-label={props.label}>
      {props.options.map((o) => (
        <button
          type="button"
          role="radio"
          aria-checked={o.value === props.value}
          class={o.value === props.value ? "on" : ""}
          onClick={() => props.onChange(o.value)}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

function shapeOfKind(kind: Shape["kind"], current: Design): Shape {
  const ext = extentOf(outlineOf(current.shape));
  const span = Math.max(ext.maxX - ext.minX, ext.maxY - ext.minY);
  switch (kind) {
    case "bar":
      return {
        kind,
        length: ext.maxX - ext.minX,
        width: Math.min(ext.maxY - ext.minY, (ext.maxX - ext.minX) / 3),
      };
    case "disc":
      return { kind, diameter: span };
    case "polygon":
      return { kind, sides: 6, diameter: span };
    case "free": {
      const outline = outlineOf(current.shape);
      const keep = Math.max(1, Math.ceil(outline.length / 16));
      return {
        kind,
        points: outline.filter((_, i) => i % keep === 0).map(([x, y]) => [x, y] as const),
      };
    }
  }
}

function PiecePanel() {
  const d = state.design.value;
  const shape = d.shape;
  const setShape = (next: Shape) => state.update({ shape: next, name: "Custom" });
  const material = materialOf(d);
  return (
    <aside class="panel left">
      <header class="brand">
        <h1>Pinna</h1>
        <p>Design a struck instrument. Solve it, hear it, tune it.</p>
      </header>

      <section>
        <h2>Start from</h2>
        <select
          class="select"
          value={PRESETS.findIndex((p) => p.name === d.name)}
          onChange={(e) => {
            const preset = PRESETS[Number(e.currentTarget.value)];
            if (preset) {
              state.selectedMode.value = null;
              state.tuneProgress.value = null;
              state.design.value = preset;
            }
          }}
        >
          {!PRESETS.some((p) => p.name === d.name) && <option value={-1}>{d.name}</option>}
          {PRESETS.map((p, i) => (
            <option value={i}>{p.name}</option>
          ))}
        </select>
      </section>

      <section>
        <h2>Outline</h2>
        <Segmented
          label="Outline"
          value={shape.kind}
          options={[
            { value: "bar", label: "Bar" },
            { value: "disc", label: "Disc" },
            { value: "polygon", label: "Polygon" },
            { value: "free", label: "Drawn" },
          ]}
          onChange={(kind) => {
            if (kind === shape.kind) return;
            const next = shapeOfKind(kind, d);
            state.update({
              shape: next,
              name: "Custom",
              profile: { ...d.profile, axis: kind === "bar" ? "axial" : d.profile.axis },
            });
          }}
        />
        {shape.kind === "bar" && (
          <div class="fields">
            <NumberField
              label="Length"
              unit="mm"
              value={mm(shape.length)}
              min={40}
              max={2000}
              onChange={(v) => setShape({ ...shape, length: v / 1000 })}
            />
            <NumberField
              label="Width"
              unit="mm"
              value={mm(shape.width)}
              min={8}
              max={600}
              onChange={(v) => setShape({ ...shape, width: v / 1000 })}
            />
          </div>
        )}
        {shape.kind === "disc" && (
          <div class="fields">
            <NumberField
              label="Diameter"
              unit="mm"
              value={mm(shape.diameter)}
              min={30}
              max={2000}
              onChange={(v) => setShape({ ...shape, diameter: v / 1000 })}
            />
          </div>
        )}
        {shape.kind === "polygon" && (
          <div class="fields">
            <NumberField
              label="Sides"
              value={shape.sides}
              min={3}
              max={12}
              digits={0}
              onChange={(v) => setShape({ ...shape, sides: Math.round(v) })}
            />
            <NumberField
              label="Across corners"
              unit="mm"
              value={mm(shape.diameter)}
              min={30}
              max={2000}
              onChange={(v) => setShape({ ...shape, diameter: v / 1000 })}
            />
          </div>
        )}
        {shape.kind === "free" && (
          <OutlineEditor
            points={shape.points}
            onChange={(points, settle) =>
              setShape({ kind: "free", points: settle ? centred(points) : points })
            }
          />
        )}
      </section>

      <section>
        <h2>Blank</h2>
        <select
          class="select"
          value={d.materialId}
          onChange={(e) => state.update({ materialId: e.currentTarget.value })}
        >
          {MATERIALS.map((m) => (
            <option value={m.id}>{m.name}</option>
          ))}
        </select>
        <div class="fields">
          <NumberField
            label="Thickness"
            unit="mm"
            value={mm(d.thickness)}
            min={0.3}
            max={80}
            step={0.1}
            digits={2}
            onChange={(v) => state.update({ thickness: v / 1000 })}
          />
          {material.kind === "wood" && (
            <NumberField
              label="Grain angle"
              unit="°"
              value={d.grainAngle}
              min={-90}
              max={90}
              digits={0}
              onChange={(v) => state.update({ grainAngle: v })}
            />
          )}
        </div>
        <p class="note">
          {material.kind === "wood"
            ? `Stiffness ${(material.E1 / 1e9).toFixed(1)} GPa along the grain, ${(material.E2 / 1e9).toFixed(1)} across`
            : `Stiffness ${(material.E1 / 1e9).toFixed(0)} GPa`}
          , density {material.rho} kg/m³, Q ≈ {Math.round(1 / material.eta)}. Handbook values:
          measure your blank when it matters.
        </p>
      </section>

      <section>
        <h2>Mallet</h2>
        <label class="slider">
          <span>Soft</span>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={1 - Math.log(state.contactTime.value / 0.0002) / Math.log(15)}
            onInput={(e) =>
              (state.contactTime.value = 0.0002 * 15 ** (1 - Number(e.currentTarget.value)))
            }
            aria-label="Mallet hardness"
          />
          <span>Hard</span>
        </label>
        <p class="note">
          Contact lasts {(state.contactTime.value * 1000).toFixed(2)} ms. A longer contact excites
          fewer high partials.
        </p>
      </section>

      <section>
        <h2>Solver</h2>
        <div class="fields">
          <NumberField
            label="Mesh nodes"
            value={state.nodeBudget.value}
            min={300}
            max={6000}
            step={100}
            digits={0}
            onChange={(v) => (state.nodeBudget.value = Math.round(v))}
          />
          <NumberField
            label="Partials"
            value={state.modeCount.value}
            min={6}
            max={40}
            digits={0}
            onChange={(v) => (state.modeCount.value = Math.round(v))}
          />
        </div>
        <div class="toggles">
          <label>
            <input
              type="checkbox"
              checked={state.showSand.value}
              onChange={(e) => (state.showSand.value = e.currentTarget.checked)}
            />{" "}
            Sand on nodal lines
          </label>
          <label>
            <input
              type="checkbox"
              checked={state.showMesh.value}
              onChange={(e) => (state.showMesh.value = e.currentTarget.checked)}
            />{" "}
            Mesh
          </label>
        </div>
      </section>

      <section>
        <h2>Files</h2>
        <div class="buttons">
          <button
            type="button"
            onClick={() =>
              download(
                `${slug(d.name)}.pinna.json`,
                new Blob([JSON.stringify(d, null, 2)], { type: "application/json" }),
              )
            }
          >
            Save design
          </button>
          <label class="button">
            Open design
            <input
              type="file"
              accept=".json,application/json"
              hidden
              onChange={async (e) => {
                const file = e.currentTarget.files?.[0];
                e.currentTarget.value = "";
                if (!file) return;
                const parsed = state.parseDesign(await file.text());
                if (parsed) state.design.value = parsed;
                else state.error.value = "That file is not a Pinna design.";
              }}
            />
          </label>
          <button type="button" onClick={exportProfile}>
            Cut profile .csv
          </button>
          <button type="button" onClick={exportWav}>
            Strike .wav
          </button>
        </div>
      </section>
    </aside>
  );
}

const slug = (name: string) =>
  name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "") || "design";

function download(name: string, blob: Blob) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function exportProfile() {
  const d = state.design.value;
  const ext = extentOf(outlineOf(d.shape));
  const reach = d.profile.axis === "axial" ? ext.halfLength : ext.radius;
  const rows = [
    d.profile.axis === "axial"
      ? "position_along_length_mm,thickness_mm,cut_depth_mm"
      : "distance_from_centre_mm,thickness_mm,cut_depth_mm",
  ];
  const steps = 200;
  for (let i = 0; i <= steps; i++) {
    const u = d.profile.axis === "axial" ? -1 + (2 * i) / steps : i / steps;
    const cut = depthAt(d.profile.depth, u) * d.thickness;
    rows.push(
      `${mm(u * reach).toFixed(3)},${mm(d.thickness - cut).toFixed(4)},${mm(cut).toFixed(4)}`,
    );
  }
  download(
    `${slug(d.name)}-cut-profile.csv`,
    new Blob([rows.join("\n") + "\n"], { type: "text/csv" }),
  );
}

function strikeNode(): number {
  const s = state.solution.value!;
  return state.lastStrike.value && state.lastStrike.value.node < s.nodes.length / 2
    ? state.lastStrike.value.node
    : state.nearestNode(s, 0, 0);
}

function exportWav() {
  const s = state.solution.value;
  if (!s) return;
  const strike = strikeAt(s, materialOf(s.design), strikeNode(), state.contactTime.value);
  download(
    `${slug(s.design.name)}.wav`,
    wavBlob(renderStrike(strike, 48000, longestRing(strike)), 48000),
  );
}

function PartialsPanel() {
  const s = state.solution.value;
  const d = state.design.value;
  const targets = d.tuning.ratios.map((r) => r * d.tuning.fundamental);
  if (!s) return <section class="partials" />;
  const first = s.modes.find((m) => m.partial === 0) ?? s.modes[0];
  const shown = state.shownMode.value;
  return (
    <section class="partials">
      <h2>
        Partials <span class="hint">hover to see, click to hold</span>
      </h2>
      <div class="table" onPointerLeave={() => (state.hoveredMode.value = null)}>
        <div class="row head">
          <span>#</span>
          <span>Hz</span>
          <span>Note</span>
          <span>Ratio</span>
          <span>Target</span>
        </div>
        {s.modes.map((m, i) => {
          const p = pitchOf(m.frequency);
          const target = m.partial >= 0 && m.partial < targets.length ? targets[m.partial] : null;
          const off = target ? centsBetween(m.frequency, target) : null;
          return (
            <button
              type="button"
              class={`row${shown === i ? " on" : ""}${d.tuning.family === "bending" && m.partial < 0 ? " dim" : ""}`}
              onPointerEnter={() => (state.hoveredMode.value = i)}
              onClick={() => (state.selectedMode.value = state.selectedMode.value === i ? null : i)}
            >
              <span>{i + 1}</span>
              <span>{m.frequency < 1000 ? m.frequency.toFixed(1) : m.frequency.toFixed(0)}</span>
              <span>
                {p.name} <i>{signed(p.cents)}</i>
              </span>
              <span>{(m.frequency / first.frequency).toFixed(3)}</span>
              <span
                class={
                  off === null
                    ? ""
                    : Math.abs(off) < 2
                      ? "good"
                      : Math.abs(off) < 15
                        ? "near"
                        : "far"
                }
              >
                {off === null
                  ? d.tuning.family === "bending" && m.partial < 0
                    ? "twist"
                    : ""
                  : `${signed(off, Math.abs(off) < 10 ? 1 : 0)} ¢`}
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}

const RATIO_SETS: ReadonlyArray<{ label: string; ratios: number[] }> = [
  { label: "1 : 4 : 10", ratios: [1, 4, 10] },
  { label: "1 : 3 : 6", ratios: [1, 3, 6] },
  { label: "1 : 4", ratios: [1, 4] },
  { label: "1 : 3", ratios: [1, 3] },
  { label: "1 : 2 : 3", ratios: [1, 2, 3] },
];

function parseRatios(text: string): number[] | null {
  const parts = text.split(/[:,\s]+/).filter((p) => p !== "");
  const values = parts.map(Number);
  if (values.length === 0 || values.some((v) => !Number.isFinite(v) || v <= 0)) return null;
  for (let i = 1; i < values.length; i++) if (values[i] <= values[i - 1]) return null;
  return values;
}

function TuningPanel() {
  const d = state.design.value;
  const s = state.solution.value;
  const progress = state.tuneProgress.value;
  const [ratioText, setRatioText] = useState<string | null>(null);
  const first = s?.modes.find((m) => m.partial === 0) ?? s?.modes[0];
  const fundamental = d.tuning.fundamental > 0 ? d.tuning.fundamental : (first?.frequency ?? 440);
  const ratios = d.tuning.ratios.length > 0 ? d.tuning.ratios : [1];
  const setTuning = (patch: Partial<Design["tuning"]>) =>
    state.update({ tuning: { ...d.tuning, fundamental, ratios, ...patch } });
  const pitch = pitchOf(fundamental);
  const ratioLabel = ratios.map((r) => String(Number(r.toFixed(4)))).join(" : ");
  const cut = d.profile.depth.some((v) => v > 0);
  const worst = progress?.history.map((h) => Math.max(...h.map(Math.abs))) ?? [];
  return (
    <section class="tuning">
      <h2>Tune</h2>
      <div class="pitch">
        <button
          type="button"
          aria-label="Down a semitone"
          onClick={() =>
            setTuning({
              fundamental: midiFrequency(Math.round(69 + 12 * Math.log2(fundamental / 440)) - 1),
            })
          }
        >
          −
        </button>
        <div>
          <strong>{midiName(pitch.midi)}</strong>
          <NumberField
            label=""
            unit="Hz"
            value={fundamental}
            min={20}
            max={8000}
            step={0.1}
            digits={2}
            onChange={(v) => setTuning({ fundamental: v })}
          />
        </div>
        <button
          type="button"
          aria-label="Up a semitone"
          onClick={() =>
            setTuning({
              fundamental: midiFrequency(Math.round(69 + 12 * Math.log2(fundamental / 440)) + 1),
            })
          }
        >
          +
        </button>
        <button
          type="button"
          class="ghost"
          onClick={() => playReference(fundamental)}
          title="Play the target pitch"
        >
          Hear target
        </button>
      </div>
      <label class="field wide">
        <span>Partials at</span>
        <span class="input">
          <input
            type="text"
            value={ratioText ?? ratioLabel}
            class={ratioText !== null && !parseRatios(ratioText) ? "bad" : ""}
            onInput={(e) => {
              setRatioText(e.currentTarget.value);
              const parsed = parseRatios(e.currentTarget.value);
              if (parsed) setTuning({ ratios: parsed });
            }}
            onBlur={() => setRatioText(null)}
            spellcheck={false}
          />
          <em>× fundamental</em>
        </span>
      </label>
      <div class="chips">
        {RATIO_SETS.map((set) => (
          <button
            type="button"
            class={set.label === ratioLabel ? "on" : ""}
            onClick={() => setTuning({ ratios: set.ratios })}
          >
            {set.label}
          </button>
        ))}
      </div>
      <Segmented
        label="Which partials the targets count"
        value={d.tuning.family}
        options={[
          { value: "bending", label: "Bending partials" },
          { value: "all", label: "Every partial" },
        ]}
        onChange={(family) => setTuning({ family })}
      />
      <div class="actions">
        <button
          type="button"
          class="primary"
          disabled={progress?.running || !s}
          onClick={state.startTune}
        >
          {progress?.running ? "Cutting…" : cut ? "Tune from this cut" : "Compute the undercut"}
        </button>
        <button
          type="button"
          disabled={!cut || progress?.running}
          onClick={() =>
            state.update({ profile: { ...d.profile, depth: d.profile.depth.map(() => 0) } })
          }
        >
          Uncut blank
        </button>
      </div>
      {progress && (
        <div class="progress">
          <svg viewBox="0 0 200 36" preserveAspectRatio="none" aria-hidden="true">
            {worst.length > 1 && (
              <polyline
                points={worst
                  .map((w, i) => {
                    const y =
                      34 -
                      (32 * (Math.log10(Math.max(w, 0.01)) + 2)) /
                        (Math.log10(Math.max(worst[0], 1)) + 2);
                    return `${(200 * i) / Math.max(1, worst.length - 1)},${Math.max(2, Math.min(34, y)).toFixed(1)}`;
                  })
                  .join(" ")}
              />
            )}
          </svg>
          <p>
            {progress.running
              ? `Step ${Math.max(0, worst.length - 1)}: worst partial ${worst.length ? worst[worst.length - 1].toFixed(1) : "…"} ¢ off`
              : progress.converged
                ? `In tune after ${progress.iterations} steps: every target within ${Math.max(0.1, worst[worst.length - 1] ?? 0).toFixed(1)} ¢.`
                : (progress.note ?? "Stopped short of the targets.")}
          </p>
        </div>
      )}
    </section>
  );
}

function Stage() {
  const canvas = useRef<HTMLCanvasElement>(null);
  const view = useRef<View | null>(null);
  const s = state.solution.value;
  const d = state.design.value;

  useEffect(() => {
    const v = new View(canvas.current!);
    view.current = v;
    v.onStrike = (x, y) => {
      const current = state.solution.value;
      if (current) state.strike(state.nearestNode(current, x, y));
    };
    const key = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (e.code !== "Space" || target.closest("input, select, textarea, button")) return;
      e.preventDefault();
      if (state.solution.value) state.strike(strikeNode());
    };
    window.addEventListener("keydown", key);
    return () => {
      window.removeEventListener("keydown", key);
      v.dispose();
    };
  }, []);

  useEffect(() => {
    if (s) view.current?.setSolution(s, materialOf(s.design));
  }, [s]);

  const shown = state.shownMode.value;
  const struck = state.lastStrike.value;
  const contact = state.contactTime.value;
  useEffect(() => {
    if (shown !== null) view.current?.setMotion({ kind: "mode", index: shown });
    else if (struck && performance.now() - struck.time < 200)
      view.current?.setMotion({
        kind: "strike",
        node: struck.node,
        start: struck.time,
        contactTime: contact,
      });
    else view.current?.setMotion({ kind: "rest" });
  }, [shown, struck]);

  const sand = state.showSand.value;
  const wireframe = state.showMesh.value;
  useEffect(() => view.current?.setOptions({ sand, wireframe }), [sand, wireframe]);

  const mode = s && shown !== null ? s.modes[shown] : null;
  const first = s?.modes.find((m) => m.partial === 0) ?? s?.modes[0];
  return (
    <main class="stage">
      <canvas ref={canvas} />
      <div class="overlay top">
        <div class="title">
          <h2>{d.name}</h2>
          {s && (
            <p>
              {materialOf(d).name} ·{" "}
              {s.mass < 1 ? `${(s.mass * 1000).toFixed(0)} g` : `${s.mass.toFixed(2)} kg`} ·{" "}
              {s.nodes.length / 2} nodes · solved in {s.solveMs.toFixed(0)} ms
            </p>
          )}
        </div>
        <div class={`status${state.busy.value ? " busy" : ""}`}>
          {state.busy.value ? "Solving" : ""}
        </div>
      </div>
      {mode && first ? (
        <div class="overlay readout">
          <strong>{mode.frequency.toFixed(1)} Hz</strong>
          <span>
            {pitchOf(mode.frequency).name} {signed(pitchOf(mode.frequency).cents)} ¢ ·{" "}
            {(mode.frequency / first.frequency).toFixed(2)} × the fundamental
          </span>
        </div>
      ) : (
        <div class="overlay readout quiet">
          <span>Click the piece to strike it there. Drag to turn it. Space strikes again.</span>
        </div>
      )}
      {state.error.value && <div class="overlay error">{state.error.value}</div>}
      <div class="bench">
        <ProfileEditor />
        <Spectrum />
      </div>
    </main>
  );
}

export function App() {
  useEffect(() => state.requestSolve(), []);
  return (
    <div class="app">
      <PiecePanel />
      <Stage />
      <aside class="panel right">
        <TuningPanel />
        <PartialsPanel />
      </aside>
    </div>
  );
}
