import { MAX_DEPTH, depthAt } from "../core/design.ts";
import * as state from "./state.ts";
import { useWidth } from "./useWidth.ts";

const H = 132;
const PAD_X = 28;
const TOP = 26;
const BODY = 78;

/**
 * The piece in cross-section, thickness exaggerated. The handles are the
 * control values of the cut, mirrored about the centre; drag one to carve by hand.
 */
export function ProfileEditor() {
  const d = state.design.value;
  const [svg, W] = useWidth<SVGSVGElement>(640);
  const stations = d.profile.depth.length;
  const xOf = (u: number) => PAD_X + ((u + 1) / 2) * (W - 2 * PAD_X);
  const yOf = (depth: number) => TOP + BODY * (1 - depth);

  const samples = 160;
  let path = `M ${xOf(-1)} ${TOP} L ${xOf(1)} ${TOP}`;
  for (let i = samples; i >= 0; i--) {
    const u = -1 + (2 * i) / samples;
    path += ` L ${xOf(u).toFixed(2)} ${yOf(depthAt(d.profile.depth, d.profile.axis === "axial" ? u : Math.abs(u))).toFixed(2)}`;
  }
  path += " Z";

  const drag = (k: number) => (e: PointerEvent) => {
    e.preventDefault();
    const target = e.currentTarget as SVGElement;
    target.setPointerCapture(e.pointerId);
    const move = (ev: PointerEvent) => {
      const rect = svg.current!.getBoundingClientRect();
      const y = ((ev.clientY - rect.top) / rect.height) * H;
      const value = Math.min(MAX_DEPTH, Math.max(0, 1 - (y - TOP) / BODY));
      const current = state.design.value;
      state.update({
        profile: {
          ...current.profile,
          depth: current.profile.depth.map((v, i) => (i === k ? value : v)),
        },
      });
    };
    const up = () => {
      target.removeEventListener("pointermove", move);
      target.removeEventListener("pointerup", up);
      target.removeEventListener("pointercancel", up);
    };
    target.addEventListener("pointermove", move);
    target.addEventListener("pointerup", up);
    target.addEventListener("pointercancel", up);
  };

  const deepest = Math.max(...d.profile.depth);
  const handles: Array<{ k: number; u: number }> = [];
  for (let k = 0; k < stations; k++) {
    const u = k / (stations - 1);
    handles.push({ k, u });
    if (k > 0) handles.push({ k, u: -u });
  }
  return (
    <div class="profile">
      <div class="caption">
        <h3>Undercut</h3>
        <span>
          {deepest > 0
            ? `${(deepest * d.thickness * 1000).toFixed(1)} mm deep at most, of ${(d.thickness * 1000).toFixed(1)} mm`
            : "Uncut. Drag a handle to carve."}
        </span>
        <div class="axis">
          <button
            type="button"
            class={d.profile.axis === "axial" ? "on" : ""}
            onClick={() => state.update({ profile: { ...d.profile, axis: "axial" } })}
          >
            Along length
          </button>
          <button
            type="button"
            class={d.profile.axis === "radial" ? "on" : ""}
            onClick={() => state.update({ profile: { ...d.profile, axis: "radial" } })}
          >
            From centre
          </button>
        </div>
      </div>
      <svg ref={svg} viewBox={`0 0 ${W} ${H}`}>
        <line class="limit" x1={xOf(-1)} x2={xOf(1)} y1={yOf(MAX_DEPTH)} y2={yOf(MAX_DEPTH)} />
        <path class="section" d={path} />
        {handles.map(({ k, u }) => (
          <g class="handle" onPointerDown={drag(k)}>
            <line x1={xOf(u)} x2={xOf(u)} y1={yOf(0)} y2={yOf(d.profile.depth[k])} />
            <rect x={xOf(u) - 14} y={TOP - 8} width={28} height={BODY + 16} />
            <circle cx={xOf(u)} cy={yOf(d.profile.depth[k])} r={4.5} />
          </g>
        ))}
      </svg>
    </div>
  );
}
