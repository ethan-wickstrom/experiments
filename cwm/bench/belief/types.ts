/** Operational forecast at one indexed write. Array slots are roles, not object identities. */
export interface Input {
  setup: string;
  write: string;
  signal: boolean | null;
  index: number;
  before: number[][];
}
export interface Example {
  input: Input;
  after: number[][];
}
export interface Atom {
  state: number[][];
  prob: number;
}
export type Forecast = (x: Input) => Atom[];
