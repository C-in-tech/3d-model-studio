#!/usr/bin/env python3
"""
Generate a rigged, smooth mid-poly human male character as glTF 2.0 binary (GLB).

- Y-up, meters, ~1.8 m tall, feet at y=0, character faces +Z, rest pose = T-pose.
- Single skinned mesh with a Mixamo-compatible bone hierarchy (mixamorig: prefix),
  so Mixamo animations can be retargeted onto it.
- Per-vertex skin weights via smooth gaussian falloff to bone segments (top 4).
- Vertex colors tint hair, eyes and eyebrows; material base color is skin.

Usage: python generate_human_model.py [output.glb]
"""
import json
import math
import struct
import sys

import numpy as np

# ----------------------------------------------------------------------------
# Skeleton definition: (name, parent, world position of the joint), parents first
# ----------------------------------------------------------------------------
BONES = [
    ("mixamorig:Hips",              None,                        (0.0, 0.95, 0.0)),
    ("mixamorig:Spine",             "mixamorig:Hips",            (0.0, 1.08, 0.0)),
    ("mixamorig:Chest",             "mixamorig:Spine",           (0.0, 1.24, 0.0)),
    ("mixamorig:Neck",              "mixamorig:Chest",           (0.0, 1.435, 0.0)),
    ("mixamorig:Head",              "mixamorig:Neck",            (0.0, 1.53, 0.0)),
    ("mixamorig:LeftShoulder",      "mixamorig:Chest",           (0.055, 1.425, 0.0)),
    ("mixamorig:LeftArm",           "mixamorig:LeftShoulder",    (0.185, 1.44, 0.005)),
    ("mixamorig:LeftForeArm",       "mixamorig:LeftArm",         (0.46, 1.438, 0.0)),
    ("mixamorig:LeftHand",          "mixamorig:LeftForeArm",     (0.70, 1.438, 0.0)),
    ("mixamorig:LeftHandThumb1",    "mixamorig:LeftHand",        (0.775, 1.43, 0.026)),
    ("mixamorig:LeftHandIndex1",    "mixamorig:LeftHand",        (0.845, 1.458, 0.012)),
    ("mixamorig:LeftHandMiddle1",   "mixamorig:LeftHand",        (0.845, 1.446, 0.004)),
    ("mixamorig:LeftHandRing1",     "mixamorig:LeftHand",        (0.845, 1.434, -0.004)),
    ("mixamorig:LeftHandPinky1",    "mixamorig:LeftHand",        (0.845, 1.422, -0.014)),
    ("mixamorig:RightShoulder",     "mixamorig:Chest",           (-0.055, 1.425, 0.0)),
    ("mixamorig:RightArm",          "mixamorig:RightShoulder",   (-0.185, 1.44, 0.005)),
    ("mixamorig:RightForeArm",      "mixamorig:RightArm",        (-0.46, 1.438, 0.0)),
    ("mixamorig:RightHand",         "mixamorig:RightForeArm",    (-0.70, 1.438, 0.0)),
    ("mixamorig:RightHandThumb1",   "mixamorig:RightHand",       (-0.775, 1.43, 0.026)),
    ("mixamorig:RightHandIndex1",   "mixamorig:RightHand",       (-0.845, 1.458, 0.012)),
    ("mixamorig:RightHandMiddle1",  "mixamorig:RightHand",       (-0.845, 1.446, 0.004)),
    ("mixamorig:RightHandRing1",    "mixamorig:RightHand",       (-0.845, 1.434, -0.004)),
    ("mixamorig:RightHandPinky1",   "mixamorig:RightHand",       (-0.845, 1.422, -0.014)),
    ("mixamorig:LeftUpLeg",         "mixamorig:Hips",            (0.095, 0.94, 0.0)),
    ("mixamorig:LeftLeg",           "mixamorig:LeftUpLeg",       (0.105, 0.48, 0.0)),
    ("mixamorig:LeftFoot",          "mixamorig:LeftLeg",         (0.105, 0.085, -0.02)),
    ("mixamorig:LeftToeBase",       "mixamorig:LeftFoot",        (0.105, 0.05, 0.10)),
    ("mixamorig:RightUpLeg",        "mixamorig:Hips",            (-0.095, 0.94, 0.0)),
    ("mixamorig:RightLeg",          "mixamorig:RightUpLeg",      (-0.105, 0.48, 0.0)),
    ("mixamorig:RightFoot",         "mixamorig:RightLeg",        (-0.105, 0.085, -0.02)),
    ("mixamorig:RightToeBase",      "mixamorig:RightFoot",       (-0.105, 0.05, 0.10)),
]

