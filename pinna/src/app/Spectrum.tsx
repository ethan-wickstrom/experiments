import * as state from "./state.ts";
import { useWidth } from "./useWidth.ts";

const H = 132;
const PAD = 28;
const BASE = 104;

/** Where the partials fall on a logarithmic frequency axis, against the tuning targets. */
export function Spectrum() {
  const s = state.solution.value;
  const d = state.design.value;
  const [svg, W] = useWidth<SVGSVGElement>(640);
  if (!s || s.modes.length === 0)
    return (
      <div class="spectrum">
        <svg ref={svg} />
      </div>
    );
  const targets = d.tuning.ratios.map((r) => r * d.tuning.fundamental).filter((t) => t > 0);
  const low = Math.min(s.modes[0].frequency, ...targets) / 1.25;
  const high = Math.max(s.modes[s.modes.length - 1].frequency, ...targets) * 1.1;
  const xOf = (f: number) => PAD + ((W - 2 * PAD) * Math.log(f / low)) / Math.log(high / low);
  const shown = state.shownMode.value;
  const octaves: number[] = [];
  for (let f = 27.5; f < high; f *= 2) if (f > low) octaves.push(f);
  return (
    <div class="spectrum">
      <div class="caption">
        <h3>Spectrum</h3>
        <span>Log scale. Arrows mark the targets.</span>
      </div>
      <svg
        ref={svg}
        viewBox={`0 0 ${W} ${H}`}
        onPointerLeave={() => (state.hoveredMode.value = null)}
      >
        {octaves.map((f) => (
          <g class="octave">
            <line x1={xOf(f)} x2={xOf(f)} y1={BASE} y2={BASE + 5} />
            <text x={xOf(f)} y={BASE + 18}>
              A{Math.round(Math.log2(f / 27.5))}
            </text>
          </g>
        ))}
        <line class="base" x1={PAD} x2={W - PAD} y1={BASE} y2={BASE} />
        {targets.map((t) => (
          <path class="target" d={`M ${xOf(t) - 5} 14 L ${xOf(t) + 5} 14 L ${xOf(t)} 23 Z`} />
        ))}
        {s.modes.map((m, i) => {
          const tuned = m.partial >= 0 && m.partial < targets.length;
          const height = tuned ? 76 : d.tuning.family === "bending" && m.partial < 0 ? 30 : 52;
          return (
            <g
              class={`partial${tuned ? " tuned" : ""}${shown === i ? " on" : ""}`}
              onPointerEnter={() => (state.hoveredMode.value = i)}
              onClick={() => (state.selectedMode.value = state.selectedMode.value === i ? null : i)}
            >
              <rect x={xOf(m.frequency) - 5} y={BASE - 80} width={10} height={80} />
              <line x1={xOf(m.frequency)} x2={xOf(m.frequency)} y1={BASE} y2={BASE - height} />
            </g>
          );
        })}
      </svg>
    </div>
  );
}
