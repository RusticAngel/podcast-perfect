import { defineTool } from "@lovable.dev/mcp-js";
import { z } from "zod";
import { DUCKING, MOODS, VOICES } from "../catalog";

const MOOD_BY_GENRE: Record<string, { mood: string; intensity: number; duckDb: number; voices: string[] }> = {
  "technology": { mood: "excited", intensity: 0.6, duckDb: -14, voices: ["Kore", "Zephyr"] },
  "business": { mood: "serious", intensity: 0.4, duckDb: -16, voices: ["Orus", "Kore"] },
  "true crime": { mood: "nervous", intensity: 0.7, duckDb: -12, voices: ["Charon", "Leda"] },
  "health": { mood: "calm", intensity: 0.35, duckDb: -18, voices: ["Leda", "Orus"] },
  "comedy": { mood: "funny", intensity: 0.7, duckDb: -10, voices: ["Puck", "Zephyr"] },
  "education": { mood: "neutral", intensity: 0.4, duckDb: -16, voices: ["Orus", "Aoede"] },
  "news": { mood: "serious", intensity: 0.5, duckDb: -15, voices: ["Charon", "Kore"] },
};

export default defineTool({
  name: "suggest_production_settings",
  title: "Suggest production settings",
  description:
    "Recommend a music mood, intensity, ducking level and voice cast for a podcast, based on its genre and number of speakers.",
  inputSchema: {
    genre: z.string().describe("Podcast genre, e.g. technology, true crime, comedy."),
    speakers: z
      .number()
      .int()
      .optional()
      .describe("How many distinct speakers appear in the script. Defaults to 2."),
  },
  annotations: { readOnlyHint: true, idempotentHint: true, openWorldHint: false },
  handler: ({ genre, speakers }) => {
    const key = genre.trim().toLowerCase();
    const base = MOOD_BY_GENRE[key] ?? { mood: "neutral", intensity: 0.5, duckDb: DUCKING.defaultDb, voices: ["Kore", "Puck"] };
    const count = Math.min(Math.max(speakers ?? 2, 1), VOICES.length);
    const pool = [...base.voices, ...VOICES.map((v) => v.value).filter((v) => !base.voices.includes(v))];
    const cast = pool.slice(0, count);
    const moodLabel = MOODS.find((m) => m.value === base.mood)?.label ?? base.mood;

    return {
      content: [
        {
          type: "text",
          text: [
            `Genre: ${genre}${MOOD_BY_GENRE[key] ? "" : " (no exact match, using a neutral default)"}`,
            `Music mood: ${base.mood} (${moodLabel})`,
            `Intensity: ${base.intensity}`,
            `Ducking: ${base.duckDb} dB`,
            `Suggested cast: ${cast.join(", ")}`,
          ].join("\n"),
        },
      ],
      structuredContent: {
        music_mood: base.mood,
        music_intensity: base.intensity,
        duck_db: base.duckDb,
        voice_cast: cast,
        matched_genre: Boolean(MOOD_BY_GENRE[key]),
      },
    };
  },
});
