/**
 * Rig control model for the human-male character.
 *
 * Plain data + a tiny mutable store: the pose panel writes values, the scene
 * reads them every frame and rotates the bones. No React in the hot path.
 *
 * Angles are degrees. Positive = the semantic direction named by the control.
 * Each control drives one or more bones; per-bone `sign` flips the axis so one
 * slider can mirror left/right sides.
 */

export type Axis = "x" | "y" | "z";

export interface BoneTarget {
  bone: string;
  axis: Axis;
  sign: 1 | -1;
}

export interface Control {
  id: string;
  label: string;
  group: string;
  min: number;
  max: number;
  default: number;
  targets: BoneTarget[];
}

const L = "mixamorig:Left";
const R = "mixamorig:Right";

// T-pose rest: arms along ±X, legs along -Y, feet pointing +Z.
export const CONTROLS: Control[] = [
  // --- Neck & head ---
  {
    id: "neckNod", label: "Neck nod", group: "Head & Neck",
    min: -30, max: 30, default: 0,
    targets: [{ bone: "mixamorig:Neck", axis: "x", sign: 1 }],
  },
  {
    id: "neckTurn", label: "Neck turn", group: "Head & Neck",
    min: -70, max: 70, default: 0,
    targets: [{ bone: "mixamorig:Neck", axis: "y", sign: 1 }],
  },
  {
    id: "headNod", label: "Head nod", group: "Head & Neck",
    min: -30, max: 30, default: 0,
    targets: [{ bone: "mixamorig:Head", axis: "x", sign: 1 }],
  },
  {
    id: "headTurn", label: "Head turn", group: "Head & Neck",
    min: -70, max: 70, default: 0,
    targets: [{ bone: "mixamorig:Head", axis: "y", sign: 1 }],
  },
  {
    id: "headTilt", label: "Head tilt", group: "Head & Neck",
    min: -30, max: 30, default: 0,
    targets: [{ bone: "mixamorig:Head", axis: "z", sign: 1 }],
  },
  // --- Torso ---
  {
    id: "spineLean", label: "Spine lean", group: "Torso",
    min: -35, max: 45, default: 0,
    targets: [{ bone: "mixamorig:Spine", axis: "x", sign: 1 }],
  },
  {
    id: "spineTwist", label: "Spine twist", group: "Torso",
    min: -55, max: 55, default: 0,
    targets: [{ bone: "mixamorig:Spine", axis: "y", sign: 1 }],
  },
  {
    id: "spineSide", label: "Spine side bend", group: "Torso",
    min: -35, max: 35, default: 0,
    targets: [{ bone: "mixamorig:Spine", axis: "z", sign: 1 }],
  },
  {
    id: "chestLean", label: "Chest lean", group: "Torso",
    min: -30, max: 35, default: 0,
    targets: [{ bone: "mixamorig:Chest", axis: "x", sign: 1 }],
  },
  {
    id: "chestTwist", label: "Chest twist", group: "Torso",
    min: -45, max: 45, default: 0,
    targets: [{ bone: "mixamorig:Chest", axis: "y", sign: 1 }],
  },
  // --- Left arm ---
  {
    id: "lArmRaise", label: "Arm raise", group: "Left Arm",
    min: -110, max: 115, default: 0,
    targets: [{ bone: `${L}Arm`, axis: "z", sign: 1 }],
  },
  {
    id: "lArmSwing", label: "Arm swing", group: "Left Arm",
    min: -90, max: 70, default: 0,
    targets: [{ bone: `${L}Arm`, axis: "y", sign: 1 }],
  },
  {
    id: "lArmTwist", label: "Arm twist", group: "Left Arm",
    min: -90, max: 90, default: 0,
    targets: [{ bone: `${L}Arm`, axis: "x", sign: 1 }],
  },
  {
    id: "lElbow", label: "Elbow bend", group: "Left Arm",
    min: 0, max: 150, default: 0,
    targets: [{ bone: `${L}ForeArm`, axis: "z", sign: 1 }],
  },
  {
    id: "lHandWave", label: "Hand wave", group: "Left Arm",
    min: -45, max: 45, default: 0,
    targets: [{ bone: `${L}Hand`, axis: "z", sign: 1 }],
  },
  {
    id: "lHandTwist", label: "Hand twist", group: "Left Arm",
    min: -90, max: 90, default: 0,
    targets: [{ bone: `${L}Hand`, axis: "x", sign: 1 }],
  },
  // --- Right arm (mirrored axes) ---
  {
    id: "rArmRaise", label: "Arm raise", group: "Right Arm",
    min: -110, max: 115, default: 0,
    targets: [{ bone: `${R}Arm`, axis: "z", sign: -1 }],
  },
  {
    id: "rArmSwing", label: "Arm swing", group: "Right Arm",
    min: -90, max: 70, default: 0,
    targets: [{ bone: `${R}Arm`, axis: "y", sign: -1 }],
  },
  {
    id: "rArmTwist", label: "Arm twist", group: "Right Arm",
    min: -90, max: 90, default: 0,
    targets: [{ bone: `${R}Arm`, axis: "x", sign: -1 }],
  },
  {
    id: "rElbow", label: "Elbow bend", group: "Right Arm",
    min: 0, max: 150, default: 0,
    targets: [{ bone: `${R}ForeArm`, axis: "z", sign: -1 }],
  },
  {
    id: "rHandWave", label: "Hand wave", group: "Right Arm",
    min: -45, max: 45, default: 0,
    targets: [{ bone: `${R}Hand`, axis: "z", sign: -1 }],
  },
  {
    id: "rHandTwist", label: "Hand twist", group: "Right Arm",
    min: -90, max: 90, default: 0,
    targets: [{ bone: `${R}Hand`, axis: "x", sign: -1 }],
  },
  // --- Independent finger curls ---
  ...([
    ["Thumb", "Thumb curl"],
    ["Index", "Index curl"],
    ["Middle", "Middle curl"],
    ["Ring", "Ring curl"],
    ["Pinky", "Pinky curl"],
  ] as const).flatMap(([finger, label]) => ([
    {
      id: `l${finger}Curl`, label, group: "Left Hand",
      min: 0, max: 90, default: 0,
      targets: [1, 2, 3].map((joint) => ({ bone: `${L}Hand${finger}${joint}`, axis: "y" as const, sign: -1 as const })),
    },
    {
      id: `r${finger}Curl`, label, group: "Right Hand",
      min: 0, max: 90, default: 0,
      targets: [1, 2, 3].map((joint) => ({ bone: `${R}Hand${finger}${joint}`, axis: "y" as const, sign: 1 as const })),
    },
  ])),
  // --- Left leg ---
  {
    id: "lHipSwing", label: "Hip swing", group: "Left Leg",
    min: -100, max: 35, default: 0,
    targets: [{ bone: `${L}UpLeg`, axis: "x", sign: 1 }],
  },
  {
    id: "lHipSide", label: "Hip spread", group: "Left Leg",
    min: -25, max: 45, default: 0,
    targets: [{ bone: `${L}UpLeg`, axis: "z", sign: 1 }],
  },
  {
    id: "lKnee", label: "Knee bend", group: "Left Leg",
    min: 0, max: 145, default: 0,
    targets: [{ bone: `${L}Leg`, axis: "x", sign: 1 }],
  },
  {
    id: "lFootFlex", label: "Foot flex", group: "Left Leg",
    min: -45, max: 55, default: 0,
    targets: [{ bone: `${L}Foot`, axis: "x", sign: -1 }],
  },
  // --- Right leg ---
  {
    id: "rHipSwing", label: "Hip swing", group: "Right Leg",
    min: -100, max: 35, default: 0,
    targets: [{ bone: `${R}UpLeg`, axis: "x", sign: 1 }],
  },
  {
    id: "rHipSide", label: "Hip spread", group: "Right Leg",
    min: -45, max: 25, default: 0,
    targets: [{ bone: `${R}UpLeg`, axis: "z", sign: -1 }],
  },
  {
    id: "rKnee", label: "Knee bend", group: "Right Leg",
    min: 0, max: 145, default: 0,
    targets: [{ bone: `${R}Leg`, axis: "x", sign: 1 }],
  },
  {
    id: "rFootFlex", label: "Foot flex", group: "Right Leg",
    min: -45, max: 55, default: 0,
    targets: [{ bone: `${R}Foot`, axis: "x", sign: -1 }],
  },
];

