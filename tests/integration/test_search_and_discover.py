"""Integration tests for search and explainable discovery engines."""

from tools.search.engine import SearchEngine
from tools.discovery.recommender import DiscoveryEngine


def test_search_engine_ranking(registry):
    engine = SearchEngine(registry)
    results = engine.search("mongodb nosql")
    assert len(results) > 0
    top_result = results[0]
    assert top_result.skill.id == "mongodb"
    assert top_result.score > 0


def test_discovery_intent_matching(registry):
    engine = DiscoveryEngine(registry)
    recs = engine.discover("build a production Node.js backend with MongoDB")
    rec_ids = [r.id for r in recs]

    assert "nodejs" in rec_ids
    assert "mongodb" in rec_ids
    assert "architecture.system-validator" in rec_ids
    assert "testing" in rec_ids

    # Check that explainable reasons are populated
    for r in recs:
        assert len(r.reasons) > 0
        assert r.confidence > 0.5


def test_discovery_flutter_mobile(registry):
    engine = DiscoveryEngine(registry)
    recs = engine.discover("create a cross-platform mobile app with Flutter and Dart widgets")
    rec_ids = [r.id for r in recs]
    assert "flutter" in rec_ids
