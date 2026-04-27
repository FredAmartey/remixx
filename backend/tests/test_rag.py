from app.rag import RAGRetriever


def test_retriever_returns_top_k():
    r = RAGRetriever.load()
    results = r.search("late night driving with hopeful tilt", k=10)
    assert len(results) == 10
    assert all("id" in t and "score" in t for t in results)
    # Top result has positive cosine similarity
    assert results[0]["score"] > 0
    # Results are sorted by score descending
    scores = [t["score"] for t in results]
    assert scores == sorted(scores, reverse=True)
