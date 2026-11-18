import type { Design } from "../core/design.ts";

export interface SolvedMode {
  readonly frequency: number;
  readonly shape: Float32Array;
  /** Position among the partials the tuning counts through, or −1. */
  readonly partial: number;
}

export interface Solution {
  readonly design: Design;
  readonly nodes: Float64Array;
  readonly tris: Int32Array;
  readonly boundaryEdges: Int32Array;
  /** Thickness of each element, metres. */
  readonly thickness: Float64Array;
  readonly modes: ReadonlyArray<SolvedMode>;
  readonly mass: number;
  readonly solveMs: number;
}

export type Request =
  | {
      readonly type: "solve";
      readonly id: number;
      readonly design: Design;
      readonly nodeBudget: number;
      readonly modeCount: number;
    }
  | {
      readonly type: "tune";
      readonly id: number;
      readonly design: Design;
      readonly nodeBudget: number;
      readonly modeCount: number;
    };

export type Response =
  | { readonly type: "solved"; readonly id: number; readonly solution: Solution }
  | {
      readonly type: "tuneStep";
      readonly id: number;
      readonly iteration: number;
      readonly depth: number[];
      readonly cents: number[];
    }
  | {
      readonly type: "tuned";
      readonly id: number;
      readonly depth: number[];
      readonly cents: number[];
      readonly converged: boolean;
      readonly iterations: number;
      readonly note?: string;
      readonly solution: Solution;
    }
  | { readonly type: "error"; readonly id: number; readonly message: string };
