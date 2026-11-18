import {
  type Design,
  buildMesh,
  familyModes,
  materialOf,
  thicknessField,
  type ThicknessField,
} from "../core/design.ts";
import type { Mesh } from "../core/mesh.ts";
import { type Mode, PlateSystem } from "../core/plate.ts";
import { solveDesign, tune } from "../core/tune.ts";
import type { Request, Response, Solution } from "./protocol.ts";

/** The mesh and assembled operators depend only on outline, material and grain; keep them between solves. */
let cache:
  | { key: string; mesh: Mesh; system: PlateSystem; warm?: Float64Array; warmCount: number }
  | undefined;

function systemFor(design: Design, nodeBudget: number) {
  const key = JSON.stringify([design.shape, design.materialId, design.grainAngle, nodeBudget]);
  if (!cache || cache.key !== key) {
    const mesh = buildMesh(design, nodeBudget);
    cache = {
      key,
      mesh,
      system: new PlateSystem(mesh, materialOf(design), (design.grainAngle * Math.PI) / 180),
      warmCount: 0,
    };
  }
  return cache;
}

function package_(
  design: Design,
  mesh: Mesh,
  thickness: Float64Array,
  modes: ReadonlyArray<Mode>,
  solveMs: number,
): Solution {
  const family = familyModes(mesh, modes, design);
  const rho = materialOf(design).rho;
  let mass = 0;
  const { nodes, tris } = mesh;
  for (let e = 0; e < thickness.length; e++) {
    const a = tris[3 * e];
    const b = tris[3 * e + 1];
    const c = tris[3 * e + 2];
    const area =
      0.5 *
      ((nodes[2 * b] - nodes[2 * a]) * (nodes[2 * c + 1] - nodes[2 * a + 1]) -
        (nodes[2 * c] - nodes[2 * a]) * (nodes[2 * b + 1] - nodes[2 * a + 1]));
    mass += rho * area * thickness[e];
  }
  return {
    design,
    nodes: mesh.nodes,
    tris: mesh.tris,
    boundaryEdges: mesh.boundaryEdges,
    thickness,
    modes: modes.map((m, i) => ({
      frequency: m.frequency,
      shape: m.shape,
      partial: family.indexOf(i),
    })),
    mass,
    solveMs,
  };
}

const post = (message: Response) => (self as unknown as Worker).postMessage(message);

self.onmessage = (event: MessageEvent<Request>) => {
  const request = event.data;
  try {
    const start = performance.now();
    const entry = systemFor(request.design, request.nodeBudget);
    const field: ThicknessField = thicknessField(entry.mesh, request.design);
    if (request.type === "solve") {
      const warm = entry.warmCount === request.modeCount ? entry.warm : undefined;
      const { thickness, result } = solveDesign(
        entry.system,
        request.design,
        field,
        request.design.profile.depth,
        request.modeCount,
        warm,
      );
      entry.warm = result.subspace;
      entry.warmCount = request.modeCount;
      post({
        type: "solved",
        id: request.id,
        solution: package_(
          request.design,
          entry.mesh,
          thickness,
          result.modes,
          performance.now() - start,
        ),
      });
      return;
    }
    const result = tune(
      entry.system,
      entry.mesh,
      request.design,
      field,
      request.modeCount,
      (step) =>
        post({
          type: "tuneStep",
          id: request.id,
          iteration: step.iteration,
          depth: step.depth,
          cents: step.cents,
        }),
    );
    entry.warm = undefined;
    const design: Design = {
      ...request.design,
      profile: { ...request.design.profile, depth: result.depth },
    };
    post({
      type: "tuned",
      id: request.id,
      depth: result.depth,
      cents: result.cents,
      converged: result.converged,
      iterations: result.iterations,
      note: result.note,
      solution: package_(
        design,
        entry.mesh,
        result.thickness,
        result.modes,
        performance.now() - start,
      ),
    });
  } catch (error) {
    post({
      type: "error",
      id: request.id,
      message: error instanceof Error ? error.message : String(error),
    });
  }
};
