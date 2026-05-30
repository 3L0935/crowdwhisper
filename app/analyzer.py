"""Review analysis — sentiment, trends, keywords."""

from collections import Counter
from datetime import datetime, timezone


def analyze_reviews(reviews: list[dict]) -> dict:
    """Analyze a list of Steam reviews and return structured insights."""
    total = len(reviews)
    if total == 0:
        return {
            "total": 0,
            "positive": 0,
            "negative": 0,
            "positive_pct": 0,
            "negative_pct": 0,
            "recent_trend": {},
            "top_keywords": [],
            "top_complaints": [],
            "top_praise": [],
            "recent_reviews": [],
        }

    positive = [r for r in reviews if r.get("voted_up")]
    negative = [r for r in reviews if not r.get("voted_up")]

    # Recent reviews (last 30 days)
    now = datetime.now(timezone.utc)
    recent = [
        r
        for r in reviews
        if r.get("timestamp_created")
        and (now - datetime.fromtimestamp(r["timestamp_created"], tz=timezone.utc)).days
        <= 30
    ]

    # Simple keyword extraction
    all_words = []
    complaint_words = []
    praise_words = []

    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "have", "has", "had", "do", "does", "did", "will", "would",
        "can", "could", "shall", "should", "may", "might", "must",
        "i", "you", "he", "she", "it", "we", "they", "me", "him",
        "her", "us", "them", "my", "your", "his", "its", "our",
        "their", "this", "that", "these", "those", "and", "but",
        "or", "nor", "not", "so", "yet", "for", "with", "without",
        "at", "from", "into", "through", "during", "before", "after",
        "above", "below", "to", "of", "in", "out", "on", "off", "over",
        "under", "again", "further", "then", "once", "here", "there",
        "when", "where", "why", "how", "all", "each", "every", "both",
        "few", "more", "most", "other", "some", "such", "no", "nor",
        "only", "own", "same", "too", "very", "just", "also", "get",
        "got", "really", "like", "one", "game", "play", "good", "bad",
        "would", "could", "even", "much", "still", "well", "back",
        "time", "make", "made", "take", "know", "see", "think",
        "thing", "things", "way", "going", "say", "said", "use",
        "used", "need", "new", "try", "tried", "fun",
    }

    for r in reviews:
        review_text = r.get("review", "").lower()
        words = review_text.split()
        filtered = [w.strip(".,!?;:\"'()[]{}") for w in words if w.strip(".,!?;:\"'()[]{}") not in stopwords and len(w) > 2]
        all_words.extend(filtered)

        if r.get("voted_up"):
            praise_words.extend(filtered)
        else:
            complaint_words.extend(filtered)

    word_counts = Counter(all_words)
    complaint_counts = Counter(complaint_words)
    praise_counts = Counter(praise_words)

    # Get top reviews for display
    def sort_by_helpful(revs):
        return sorted(
            revs,
            key=lambda r: r.get("votes_up", 0) - r.get("votes_down", 0),
            reverse=True,
        )[:10]

    return {
        "total": total,
        "positive": len(positive),
        "negative": len(negative),
        "positive_pct": round(len(positive) / total * 100, 1) if total else 0,
        "negative_pct": round(len(negative) / total * 100, 1) if total else 0,
        "recent": {
            "count": len(recent),
            "positive": len([r for r in recent if r.get("voted_up")]),
            "negative": len([r for r in recent if not r.get("voted_up")]),
        },
        "top_keywords": word_counts.most_common(20),
        "top_complaints": complaint_counts.most_common(15),
        "top_praise": praise_counts.most_common(15),
        "top_reviews": {
            "positive": sort_by_helpful(positive),
            "negative": sort_by_helpful(negative),
        },
        "recent_reviews": sort_by_helpful(recent),
    }
