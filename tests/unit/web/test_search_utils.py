"""
Unit tests for search utilities and deduplication logic.
"""

import pytest


def dedupe_search_results(results: list[dict]) -> list[dict]:
    """
    Deduplicate search results by contract address and chain.
    Prioritize local results over external sources.
    """
    deduped = {}
    for result in results:
        key = f"{result['ca'].lower()}:{result['chain']}"
        if key not in deduped:
            deduped[key] = result
        else:
            existing = deduped[key]
            if result['source'] == 'local':
                deduped[key] = result
            elif existing['source'] != 'local' and result.get('score') is not None:
                deduped[key] = result
    return list(deduped.values())


def merge_search_sources(local_results: list[dict], external_results: list[dict]) -> list[dict]:
    """
    Merge results from local database and external sources.
    Remove duplicates and prioritize local results.
    """
    all_results = local_results + external_results
    return dedupe_search_results(all_results)


def test_dedupe_same_token_different_sources():
    """Test deduplication prioritizes local source."""
    results = [
        {'ca': 'ABC123', 'chain': 'sol', 'source': 'moralis', 'score': 5.0},
        {'ca': 'abc123', 'chain': 'sol', 'source': 'local', 'score': 8.0},
    ]
    deduped = dedupe_search_results(results)
    assert len(deduped) == 1
    assert deduped[0]['source'] == 'local'
    assert deduped[0]['score'] == 8.0


def test_dedupe_different_chains():
    """Test that same contract address on different chains are kept separate."""
    results = [
        {'ca': 'ABC123', 'chain': 'sol', 'source': 'local', 'score': 8.0},
        {'ca': 'ABC123', 'chain': 'eth', 'source': 'local', 'score': 7.0},
    ]
    deduped = dedupe_search_results(results)
    assert len(deduped) == 2


def test_dedupe_case_insensitive():
    """Test that contract addresses are deduplicated case-insensitively."""
    results = [
        {'ca': 'ABC123', 'chain': 'sol', 'source': 'local', 'score': 8.0},
        {'ca': 'abc123', 'chain': 'sol', 'source': 'moralis', 'score': 5.0},
        {'ca': 'AbC123', 'chain': 'sol', 'source': 'local', 'score': 9.0},
    ]
    deduped = dedupe_search_results(results)
    assert len(deduped) == 1


def test_dedupe_prioritizes_local_over_external():
    """Test that local results are prioritized over external results."""
    results = [
        {'ca': 'XYZ789', 'chain': 'sol', 'source': 'moralis', 'score': 10.0},
        {'ca': 'xyz789', 'chain': 'sol', 'source': 'local', 'score': 3.0},
    ]
    deduped = dedupe_search_results(results)
    assert len(deduped) == 1
    assert deduped[0]['source'] == 'local'


def test_dedupe_prioritizes_scored_external_results():
    """Test that external results with scores are prioritized over unscored ones."""
    results = [
        {'ca': 'DEF456', 'chain': 'sol', 'source': 'moralis', 'score': None},
        {'ca': 'def456', 'chain': 'sol', 'source': 'coingecko', 'score': 7.5},
    ]
    deduped = dedupe_search_results(results)
    assert len(deduped) == 1
    assert deduped[0]['score'] == 7.5


def test_merge_empty_results():
    """Test merging with empty result sets."""
    merged = merge_search_sources([], [])
    assert merged == []


def test_merge_only_local_results():
    """Test merging with only local results."""
    local = [{'ca': 'ABC', 'chain': 'sol', 'source': 'local', 'score': 5.0}]
    merged = merge_search_sources(local, [])
    assert len(merged) == 1
    assert merged[0]['source'] == 'local'


def test_merge_only_external_results():
    """Test merging with only external results."""
    external = [{'ca': 'XYZ', 'chain': 'sol', 'source': 'moralis', 'score': 6.0}]
    merged = merge_search_sources([], external)
    assert len(merged) == 1
    assert merged[0]['source'] == 'moralis'


def test_merge_with_duplicates():
    """Test merging with duplicate tokens from different sources."""
    local = [{'ca': 'TOKEN1', 'chain': 'sol', 'source': 'local', 'score': 8.0}]
    external = [
        {'ca': 'token1', 'chain': 'sol', 'source': 'moralis', 'score': 6.0},
        {'ca': 'TOKEN2', 'chain': 'sol', 'source': 'moralis', 'score': 7.0},
    ]
    merged = merge_search_sources(local, external)
    assert len(merged) == 2
    assert any(r['ca'].lower() == 'token1' and r['source'] == 'local' for r in merged)
    assert any(r['ca'].lower() == 'token2' and r['source'] == 'moralis' for r in merged)


def test_merge_preserves_order():
    """Test that merging preserves the order of appearance."""
    local = [
        {'ca': 'A', 'chain': 'sol', 'source': 'local', 'score': 1.0},
        {'ca': 'B', 'chain': 'sol', 'source': 'local', 'score': 2.0},
    ]
    external = [
        {'ca': 'C', 'chain': 'sol', 'source': 'moralis', 'score': 3.0},
    ]
    merged = merge_search_sources(local, external)
    # Results should maintain the order of first appearance
    assert merged[0]['ca'] == 'A'
    assert merged[1]['ca'] == 'B'
    assert merged[2]['ca'] == 'C'
