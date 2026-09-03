export const GENRES = [
  "technology",
  "business",
  "true crime",
  "health",
  "comedy",
  "education",
  "news",
] as const;

export const MOODS = [
  { value: "auto", label: "Auto (match the script)", hint: "The director picks a bed from the script's tone." },
  { value: "calm", label: "Calm", hint: "Ambient pads, gentle and unobtrusive." },
  { value: "happy", label: "Warm & upbeat", hint: "Acoustic bed with light percussion." },
  { value: "excited", label: "Energetic", hint: "Electronic pulse with drive." },
  { value: "serious", label: "Documentary", hint: "Restrained, steady strings." },
  { value: "nervous", label: "Suspenseful", hint: "Sparse pulse and muted plucks." },
  { value: "sad", label: "Reflective", hint: "Melancholic solo piano." },
  { value: "funny", label: "Playful", hint: "Ukulele and handclaps." },
  { value: "neutral", label: "Neutral lo-fi", hint: "Soft instrumental bed." },
] as const;

export const VOICES = [
  { value: "Kore", label: "Kore", hint: "Warm, measured host" },
  { value: "Puck", label: "Puck", hint: "Bright and upbeat" },
  { value: "Charon", label: "Charon", hint: "Deep and steady" },
  { value: "Aoede", label: "Aoede", hint: "Airy, expressive" },
  { value: "Fenrir", label: "Fenrir", hint: "Gravelly, forceful" },
  { value: "Leda", label: "Leda", hint: "Youthful and clear" },
  { value: "Orus", label: "Orus", hint: "Calm narrator" },
  { value: "Zephyr", label: "Zephyr", hint: "Light and quick" },
] as const;

export const PIPELINE_STAGES = [
  { id: "parse", name: "Script ingestion", detail: "The uploaded PDF is parsed into speaker-tagged dialogue lines." },
  { id: "director", name: "Director analysis", detail: "An agent reads the script for tone, pacing and per-line delivery notes." },
  { id: "research", name: "Market research", detail: "A researcher agent grounds comparable podcasts in real search results (needs PARALLEL_API_KEY)." },
  { id: "voice", name: "Voice production", detail: "Each speaker line is rendered with a Gemini TTS voice, honouring the voice cast." },
  { id: "music", name: "Score & mix", detail: "A music bed is synthesised for the chosen mood/intensity and ducked under the dialogue." },
  { id: "deliver", name: "Delivery", detail: "The final episode WAV, music bed and per-speaker clips are published as downloads." },
] as const;

export const DUCKING = {
  minDb: -40,
  maxDb: 0,
  defaultDb: -14,
  note: "Ducking is how far the music bed is attenuated under speech. -40 dB is nearly silent, 0 dB leaves the bed at full level.",
} as const;
