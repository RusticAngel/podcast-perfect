import { defineTool } from "@lovable.dev/mcp-js";
import { VOICES } from "../catalog";

export default defineTool({
  name: "list_voices",
  title: "List narration voices",
  description:
    "List the Gemini text-to-speech voices this studio can cast for podcast speakers, with a short character hint for each.",
  inputSchema: {},
  annotations: { readOnlyHint: true, idempotentHint: true, openWorldHint: false },
  handler: () => ({
    content: [
      {
        type: "text",
        text: VOICES.map((v) => `${v.value} — ${v.hint}`).join("\n"),
      },
    ],
    structuredContent: { voices: VOICES.map((v) => ({ ...v })) },
  }),
});
