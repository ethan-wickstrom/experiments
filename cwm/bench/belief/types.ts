import * as S from "effect/Schema";

export const list = <A extends S.Top>(item: A) => S.mutable(S.Array(item));
export const State = list(list(S.Int));
export const Input = S.Struct({
  setup: S.String,
  write: S.String,
  signal: S.NullOr(S.Boolean),
  index: S.Int,
  before: State,
});
export const Example = S.Struct({ input: Input, after: State });
export const Atom = S.Struct({ state: State, prob: S.mutableKey(S.Finite) });
export type Input = typeof Input.Type;
export type Example = typeof Example.Type;
export type Atom = typeof Atom.Type;
export type Forecast = (x: Input) => Atom[];
export const digest = (inputs: Input[]) =>
  new Bun.CryptoHasher("sha256")
    .update(JSON.stringify(inputs.map((x) => [x.setup, x.write, x.signal, x.index, x.before])))
    .digest("hex");
export const Bundle = S.Struct({
  digest: S.String,
  models: list(S.Struct({ name: S.String, predictions: list(list(Atom)) })),
});
export const Labels = S.Struct({ digest: S.String, states: list(State) });
export const strict = { onExcessProperty: "error" } as const;
