import { StudioScene } from "./studio-scene";
import { PosePanel } from "./pose-panel";

export default function HumanStudio() {
  return (
    <div
      data-studio-root
      className="flex h-dvh w-full flex-col bg-background text-foreground lg:flex-row"
    >
      <div className="relative min-h-[58vh] flex-1 lg:min-h-0">
        <StudioScene />
        <div className="pointer-events-none absolute left-5 top-5 select-none">
          <h1 className="font-display text-lg font-semibold tracking-tight text-foreground">
            Human Studio
          </h1>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Rigged male figure · drag to orbit · scroll to zoom
          </p>
        </div>
      </div>
      <aside className="h-[42vh] w-full shrink-0 border-t border-border/60 bg-card/50 backdrop-blur lg:h-full lg:w-[340px] lg:border-l lg:border-t-0">
        <PosePanel />
      </aside>
    </div>
  );
}