# Influence segment end points for bones whose segment must not default to a child.
SEG_TIPS = {
    "mixamorig:Hips":            (0.0, 1.03, 0.0),
    "mixamorig:Head":            (0.0, 1.74, 0.0),
    "mixamorig:LeftHand":        (0.845, 1.44, 0.0),
    "mixamorig:RightHand":       (-0.845, 1.44, 0.0),
    "mixamorig:LeftFoot":        (0.105, 0.05, 0.10),
    "mixamorig:RightFoot":       (-0.105, 0.05, 0.10),
    "mixamorig:LeftToeBase":     (0.105, 0.03, 0.18),
    "mixamorig:RightToeBase":    (-0.105, 0.03, 0.18),
    "mixamorig:LeftHandThumb1":  (0.86, 1.422, 0.052),
    "mixamorig:RightHandThumb1": (-0.86, 1.422, 0.052),
    "mixamorig:LeftHandIndex1":  (0.945, 1.456, 0.012),
    "mixamorig:RightHandIndex1": (-0.945, 1.456, 0.012),
    "mixamorig:LeftHandMiddle1": (0.950, 1.444, 0.004),
    "mixamorig:RightHandMiddle1": (-0.950, 1.444, 0.004),
    "mixamorig:LeftHandRing1":   (0.930, 1.432, -0.006),
    "mixamorig:RightHandRing1":  (-0.930, 1.432, -0.006),
    "mixamorig:LeftHandPinky1":  (0.912, 1.420, -0.016),
    "mixamorig:RightHandPinky1": (-0.912, 1.420, -0.016),
}
SIGMAS = {
    "mixamorig:Hips": 0.105,
    "mixamorig:Spine": 0.10,
    "mixamorig:Chest": 0.11,
    "mixamorig:Neck": 0.05,
    "mixamorig:Head": 0.085,
    "mixamorig:LeftShoulder": 0.06,
    "mixamorig:RightShoulder": 0.06,
    "mixamorig:LeftArm": 0.048,
    "mixamorig:RightArm": 0.048,
    "mixamorig:LeftHand": 0.035,
    "mixamorig:RightHand": 0.035,
}
FINGER_SIGMA = 0.022
DEFAULT_SIGMA = 0.05


def sigma_for(name):
    if "Hand" in name and name not in SIGMAS:  # finger bones
        return FINGER_SIGMA
    return SIGMAS.get(name, DEFAULT_SIGMA)


# ----------------------------------------------------------------------------
# Geometry helpers
# ----------------------------------------------------------------------------
def superellipse_ring(theta, rx, rz, expn):
    ct = np.cos(theta)
    st = np.sin(theta)
    u = np.sign(ct) * np.abs(ct) ** (2.0 / expn) * rx
    v = np.sign(st) * np.abs(st) ** (2.0 / expn) * rz
    return u, v


