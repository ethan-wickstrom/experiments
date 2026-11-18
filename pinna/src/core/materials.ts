/**
 * Elastic and damping constants of a plate material. Axis 1 is the grain (or
 * rolling) direction, axis 2 lies across it in the plate, axis 3 is through the
 * thickness. Isotropic materials repeat their constants.
 */
export interface Material {
  readonly id: string;
  readonly name: string;
  readonly kind: "metal" | "wood" | "glass";
  /** Young's moduli, Pa. */
  readonly E1: number;
  readonly E2: number;
  /** Major in-plane Poisson ratio. */
  readonly nu12: number;
  /** In-plane and transverse shear moduli, Pa. */
  readonly G12: number;
  readonly G13: number;
  readonly G23: number;
  /** Density, kg/m³. */
  readonly rho: number;
  /** Loss factor (1/Q) of the material itself. */
  readonly eta: number;
  /** Surface colour used to draw it. */
  readonly color: string;
  readonly metalness: number;
  readonly roughness: number;
}

function isotropic(
  id: string,
  name: string,
  kind: Material["kind"],
  E: number,
  nu: number,
  rho: number,
  eta: number,
  color: string,
  metalness: number,
  roughness: number,
): Material {
  const G = E / (2 * (1 + nu));
  return {
    id,
    name,
    kind,
    E1: E,
    E2: E,
    nu12: nu,
    G12: G,
    G13: G,
    G23: G,
    rho,
    eta,
    color,
    metalness,
    roughness,
  };
}

/**
 * Nominal handbook values. Wood varies by tens of percent between boards, and
 * loss factors depend on frequency, humidity and temper, so treat these as a
 * starting point and measure the blank when it matters.
 */
export const MATERIALS: ReadonlyArray<Material> = [
  {
    id: "rosewood",
    name: "Honduras rosewood",
    kind: "wood",
    E1: 22.0e9,
    E2: 2.4e9,
    nu12: 0.36,
    G12: 1.9e9,
    G13: 1.9e9,
    G23: 0.55e9,
    rho: 1050,
    eta: 0.0075,
    color: "#6b3a2a",
    metalness: 0,
    roughness: 0.55,
  },
  {
    id: "padauk",
    name: "African padauk",
    kind: "wood",
    E1: 11.7e9,
    E2: 1.3e9,
    nu12: 0.37,
    G12: 1.0e9,
    G13: 1.0e9,
    G23: 0.3e9,
    rho: 745,
    eta: 0.009,
    color: "#9a4a2c",
    metalness: 0,
    roughness: 0.6,
  },
  {
    id: "spruce",
    name: "Sitka spruce",
    kind: "wood",
    E1: 10.8e9,
    E2: 0.85e9,
    nu12: 0.37,
    G12: 0.7e9,
    G13: 0.7e9,
    G23: 0.04e9,
    rho: 420,
    eta: 0.009,
    color: "#d9bf8f",
    metalness: 0,
    roughness: 0.7,
  },
  isotropic(
    "aluminium",
    "Aluminium 6061",
    "metal",
    68.9e9,
    0.33,
    2700,
    0.0003,
    "#c9ccce",
    0.9,
    0.35,
  ),
  isotropic("steel", "Carbon steel", "metal", 205e9, 0.29, 7850, 0.0002, "#9aa0a6", 0.95, 0.3),
  isotropic("bronze", "Bell bronze", "metal", 103e9, 0.34, 8600, 0.0004, "#b08d57", 0.95, 0.3),
  isotropic("brass", "Brass C260", "metal", 110e9, 0.35, 8530, 0.001, "#c8a951", 0.95, 0.28),
  isotropic("glass", "Soda-lime glass", "glass", 72e9, 0.23, 2500, 0.0012, "#bcd3d0", 0.1, 0.08),
];

export function materialById(id: string): Material {
  const found = MATERIALS.find((m) => m.id === id);
  if (!found) throw new Error(`unknown material ${id}`);
  return found;
}
