"""Review analysis — sentiment, trends, keywords."""

from collections import Counter
from datetime import datetime, timezone

# Massively expanded stopwords — covers EN, FR, DE, ES, PT, RU (basic), NL, IT
_STOPWORDS = {
    # English
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having", "do", "does", "did", "doing",
    "will", "would", "can", "could", "shall", "should", "may", "might", "must",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "his", "its", "our", "their", "mine", "yours", "hers", "ours", "theirs",
    "this", "that", "these", "those", "myself", "yourself", "himself", "herself",
    "and", "but", "or", "nor", "not", "so", "yet", "for", "with", "without",
    "at", "from", "into", "through", "during", "before", "after", "above", "below",
    "to", "of", "in", "out", "on", "off", "over", "under", "again", "further",
    "then", "once", "here", "there", "when", "where", "why", "how",
    "all", "each", "every", "both", "few", "more", "most", "other", "some", "such",
    "no", "nor", "not", "only", "own", "same", "too", "very", "just", "also",
    "get", "got", "gets", "getting", "really", "like", "one", "would", "could",
    "even", "much", "still", "well", "back", "time", "make", "made", "take", "took",
    "know", "see", "think", "thing", "things", "way", "going", "say", "said",
    "use", "used", "need", "new", "try", "tried", "fun", "go", "went", "come",
    "came", "look", "let", "put", "set", "find", "found", "give", "given",
    "tell", "told", "ask", "asked", "work", "worked", "seem", "seems", "seemed",
    "want", "wants", "wanted", "mean", "means", "meant", "done", "doing",
    "first", "last", "next", "every", "ever", "never", "always", "sometimes",
    "something", "anything", "everything", "nothing", "someone", "anyone",
    "somewhere", "anywhere", "because", "since", "while", "though", "although",
    "if", "whether", "about", "around", "between", "among", "throughout",
    "up", "down", "here", "there", "where", "hereby", "thereby",
    "enough", "almost", "nearly", "quite", "rather", "somewhat",
    "much", "many", "lot", "lots", "plenty", "little", "less", "least",
    "most", "several", "various", "regarding", "including",
    "however", "therefore", "thus", "hence", "nonetheless", "nevertheless",
    "anyway", "otherwise", "indeed", "instead", "meanwhile",
    "etc", "eg", "ie", "vs", "versus",

    # French
    "le", "la", "les", "du", "des", "de", "au", "aux", "un", "une", "que", "qui",
    "dans", "sur", "par", "pour", "avec", "sans", "est", "sont", "était", "été",
    "ont", "avaient", "avoir", "être", "fait", "faire", "a", "ces", "cette", "ce",
    "cet", "ses", "sa", "son", "mes", "ma", "mon", "tes", "ta", "ton", "nos",
    "notre", "vos", "votre", "leurs", "leur", "nous", "vous", "ils", "elles",
    "ont", "ont", "peut", "peuvent", "pouvoir", "vouloir", "bien", "tres",
    "plus", "moins", "aussi", "mais", "ou", "où", "donc", "car", "ni", "ne",
    "pas", "rien", "personne", "quelque", "quelques", "chaque", "tous", "toutes",
    "tout", "toute", "sur", "sous", "entre", "chez", "après", "avant", "pendant",
    "combien", "comment", "pourquoi", "quand", "ici", "là", "alors",

    # German
    "der", "die", "das", "den", "dem", "des", "ein", "eine", "einen", "einer",
    "einem", "eines", "und", "oder", "aber", "denn", "doch", "auch", "nicht",
    "mit", "von", "für", "zu", "auf", "an", "in", "aus", "bei", "nach", "um",
    "vor", "durch", "über", "unter", "zwischen", "neben", "gegen", "ohne",
    "ist", "sind", "war", "waren", "wird", "werden", "wurde", "würde", "kann",
    "können", "konnte", "muss", "müssen", "hat", "haben", "hatte", "hätte",
    "sein", "seine", "seinen", "seiner", "seines", "ihr", "ihre", "ihren",
    "ich", "du", "er", "sie", "es", "wir", "ihr", "sie", "Sie", "mich", "dich",
    "mir", "dir", "uns", "euch", "man", "alle", "viele", "einige", "wenige",
    "dies", "diese", "dieser", "dieses", "diesen", "diesem", "jetzt", "schon",
    "noch", "immer", "nie", "nur", "sehr", "etwas", "gar", "wohl", "auch",
    "da", "dort", "hier", "dann", "damn", "also", "blob", "halt", "eben",
    "mal", "erst", "sogar", "allerdings", "allerdings",

    # Spanish
    "el", "la", "los", "las", "lo", "un", "una", "unos", "unas", "del", "al",
    "con", "sin", "por", "para", "es", "son", "era", "eran", "ha", "han",
    "he", "hemos", "habia", "habian", "está", "estan", "estaba", "estaban",
    "tiene", "tienen", "tenia", "tenian", "muy", "mucho", "poco", "todo",
    "toda", "todos", "todas", "cada", "más", "menos", "también", "si",
    "no", "qué", "quien", "como", "cuando", "donde", "porque", "aunque",
    "pero", "sin", "entre", "contra", "hasta", "desde", "sobre",
    "yo", "tu", "el", "ella", "usted", "nosotros", "vosotros", "ellos",
    "ellas", "ustedes", "mi", "mis", "tu", "tus", "su", "sus", "nuestro",
    "nuestros", "nuestra", "nuestras", "vuestro", "vuestros",
    "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas",
    "aquel", "aquella", "aquellos", "aquellas",

    # Portuguese
    "o", "a", "os", "as", "um", "uma", "uns", "umas", "do", "da", "dos", "das",
    "no", "na", "nos", "nas", "ao", "aos", "pelo", "pela", "pelos", "pelas",
    "para", "com", "sem", "por", "de", "em", "é", "são", "era", "foram",
    "tem", "têm", "tinha", "tinham", "está", "estão", "muito", "pouco",
    "tudo", "toda", "todos", "todas", "cada", "mais", "menos", "também",
    "sim", "não", "que", "quem", "como", "quando", "onde", "porque",
    "embora", "mas", "entre", "contra", "até", "desde", "sobre",
    "eu", "tu", "ele", "ela", "nós", "vós", "eles", "elas",
    "meu", "minha", "meus", "minhas", "teu", "tua", "teus", "tuas",
    "seu", "sua", "seus", "suas", "nosso", "nossa", "nossos", "nossas",
    "este", "esta", "estes", "estas", "esse", "essa", "esses", "essas",
    "aquele", "aquela", "aqueles", "aquelas",

    # Italian
    "il", "lo", "la", "gli", "le", "un", "uno", "una", "del", "dello", "della",
    "degli", "delle", "al", "allo", "alla", "agli", "alle", "con", "senza",
    "per", "di", "da", "in", "su", "tra", "fra", "è", "sono", "era",
    "ha", "hanno", "ho", "hai", "abbiamo", "avete",
    "molto", "poco", "tutto", "tanta", "tante", "tanti", "ogni",
    "più", "meno", "anche", "ma", "però", "se", "che", "chi",
    "come", "quando", "dove", "perché", "sebbene",
    "io", "tu", "lui", "lei", "noi", "voi", "loro",
    "mio", "mia", "miei", "mie", "tuo", "tua", "tuoi", "tue",
    "suo", "sua", "suoi", "sue", "nostro", "nostra", "nostri", "nostre",
    "vostro", "vostra", "vostri", "vostre",
    "questo", "questa", "questi", "queste", "quello", "quella", "quelli", "quelle",

    # Dutch
    "de", "het", "een", "van", "met", "voor", "op", "in", "uit", "aan", "bij",
    "over", "onder", "tussen", "door", "zonder", "om", "na", "naar",
    "is", "zijn", "was", "waren", "wordt", "worden", "kan", "kunnen",
    "heeft", "hebben", "had", "hadden", "zal", "zullen",
    "ik", "jij", "hij", "zij", "het", "wij", "jullie", "zij",
    "mijn", "jouw", "zijn", "haar", "ons", "hun", "uw",
    "dit", "dat", "deze", "die", "veel", "weinig", "alle", "enkele",
    "maar", "dus", "want", "ook", "nog", "al", "even", "wel", "niet",
    "geen", "je", "u", "ze", "er", "dan", "pas",

    # Russian (basic latin transliteration — cyrillic handled separately)
    "eto", "chto", "kak", "tak", "kogda", "gde", "pochemu", "potomu",
    "no", "i", "a", "ili", "esli", "chto", "kak", "vot", "uzh", "esche",
    "uzhe", "bylo", "budet", "est", "byl", "byla", "byli",
    "ya", "ty", "on", "ona", "ono", "my", "vy", "oni",
    "menya", "tebya", "yego", "yeye", "nas", "vas", "ikh",
    "moy", "tvoy", "yego", "yeyo", "nash", "vash", "ikh",
    "ot", "do", "bez", "s", "so", "iz", "k", "ko", "u", "ob", "pro",
    "cherez", "nad", "pod", "per", "pered", "posle",

    # Common gaming-community words that are noise
    "play", "played", "playing", "game", "games", "player", "players",
    "like", "really", "just", "get", "got", "one", "even", "way",
    "much", "still", "also", "well", "back", "time", "thing", "things",
    "going", "make", "made", "take", "know", "see", "say", "said",
    "need", "new", "try", "use", "used", "fun", "go", "come",
    "first", "last", "next", "something", "anything", "everything",
    "lot", "lots", "little", "bit",
}