export type PoseValues = Record<string, number>;

export const CONTROL_BY_ID: Record<string, Control> = Object.fromEntries(
  CONTROLS.map((c) => [c.id, c]),
);

export const GROUPS = [...new Set(CONTROLS.map((c) => c.group))];

export function defaultPose(): PoseValues {
  return Object.fromEntries(CONTROLS.map((c) => [c.id, c.default]));
}

export interface PosePreset {
  id: string;
  label: string;
  values: PoseValues;
}

export const PRESETS: PosePreset[] = [
  { id: "tpose", label: "T-Pose", values: {} },
  {
    id: "apose", label: "A-Pose",
    values: { lArmRaise: -45, rArmRaise: -45, lElbow: 8, rElbow: 8 },
  },
  {
    id: "relaxed", label: "Relaxed",
    values: {
      lArmRaise: -72, rArmRaise: -72, lArmTwist: -12, rArmTwist: -12,
      lElbow: 14, rElbow: 14, lHandTwist: -8, rHandTwist: -8,
      chestLean: 4, spineLean: 3, headNod: 4,
    },
  },
  {
    id: "wave", label: "Wave",
    values: {
      lArmRaise: -75, lElbow: 12,
      rArmRaise: 60, rElbow: 55, rHandWave: 28, rHandTwist: -20,
      headTilt: -10, headTurn: 18, spineSide: -4,
    },
  },
  {
    id: "sit", label: "Sit",
    values: {
      lHipSwing: -88, rHipSwing: -88, lKnee: 88, rKnee: 88,
      lHipSide: 6, rHipSide: 6, lFootFlex: 18, rFootFlex: 18,
      lArmRaise: -68, rArmRaise: -68, lElbow: 22, rElbow: 22,
      lArmSwing: -18, rArmSwing: -18,
    },
  },
];

