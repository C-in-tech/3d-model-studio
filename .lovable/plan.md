# Rigged Human Male 3D Model + Live Viewer

## What you get

1. **A rigged GLB model file** — a smooth, mid-poly full male human figure with a complete
   humanoid skeleton (hips, spine, chest, neck, head, both shoulders/arms/hands with fingers,
   both legs/feet). You can download it and open it in Blender, Unity, Unreal, or any glTF tool;
   the bones are there and ready to pose or animate. No textures required — clean shaded
   surfaces you can reskin or texture yourself.
2. **A live viewer page in your app** — the home page becomes a studio viewer: the model on a
   turntable with orbit controls, plus a side panel of sliders that rotate the bones live
   (head, spine, arms, elbows, hands, hips, knees, feet) and preset poses (T-pose, A-pose,
   Wave, Relaxed) with a reset button.

Honest scope note: I build the shape procedurally, so it is a clean stylized mid-poly human
( smooth contours, good proportions, roughly 15–25k triangles), not a photoreal sculpt. The
rig topology and clean quad-ish flow are what make it genuinely riggable and reusable.

## How it's built

1. **Generator script** (`scripts/generate_human_model.py`, kept in the project so we can
   regenerate/tweak):
   - Body built from lofted parametric surfaces — torso, head, arms, legs — smooth normals,
     anatomically proportioned male silhouette.
   - Skeleton: ~24 bones in a standard humanoid hierarchy, correct parent-child chains.
   - Per-vertex skin weights computed by distance falloff to the nearest bone, top 4 weights,
     so the mesh deforms smoothly when bones rotate.
   - Exports glTF 2.0 binary (GLB) with skin, joints, inverse bind matrices and a simple
     material. Validated with gltf-transform inspect and loaded in the viewer before delivery.
2. **Model hosting**: the GLB is copied to `/mnt/documents/human-male-rigged.glb` as your
   downloadable file and hosted in the app via the standard asset pipeline.
3. **Viewer page** (replaces the current placeholder home page):
   - React Three Fiber scene, server-side rendering off (`ssr: false`), orbit controls,
     studio lighting with soft shadows, neutral backdrop.
   - Bone rotation sliders (grouped: Head/Neck, Spine, Arms, Hands, Legs) writing directly to
     bone refs — no per-frame React re-renders.
   - Preset pose buttons + reset.
   - Ready signal + browser verification screenshot before I call it done.

## Packages

`three`, `@react-three/fiber@^9`, `@react-three/drei@^10`, `@types/three` (dev) — matches the
project's TanStack Start + React 19 stack.

## Files touched

```
scripts/generate_human_model.py        # model generator (rerunnable)
/mnt/documents/human-male-rigged.glb   # your downloadable rigged model
src/assets/models/human-male.glb.asset.json
src/types/r3f.d.ts                     # R3F JSX types
src/routes/index.tsx                   # viewer page (ssr: false)
src/components/viewer/                 # scene + pose panel components
AGENTS.md                              # record the generator/route decisions
```

## Verification

- Generate → inspect the GLB (joint count, triangle count, no errors).
- Load it in the sandbox browser, screenshot the viewer, exercise pose sliders, confirm the
  ready signal and no console errors.
- What I cannot verify here: how Blender/Unity/Unreal specifically import it on your machine,
  and real-GPU lighting/framerate on your device — I'll give you the exact import steps and the
  preview link to check those.