# Additional filter: words shorter than 3 chars or purely numeric
# (but we keep them in the original review text for display)


def _is_noise_word(word: str) -> bool:
    """Return True if this word should be excluded from keyword analysis."""
    word = word.strip(".,!?;:\"'()[]{}»«—–-")
    if len(word) < 3:
        return True
    if word.isdigit():
        return True
    if word.lower() in _STOPWORDS:
        return True
    return False


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
            "recent": {"count": 0, "positive": 0, "negative": 0},
            "top_keywords": [],
            "top_complaints": [],
            "top_praise": [],
            "top_reviews": {"positive": [], "negative": []},
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

    # Keyword extraction with noise filtering
    all_words = []
    complaint_words = []
    praise_words = []

    for r in reviews:
        review_text = r.get("review", "").lower()
        words = review_text.split()
        filtered = [
            w.strip(".,!?;:\"'()[]{}»«—–-")
            for w in words
            if not _is_noise_word(w)
        ]
        all_words.extend(filtered)

        if r.get("voted_up"):
            praise_words.extend(filtered)
        else:
            complaint_words.extend(filtered)

    word_counts = Counter(all_words)
    complaint_counts = Counter(complaint_words)
    praise_counts = Counter(praise_words)

    # Score a review's "informativeness" — combine votes + text substance
    def informative_score(r):
        text = r.get("review", "")
        votes_up = r.get("votes_up", 0)
        votes_down = r.get("votes_down", 0)
        total_votes = votes_up + votes_down

        # Penalize <10-word reviews
        word_count = len(text.split())
        if word_count < 10:
            return -1

        char_len = len(text)

        # Weighted vote score (sqrt scale)
        vote_score = 0
        if total_votes > 0:
            ratio = votes_up / total_votes
            vote_score = (votes_up ** 0.5) * ratio

        # Content bonus (capped at 500 chars)
        content_bonus = min(char_len, 500) / 500 * 3

        # Extra penalty for purely profanity/rage reviews — detect via avg word length < 3
        # (short words = screaming, not explaining)
        avg_word_len = char_len / max(word_count, 1)
        if avg_word_len < 2.5 and word_count < 20:
            content_bonus *= 0.3

        return vote_score + content_bonus

    def sort_by_helpful(revs, limit=10):
        scored = [(r, informative_score(r)) for r in revs]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [r for r, s in scored[:limit]]

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
            "positive": sort_by_helpful(positive, limit=10),
            "negative": sort_by_helpful(negative, limit=10),
        },
        "recent_reviews": sort_by_helpful(recent, limit=10),
    }