// --- store -------------------------------------------------------------------
const listeners = new Set<() => void>();
let pose: PoseValues = defaultPose();
let bonesVisible = false;

export function getPose(): PoseValues {
  return pose;
}

export function setControl(id: string, value: number) {
  pose = { ...pose, [id]: value };
  listeners.forEach((fn) => fn());
}

export function applyPreset(p: PosePreset) {
  pose = { ...defaultPose(), ...p.values };
  listeners.forEach((fn) => fn());
}

export function subscribePose(fn: () => void): () => void {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

export function getBonesVisible(): boolean {
  return bonesVisible;
}

export function setBonesVisible(v: boolean) {
  bonesVisible = v;
  listeners.forEach((fn) => fn());
}

let turntable = false;

export function getTurntable(): boolean {
  return turntable;
}

export function setTurntable(v: boolean) {
  turntable = v;
  listeners.forEach((fn) => fn());
}

/** bone name -> contributions [(controlId, axis, sign)] */
export function buildBoneMap(): Map<string, { id: string; axis: Axis; sign: number }[]> {
  const map = new Map<string, { id: string; axis: Axis; sign: number }[]>();
  for (const c of CONTROLS) {
    for (const t of c.targets) {
      const list = map.get(t.bone) ?? [];
      list.push({ id: c.id, axis: t.axis, sign: t.sign });
      map.set(t.bone, list);
    }
  }
  return map;
}
