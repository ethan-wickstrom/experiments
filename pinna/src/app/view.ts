import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import type { Material } from "../core/materials.ts";
import { pulseSpectrum } from "./audio.ts";
import type { Solution } from "./protocol.ts";

/** What the view draws on the piece. */
export type Motion =
  | { readonly kind: "rest" }
  | { readonly kind: "mode"; readonly index: number }
  | {
      readonly kind: "strike";
      readonly node: number;
      readonly start: number;
      readonly contactTime: number;
    };

export interface ViewOptions {
  readonly sand: boolean;
  readonly wireframe: boolean;
}

const OVERLAY_VERTEX = /* glsl */ `
  attribute float amp;
  varying float vAmp;
  varying vec2 vPlane;
  void main() {
    vAmp = amp;
    vPlane = position.xy;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const OVERLAY_FRAGMENT = /* glsl */ `
  precision highp float;
  varying float vAmp;
  varying vec2 vPlane;
  uniform float phase;
  uniform float sand;
  uniform float tint;
  uniform float grain;
  uniform vec3 warm;
  uniform vec3 cool;
  uniform vec3 sandColor;
  float hash(vec2 p) {
    vec3 q = fract(vec3(p.xyx) * 0.1031);
    q += dot(q, q.yzx + 33.33);
    return fract((q.x + q.y) * q.z);
  }
  void main() {
    float a = vAmp * phase;
    vec3 color = mix(cool, warm, step(0.0, a));
    float alpha = tint * smoothstep(0.0, 1.0, abs(a)) * 0.62;
    // Sand gathers where the surface stays still: the nodal lines of the mode.
    float width = fwidth(vAmp);
    float still = 1.0 - smoothstep(0.0, 1.0, abs(vAmp) / max(width * 5.0, 0.035));
    float speck = hash(floor(vPlane * grain));
    float grains = smoothstep(0.35, 1.0, still * (0.55 + 0.9 * speck));
    float s = sand * grains;
    color = mix(color, sandColor * (0.82 + 0.3 * speck), s);
    alpha = max(alpha * (1.0 - s), s * 0.96);
    gl_FragColor = vec4(color, alpha);
  }
