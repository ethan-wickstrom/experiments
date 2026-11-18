const NAMES = ["C", "C♯", "D", "E♭", "E", "F", "F♯", "G", "A♭", "A", "B♭", "B"];

export interface Pitch {
  readonly name: string;
  readonly cents: number;
  readonly midi: number;
}

/** Nearest equal-tempered note at A4 = 440 Hz, and the deviation from it. */
export function pitchOf(frequency: number): Pitch {
  const exact = 69 + 12 * Math.log2(frequency / 440);
  const midi = Math.round(exact);
  return {
    name: `${NAMES[((midi % 12) + 12) % 12]}${Math.floor(midi / 12) - 1}`,
    cents: (exact - midi) * 100,
    midi,
  };
}

export const midiFrequency = (midi: number): number => 440 * 2 ** ((midi - 69) / 12);
export const midiName = (midi: number): string =>
  `${NAMES[((midi % 12) + 12) % 12]}${Math.floor(midi / 12) - 1}`;
export const centsBetween = (frequency: number, target: number): number =>
  1200 * Math.log2(frequency / target);

export function signed(value: number, digits = 0): string {
  const s = Math.abs(value).toFixed(digits);
  return `${value < 0 && Number(s) !== 0 ? "−" : "+"}${s}`;
}
