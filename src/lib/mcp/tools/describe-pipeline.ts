import { defineTool } from "@lovable.dev/mcp-js";
import { GENRES, PIPELINE_STAGES } from "../catalog";

export default defineTool({
  name: "describe_pipeline",
  title: "Describe the production pipeline",
  description:
    "Explain how the Podcast Perfect studio turns a script PDF into a finished episode: the ordered production stages, the supported genres, and the options accepted when starting a production.",
  inputSchema: {},
  annotations: { readOnlyHint: true, idempotentHint: true, openWorldHint: false },
  handler: () => ({
    content: [
      {
        type: "text",
        text: [
          PIPELINE_STAGES.map((s, i) => `${i + 1}. ${s.name} — ${s.detail}`).join("\n"),
          "",
          `Genres: ${GENRES.join(", ")}`,
          "Options when starting a production: genre, music_mood, music_intensity (0–1), duck_db (-40–0), voice_map (speaker → voice name).",
          "Productions themselves are started by uploading a script PDF in the app; that upload step is not available over MCP.",
        ].join("\n"),
      },
    ],
    structuredContent: {
      stages: PIPELINE_STAGES.map((s) => ({ ...s })),
      genres: [...GENRES],
    },
  }),
});