`;

export class View {
  readonly canvas: HTMLCanvasElement;
  private readonly renderer: THREE.WebGLRenderer;
  private readonly scene = new THREE.Scene();
  private readonly camera = new THREE.PerspectiveCamera(32, 1, 0.01, 100);
  private readonly controls: OrbitControls;
  private readonly piece = new THREE.Group();
  private readonly body: THREE.MeshStandardMaterial;
  private readonly overlay: THREE.ShaderMaterial;
  private readonly wire: THREE.LineBasicMaterial;
  private readonly marker: THREE.Mesh;
  private readonly ripple: THREE.Mesh;
  private readonly raycaster = new THREE.Raycaster();
  private top: THREE.Mesh | undefined;
  private parts: THREE.Object3D[] = [];
  private solution: Solution | undefined;
  private nodeThickness = new Float32Array(0);
  private sideNodes = new Int32Array(0);
  private displacement = new Float32Array(0);
  private amp = new Float32Array(0);
  private motion: Motion = { kind: "rest" };
  private options: ViewOptions = { sand: true, wireframe: false };
  private scale = 1;
  private extent = 1;
  private outlineKey = "";
  private frame = 0;
  private needsFrame = true;
  private grainTexture: THREE.CanvasTexture | undefined;
  private readonly resizeObserver: ResizeObserver;
  onStrike: (x: number, y: number, velocity: number) => void = () => {};
  onHover: (x: number, y: number) => void = () => {};

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    this.renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.05;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    const pmrem = new THREE.PMREMGenerator(this.renderer);
    this.scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    this.scene.environmentIntensity = 0.55;

    const key = new THREE.DirectionalLight(0xfff1dc, 2.6);
    key.position.set(-2.2, 4.2, 2.6);
    key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048);
    key.shadow.camera.left = -2.2;
    key.shadow.camera.right = 2.2;
    key.shadow.camera.top = 2.2;
    key.shadow.camera.bottom = -2.2;
    key.shadow.camera.near = 0.5;
    key.shadow.camera.far = 12;
    key.shadow.radius = 7;
    key.shadow.bias = -0.0005;
    this.scene.add(key);
    const rim = new THREE.DirectionalLight(0x9fb6ff, 0.7);
    rim.position.set(3, 1.5, -3);
    this.scene.add(rim);

    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(40, 40),
      new THREE.ShadowMaterial({ opacity: 0.42 }),
    );
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.34;
    ground.receiveShadow = true;
    this.scene.add(ground);

    this.body = new THREE.MeshStandardMaterial({ color: 0xffffff, side: THREE.DoubleSide });
    this.overlay = new THREE.ShaderMaterial({
      vertexShader: OVERLAY_VERTEX,
      fragmentShader: OVERLAY_FRAGMENT,
      transparent: true,
      depthWrite: false,
      polygonOffset: true,
      polygonOffsetFactor: -2,
      polygonOffsetUnits: -2,
      uniforms: {
        phase: { value: 0 },
        sand: { value: 0 },
        tint: { value: 0 },
        grain: { value: 900 },
        warm: { value: new THREE.Color("#ff8a4c") },
        cool: { value: new THREE.Color("#4aa8ff") },
        sandColor: { value: new THREE.Color("#f4ead2") },
      },
    });
    this.wire = new THREE.LineBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.16,
      depthWrite: false,
    });

    this.piece.rotation.x = -Math.PI / 2;
    this.scene.add(this.piece);

    this.marker = new THREE.Mesh(
      new THREE.RingGeometry(0.9, 1, 48),
      new THREE.MeshBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.85,
        depthTest: false,
      }),
    );
    this.marker.visible = false;
    this.marker.renderOrder = 5;
    this.piece.add(this.marker);
    this.ripple = new THREE.Mesh(
      new THREE.RingGeometry(0.93, 1, 64),
      new THREE.MeshBasicMaterial({
        color: 0xffd9a8,
        transparent: true,
        opacity: 0,
        depthTest: false,
      }),
    );
    this.ripple.visible = false;
    this.ripple.renderOrder = 5;
    this.piece.add(this.ripple);

    this.camera.position.set(1.9, 1.7, 2.7);
    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.minDistance = 0.8;
    this.controls.maxDistance = 9;
    this.controls.maxPolarAngle = Math.PI * 0.95;
    this.controls.addEventListener("change", () => (this.needsFrame = true));

    let down: { x: number; y: number; t: number } | null = null;
    canvas.addEventListener(
      "pointerdown",
      (e) => (down = { x: e.clientX, y: e.clientY, t: performance.now() }),
    );
    canvas.addEventListener("pointerup", (e) => {
      if (!down) return;
      const moved = Math.hypot(e.clientX - down.x, e.clientY - down.y);
      down = null;
      if (moved > 4) return;
      const hit = this.pick(e);
      if (hit) this.onStrike(hit.x, hit.y, 1);
    });
    canvas.addEventListener("pointermove", (e) => {
      const hit = down ? null : this.pick(e);
      this.marker.visible = hit !== null;
      canvas.style.cursor = hit ? "crosshair" : "grab";
      if (hit) {
        this.marker.position.set(hit.x, hit.y, 0);
        this.onHover(hit.x, hit.y);
      }
      this.needsFrame = true;
    });
    canvas.addEventListener("pointerleave", () => {
      this.marker.visible = false;
      this.needsFrame = true;
    });

    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(canvas.parentElement!);
    this.resize();
    this.frame = requestAnimationFrame(this.tick);
  }

  dispose() {
    cancelAnimationFrame(this.frame);
    this.resizeObserver.disconnect();
    this.controls.dispose();
    this.renderer.dispose();
  }

  private resize() {
    const parent = this.canvas.parentElement!;
    const w = Math.max(1, parent.clientWidth);
    const h = Math.max(1, parent.clientHeight);
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.needsFrame = true;
  }

  private pick(e: PointerEvent): { x: number; y: number } | null {
    if (!this.top) return null;
    const rect = this.canvas.getBoundingClientRect();
    this.raycaster.setFromCamera(
      new THREE.Vector2(
        ((e.clientX - rect.left) / rect.width) * 2 - 1,
        -((e.clientY - rect.top) / rect.height) * 2 + 1,
      ),
      this.camera,
    );
    const hits = this.raycaster.intersectObject(this.top, false);
    if (hits.length === 0) return null;
    const local = this.piece.worldToLocal(hits[0].point.clone());
    return { x: local.x, y: local.y };
  }

  setOptions(options: ViewOptions) {
    this.options = options;
    for (const part of this.parts)
      if (part instanceof THREE.LineSegments) part.visible = options.wireframe;
    this.needsFrame = true;
  }

  setMotion(motion: Motion) {
    this.motion = motion;
    this.needsFrame = true;
  }

  setSolution(solution: Solution, material: Material) {
    this.solution = solution;
    const { nodes, tris, boundaryEdges, thickness } = solution;
    const n = nodes.length / 2;

    // Thickness at a node is the area-weighted mean of the elements around it.
    const sum = new Float64Array(n);
    const weight = new Float64Array(n);
    for (let e = 0; e < tris.length / 3; e++) {
      const a = tris[3 * e];
      const b = tris[3 * e + 1];
      const c = tris[3 * e + 2];
      const area =
        0.5 *
        ((nodes[2 * b] - nodes[2 * a]) * (nodes[2 * c + 1] - nodes[2 * a + 1]) -
          (nodes[2 * c] - nodes[2 * a]) * (nodes[2 * b + 1] - nodes[2 * a + 1]));
      for (const i of [a, b, c]) {
        sum[i] += area * thickness[e];
        weight[i] += area;
      }
    }
    this.nodeThickness = new Float32Array(n);
    for (let i = 0; i < n; i++) this.nodeThickness[i] = sum[i] / weight[i];
    this.displacement = new Float32Array(n);
    this.amp = new Float32Array(n);

    let extent = 0;
    for (let i = 0; i < n; i++)
      extent = Math.max(extent, Math.abs(nodes[2 * i]), Math.abs(nodes[2 * i + 1]));
    this.extent = extent;
    this.scale = 1.25 / extent;
    this.piece.scale.setScalar(this.scale);
    this.marker.scale.setScalar(extent * 0.035);

    for (const part of this.parts) {
      this.piece.remove(part);
      (part as THREE.Mesh).geometry.dispose();
    }
    this.parts = [];

    const topGeometry = new THREE.BufferGeometry();
    topGeometry.setAttribute("position", new THREE.BufferAttribute(new Float32Array(3 * n), 3));
    topGeometry.setAttribute("amp", new THREE.BufferAttribute(this.amp, 1));
    const uv = new Float32Array(2 * n);
    const angle = (solution.design.grainAngle * Math.PI) / 180;
    for (let i = 0; i < n; i++) {
      const x = nodes[2 * i];
      const y = nodes[2 * i + 1];
      uv[2 * i] = (x * Math.cos(angle) + y * Math.sin(angle)) / (2 * extent) + 0.5;
      uv[2 * i + 1] = ((-x * Math.sin(angle) + y * Math.cos(angle)) / (2 * extent)) * 6 + 0.5;
    }
    topGeometry.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
    topGeometry.setIndex(new THREE.BufferAttribute(new Uint32Array(tris), 1));
    const top = new THREE.Mesh(topGeometry, this.body);
    top.castShadow = true;
    this.top = top;

    const bottomGeometry = new THREE.BufferGeometry();
    bottomGeometry.setAttribute("position", new THREE.BufferAttribute(new Float32Array(3 * n), 3));
    bottomGeometry.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
    const reversed = new Uint32Array(tris.length);
    for (let e = 0; e < tris.length / 3; e++) {
      reversed[3 * e] = tris[3 * e];
      reversed[3 * e + 1] = tris[3 * e + 2];
      reversed[3 * e + 2] = tris[3 * e + 1];
    }
    bottomGeometry.setIndex(new THREE.BufferAttribute(reversed, 1));
    const bottom = new THREE.Mesh(bottomGeometry, this.body);
    bottom.castShadow = true;

    // Each boundary edge is its own quad, so the wall is shaded flat against the faces.
    const edges = boundaryEdges.length / 2;
    this.sideNodes = new Int32Array(edges * 4);
    const sideIndex = new Uint32Array(edges * 6);
    const sideUv = new Float32Array(edges * 8);
    for (let e = 0; e < edges; e++) {
      const a = boundaryEdges[2 * e];
      const b = boundaryEdges[2 * e + 1];
      this.sideNodes.set([a, b, b, a], 4 * e);
      sideIndex.set([4 * e, 4 * e + 3, 4 * e + 2, 4 * e, 4 * e + 2, 4 * e + 1], 6 * e);
      for (let k = 0; k < 4; k++) {
        const node = this.sideNodes[4 * e + k];
        sideUv[8 * e + 2 * k] = uv[2 * node];
        sideUv[8 * e + 2 * k + 1] = uv[2 * node + 1] + (k >= 2 ? 0.02 : 0);
      }
    }
    const sideGeometry = new THREE.BufferGeometry();
    sideGeometry.setAttribute(
      "position",
      new THREE.BufferAttribute(new Float32Array(edges * 12), 3),
    );
    sideGeometry.setAttribute("uv", new THREE.BufferAttribute(sideUv, 2));
    sideGeometry.setIndex(new THREE.BufferAttribute(sideIndex, 1));
    const side = new THREE.Mesh(sideGeometry, this.body);
    side.castShadow = true;

    const overlay = new THREE.Mesh(topGeometry, this.overlay);
    overlay.renderOrder = 2;

    const wireIndex = new Uint32Array(tris.length * 2);
    for (let e = 0; e < tris.length / 3; e++)
      for (let k = 0; k < 3; k++)
        wireIndex.set([tris[3 * e + k], tris[3 * e + ((k + 1) % 3)]], 6 * e + 2 * k);
    const wireGeometry = new THREE.BufferGeometry();
    wireGeometry.setAttribute("position", topGeometry.getAttribute("position"));
    wireGeometry.setIndex(new THREE.BufferAttribute(wireIndex, 1));
    const wire = new THREE.LineSegments(wireGeometry, this.wire);
    wire.visible = this.options.wireframe;
    wire.renderOrder = 3;

    this.parts = [top, bottom, side, overlay, wire];
    for (const part of this.parts) this.piece.add(part);

    this.body.color.set(material.color);
    this.body.metalness = material.metalness;
    this.body.roughness = material.roughness;
    this.body.map = material.kind === "wood" ? this.grain() : null;
    this.body.needsUpdate = true;
    this.overlay.uniforms.grain.value = 260 / extent;

    const key = JSON.stringify(solution.design.shape);
    if (key !== this.outlineKey) {
      this.outlineKey = key;
      this.controls.target.set(0, 0, 0);
      this.frameCamera();
    }
    this.needsFrame = true;
  }

  /** Pull the camera back until the whole piece, which spans 2.5 units at most, is in view. */
  private frameCamera() {
    const half = Math.tan((this.camera.fov * Math.PI) / 360);
    const distance = Math.max(1.5 / half, 1.55 / (half * this.camera.aspect));
    this.camera.position.set(1.9, 1.7, 2.7).setLength(distance);
    this.controls.maxDistance = distance * 2.5;
  }

  /** A streaked greyscale texture that multiplies the wood colour; u runs along the grain. */
  private grain(): THREE.CanvasTexture {
    if (this.grainTexture) return this.grainTexture;
    const canvas = document.createElement("canvas");
    canvas.width = 1024;
    canvas.height = 1024;
    const g = canvas.getContext("2d")!;
    g.fillStyle = "#e9e9e9";
    g.fillRect(0, 0, 1024, 1024);
    let seed = 7;
    const random = () => {
      seed = (seed * 1664525 + 1013904223) >>> 0;
      return seed / 4294967296;
    };
    for (let i = 0; i < 520; i++) {
      const y = random() * 1024;
      const shade = Math.floor(120 + random() * 135);
      g.strokeStyle = `rgba(${shade},${shade},${shade},${0.12 + random() * 0.3})`;
      g.lineWidth = 0.5 + random() * 3.5;
      g.beginPath();
      const drift = (random() - 0.5) * 14;
      const wave = random() * 6;
      g.moveTo(0, y);
      for (let x = 0; x <= 1024; x += 64)
        g.lineTo(x, y + (drift * x) / 1024 + wave * Math.sin((2 * Math.PI * x) / 1024));
      g.stroke();
    }
    const texture = new THREE.CanvasTexture(canvas);
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.RepeatWrapping;
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.anisotropy = 8;
    this.grainTexture = texture;
    return texture;
  }

  /** Fill the displacement of every node (metres, exaggerated) for this instant. Returns whether the piece is moving. */
  private animate(now: number): boolean {
    const s = this.solution;
    const u = this.overlay.uniforms;
    if (!s) return false;
    const n = this.displacement.length;
    const reach = this.extent * 0.075;
    const motion = this.motion;
    if (motion.kind === "mode" && s.modes[motion.index]) {
      const shape = s.modes[motion.index].shape;
      let peak = 0;
      for (let i = 0; i < n; i++) peak = Math.max(peak, Math.abs(shape[i]));
      const phase = Math.sin((now / 1000) * 2 * Math.PI * 0.9);
      for (let i = 0; i < n; i++) {
        this.amp[i] = shape[i] / peak;
        this.displacement[i] = this.amp[i] * phase * reach;
      }
      u.phase.value = phase;
      u.tint.value = 1;
      u.sand.value = this.options.sand ? 1 : 0;
      this.ripple.visible = false;
      return true;
    }
    if (motion.kind === "strike") {
      // Slowed so the lowest partial swings about once a second, with the decays
      // of the partials kept in proportion to each other.
      const t = (now - motion.start) / 1000;
      const f0 = s.modes[0].frequency;
      const eta = 0.55;
      let envelope = 0;
      this.displacement.fill(0);
      let norm = 0;
      const weights: number[] = [];
      for (const mode of s.modes) {
        const w =
          (mode.shape[motion.node] * pulseSpectrum(mode.frequency, motion.contactTime)) /
          mode.frequency;
        weights.push(w);
        let peak = 0;
        for (let i = 0; i < n; i++) peak = Math.max(peak, Math.abs(mode.shape[i]));
        norm += Math.abs(w) * peak;
      }
      for (let m = 0; m < s.modes.length; m++) {
        const mode = s.modes[m];
        const ratio = mode.frequency / f0;
        const decay = Math.exp(-eta * Math.sqrt(ratio) * t);
        const c =
          (weights[m] / norm) * decay * Math.sin(2 * Math.PI * 1.1 * ratio * t) * reach * 1.6;
        envelope = Math.max(envelope, decay);
        if (Math.abs(c) < reach * 1e-4) continue;
        for (let i = 0; i < n; i++) this.displacement[i] += c * mode.shape[i];
      }
      for (let i = 0; i < n; i++) this.amp[i] = this.displacement[i] / reach;
      u.phase.value = 1;
      u.tint.value = 0.9;
      u.sand.value = 0;
      const ring = Math.min(1, t / 0.7);
      this.ripple.visible = ring < 1;
      this.ripple.position.set(s.nodes[2 * motion.node], s.nodes[2 * motion.node + 1], 0);
      this.ripple.scale.setScalar(this.extent * (0.03 + 0.22 * ring));
      (this.ripple.material as THREE.MeshBasicMaterial).opacity = 0.8 * (1 - ring) ** 2;
      if (envelope < 0.004) {
        this.motion = { kind: "rest" };
      }
      return true;
    }
    this.displacement.fill(0);
    this.amp.fill(0);
    u.tint.value = 0;
    u.sand.value = 0;
    this.ripple.visible = false;
    return false;
  }

  private writeGeometry() {
    const s = this.solution;
    if (!s || this.parts.length === 0) return;
    const [top, bottom, side] = this.parts as THREE.Mesh[];
    const n = this.displacement.length;
    const topPosition = top.geometry.getAttribute("position") as THREE.BufferAttribute;
    const bottomPosition = bottom.geometry.getAttribute("position") as THREE.BufferAttribute;
    const sidePosition = side.geometry.getAttribute("position") as THREE.BufferAttribute;
    const tp = topPosition.array as Float32Array;
    const bp = bottomPosition.array as Float32Array;
    const sp = sidePosition.array as Float32Array;
    for (let i = 0; i < n; i++) {
      const x = s.nodes[2 * i];
      const y = s.nodes[2 * i + 1];
      tp[3 * i] = x;
      tp[3 * i + 1] = y;
      tp[3 * i + 2] = this.displacement[i];
      bp[3 * i] = x;
      bp[3 * i + 1] = y;
      bp[3 * i + 2] = this.displacement[i] - this.nodeThickness[i];
    }
    for (let k = 0; k < this.sideNodes.length; k++) {
      const node = this.sideNodes[k];
      sp[3 * k] = s.nodes[2 * node];
      sp[3 * k + 1] = s.nodes[2 * node + 1];
      sp[3 * k + 2] = this.displacement[node] - (k % 4 >= 2 ? this.nodeThickness[node] : 0);
    }
    topPosition.needsUpdate = true;
    bottomPosition.needsUpdate = true;
    sidePosition.needsUpdate = true;
    (top.geometry.getAttribute("amp") as THREE.BufferAttribute).needsUpdate = true;
    top.geometry.computeVertexNormals();
    bottom.geometry.computeVertexNormals();
    side.geometry.computeVertexNormals();
    top.geometry.computeBoundingSphere();
  }

  private readonly tick = (now: number) => {
    this.frame = requestAnimationFrame(this.tick);
    const moving = this.animate(now);
    const damping = this.controls.update();
    if (!moving && !damping && !this.needsFrame) return;
    this.needsFrame = moving;
    this.writeGeometry();
    this.renderer.render(this.scene, this.camera);
  };
}
