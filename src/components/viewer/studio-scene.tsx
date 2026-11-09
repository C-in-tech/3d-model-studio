import { useEffect, useMemo, useRef, useSyncExternalStore, useState } from "react";
import * as THREE from "three";
import { Canvas, useFrame } from "@react-three/fiber";
import {
  ContactShadows,
  Environment,
  Lightformer,
  OrbitControls,
  useGLTF,
} from "@react-three/drei";
import { clone as cloneSkinned } from "three/examples/jsm/utils/SkeletonUtils.js";
import {
  buildBoneMap,
  getBonesVisible,
  getPose,
  getTurntable,
  subscribePose,
} from "./pose-rig";
import modelPointer from "@/assets/models/human-male-rigged.glb.asset.json";

useGLTF.preload(modelPointer.url);

const BACKDROP = "#241d14";
const PLATFORM = "#2c241a";
const RIG_COLOR = "#ffb35c";

function HumanModel({ onBones }: { onBones: (bones: THREE.Bone[]) => void }) {
  const { scene } = useGLTF(modelPointer.url);
  const clone = useMemo(() => cloneSkinned(scene), [scene]);
  const boneMap = useMemo(buildBoneMap, []);
  const boneList = useMemo(() => {
    const bones: THREE.Bone[] = [];
    clone.traverse((o) => {
      if ((o as THREE.Bone).isBone) bones.push(o as THREE.Bone);
    });
    return bones;
  }, [clone]);
  const bonesByName = useMemo(() => {
    const map = new Map<string, THREE.Bone>();
    // GLTFLoader sanitizes names ("mixamorig:Hips" -> "mixamorigHips")
    for (const b of boneList) map.set(b.name.replace(/[:\[\]./]/g, ""), b);
    return map;
  }, [boneList]);
  const applied = useRef(false);

  useEffect(() => {
    clone.traverse((o) => {
      const mesh = o as THREE.Mesh;
      if (mesh.isMesh) {
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        mesh.frustumCulled = false;
      }
    });
    onBones(boneList);
  }, [clone, boneList, onBones]);

  useFrame(() => {
    const pose = getPose();
    for (const [name, contribs] of boneMap) {
      const bone = bonesByName.get(name.replace(/[:\[\]./]/g, ""));
      if (!bone) continue;
      let x = 0;
      let y = 0;
      let z = 0;
      for (const c of contribs) {
        const rad = THREE.MathUtils.degToRad(pose[c.id] ?? 0) * c.sign;
        if (c.axis === "x") x += rad;
        else if (c.axis === "y") y += rad;
        else z += rad;
      }
      bone.rotation.set(x, y, z);
    }
    if (!applied.current) applied.current = true;
  });

  return <primitive object={clone} />;
}

function RigHelpers({ bones }: { bones: THREE.Bone[] }) {
  const visible = useSyncExternalStore(subscribePose, getBonesVisible);
  const instRef = useRef<THREE.InstancedMesh>(null);
  const lineRef = useRef<THREE.LineSegments>(null);

  const linePositions = useMemo(
    () => new Float32Array(Math.max(0, bones.length - 1) * 6),
    [bones.length],
  );

  const tmp = useMemo(() => new THREE.Vector3(), []);
  const tmpMat = useMemo(() => new THREE.Matrix4(), []);

  useFrame(() => {
    if (!visible || !instRef.current) return;
    bones.forEach((b, i) => {
      b.getWorldPosition(tmp);
      tmpMat.makeTranslation(tmp.x, tmp.y, tmp.z);
      instRef.current!.setMatrixAt(i, tmpMat);
    });
    instRef.current.instanceMatrix.needsUpdate = true;
    const geo = lineRef.current?.geometry as THREE.BufferGeometry | undefined;
    const attr = geo?.getAttribute("position") as THREE.BufferAttribute | undefined;
    if (attr) {
      for (let i = 1; i < bones.length; i++) {
        const b = bones[i]!;
        b.getWorldPosition(tmp);
        attr.setXYZ((i - 1) * 2, tmp.x, tmp.y, tmp.z);
        b.parent?.getWorldPosition(tmp);
        attr.setXYZ((i - 1) * 2 + 1, tmp.x, tmp.y, tmp.z);
      }
      attr.needsUpdate = true;
    }
  });

  if (!visible || bones.length === 0) return null;
  return (
    <group>
      <instancedMesh args={[undefined, undefined, bones.length]} ref={instRef}>
        <octahedronGeometry args={[0.016]} />
        <meshBasicMaterial color={RIG_COLOR} depthTest={false} transparent opacity={0.95} />
      </instancedMesh>
      <lineSegments ref={lineRef}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[linePositions, 3]} />
        </bufferGeometry>
        <lineBasicMaterial color={RIG_COLOR} depthTest={false} transparent opacity={0.45} />
      </lineSegments>
    </group>
  );
}

function TurntableControls() {
  const autoRotate = useSyncExternalStore(subscribePose, getTurntable);
  return (
    <OrbitControls
      makeDefault
      target={[0, 0.95, 0]}
      autoRotate={autoRotate}
      autoRotateSpeed={0.9}
      enablePan={false}
      minDistance={1.1}
      maxDistance={6}
      maxPolarAngle={Math.PI / 2 + 0.12}
    />
  );
}

function ReadySignal() {
  const done = useRef(false);
  useFrame(() => {
    if (done.current) return;
    done.current = true;
    const root = document.querySelector("[data-studio-root]");
    if (root) root.setAttribute("data-scene-ready", "");
  });
  return null;
}

export function StudioScene() {
  const [bones, setBones] = useState<THREE.Bone[]>([]);
  return (
    <Canvas
      shadows
      dpr={[1, 2]}
      gl={{ antialias: true }}
      camera={{ position: [2.2, 1.5, 3.6], fov: 34 }}
    >
      <color attach="background" args={[BACKDROP]} />
      <fog attach="fog" args={[BACKDROP, 7, 16]} />

      <ambientLight intensity={0.35} />
      <directionalLight
        position={[2.5, 4, 2.5]}
        intensity={2.4}
        color="#fff1de"
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
        shadow-camera-near={0.5}
        shadow-camera-far={12}
        shadow-camera-left={-2}
        shadow-camera-right={2}
        shadow-camera-top={3}
        shadow-camera-bottom={-1}
      />
      <directionalLight position={[-3, 2, -2.5]} intensity={0.7} color="#9db8d8" />

      <Environment resolution={128}>
        <Lightformer intensity={1.6} position={[0, 5, 0]} scale={[10, 10, 1]} />
        <Lightformer intensity={0.8} color="#8bb" position={[-5, 1, -1]} rotation-y={Math.PI / 2} scale={[20, 1, 1]} />
        <Lightformer intensity={0.8} color="#fca" position={[5, 1, 1]} rotation-y={-Math.PI / 2} scale={[20, 1, 1]} />
      </Environment>

      {/* floor */}
      <mesh rotation-x={-Math.PI / 2} position={[0, -0.001, 0]} receiveShadow>
        <circleGeometry args={[3.2, 64]} />
        <meshStandardMaterial color={PLATFORM} roughness={0.95} metalness={0} />
      </mesh>
      <ContactShadows position={[0, 0.002, 0]} scale={4} blur={2.4} far={2} opacity={0.6} />

      <HumanModel onBones={setBones} />
      <RigHelpers bones={bones} />
      <TurntableControls />
      <ReadySignal />
    </Canvas>
  );
}
