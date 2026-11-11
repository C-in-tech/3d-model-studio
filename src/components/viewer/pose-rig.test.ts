import { describe, expect, it } from "vitest";
import { CONTROLS } from "./pose-rig";

describe("independent finger rig controls", () => {
  it("exposes five separate three-joint curl controls per hand", () => {
    const fingers = ["Thumb", "Index", "Middle", "Ring", "Pinky"];

    for (const [side, prefix, sign] of [
      ["Left", "l", -1],
      ["Right", "r", 1],
    ] as const) {
      const controls = CONTROLS.filter((control) => control.group === `${side} Hand`);
      expect(controls).toHaveLength(5);

      for (const finger of fingers) {
        const control = controls.find((entry) => entry.id === `${prefix}${finger}Curl`);
        expect(control).toBeDefined();
        expect(control?.targets).toEqual([
          { bone: `mixamorig:${side}Hand${finger}1`, axis: "y", sign },
          { bone: `mixamorig:${side}Hand${finger}2`, axis: "y", sign },
          { bone: `mixamorig:${side}Hand${finger}3`, axis: "y", sign },
        ]);
      }
    }
  });
});