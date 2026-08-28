"""Multi-agent workflow coordinator."""

from typing import Dict, List

from src.phase2_document_processing.pdf_parser import PDFScriptParser
from src.phase2_document_processing.script_analyzer import ScriptAnalyzer
from src.phase2_document_processing.speaker_identifier import SpeakerIdentifier
from src.phase3_partner_integration.parallel_search import ParallelResearchTool

from .audio_producer_agent import AudioProducerAgent
from .director_agent import DirectorAgent
from .researcher_agent import ResearcherAgent


class PodcastOrchestrator:
    """Orchestrates the complete multi-agent workflow."""

    def __init__(self):
        self.director = DirectorAgent()
        self.researcher = ResearcherAgent()
        self.producer = AudioProducerAgent()
        self.parser = PDFScriptParser()
        self.speaker_identifier = SpeakerIdentifier()
        self.script_analyzer = ScriptAnalyzer()
        self.parallel_tool = ParallelResearchTool()

    def process_script(
        self,
        pdf_path: str,
        genre: str = "general",
        music_mood: str = "auto",
        music_intensity: float = 0.6,
    ) -> Dict:
        """
        Complete multi-agent pipeline:
        1. Parse PDF -> structured data
        2. Director analyzes structure and tone
        3. Researcher finds market intelligence
        4. Producer generates audio assets
        """
        print("Step 1: Parsing PDF script...")
        script_data = self.parser.parse(pdf_path)
        script_data["genre"] = genre
        script_data["speaker_profiles"] = self.speaker_identifier.identify(
            script_data.get("dialogue_segments", [])
        )
        script_data["structural_analysis"] = self.script_analyzer.analyze(script_data)

        print("Step 2: Director analyzing script...")
        director_analysis = self.director.run(script_data)

        print("Step 3: Researcher gathering market data...")
        research = self.researcher.run(script_data, director_analysis)

        print("Step 4: Producer generating audio...")
        audio_output = self.producer.run(
            script_data,
            director_analysis,
            music_mood=music_mood,
            music_intensity=music_intensity,
        )

        print("Orchestration complete.")

        return {
            "script_analysis": script_data,
            "director_notes": director_analysis,
            "market_research": research,
            "audio_production": audio_output,
            "recommendations": self._generate_recommendations(
                script_data, director_analysis, research
            ),
            "status": "success",
        }

    def _generate_recommendations(
        self, script_data: Dict, analysis: Dict, research: Dict
    ) -> List[str]:
        """Generate production recommendations."""
        recommendations: List[str] = []

        if len(script_data.get("speakers", [])) > 3:
            recommendations.append(
                "Consider assigning unique voices to each speaker for better "
                "listener engagement."
            )

        similar_podcasts = (
            research.get("market_data", {}).get("comparable_podcasts", [])
            or research.get("market_research", [])
        )
        if similar_podcasts and isinstance(similar_podcasts[0], dict):
            title = similar_podcasts[0].get("title") or "popular podcasts"
            recommendations.append(
                f"Format similar to {title} - consider adopting their pacing."
            )

        duration = script_data.get("estimated_duration", 30)
        if duration > 60:
            recommendations.append(
                "Consider breaking this episode into 2 parts for better "
                "listener retention."
            )

        recommendations.extend(
            script_data.get("structural_analysis", {}).get("production_notes", [])
        )

        return recommendations
