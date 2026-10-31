import type { FrameColor, ObjectInfo } from "./types";

/** Farbe des Frames einer Angabe; `null`, wenn die Angabe in keinem Frame steht. */
export function colorOf(info: ObjectInfo, colors: readonly FrameColor[]): FrameColor | null {
  return colors.find((color) => color.key === info.colorKey) ?? null;
}
