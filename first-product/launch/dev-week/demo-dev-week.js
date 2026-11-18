// A sample developer's home folder on a Monday, and on the Friday after a week of work with coding
// agents. The projects are made up and generated the same way on every load from fixed seeds, so
// the two maps match wherever nothing changed, and no one's own files are ever in them. Folder
// names follow the tools that make them; sizes are typical of what developers report, not measured.
// Kinds are indices into KINDS in map.js.
const APPS = 0, IMAGES = 2, AUDIO = 3, DOCUMENTS = 4, ARCHIVES = 5, DISK_IMAGES = 6, CODE = 7, SYSTEM = 8, CACHES = 9, OTHER = 10;
const KB = 1e3, MB = 1e6, GB = 1e9;

// A random source seeded from a key, such as a folder's path, so the same key gives the same files
// on both days.
function seeded(key) {
  let seed = 11;
  for (let i = 0; i < key.length; i++) seed = Math.imul(seed ^ key.charCodeAt(i), 2654435761) | 0;
  return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}

const F = (name, children) => ({ name, children });
const f = (name, size, kind) => ({ name, size: Math.round(size), kind });
// n files named stem01, stem02…, sized between a and b bytes, spread evenly on a log scale. The
// first n files of a key are the same whatever n is, so a folder can grow by adding files.
const many = (key, n, stem, ext, kind, a, b) => {
  const r = seeded(key);
  return Array.from({ length: n }, (_, i) => f(stem + String(i + 1).padStart(2, '0') + (ext ? '.' + ext : ''), Math.exp(Math.log(a) + r() * (Math.log(b) - Math.log(a))), kind));
};

// A Next.js checkout: its source, its own node_modules and its .next build cache.
const nextCheckout = (key, builds) => [
  F('src', many(key + '/src', 140, 'module', 'tsx', CODE, 2 * KB, 60 * KB)),
  F('public', many(key + '/public', 24, 'image', 'png', IMAGES, 20 * KB, 900 * KB)),
  F('node_modules', Array.from({ length: 60 }, (_, i) => F('package-' + String(i + 1).padStart(2, '0'), many(key + '/node_modules/' + i, 40, 'file', 'js', CODE, 2 * KB, 2 * MB)))),
  F('.next', [F('cache', many(key + '/next', 30 * builds, 'chunk', 'pack', CACHES, 1 * MB, 30 * MB))]),
];

