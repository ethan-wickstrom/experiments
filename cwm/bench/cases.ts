import type { Program } from "../cwm.ts";

// Split by source before collecting labels. Each body is a distinct program, not a rename.
const familiar = {
  affine: "return 2*x - 3*y + 7;",
  product: "return x*y;",
  clamp: "return Math.max(-2, Math.min(x,y));",
  parity: "return (x & 1) === (y & 1);",
  sign: "if (x < 0) return -1;\nif (x > 0) return 1;\nreturn 0;",
  power: "return x ** Math.abs(y);",
  quotient: "if (!y) throw 'zero';\nreturn Math.trunc(x/y);",
  swap: "let a=x, b=y;\n[a,b]=[b,a];\nreturn [a,b];",
  prefix: "let a=[];\nfor(let i=0;i<Math.abs(x);i++) a.push(y+i);\nreturn a;",
  format: "return x.toString(16) + ':' + y.toString(16);",
  repeat: "return String(y).repeat(Math.abs(x));",
  dict: "const o:Record<string,number>={};\no[String(x)]=1;\no[String(y)]=(o[String(y)]??0)+1;\nreturn o;",
  search: "return [x,0,1].indexOf(y);",
  gcd: "let a=Math.abs(x), b=Math.abs(y);\nwhile(b) [a,b]=[b,a%b];\nreturn a;",
  countdown: "return x <= 0 ? y : run(x-1,y+2);",
  closure: "const shift=(v:number)=>v+y;\nreturn shift(x);",
  sum: "let n=0;\nfor (const v of [x,y,x]) n+=v;\nreturn n;",
  select: "switch(x){case 0:return y;case 1:return -y;default:return x;}",
  finally: "try {return x;} finally {if(y>0) return y;}",
  sort: "return [x,y,0].sort((a,b)=>a-b);",
  slice: "return [y,x,0,1].slice(x,y);",
  destructure: "const [a,...rest]=[x,y,x];\nreturn {a,rest};",
  path: "const a={next:y?{n:x}:null};\nreturn a.next?.n ?? 7;",
  reverse: "return Array.from(String(x)+String(y)).reverse().join('');",
};
const novel = {
  euclideanDistance: "return Math.hypot(x,y);",
  collatz: "let n=Math.abs(x)+1;\nlet k=0;\nwhile(n!==1){n=n%2===0?n/2:3*n+1;k++;}\nreturn k+y;",
  histogram: "const a=[0,0];\nfor(const n of [x,y]) a[Math.abs(n)%2]++;\nreturn a;",
  exceptionRecovery: "try {if(x<0)throw y; return x;} catch(e){return {caught:e};}",
  binaryEncoding: "return (x>>>0).toString(2).padStart(Math.abs(y),'0');",
  palindrome:
    "const s=String(Math.abs(x))+String(Math.abs(y));\nreturn s===Array.from(s).reverse().join('');",
  interleave: "return [x,y].flatMap(n=>[n,-n]);",
  fibonacci: "function f(n:number):number{return n<2?n:f(n-1)+f(n-2);}\nreturn f(Math.abs(x))+y;",
};

export type Split = "train" | "new-input" | "new-source";
export function* cases() {
  for (const [family, body] of Object.entries({ ...familiar, ...novel })) {
    const entry = family + ".ts";
    const files = { [entry]: `export function run(x:number,y:number){\n${body}\n}` };
    for (let i = 0; i < 32; i++) {
      const x = (i % 8) - 4,
        y = Math.floor(i / 8) - 2;
      const split: Split = Object.hasOwn(novel, family)
        ? "new-source"
        : (x + y) % 4 === 0
          ? "new-input"
          : "train";
      yield { family, split, program: { entry, files, fn: "run", args: [x, y] } satisfies Program };
    }
  }
}
