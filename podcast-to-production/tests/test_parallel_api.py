from src.phase3_partner_integration.parallel_search import ParallelResearchTool


class FakeClient:
    def __init__(self, results):
        self.results = results
        self.last_query = None

    def search(self, query, max_results=10):
        self.last_query = query
        return {"results": self.results[:max_results]}


def test_returns_error_without_key():
    tool = ParallelResearchTool(api_key=None)
    tool.client = None
    results = tool.search_podcast_data("climate")
    assert results[0]["error"] == "Parallel API key not configured"


def test_search_maps_fields():
    tool = ParallelResearchTool(api_key="test")
    tool.client = FakeClient([
        {
            "title": "Top Climate Podcasts",
            "url": "https://example.com",
            "snippet": "A ranking of shows",
            "published_date": "2026-01-01",
        }
    ])
    results = tool.search_podcast_data("climate", genre="science")
    assert results[0]["title"] == "Top Climate Podcasts"
    assert "science" in tool.client.last_query


def test_competitor_query_shape():
    tool = ParallelResearchTool(api_key="test")
    tool.client = FakeClient([])
    tool.search_competitor_analysis("Deep Dive")
    assert "Deep Dive" in tool.client.last_query


def test_search_handles_exception():
    class Boom:
        def search(self, **_):
            raise RuntimeError("network down")

    tool = ParallelResearchTool(api_key="test")
    tool.client = Boom()
    results = tool.search_podcast_data("ai")
    assert "network down" in results[0]["error"]