// day 0 is Monday, day 1 is Friday.
function home(day) {
  const friday = day === 1;
  const worktrees = friday
    ? ['add-teams', 'onboarding-flow', 'dark-mode', 'search-index', 'stripe-webhooks', 'perf-pass']
    : ['fix-billing'];
  return F('Home', [
    F('Code', [
      F('app', [
        ...nextCheckout('app', friday ? 3 : 2),
        F('.claude', [F('worktrees', worktrees.map((w, i) => F(w, nextCheckout('worktree-' + w, 1 + (i % 3)))))]),
      ]),
      F('api', [
        F('src', many('api/src', 90, 'module', 'rs', CODE, 3 * KB, 80 * KB)),
        F('target', [
          F('debug', [
            F('deps', many('api/target/debug/deps', friday ? 560 : 240, 'lib', 'rlib', CODE, 2 * MB, 140 * MB)),
            F('incremental', Array.from({ length: friday ? 120 : 50 }, (_, i) => F('api-' + (1000 + i * 7).toString(36), many('api/incremental/' + i, 12, 'query', 'bin', CACHES, 1 * MB, 40 * MB)))),
          ]),
          ...(friday ? [F('release', [F('deps', many('api/target/release/deps', 160, 'lib', 'rlib', CODE, 2 * MB, 120 * MB))])] : []),
        ]),
      ]),
      F('ios-app', [F('Sources', many('ios/src', 80, 'View', 'swift', CODE, 2 * KB, 40 * KB)), F('Assets.xcassets', many('ios/assets', 40, 'image', 'png', IMAGES, 40 * KB, 2 * MB))]),
      F('experiments', Array.from({ length: 5 }, (_, i) => F('prototype-' + (i + 1), [F('node_modules', many('proto/' + i, 120, 'file', 'js', CODE, 2 * KB, 3 * MB))]))),
    ]),
    F('Library', [
      F('Developer', [
        F('Xcode', [
          F('DerivedData', [F('App-gdyobkreqzchlzbfnmkqsmhkvgtr', [
            F('Build', many('xcode/build', friday ? 260 : 170, 'Intermediate', 'o', CODE, 1 * MB, 60 * MB)),
            F('Index.noindex', many('xcode/index', friday ? 70 : 50, 'Index', 'idx', CODE, 4 * MB, 90 * MB)),
          ])]),
          F('iOS DeviceSupport', [F('iPhone18,1 27.0 (24A335)', many('xcode/devicesupport', 50, 'Symbols', 'dylib', CODE, 10 * MB, 120 * MB))]),
        ]),
        F('CoreSimulator', [F('Devices', (friday ? ['iPhone 17', 'iPhone 17 Pro', 'iPhone Air', 'iPad Pro 13-inch', 'iPhone 17e'] : ['iPhone 17', 'iPhone 17 Pro', 'iPhone Air'])
          .map((d) => F(d, many('sim/' + d, 30, 'data', '', OTHER, 10 * MB, 200 * MB))))]),
      ]),
      F('Containers', [F('com.docker.docker', [F('Data', [F('vms', [F('0', [F('data', [f('Docker.raw', friday ? 31 * GB : 22 * GB, DISK_IMAGES)])])])])])]),
      F('Caches', [
        F('ms-playwright', (friday ? ['chromium-1194', 'chromium_headless_shell-1194', 'chromium-1200', 'chromium_headless_shell-1200'] : ['chromium-1194', 'chromium_headless_shell-1194'])
          .map((b) => F(b, many('playwright/' + b, 40, 'part', '', APPS, 1 * MB, 60 * MB)))),
        F('Homebrew', many('brew', 40, 'download', 'tar.gz', ARCHIVES, 2 * MB, 150 * MB)),
        ...Array.from({ length: 16 }, (_, i) => F('com.app' + (i + 1), many('caches/' + i, 20, 'cache', 'db', CACHES, 50 * KB, 30 * MB))),
      ]),
      F('Application Support', [F('Slack', many('slack', 50, 'blob', 'dat', SYSTEM, 200 * KB, 40 * MB)), F('Code', many('vscode', 60, 'state', 'db', SYSTEM, 100 * KB, 30 * MB))]),
    ]),
    F('.cache', [F('huggingface', [F('hub', [
      F('models--meta-llama--Llama-3.1-8B-Instruct', many('hf/llama', 4, 'model-0000', 'safetensors', OTHER, 3.6 * GB, 4.9 * GB)),
      ...(friday ? [F('models--mlx-community--Qwen3-30B-A3B-4bit', many('hf/qwen', 4, 'model-0000', 'safetensors', OTHER, 3.9 * GB, 4.6 * GB))] : []),
    ])])]),
    F('.ollama', [F('models', [F('blobs', many('ollama', 3, 'sha256-blob', '', OTHER, 2.2 * GB, 4.7 * GB))])]),
    F('.npm', [F('_cacache', many('npm', friday ? 1500 : 1300, 'content', '', CACHES, 20 * KB, 8 * MB))]),
    F('.cargo', [F('registry', many('cargo', friday ? 1100 : 950, 'crate', 'crate', ARCHIVES, 10 * KB, 6 * MB))]),
    F('.claude', [F('projects', [F('-Users-you-Code-app', many('claude/transcripts', friday ? 260 : 120, 'session', 'jsonl', DOCUMENTS, 200 * KB, 30 * MB))])]),
    F('.codex', [F('sessions', many('codex/sessions', friday ? 140 : 70, 'rollout', 'jsonl', DOCUMENTS, 100 * KB, 20 * MB))]),
    F('Documents', many('docs', 80, 'Notes', 'pdf', DOCUMENTS, 100 * KB, 25 * MB)),
    F('Desktop', many('desktop', friday ? 70 : 52, 'Screenshot', 'png', IMAGES, 300 * KB, 6 * MB)),
    F('Downloads', [...many('downloads/dmg', friday ? 5 : 4, 'Installer', 'dmg', DISK_IMAGES, 200 * MB, 2 * GB), ...many('downloads/zip', 14, 'Archive', 'zip', ARCHIVES, 5 * MB, 600 * MB)]),
    F('Music', many('music', 120, 'Track ', 'm4a', AUDIO, 4 * MB, 12 * MB)),
    F('Pictures', many('pictures', 400, 'IMG_', 'heic', IMAGES, 1.5 * MB, 8 * MB)),
  ]);
}

export function makeDevWeek() {
  return { before: home(0), after: home(1) };
}
