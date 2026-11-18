const predicates: Record<string, (a: number, b: number) => boolean> = {
  never: () => false,
  always: () => true,
  lt: (a, b) => a < b,
  le: (a, b) => a <= b,
  gt: (a, b) => a > b,
  ge: (a, b) => a >= b,
  eq: (a, b) => a === b,
  ne: (a, b) => a !== b,
};
export function unique<T>(values: T[]): T | undefined {
  return values.length && values.every((v) => v === values[0]) ? values[0] : undefined;
}
export type GuardRows = Map<string, { x: number; y: number; arm: boolean }[]>;
export function fitGuards(guards: GuardRows) {
  const rules = new Map(
    [...guards].map(([token, rs]) => [
      token,
      Object.keys(predicates).filter((k) => rs.every((r) => predicates[k]!(r.x, r.y) === r.arm)),
    ]),
  );
  return {
    rules,
    decide(this: void, token: string, x: number, y: number) {
      return unique((rules.get(token) ?? []).map((k) => predicates[k]!(x, y)));
    },
  };
}
