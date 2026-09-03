import { defineTool } from "@lovable.dev/mcp-js";
import { DUCKING, MOODS } from "../catalog";

export default defineTool({
  name: "list_music_presets",
  title: "List music presets",
  description:
    "List the music mood presets available for the score, plus the intensity and ducking ranges used when mixing the bed under the dialogue.",
  inputSchema: {},
  annotations: { readOnlyHint: true, idempotentHint: true, openWorldHint: false },
  handler: () => ({
    content: [
      {
        type: "text",
        text: [
          MOODS.map((m) => `${m.value} (${m.label}) — ${m.hint}`).join("\n"),
          "",
          `Intensity: 0.0–1.0 (default 0.5).`,
          `Ducking: ${DUCKING.minDb} to ${DUCKING.maxDb} dB (default ${DUCKING.defaultDb} dB). ${DUCKING.note}`,
        ].join("\n"),
      },
    ],
    structuredContent: {
      moods: MOODS.map((m) => ({ ...m })),
      intensity: { min: 0, max: 1, default: 0.5 },
      ducking: { ...DUCKING },
    },
  }),
});
