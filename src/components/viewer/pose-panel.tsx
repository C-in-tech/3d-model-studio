import { useState, useSyncExternalStore } from "react";
import {
  CONTROLS,
  GROUPS,
  PRESETS,
  applyPreset,
  defaultPose,
  getBonesVisible,
  getPose,
  getTurntable,
  setBonesVisible,
  setControl,
  setTurntable,
  subscribePose,
  type PoseValues,
} from "./pose-rig";

function SliderRow({ id, label, min, max, value }: {
  id: string;
  label: string;
  min: number;
  max: number;
  value: number;
}) {
  return (
    <label className="group flex items-center gap-3 py-1.5" data-control={id}>
      <span className="w-24 shrink-0 text-xs font-medium text-muted-foreground group-hover:text-foreground">
        {label}
      </span>
      <input
        type="range"
        min={min}
        max={max}
        step={1}
        value={value}
        onChange={(e) => setControl(id, Number(e.target.value))}
        className="h-1.5 w-full cursor-pointer accent-primary"
        aria-label={label}
      />
      <span className="w-9 shrink-0 text-right text-[10px] tabular-nums text-muted-foreground">
        {value}°
      </span>
    </label>
  );
}

export function PosePanel() {
  const pose = useSyncExternalStore(subscribePose, getPose) as PoseValues;
  const bonesVisible = useSyncExternalStore(subscribePose, getBonesVisible);
  const turntable = useSyncExternalStore(subscribePose, getTurntable);
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(GROUPS.map((g) => [g, g === "Head & Neck" || g === "Torso"])),
  );

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border/60 px-4 pb-4 pt-4">
        <div className="flex items-baseline justify-between">
          <h2 className="font-display text-sm font-semibold tracking-wide uppercase text-foreground">
            Rig Console
          </h2>
          <button
            onClick={() => applyPreset(PRESETS[0])}
            className="text-xs text-muted-foreground underline-offset-2 hover:text-foreground hover:underline"
          >
            Reset
          </button>
        </div>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {PRESETS.map((p) => (
            <button
              key={p.id}
              onClick={() => applyPreset(p)}
              data-preset={p.id}
              className="rounded-full border border-border bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground transition-colors hover:bg-accent"
            >
              {p.label}
            </button>
          ))}
        </div>
        <div className="mt-3 flex gap-4">
          <label className="flex items-center gap-2 text-xs text-muted-foreground">
            <input
              type="checkbox"
              checked={bonesVisible}
              onChange={(e) => setBonesVisible(e.target.checked)}
              className="accent-primary"
            />
            Show bones
          </label>
          <label className="flex items-center gap-2 text-xs text-muted-foreground">
            <input
              type="checkbox"
              checked={turntable}
              onChange={(e) => setTurntable(e.target.checked)}
              className="accent-primary"
            />
            Turntable
          </label>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-3">
        {GROUPS.map((group) => (
          <details
            key={group}
            open={openGroups[group]}
            onToggle={(e) =>
              setOpenGroups((s) => ({ ...s, [group]: (e.target as HTMLDetailsElement).open }))
            }
            className="border-b border-border/40 py-2 [&:last-child]:border-0"
          >
            <summary className="cursor-pointer select-none py-1 text-xs font-semibold uppercase tracking-wider text-foreground/80">
              {group}
            </summary>
            <div className="mt-1">
              {CONTROLS.filter((c) => c.group === group).map((c) => (
                <SliderRow
                  key={c.id}
                  id={c.id}
                  label={c.label}
                  min={c.min}
                  max={c.max}
                  value={pose[c.id] ?? c.default}
                />
              ))}
            </div>
          </details>
        ))}
      </div>
    </div>
  );
}
