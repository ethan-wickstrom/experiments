import { useRef } from "preact/hooks";

type Point = readonly [number, number];

function crosses(a: Point, b: Point, c: Point, d: Point): boolean {
  const side = (p: Point, q: Point, r: Point) =>
    Math.sign((q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]));
  return side(a, b, c) !== side(a, b, d) && side(c, d, a) !== side(c, d, b);
}

/** Whether a closed outline has no two edges crossing. */
export function isSimple(points: ReadonlyArray<Point>): boolean {
  const n = points.length;
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      if (j === i + 1 || (i === 0 && j === n - 1)) continue;
      if (crosses(points[i], points[(i + 1) % n], points[j], points[(j + 1) % n])) return false;
    }
  }
  return true;
}

const SIZE = 260;

/** Drag a corner to move it. Double-click an edge to add a corner, a corner to remove it. */
export function OutlineEditor(props: {
  points: ReadonlyArray<Point>;
  onChange: (points: ReadonlyArray<Point>, settle: boolean) => void;
}) {
  const svg = useRef<SVGSVGElement>(null);
  const frozen = useRef<number | null>(null);
  let reach = 0;
  for (const [x, y] of props.points) reach = Math.max(reach, Math.abs(x), Math.abs(y));
  const span = frozen.current ?? Math.ceil((reach * 1.35) / 0.05) * 0.05;
  const toView = ([x, y]: Point): [number, number] => [
    SIZE / 2 + (x / span) * (SIZE / 2),
    SIZE / 2 - (y / span) * (SIZE / 2),
  ];
  const fromEvent = (e: PointerEvent | MouseEvent): Point => {
    const rect = svg.current!.getBoundingClientRect();
    const limit = span * 0.96;
    const x = (((e.clientX - rect.left) / rect.width) * 2 - 1) * span;
    const y = -(((e.clientY - rect.top) / rect.height) * 2 - 1) * span;
    return [Math.max(-limit, Math.min(limit, x)), Math.max(-limit, Math.min(limit, y))];
  };

  const drag = (index: number) => (e: PointerEvent) => {
    e.preventDefault();
    const target = e.currentTarget as SVGElement;
    target.setPointerCapture(e.pointerId);
    frozen.current = span;
    let latest = props.points;
    const move = (ev: PointerEvent) => {
      const next = latest.map((p, i) => (i === index ? fromEvent(ev) : p));
      if (!isSimple(next)) return;
      latest = next;
      props.onChange(next, false);
    };
    const up = () => {
      target.removeEventListener("pointermove", move);
      target.removeEventListener("pointerup", up);
      target.removeEventListener("pointercancel", up);
      frozen.current = null;
      props.onChange(latest, true);
    };
    target.addEventListener("pointermove", move);
    target.addEventListener("pointerup", up);
    target.addEventListener("pointercancel", up);
  };

  const n = props.points.length;
  const view = props.points.map(toView);
  const ticks: number[] = [];
  for (let v = -span + 0.05; v < span - 1e-9; v += 0.05) ticks.push(v);
  return (
    <div class="outline">
      <svg ref={svg} viewBox={`0 0 ${SIZE} ${SIZE}`}>
        {ticks.map((v) => (
          <g class={Math.abs(v) < 1e-9 ? "grid axis" : "grid"}>
            <line x1={toView([v, 0])[0]} x2={toView([v, 0])[0]} y1={0} y2={SIZE} />
            <line y1={toView([0, v])[1]} y2={toView([0, v])[1]} x1={0} x2={SIZE} />
          </g>
        ))}
        <polygon class="shape" points={view.map((p) => p.join(",")).join(" ")} />
        {view.map((p, i) => {
          const q = view[(i + 1) % n];
          return (
            <line
              class="edge"
              x1={p[0]}
              y1={p[1]}
              x2={q[0]}
              y2={q[1]}
              onDblClick={(e) => {
                const next = [
                  ...props.points.slice(0, i + 1),
                  fromEvent(e),
                  ...props.points.slice(i + 1),
                ];
                if (isSimple(next)) props.onChange(next, true);
              }}
            />
          );
        })}
        {view.map((p, i) => (
          <circle
            class="corner"
            cx={p[0]}
            cy={p[1]}
            r={5}
            onPointerDown={drag(i)}
            onDblClick={(e) => {
              e.stopPropagation();
              if (n <= 3) return;
              const next = props.points.filter((_, j) => j !== i);
              if (isSimple(next)) props.onChange(next, true);
            }}
          />
        ))}
      </svg>
      <p class="note">
        Drag a corner. Double-click an edge to add one, a corner to remove it. Grid squares are 50
        mm.
      </p>
    </div>
  );
}