class MeshBuilder:
    """Accumulates correctly-wound primitives with per-vertex colors."""

    def __init__(self):
        self.positions = []
        self.colors = []
        self.tris = []

    def _add(self, verts, tris, color):
        base = len(self.positions)
        self.positions.extend(verts)
        self.colors.extend([color] * len(verts))
        self.tris.extend((a + base, b + base, c + base) for a, b, c in tris)
        return base, len(self.positions)

    def loft(self, axis, sections, color, theta_res=32, cap_start=True, cap_end=True):
        """Loft superellipse cross-sections along an axis.

        sections: (pos, c1, c2, rx, rz, expn)
          axis 'y': ring plane (x, z), center offset (c1+u -> x, c2+v -> z)
          axis 'x': ring plane (y, z)
          axis 'z': ring plane (x, y)
        Ring winding is CCW in the (u, v) plane; triangles (a, c, b) face outward.
        """
        verts = []
        for (pos, c1, c2, rx, rz, expn) in sections:
            th = np.linspace(0.0, 2.0 * math.pi, theta_res, endpoint=False)
            u, v = superellipse_ring(th, rx, rz, expn)
            for ui, vi in zip(u, v):
                if axis == "y":
                    verts.append((c1 + ui, pos, c2 + vi))
                elif axis == "x":
                    verts.append((pos, c1 + ui, c2 + vi))
                else:
                    verts.append((c1 + ui, c2 + vi, pos))
        n_rings = len(sections)
        tris = []
        for r in range(n_rings - 1):
            for j in range(theta_res):
                a = r * theta_res + j
                b = r * theta_res + (j + 1) % theta_res
                c = (r + 1) * theta_res + j
                d = (r + 1) * theta_res + (j + 1) % theta_res
                tris.append((a, c, b))
                tris.append((b, c, d))

        def ring_center(r):
            return np.mean(np.array(verts[r * theta_res:(r + 1) * theta_res]), axis=0)

        extra_verts = []
        extra_tris = []
        if cap_start:
            apex = len(verts) + len(extra_verts)
            extra_verts.append(tuple(ring_center(0)))
            for j in range(theta_res):
                extra_tris.append((apex, j, (j + 1) % theta_res))
        if cap_end:
            apex = len(verts) + len(extra_verts)
            extra_verts.append(tuple(ring_center(n_rings - 1)))
            ring0 = (n_rings - 1) * theta_res
            for j in range(theta_res):
                extra_tris.append((apex, ring0 + (j + 1) % theta_res, ring0 + j))
        all_verts = np.array(verts + extra_verts, dtype=np.float64)
        centers = [ring_center(r) for r in range(n_rings)]
        n_side = len(tris)
        fixed = []
        for ti, (a, b, c) in enumerate(tris + extra_tris):
            pa, pb, pc = all_verts[a], all_verts[b], all_verts[c]
            nrm = np.cross(pb - pa, pc - pa)
            face = (pa + pb + pc) / 3.0
            if ti < n_side:
                ref = centers[a // theta_res]
            else:
                # cap: point away from the neighbouring ring
                is_start = cap_start and ti - n_side < theta_res
                ref = centers[1] if is_start else centers[n_rings - 2]
                if n_rings < 2:
                    ref = face - (1.0, 0, 0)
            if np.dot(nrm, face - ref) < 0:
                b, c = c, b
            fixed.append((a, b, c))
        return self._add(verts + extra_verts, fixed, color)

    def sphere(self, center, radius, color, seg=14, rings=10, squash=1.0):
        verts = []
        for i in range(rings + 1):
            phi = math.pi * i / rings
            for j in range(seg):
                th = 2.0 * math.pi * j / seg
                x = radius * math.sin(phi) * math.cos(th)
                y = radius * math.cos(phi) * squash
                z = radius * math.sin(phi) * math.sin(th)
                verts.append((center[0] + x, center[1] + y, center[2] + z))
        tris = []
        for i in range(rings):
            for j in range(seg):
                a = i * seg + j
                b = i * seg + (j + 1) % seg
                c = (i + 1) * seg + j
                d = (i + 1) * seg + (j + 1) % seg
                tris.append((a, b, c))
                tris.append((b, d, c))
        return self._add(verts, tris, color)

    def finalize(self):
        pos = np.array(self.positions, dtype=np.float32)
        col = np.array(self.colors, dtype=np.float32)
        tris = np.array(self.tris, dtype=np.uint32)
        nrm = np.zeros_like(pos)
        p0, p1, p2 = pos[tris[:, 0]], pos[tris[:, 1]], pos[tris[:, 2]]
        fn = np.cross(p1 - p0, p2 - p0)
        for k in range(3):
            np.add.at(nrm, tris[:, k], fn)
        ln = np.linalg.norm(nrm, axis=1, keepdims=True)
        ln[ln == 0] = 1.0
        nrm = (nrm / ln).astype(np.float32)
        return pos, nrm, col, tris


SKIN = (1.0, 1.0, 1.0)          # tinted by the material base color
DARK = (0.09, 0.062, 0.048)     # hair / brows
EYE = (0.05, 0.055, 0.07)


def build_body(mb: MeshBuilder):
    # ---- torso ----
    mb.loft("y", [
        (0.895, 0.0, -0.005, 0.155, 0.108, 2.2),
        (0.955, 0.0, -0.004, 0.168, 0.112, 2.2),
        (1.045, 0.0, 0.0, 0.160, 0.113, 2.4),
        (1.150, 0.0, 0.004, 0.172, 0.120, 2.3),
        (1.270, 0.0, 0.010, 0.192, 0.128, 2.1),
        (1.380, 0.0, 0.010, 0.180, 0.118, 2.1),
        (1.455, 0.0, 0.006, 0.128, 0.096, 2.0),
    ], SKIN, theta_res=48)

    # ---- neck ----
    mb.loft("y", [
        (1.435, 0.0, 0.002, 0.054, 0.056, 2.0),
        (1.532, 0.0, 0.004, 0.052, 0.055, 2.0),
    ], SKIN, theta_res=32, cap_end=False)

    # ---- head ----
    head_secs = [
        (1.515, 0.0, 0.004, 0.058, 0.060, 2.0),
        (1.550, 0.0, 0.008, 0.076, 0.086, 2.2),
        (1.600, 0.0, 0.012, 0.092, 0.100, 2.4),
        (1.660, 0.0, 0.014, 0.096, 0.106, 2.6),
        (1.700, 0.0, 0.010, 0.090, 0.100, 2.6),
        (1.740, 0.0, 0.0, 0.074, 0.084, 2.4),
        (1.772, 0.0, -0.008, 0.048, 0.058, 2.2),
    ]
    mb.loft("y", head_secs, SKIN, theta_res=48, cap_start=False, cap_end=False)

    # ---- nose ----
    mb.loft("z", [
        (0.098, 0.0, 1.650, 0.024, 0.022, 2.0),
        (0.116, 0.0, 1.646, 0.019, 0.017, 2.0),
        (0.126, 0.0, 1.642, 0.014, 0.012, 2.0),
    ], SKIN, theta_res=16)

    # ---- ears ----
    for sx in (1, -1):
        mb.loft("x", [
            (0.088 * sx, 1.660, 0.0, 0.016, 0.024, 2.0),
            (0.104 * sx, 1.660, -0.004, 0.011, 0.019, 2.0),
        ], SKIN, theta_res=12)

    # ---- hair: shell over the skull, hairline pulled back over the face ----
    hair_secs = []
    for (pos, cx, cz, rx, rz, expn) in head_secs:
        if pos < 1.585:
            continue
        hair_secs.append((pos, cx, cz + 0.004, rx * 1.05, rz * 1.05, expn))
    hair_start, hair_end = mb.loft("y", hair_secs, DARK, theta_res=48,
                                   cap_start=False, cap_end=True)
    hp = np.array(mb.positions, dtype=object)
    for i in range(hair_start, hair_end):
        x, y, z = mb.positions[i]
        if z > 0.0 and y < 1.72:
            # front hairline: pull flush with the head surface, sloped
            t = max(0.0, min(1.0, (1.72 - y) / 0.135))
            pull = 1.05 - 0.042 * t
            mb.positions[i] = (x * pull, y, z * pull)
    for i in range(hair_start, hair_end):
        x, y, z = mb.positions[i]
        if z < -0.02 and y < 1.60:
            # nape line
            mb.positions[i] = (x * 1.02, y, z * 1.02)

    # ---- eyes + brows ----
    for sx in (1, -1):
        mb.sphere((0.034 * sx, 1.660, 0.093), 0.0145, EYE, squash=0.9)
        mb.loft("z", [(0.100, 0.0, 1.694, 0.024 * sx, 0.007, 2.0)], DARK, theta_res=8)

    # ---- arms (T-pose along X) ----
    def arm(sx):
        x = lambda v: v * sx
        mb.loft("x", [
            (x(0.150), 1.440, 0.004, 0.064, 0.064, 2.0),
            (x(0.200), 1.440, 0.004, 0.056, 0.058, 2.0),
            (x(0.310), 1.440, 0.001, 0.049, 0.052, 2.0),
            (x(0.460), 1.438, -0.001, 0.045, 0.048, 2.0),
            (x(0.600), 1.438, -0.002, 0.038, 0.041, 2.0),
            (x(0.720), 1.438, -0.002, 0.034, 0.036, 2.0),
        ], SKIN, theta_res=24)
        mb.loft("x", [
            (x(0.725), 1.438, -0.002, 0.036, 0.026, 2.2),
            (x(0.790), 1.440, -0.002, 0.034, 0.024, 2.2),
            (x(0.855), 1.440, -0.002, 0.030, 0.022, 2.2),
        ], SKIN, theta_res=16)
        fingers = [
            (1.458, 0.010, 0.940, 0.0105),
            (1.446, 0.002, 0.950, 0.0110),
            (1.434, -0.006, 0.930, 0.0100),
            (1.422, -0.016, 0.912, 0.0090),
        ]
        for fy, fz, tip, r in fingers:
            mb.loft("x", [
                (x(0.850), fy, fz, r, r, 2.0),
                (x(0.850 + (tip - 0.85) * 0.55), fy - 0.001, fz, r * 0.85, r * 0.85, 2.0),
                (x(tip), fy - 0.002, fz, r * 0.62, r * 0.62, 2.0),
            ], SKIN, theta_res=10)
        mb.loft("x", [
            (x(0.770), 1.430, 0.024, 0.014, 0.014, 2.0),
            (x(0.815), 1.426, 0.038, 0.0125, 0.0125, 2.0),
            (x(0.855), 1.424, 0.050, 0.010, 0.010, 2.0),
        ], SKIN, theta_res=10)

    arm(+1)
    arm(-1)

    # ---- legs ----
    def leg(sx):
        x = lambda v: v * sx
        mb.loft("y", [
            (0.960, x(0.095), 0.0, 0.084, 0.086, 2.2),
            (0.880, x(0.098), 0.0, 0.079, 0.083, 2.2),
            (0.700, x(0.104), 0.001, 0.067, 0.072, 2.2),
            (0.480, x(0.106), 0.006, 0.056, 0.060, 2.2),
            (0.330, x(0.105), 0.010, 0.049, 0.052, 2.2),
            (0.170, x(0.105), 0.003, 0.039, 0.043, 2.2),
            (0.085, x(0.105), -0.002, 0.032, 0.036, 2.2),
        ], SKIN, theta_res=28)
        mb.loft("z", [
            (-0.078, x(0.105), 0.048, 0.042, 0.048, 2.4),
            (-0.020, x(0.105), 0.038, 0.046, 0.038, 2.4),
            (0.050, x(0.104), 0.034, 0.048, 0.034, 2.4),
            (0.120, x(0.104), 0.030, 0.043, 0.030, 2.4),
            (0.170, x(0.103), 0.024, 0.030, 0.024, 2.4),
        ], SKIN, theta_res=20)

    leg(+1)
    leg(-1)


# ----------------------------------------------------------------------------
# Skin weights
# ----------------------------------------------------------------------------
def bone_segments():
    by_name = {n: np.array(p) for n, _, p in BONES}
    segs = []
    for name, parent, pos in BONES:
        start = np.array(pos)
        if name in SEG_TIPS:
            end = np.array(SEG_TIPS[name])
        else:
            children = [by_name[c] for c, par, _ in BONES if par == name]
            end = children[0] if children else by_name[parent]
        segs.append((name, start, end))
    return segs


def seg_dist(points, a, b):
    ab = b - a
    denom = float(ab @ ab)
    if denom < 1e-12:
        return np.linalg.norm(points - a, axis=1)
    t = np.clip(((points - a) @ ab) / denom, 0.0, 1.0)
    proj = a + t[:, None] * ab
    return np.linalg.norm(points - proj, axis=1)


def compute_weights(positions, segs, joints_index):
    n = len(positions)
    weights = np.zeros((n, len(segs)))
    sigs = np.array([sigma_for(name) for name, _, _ in segs])
    for bi, (name, a, b) in enumerate(segs):
        d = seg_dist(positions, a, b)
        weights[:, bi] = np.exp(-((d / sigs[bi]) ** 2))
    weights[weights < 1e-4] = 0.0
    top4 = np.argsort(weights, axis=1)[:, -4:]
    w4 = np.zeros((n, 4))
    j4 = np.zeros((n, 4), dtype=np.int64)
    for i in range(n):
        for k, bi in enumerate(top4[i]):
            w4[i, k] = weights[i, bi]
            j4[i, k] = joints_index[segs[bi][0]]
    s = w4.sum(axis=1, keepdims=True)
    s[s == 0] = 1.0
    w4 = w4 / s
    return j4.astype(np.uint16), w4.astype(np.float32)


# ----------------------------------------------------------------------------
# glTF assembly
# ----------------------------------------------------------------------------
def write_glb(path, positions, normals, colors, indices, joints, weights,
              bone_defs, ibms):
    buffer_bytes = bytearray()

    buffer_views = []
    accessors = []

    def add_view(data, target=None):
        offset = len(buffer_bytes)
        buffer_bytes.extend(data)
        while len(buffer_bytes) % 4:
            buffer_bytes.extend(b"\x00")
        bv = {"buffer": 0, "byteOffset": offset, "byteLength": len(data)}
        if target:
            bv["target"] = target
        buffer_views.append(bv)
        return len(buffer_views) - 1

    # indices
    iv = add_view(indices.astype("<u4").tobytes(), 34963)
    accessors.append({
        "bufferView": iv, "componentType": 5125, "count": len(indices),
        "type": "SCALAR", "min": [int(indices.min())], "max": [int(indices.max())],
    })
    idx_acc = len(accessors) - 1
    # positions
    pv = add_view(positions.astype("<f4").tobytes(), 34962)
    accessors.append({
        "bufferView": pv, "componentType": 5126, "count": len(positions),
        "type": "VEC3",
        "min": positions.min(axis=0).tolist(), "max": positions.max(axis=0).tolist(),
    })
    pos_acc = len(accessors) - 1
    # normals
    nv = add_view(normals.astype("<f4").tobytes(), 34962)
    accessors.append({"bufferView": nv, "componentType": 5126, "count": len(normals), "type": "VEC3"})
    nrm_acc = len(accessors) - 1
    # vertex colors
    cv = add_view(colors.astype("<f4").tobytes(), 34962)
    accessors.append({"bufferView": cv, "componentType": 5126, "count": len(colors), "type": "VEC3"})
    col_acc = len(accessors) - 1
    # joints
    jv = add_view(joints.astype("<u2").tobytes(), 34962)
    accessors.append({"bufferView": jv, "componentType": 5123, "count": len(joints), "type": "VEC4"})
    jnt_acc = len(accessors) - 1
    # weights
    wv = add_view(weights.astype("<f4").tobytes(), 34962)
    accessors.append({"bufferView": wv, "componentType": 5126, "count": len(weights), "type": "VEC4"})
    wgt_acc = len(accessors) - 1
    # inverse bind matrices
    # glTF matrices are column-major
    ibm_flat = np.concatenate([m.T.reshape(-1) for m in ibms]).astype("<f4")
    ibv = add_view(ibm_flat.tobytes())
    accessors.append({"bufferView": ibv, "componentType": 5126, "count": len(ibms), "type": "MAT4"})
    ibm_acc = len(accessors) - 1

    # joint nodes, parents first
    nodes = []
    name_to_node = {}
    joint_order = [n for n, _, _ in bone_defs]
    world_pos = {n: np.array(p) for n, _, p in bone_defs}
    for name, parent, pos in bone_defs:
        node_idx = len(nodes)
        local = np.array(pos) - (world_pos[parent] if parent else 0.0)
        nodes.append({
            "name": name,
            "translation": [float(c) for c in local],
            "rotation": [0, 0, 0, 1],
        })
        name_to_node[name] = node_idx
        if parent:
            nodes[name_to_node[parent]].setdefault("children", []).append(node_idx)
    joints_list = [name_to_node[n] for n in joint_order]

    mesh_node_idx = len(nodes)
    nodes.append({"name": "HumanMale", "mesh": 0, "skin": 0})

    gltf = {
        "asset": {"version": "2.0", "generator": "lovable-procedural-human"},
        "scene": 0,
        "scenes": [{"nodes": [mesh_node_idx, joints_list[0]], "name": "Scene"}],
        "nodes": nodes,
        "meshes": [{
            "name": "HumanMale",
            "primitives": [{
                "attributes": {
                    "POSITION": pos_acc,
                    "NORMAL": nrm_acc,
                    "COLOR_0": col_acc,
                    "JOINTS_0": jnt_acc,
                    "WEIGHTS_0": wgt_acc,
                },
                "indices": idx_acc,
                "material": 0,
                "mode": 4,
            }],
        }],
        "skins": [{
            "joints": joints_list,
            "inverseBindMatrices": ibm_acc,
            "skeleton": joints_list[0],
        }],
        "materials": [{
            "name": "Skin",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.845, 0.640, 0.535, 1.0],
                "metallicFactor": 0.0,
                "roughnessFactor": 0.75,
            },
        }],
        "accessors": accessors,
        "bufferViews": buffer_views,
        "buffers": [{"byteLength": len(buffer_bytes)}],
    }

    json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    while len(json_bytes) % 4:
        json_bytes += b" "
    while len(buffer_bytes) % 4:
        buffer_bytes += b"\x00"

    total = 12 + 8 + len(json_bytes) + 8 + len(buffer_bytes)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(json_bytes), 0x4E4F534A))
        f.write(json_bytes)
        f.write(struct.pack("<II", len(buffer_bytes), 0x004E4942))
        f.write(buffer_bytes)
    print(f"wrote {path}: {len(positions)} verts, {len(indices) // 3} tris, "
          f"{len(bone_defs)} bones, {total // 1024} KB")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/human-male-rigged.glb"
    mb = MeshBuilder()
    build_body(mb)
    positions, normals, colors, tris = mb.finalize()

    bone_defs = [(n, p, np.array(pos)) for n, p, pos in BONES]
    joints_index = {name: i for i, (name, _, _) in enumerate(bone_defs)}

    segs = bone_segments()
    joints4, weights4 = compute_weights(positions, segs, joints_index)

    world = {}
    ibms = []
    for name, parent, pos in bone_defs:
        M = np.eye(4)
        M[:3, 3] = pos  # rest pose has identity rotations: world = translation
        world[name] = M
        ibms.append(np.linalg.inv(M))

    write_glb(out, positions, normals, colors, tris, joints4, weights4,
              bone_defs, ibms)


if __name__ == "__main__":
    main()
