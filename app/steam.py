"""CrowdWhisper — Steam review monitoring and analysis."""

import httpx
import re

STEAM_API_URL = "https://store.steampowered.com/appreviews/{appid}"
STEAM_STORE_API = "https://store.steampowered.com/api/appdetails?appids={appid}"


async def fetch_reviews(
    appid: int,
    num_per_page: int = 100,
    filter_: str = "all",
    language: str = "all",
    cursor: str = "*",
    day_range: int | None = None,
) -> dict:
    """Fetch reviews from the Steam API."""
    params = {
        "json": 1,
        "num_per_page": min(num_per_page, 100),
        "filter": filter_,
        "language": language,
        "cursor": cursor,
    }
    if day_range is not None:
        params["day_range"] = day_range

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            STEAM_API_URL.format(appid=appid), params=params
        )
        resp.raise_for_status()
        data = resp.json()

    if data.get("success") != 1:
        raise ValueError(
            f"Steam API returned success={data.get('success')}: "
            f"{data.get('query_summary', {})}"
        )

    return data


async def fetch_all_reviews(
    appid: int, max_reviews: int = 500
) -> tuple[list[dict], dict]:
    """Fetch up to max_reviews for a given AppID, paginating.

    Returns (reviews, query_summary) where query_summary has the REAL
    total_positive / total_negative from Steam.
    """
    all_reviews = []
    cursor = "*"
    query_summary = {}

    while len(all_reviews) < max_reviews:
        data = await fetch_reviews(
            appid,
            num_per_page=min(100, max_reviews - len(all_reviews)),
            cursor=cursor,
        )

        # Grab the real totals from the first response
        if not query_summary:
            query_summary = data.get("query_summary", {})

        reviews = data.get("reviews", [])
        if not reviews:
            break

        all_reviews.extend(reviews)
        cursor = data.get("cursor", "*")

        if cursor == "*":
            break
        if (
            query_summary.get("total_reviews", 0)
            and len(all_reviews) >= query_summary["total_reviews"]
        ):
            break

    return all_reviews, query_summary


async def fetch_recent_reviews(
    appid: int, day_range: int = 30, max_reviews: int = 500
) -> tuple[list[dict], dict]:
    """Fetch recent reviews using Steam's day_range filter."""
    all_reviews = []
    cursor = "*"
    query_summary = {}

    while len(all_reviews) < max_reviews:
        data = await fetch_reviews(
            appid,
            num_per_page=min(100, max_reviews - len(all_reviews)),
            cursor=cursor,
            day_range=day_range,
        )

        if not query_summary:
            query_summary = data.get("query_summary", {})

        reviews = data.get("reviews", [])
        if not reviews:
            break

        all_reviews.extend(reviews)
        cursor = data.get("cursor", "*")

        if cursor == "*":
            break

    return all_reviews, query_summary


async def get_game_info(appid: int) -> dict | None:
    """Get basic game info (name, etc.) from Steam Store API."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(STEAM_STORE_API.format(appid=appid))
        resp.raise_for_status()
        data = resp.json()

    app_data = data.get(str(appid), {})
    if app_data.get("success"):
        return app_data.get("data", {})
    return None


async def fetch_forum_topics(appid: int, max_topics: int = 10) -> list[dict]:
    """Fetch recent forum topics from Steam Community."""
    url = f"https://steamcommunity.com/app/{appid}/discussions/"

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        html = resp.text

    topics = []

    # Extract overlay URLs + their position
    overlays = list(
        re.finditer(
            r'class="forum_topic_overlay"[^>]*href="([^"]+)"',
            html,
        )
    )
    # Extract names + their position
    names = list(
        re.finditer(
            r'class="forum_topic_name[^"]*"[^>]*>\s*(.*?)\s*</div>',
            html,
            re.DOTALL,
        )
    )
    # Extract reply counts + their position
    replies = list(
        re.finditer(
            r'forum_topic_reply_count[^>]*>\s*(?:\s*<[^>]+>\s*)*(\d+)\s*',
            html,
        )
    )

    seen = set()
    for ov in overlays:
        url = ov.group(1)
        if not url.startswith("http"):
            url = f"https://steamcommunity.com{url}"

        if url in seen:
            continue
        seen.add(url)

        # Find nearest name after this overlay
        title = ""
        for nm in names:
            if nm.start() > ov.start():
                raw = nm.group(1)
                raw = re.sub(r"<[^>]+>", "", raw).strip()
                raw = re.sub(r"\s+", " ", raw).strip()
                if raw:
                    title = raw
                    break

        if not title or len(title) < 3:
            continue

        # Find nearest reply count after this overlay
        reply_count = 0
        for rp in replies:
            if rp.start() > ov.start():
                reply_count = int(rp.group(1))
                break

        topics.append(
            {"title": title, "url": url, "replies": reply_count}
        )

    return topics[:max_topics]
