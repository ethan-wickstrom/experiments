import type { Program } from "../../cwm.ts";

const bodies = [
  {
    id: "p47",
    body: `while (x > y) {
  x = x - y;
}
if (x === y) {
  y = y * 2;
} else {
  x = x + 1;
}
return x + y;`,
    pairs: [
      [9, 3],
      [8, 3],
      [2, 5],
      [4, 4],
    ],
  },
  {
    id: "p18",
    body: `if (x < y) {
  y = y - x;
} else {
  x = x - y;
}
while (y > 2) {
  y = y - 2;
}
return x * y;`,
    pairs: [
      [2, 9],
      [8, 3],
      [1, 3],
      [4, 4],
    ],
  },
  {
    id: "p63",
    body: `while (y > 1) {
  if (x > y) {
    x = x - y;
  } else {
    x = x + 2;
  }
  y = y - 1;
}
return x - y;`,
    pairs: [
      [2, 4],
      [7, 3],
      [6, 1],
      [3, 5],
    ],
  },
  {
    id: "p29",
    body: `while(x>2){x=x-2;} if(x===y){y=y*3;}else{y=y+x;}
return (x+y)*(y-x);`,
    pairs: [
      [6, 2],
      [5, 1],
      [1, 4],
      [8, 3],
    ],
  },
  {
    id: "p85",
    body: `if (
  x * x
  > y + 1
) {
  y = x + y;
} else {
  y = (y - x) * 2;
}
while (x > 1) {
  x = x - 1;
}
return (
  y * x
  - (x + 1)
);`,
    pairs: [
      [3, 2],
      [2, 5],
      [1, 3],
      [4, 6],
    ],
  },
  {
    id: "p36",
    body: `while (y > x + 1) {
  y = y - 2;
}
if (x === y) {
  x = x * (y + 1);
} else {
  y = (y + y);
}
return (x - y) * (x + y);`,
    pairs: [
      [2, 8],
      [2, 7],
      [5, 3],
      [4, 4],
    ],
  },
  {
    id: "p72",
    body: `if (x > y) {
  while (x > y + 1) {
    x = x - 2;
  }
} else {
  while (x < y) {
    x = x + 1;
  }
}
return x + (y - x) * y;`,
    pairs: [
      [9, 2],
      [4, 3],
      [2, 6],
      [5, 5],
    ],
  },
];

export const blind: Program[] = bodies.flatMap(({ id, body, pairs }) => {
  const entry = id + ".ts";
  return pairs.map((args) => ({
    entry,
    fn: "run",
    args,
    files: { [entry]: `export function run(x:number, y:number) {\n${body}\n}` },
  }));
});
