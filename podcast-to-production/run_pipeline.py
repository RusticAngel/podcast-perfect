"""End-to-end pipeline run: PDF -> agents -> audio artifacts."""

import json
import os
import sys

from src.phase4_adk_agents.orchestrator import PodcastOrchestrator
from src.tools import audio_utils

PDF = sys.argv[1] if len(sys.argv) > 1 else "static/demo_script.pdf"
GENRE = sys.argv[2] if len(sys.argv) > 2 else "technology"
OUT = "outputs"


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    result = PodcastOrchestrator().process_script(PDF, genre=GENRE)

    production = result["audio_production"]
    clips = [f["audio_path"] for f in production["audio_files"] if f.get("audio_path")]
    print(f"\nGenerated {len(clips)}/{len(production['audio_files'])} speech clips")

    dialogue = audio_utils.concatenate(clips, os.path.join(OUT, "dialogue.wav"))
    final = None
    if dialogue:
        final = audio_utils.mix_with_music(
            dialogue, production.get("music_path") or "", os.path.join(OUT, "final_episode.wav")
        )
        production["dialogue_track"] = dialogue
        production["final_episode"] = final
        production["final_duration_seconds"] = audio_utils.duration_seconds(final or dialogue)

    with open(os.path.join(OUT, "production_report.json"), "w") as handle:
        json.dump(result, handle, indent=2, default=str)

    print("Director tone:", result["director_notes"].get("tone"))
    print("Director engine:", result["director_notes"].get("engine"))
    print("Research engine:", result["market_research"].get("engine"))
    print("Music bed:", production.get("music_path"))
    print("Final episode:", final, production.get("final_duration_seconds"), "s")
    print("Recommendations:", json.dumps(result["recommendations"][:5], indent=2))


if __name__ == "__main__":
    main()
