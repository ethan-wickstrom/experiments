type Turn = {
  path: string;
  goal: string;
  visible: Record<string, string>;
  accept: string;
};

export const spliceHeld: { id: string; files: Record<string, string>; turns: Turn[] }[] = [
  {
    id: "copy-counter",
    files: {
      "stock.ts": `export interface Job {
  pages: number;
  copies: number;
  duplex: boolean;
}

export function countSheets(job: Job): number {
  const sides = job.duplex ? 2 : 1;
  const sheets = Math.ceil((job.pages * job.copies) / sides);
  return sheets;
}
`,
      "rates.ts": `export function stockRate(quantity: number): number {
  return quantity >= 40 ? 5 : 8;
}
`,
      "quote.ts": `import { countSheets, type Job } from "./stock.ts";
import { stockRate } from "./rates.ts";

export function quote(job: Job) {
  const sheets = countSheets(job);
  const centsPerSheet = stockRate(job.copies);
  return { sheets, paperCents: sheets * centsPerSheet, setupCents: 120 };
}
`,
    },
    turns: [
      {
        path: "stock.ts",
        goal: "Update stock.ts for separately bound copies: every copy must start on a fresh sheet, even when the previous copy ends on the front. Keep single-sided jobs unchanged.",
        visible: {
          "binding.test.ts": `import { strictEqual } from "node:assert";
import { test } from "node:test";
import { quote } from "./quote.ts";

test("stock for three separately bound five-page booklets", () => {
  strictEqual(quote({ pages: 5, copies: 3, duplex: true }).sheets, 9);
});

test("three sets of single-sided handouts", () => {
  strictEqual(quote({ pages: 5, copies: 3, duplex: false }).sheets, 15);
});
`,
        },
        accept: `import { deepStrictEqual, strictEqual } from "node:assert";
import { test } from "node:test";
import { countSheets } from "./stock.ts";
import { quote } from "./quote.ts";

test("each one-page invitation needs its own stock", () => {
  deepStrictEqual(quote({ pages: 1, copies: 7, duplex: true }), {
    sheets: 7, paperCents: 56, setupCents: 120,
  });
});

test("two-sided price lists use both sides within each copy", () => {
  strictEqual(countSheets({ pages: 9, copies: 4, duplex: true }), 20);
  strictEqual(countSheets({ pages: 8, copies: 4, duplex: true }), 16);
});

test("a simplex order consumes one sheet for each impression", () => {
  strictEqual(countSheets({ pages: 7, copies: 2, duplex: false }), 14);
});
`,
      },
      {
        path: "quote.ts",
        goal: "Update quote.ts so bulk paper pricing starts at forty physical sheets in a job, regardless of how many copies were ordered. Keep the setup charge separate and unchanged.",
        visible: {
          "pricing.test.ts": `import { strictEqual } from "node:assert";
import { test } from "node:test";
import { quote } from "./quote.ts";

test("a forty-sheet order earns bulk pricing", () => {
  strictEqual(quote({ pages: 8, copies: 5, duplex: false }).paperCents, 200);
});

test("a thirty-sheet order stays at the regular price", () => {
  strictEqual(quote({ pages: 6, copies: 5, duplex: false }).paperCents, 240);
});
`,
        },
        accept: `import { deepStrictEqual } from "node:assert";
import { test } from "node:test";
import { quote } from "./quote.ts";

test("odd-length duplex booklets fill an order at the threshold", () => {
  deepStrictEqual(quote({ pages: 3, copies: 20, duplex: true }), {
    sheets: 40, paperCents: 200, setupCents: 120,
  });
});

test("lots of printed sides can still be one sheet short of bulk", () => {
  deepStrictEqual(quote({ pages: 5, copies: 13, duplex: true }), {
    sheets: 39, paperCents: 312, setupCents: 120,
  });
});

test("a single simplex manuscript can qualify", () => {
  deepStrictEqual(quote({ pages: 61, copies: 1, duplex: false }), {
    sheets: 61, paperCents: 305, setupCents: 120,
  });
});
`,
      },
    ],
  },
  {
    id: "intake-desk",
    files: {
      "directory.ts": `export interface Queue {
  alias: string;
  owner: string;
  accepting: boolean;
}

function lookupKey(alias: string): string {
  return alias.trim();
}

export function findQueue(queues: Queue[], alias: string) {
  const key = lookupKey(alias);
  return queues.find((queue) => lookupKey(queue.alias) === key);
}
`,
      "dispatch.ts": `import { findQueue, type Queue } from "./directory.ts";

export function routeTicket(queues: Queue[], alias: string, fallback: string) {
  const queue = findQueue(queues, alias);
  const owner = queue ? queue.owner : fallback;
  return { owner, queue: queue?.alias ?? null };
}
`,
    },
    turns: [
      {
        path: "directory.ts",
        goal: "In directory.ts, make queue aliases match regardless of capitalization. Keep ignoring surrounding spaces, and keep the original queue spelling on receipts.",
        visible: {
          "alias.test.ts": `import { deepStrictEqual } from "node:assert";
import { test } from "node:test";
import { routeTicket } from "./dispatch.ts";

const queues = [{ alias: "Studio", owner: "Nell", accepting: true }];

test("a ticket typed in capitals reaches Studio", () => {
  deepStrictEqual(routeTicket(queues, " STUDIO ", "Intake"), {
    owner: "Nell", queue: "Studio",
  });
});

test("an unknown queue still goes to Intake", () => {
  deepStrictEqual(routeTicket(queues, "Stage", "Intake"), {
    owner: "Intake", queue: null,
  });
});
`,
        },
        accept: `import { deepStrictEqual, strictEqual } from "node:assert";
import { test } from "node:test";
import { findQueue } from "./directory.ts";
import { routeTicket } from "./dispatch.ts";

const queues = [
  { alias: "NW", owner: "Morgan", accepting: true },
  { alias: "  North Wing ", owner: "Lee", accepting: true },
];

test("both alias spellings can mix capital and small letters", () => {
  deepStrictEqual(routeTicket(queues, " nORTH wING", "Desk"), {
    owner: "Lee", queue: "  North Wing ",
  });
});

test("existing short aliases still resolve", () => {
  strictEqual(findQueue(queues, " NW ")?.owner, "Morgan");
});

test("internal spacing is part of the alias", () => {
  deepStrictEqual(routeTicket(queues, "NorthWing", "Desk"), {
    owner: "Desk", queue: null,
  });
});
`,
      },
      {
        path: "dispatch.ts",
        goal: "In dispatch.ts, send tickets for queues that aren't accepting work to the fallback owner. Keep the matched queue on the receipt so the desk knows where the ticket was meant to go; leave open and unknown queues alone.",
        visible: {
          "paused.test.ts": `import { deepStrictEqual } from "node:assert";
import { test } from "node:test";
import { routeTicket } from "./dispatch.ts";

test("a paused queue is identified but doesn't get the assignment", () => {
  const queues = [{ alias: "Repairs", owner: "Kai", accepting: false }];
  deepStrictEqual(routeTicket(queues, "Repairs", "Walk-in"), {
    owner: "Walk-in", queue: "Repairs",
  });
});
`,
        },
        accept: `import { deepStrictEqual } from "node:assert";
import { test } from "node:test";
import { routeTicket } from "./dispatch.ts";

const queues = [
  { alias: "Mail Room", owner: "Sam", accepting: true },
  { alias: "West Dock", owner: "Vic", accepting: false },
];

test("an after-hours ticket names the closed dock but reaches the duty desk", () => {
  deepStrictEqual(routeTicket(queues, "  west DOCK", "Night"), {
    owner: "Night", queue: "West Dock",
  });
});

test("a staffed queue still takes its own tickets", () => {
  deepStrictEqual(routeTicket(queues, "mail ROOM ", "Night"), {
    owner: "Sam", queue: "Mail Room",
  });
});

test("no matched queue is different from a matched but paused queue", () => {
  deepStrictEqual(routeTicket(queues, "Dock", "Weekend"), {
    owner: "Weekend", queue: null,
  });
});
`,
      },
    ],
  },
];
