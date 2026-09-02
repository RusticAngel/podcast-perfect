import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  AudioLines,
  ClipboardList,
  Download,
  FileAudio,
  FileText,
  Loader2,
  Music4,
  Radio,
  Search,
  Settings2,
  Sparkles,
  UploadCloud,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Podcast-to-Production Studio | Script to Finished Episode" },
      {
        name: "description",
        content:
          "Upload a podcast script PDF and let the multi-agent studio direct, research, voice and score a finished episode you can download.",
      },
      { property: "og:title", content: "Podcast-to-Production Studio" },
      {
        property: "og:description",
        content:
          "Drop in a script PDF and get director notes, market research, AI voices, a music bed and a mixed episode.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Studio,
});

const GENRES = [
  "technology",
  "business",
  "true crime",
  "health",
  "comedy",
  "education",
  "news",
] as const;

const MOODS = [
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

const VOICES = [
  { value: "auto", label: "Auto cast", hint: "Studio picks a voice" },
  { value: "Kore", label: "Kore", hint: "Warm, measured host" },
  { value: "Puck", label: "Puck", hint: "Bright and upbeat" },
  { value: "Charon", label: "Charon", hint: "Deep and steady" },
  { value: "Aoede", label: "Aoede", hint: "Airy, expressive" },
  { value: "Fenrir", label: "Fenrir", hint: "Gravelly, forceful" },
  { value: "Leda", label: "Leda", hint: "Youthful and clear" },
  { value: "Orus", label: "Orus", hint: "Calm narrator" },
  { value: "Zephyr", label: "Zephyr", hint: "Light and quick" },
] as const;

function intensityLabel(value: number) {
  if (value <= 25) return "Barely there";
  if (value <= 50) return "Gentle";
  if (value <= 75) return "Present";
  return "Bold";
}

const STEPS = [
  { key: "parse", label: "Reading the script", icon: FileText },
  { key: "director", label: "Director's notes", icon: ClipboardList },
  { key: "research", label: "Market research", icon: Search },
  { key: "audio", label: "Voices & music", icon: AudioLines },
  { key: "mix", label: "Mixing the episode", icon: Sparkles },
] as const;

type Report = {
  download_url?: string;
  music_url?: string;
  data?: {
    script?: {
      title?: string;
      speakers?: string[];
      dialogue_segments?: unknown[];
      topics?: string[];
    };
    director_notes?: Record<string, unknown>;
    market_research?: Record<string, unknown>;
    audio_production?: {
      audio_files?: { speaker?: string; path?: string; url?: string }[];
      final_duration_seconds?: number;
      sentiment_analysis?: Record<string, unknown>;
      recommendations?: string[];
    };
  };
};

const DEFAULT_API = "http://localhost:8100";

function Studio() {
  const [apiBase, setApiBase] = useState(DEFAULT_API);
  const [showSettings, setShowSettings] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [genre, setGenre] = useState<string>("technology");
  const [mood, setMood] = useState<string>("auto");
  const [intensity, setIntensity] = useState<number[]>([60]);
  const [duck, setDuck] = useState<number[]>([-18]);
  const [cast, setCast] = useState<string[]>([]);
  const [castLoading, setCastLoading] = useState(false);
  const [voices, setVoices] = useState<Record<string, string>>({});


  const [running, setRunning] = useState(false);
  const [step, setStep] = useState(-1);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const saved = window.localStorage.getItem("p2p-api-base");
    if (saved) setApiBase(saved);
  }, []);

  useEffect(() => {
    if (!running) return;
    setStep(0);
    const timers = [1200, 9000, 20000, 38000].map((delay, i) =>
      window.setTimeout(() => setStep(i + 1), delay),
    );
    return () => timers.forEach(window.clearTimeout);
  }, [running]);

  const progress = running
    ? Math.min(95, ((step + 1) / STEPS.length) * 100)
    : report
      ? 100
      : 0;

  const production = report?.data?.audio_production;
  const clips = production?.audio_files ?? [];
  const speakers = report?.data?.script?.speakers ?? [];
  const recommendations = production?.recommendations ?? [];

  const absolute = useMemo(
    () => (url?: string) =>
      url ? (url.startsWith("http") ? url : `${apiBase.replace(/\/$/, "")}${url}`) : undefined,
    [apiBase],
  );

  const pickFile = (next?: File | null) => {
    if (!next) return;
    if (!next.name.toLowerCase().endsWith(".pdf")) {
      setError("Please choose a PDF script.");
      return;
    }
    setError(null);
    setFile(next);
    void loadCast(next);
  };

  async function loadCast(pdf: File) {
    setCast([]);
    setVoices({});
    setCastLoading(true);
    try {
      const body = new FormData();
      body.append("file", pdf);
      const res = await fetch(`${apiBase.replace(/\/$/, "")}/analyze`, {
        method: "POST",
        body,
      });
      if (!res.ok) throw new Error(`Studio responded with ${res.status}`);
      const json = (await res.json()) as {
        script_analysis?: { speakers?: string[] };
      };
      const found = json.script_analysis?.speakers ?? [];
      setCast(found);
      setVoices(Object.fromEntries(found.map((s) => [s, "auto"])));
    } catch {
      setCast([]);
    } finally {
      setCastLoading(false);
    }
  }

  async function produce() {
    if (!file || running) return;
    setRunning(true);
    setReport(null);
    setError(null);
    try {
      const body = new FormData();
      body.append("file", file);
      const params = new URLSearchParams({
        genre,
        music_mood: mood,
        music_intensity: ((intensity[0] ?? 60) / 100).toFixed(2),
        duck_db: String(duck[0] ?? -18),
      });
      const chosen = Object.fromEntries(
        Object.entries(voices).filter(([, v]) => v && v !== "auto"),
      );
      if (Object.keys(chosen).length) {
        params.set("voice_map", JSON.stringify(chosen));
      }

      const res = await fetch(`${apiBase.replace(/\/$/, "")}/upload?${params}`, {
        method: "POST",
        body,
      });

      if (!res.ok) throw new Error(`Studio responded with ${res.status}`);
      const json = (await res.json()) as Report;
      setReport(json);
      setStep(STEPS.length - 1);
    } catch (err) {
      setError(
        err instanceof Error
          ? `${err.message}. Is the production server running at ${apiBase}?`
          : "Something went wrong.",
      );
      setStep(-1);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div
      className="min-h-screen bg-background text-foreground"
      style={{ backgroundImage: "var(--gradient-stage)" }}
    >
      <div className="mx-auto w-full max-w-5xl px-5 py-10 sm:px-8 sm:py-14">
        <header className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="grid size-11 place-items-center rounded-2xl bg-primary text-primary-foreground shadow-[var(--shadow-stage)]">
              <Radio className="size-5" />
            </span>
            <div>
              <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">
                Podcast-to-Production
              </p>
              <h1 className="text-xl font-semibold sm:text-2xl">Episode Studio</h1>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowSettings((v) => !v)}
            className="text-muted-foreground"
          >
            <Settings2 className="size-4" /> Server
          </Button>
        </header>

        {showSettings && (
          <div className="mt-5 rounded-2xl border border-border bg-card/70 p-4 backdrop-blur">
            <Label htmlFor="api" className="text-xs text-muted-foreground">
              Production server address
            </Label>
            <Input
              id="api"
              value={apiBase}
              onChange={(e) => {
                setApiBase(e.target.value);
                window.localStorage.setItem("p2p-api-base", e.target.value);
              }}
              className="mt-2"
              placeholder={DEFAULT_API}
            />
          </div>
        )}

        <p className="mt-6 max-w-2xl text-balance text-lg text-muted-foreground">
          Drop in a script PDF. The studio reads it, writes director's notes, checks
          the market, casts AI voices, scores a music bed and hands you a mixed
          episode.
        </p>

        {/* Step 1 — script */}
        <section className="mt-8 rounded-3xl border border-border bg-card/70 p-5 shadow-[var(--shadow-stage)] backdrop-blur sm:p-7">
          <StepHeading index={1} title="Bring your script" />
          <div
            role="button"
            tabIndex={0}
            onClick={() => inputRef.current?.click()}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
            }}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              pickFile(e.dataTransfer.files?.[0]);
            }}
            className={cn(
              "mt-4 grid cursor-pointer place-items-center gap-2 rounded-2xl border-2 border-dashed border-border px-6 py-10 text-center transition-colors",
              dragging && "border-primary bg-primary/10",
              file && "border-primary/60 bg-primary/5",
            )}
          >
            <UploadCloud
              className={cn("size-8", file ? "text-primary" : "text-muted-foreground")}
            />
            <p className="font-medium">
              {file ? file.name : "Drag a PDF here, or click to browse"}
            </p>
            <p className="text-sm text-muted-foreground">
              {file
                ? `${(file.size / 1024).toFixed(0)} KB · ready to produce`
                : "Scripts with speaker names work best"}
            </p>
            <input
              ref={inputRef}
              type="file"
              accept="application/pdf"
              className="sr-only"
              onChange={(e) => pickFile(e.target.files?.[0])}
            />
          </div>

          <div className="mt-6 grid gap-5 sm:grid-cols-[1fr_auto] sm:items-end">
            <div>
              <StepHeading index={2} title="Pick the vibe" compact />
              <Select value={genre} onValueChange={setGenre}>
                <SelectTrigger className="mt-3 w-full sm:w-64">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {GENRES.map((g) => (
                    <SelectItem key={g} value={g} className="capitalize">
                      {g}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <Separator className="my-6" />

          <StepHeading index={3} title="Cast the voices" compact />
          {castLoading ? (
            <p className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" /> Reading the script for
              speakers…
            </p>
          ) : cast.length ? (
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              {cast.map((speaker) => {
                const value = voices[speaker] ?? "auto";
                return (
                  <div key={speaker}>
                    <Label className="flex items-center gap-1.5 text-sm">
                      <Users className="size-3.5 text-muted-foreground" /> {speaker}
                    </Label>
                    <Select
                      value={value}
                      onValueChange={(v) =>
                        setVoices((prev) => ({ ...prev, [speaker]: v }))
                      }
                    >
                      <SelectTrigger className="mt-2 w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {VOICES.map((v) => (
                          <SelectItem key={v.value} value={v.value}>
                            {v.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="mt-1.5 text-xs text-muted-foreground">
                      {VOICES.find((v) => v.value === value)?.hint}
                    </p>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="mt-3 text-sm text-muted-foreground">
              {file
                ? "No speakers detected yet — the studio will auto-cast voices."
                : "Add a script and the speakers will appear here for casting."}
            </p>
          )}

          <Separator className="my-6" />

          <StepHeading index={4} title="Music & mix" compact />
          <div className="mt-4 grid gap-6 sm:grid-cols-2">
            <div>
              <Label className="text-sm">Mood preset</Label>
              <Select value={mood} onValueChange={setMood}>
                <SelectTrigger className="mt-2 w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MOODS.map((m) => (
                    <SelectItem key={m.value} value={m.value}>
                      {m.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="mt-2 text-xs text-muted-foreground">
                {MOODS.find((m) => m.value === mood)?.hint}
              </p>
            </div>

            <div className="space-y-6">
              <div>
                <div className="flex items-baseline justify-between">
                  <Label className="text-sm">Intensity</Label>
                  <span className="text-xs text-muted-foreground">
                    {intensityLabel(intensity[0] ?? 60)}
                  </span>
                </div>
                <Slider
                  value={intensity}
                  onValueChange={setIntensity}
                  min={10}
                  max={100}
                  step={5}
                  className="mt-3"
                  aria-label="Music intensity"
                />
                <div className="mt-1.5 flex justify-between text-xs text-muted-foreground">
                  <span>Subtle</span>
                  <span>Bold</span>
                </div>
              </div>

              <div>
                <div className="flex items-baseline justify-between">
                  <Label className="text-sm">Ducking under dialogue</Label>
                  <span className="text-xs text-muted-foreground">
                    {duck[0] ?? -18} dB
                  </span>
                </div>
                <Slider
                  value={duck}
                  onValueChange={setDuck}
                  min={-40}
                  max={0}
                  step={1}
                  className="mt-3"
                  aria-label="Music ducking level in decibels"
                />
                <div className="mt-1.5 flex justify-between text-xs text-muted-foreground">
                  <span>Music barely there</span>
                  <span>Music up front</span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-7 flex flex-wrap items-center justify-between gap-4">
            <p className="text-xs text-muted-foreground">
              {mood === "auto" ? "Mood follows the director's notes" : `${mood} bed`} ·{" "}
              {intensityLabel(intensity[0] ?? 60).toLowerCase()} · ducked{" "}
              {Math.abs(duck[0] ?? -18)} dB
            </p>
            <Button
              size="lg"
              onClick={produce}
              disabled={!file || running}
              className="w-full sm:w-auto"
            >
              {running ? (
                <>
                  <Loader2 className="size-4 animate-spin" /> Producing…
                </>
              ) : (
                <>
                  <Sparkles className="size-4" /> Produce episode
                </>
              )}
            </Button>
          </div>


          {error && (
            <p className="mt-4 rounded-xl border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-foreground">
              {error}
            </p>
          )}
        </section>

        {/* Progress */}
        {(running || report) && (
          <section className="mt-6 rounded-3xl border border-border bg-card/70 p-5 backdrop-blur sm:p-7">
            <div className="flex items-center justify-between gap-4">
              <h2 className="font-semibold">In the studio</h2>
              <span className="text-sm text-muted-foreground">
                {report ? "Done" : `Step ${Math.max(step + 1, 1)} of ${STEPS.length}`}
              </span>
            </div>
            <Progress value={progress} className="mt-4" />
            <ul className="mt-5 grid gap-2 sm:grid-cols-2">
              {STEPS.map((s, i) => {
                const done = report ? true : i < step;
                const active = !report && i === step;
                const Icon = s.icon;
                return (
                  <li
                    key={s.key}
                    className={cn(
                      "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors",
                      done && "text-foreground",
                      active && "bg-primary/10 text-foreground",
                      !done && !active && "text-muted-foreground",
                    )}
                  >
                    {active ? (
                      <Loader2 className="size-4 shrink-0 animate-spin text-primary" />
                    ) : (
                      <Icon
                        className={cn(
                          "size-4 shrink-0",
                          done ? "text-primary" : "text-muted-foreground",
                        )}
                      />
                    )}
                    {s.label}
                  </li>
                );
              })}
            </ul>
          </section>
        )}

        {/* Results */}
        {report && (
          <section className="mt-6 space-y-6">
            <div className="rounded-3xl border border-primary/30 bg-card/80 p-5 shadow-[var(--shadow-stage)] backdrop-blur sm:p-7">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold">
                    {report.data?.script?.title ?? "Your episode"}
                  </h2>
                  <p className="text-sm text-muted-foreground">
                    {formatDuration(production?.final_duration_seconds)} ·{" "}
                    {clips.length} voice clips · {speakers.length} speakers
                  </p>
                </div>
                <Button asChild>
                  <a href={absolute(report.download_url)} download>
                    <Download className="size-4" /> Download episode
                  </a>
                </Button>
              </div>
              {report.download_url && (
                <audio
                  controls
                  className="mt-5 w-full"
                  src={absolute(report.download_url)}
                />
              )}
              <div className="mt-4 flex flex-wrap gap-2">
                {speakers.map((s) => (
                  <Badge key={s} variant="secondary" className="gap-1">
                    <Users className="size-3" /> {s}
                  </Badge>
                ))}
              </div>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              <Panel title="Music bed" icon={Music4}>
                {report.music_url ? (
                  <>
                    <audio controls className="w-full" src={absolute(report.music_url)} />
                    <a
                      className="mt-3 inline-flex items-center gap-1.5 text-sm text-primary underline-offset-4 hover:underline"
                      href={absolute(report.music_url)}
                      download
                    >
                      <Download className="size-3.5" /> Download music bed
                    </a>
                  </>
                ) : (
                  <p className="text-sm text-muted-foreground">No music bed generated.</p>
                )}
              </Panel>

              <Panel title="Recommendations" icon={ClipboardList}>
                {recommendations.length ? (
                  <ul className="space-y-2 text-sm">
                    {recommendations.map((r, i) => (
                      <li key={i} className="flex gap-2">
                        <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" />
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-muted-foreground">No notes returned.</p>
                )}
              </Panel>
            </div>

            <Panel title="Voice clips" icon={FileAudio}>
              <ul className="grid gap-2 sm:grid-cols-2">
                {clips.map((c, i) => {
                  const url = absolute(c.url ?? `/download/${c.path?.split("/").pop()}`);
                  return (
                    <li
                      key={i}
                      className="flex items-center justify-between gap-3 rounded-xl bg-secondary/60 px-3 py-2 text-sm"
                    >
                      <span className="truncate">
                        {i + 1}. {c.speaker ?? "Speaker"}
                      </span>
                      <a
                        href={url}
                        download
                        className="shrink-0 text-primary underline-offset-4 hover:underline"
                      >
                        <Download className="size-4" />
                        <span className="sr-only">Download clip {i + 1}</span>
                      </a>
                    </li>
                  );
                })}
              </ul>
            </Panel>

            <details className="rounded-3xl border border-border bg-card/60 p-5 backdrop-blur">
              <summary className="cursor-pointer text-sm font-medium text-muted-foreground">
                Full production report (JSON)
              </summary>
              <Separator className="my-4" />
              <pre className="max-h-96 overflow-auto text-xs leading-relaxed text-muted-foreground">
                {JSON.stringify(report.data, null, 2)}
              </pre>
            </details>
          </section>
        )}

        <footer className="mt-12 text-center text-xs text-muted-foreground">
          Director, researcher and audio-producer agents working from one script.
        </footer>
      </div>
    </div>
  );
}

function StepHeading({
  index,
  title,
  compact,
}: {
  index: number;
  title: string;
  compact?: boolean;
}) {
  return (
    <div className="flex items-center gap-2.5">
      <span className="grid size-6 place-items-center rounded-full bg-secondary text-xs font-semibold text-secondary-foreground">
        {index}
      </span>
      <h2 className={cn("font-semibold", compact ? "text-sm" : "text-base")}>{title}</h2>
    </div>
  );
}

function Panel({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-3xl border border-border bg-card/70 p-5 backdrop-blur sm:p-6">
      <div className="mb-4 flex items-center gap-2 text-sm font-semibold">
        <Icon className="size-4 text-primary" /> {title}
      </div>
      {children}
    </div>
  );
}

function formatDuration(seconds?: number) {
  if (!seconds) return "—";
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}m ${s.toString().padStart(2, "0")}s`;
}
