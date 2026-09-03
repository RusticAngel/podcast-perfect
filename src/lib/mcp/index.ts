import { defineMcp, type AnyToolDefinition } from "@lovable.dev/mcp-js";
import describePipeline from "./tools/describe-pipeline";
import listMusicPresets from "./tools/list-music-presets";
import listVoices from "./tools/list-voices";
import suggestProductionSettings from "./tools/suggest-production-settings";

export default defineMcp({
  name: "podcast-perfect",
  title: "Podcast Perfect",
  version: "0.1.0",
  instructions:
    "Tools for Podcast Perfect, a studio that turns a script PDF into a mixed podcast episode. Use `describe_pipeline` for how production works, `list_voices` and `list_music_presets` for the available casting and score options, and `suggest_production_settings` to recommend a mood, intensity, ducking level and voice cast for a given genre.",
  tools: [
    describePipeline,
    listVoices,
    listMusicPresets,
    suggestProductionSettings,
  ] as unknown as AnyToolDefinition[],
});
