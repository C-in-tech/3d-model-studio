import { createFileRoute } from "@tanstack/react-router";
import HumanStudio from "@/components/viewer/human-studio";

export const Route = createFileRoute("/")({
  ssr: false,
  component: HumanStudio,
  head: () => ({
    meta: [
      { title: "Human Studio — Rigged 3D Figure" },
      {
        name: "description",
        content:
          "A fully rigged 3D human male model you can pose live and download for Blender, Unity or Unreal.",
      },
      { property: "og:type", content: "website" },
      { property: "og:title", content: "Human Studio — Rigged 3D Figure" },
      {
        property: "og:description",
        content:
          "A fully rigged 3D human male model you can pose live and download for Blender, Unity or Unreal.",
      },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
});
