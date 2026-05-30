"""Steam Web API client — fetch reviews for any AppID."""

import httpx

STEAM_API_URL = "https://store.steampowered.com/appreviews/{appid}"


async def fetch_reviews(
    appid: int,
    num_per_page: int = 100,
    filter_: str = "all",
    language: str = "all",
    cursor: str = "*",
) -> dict:
    """Fetch reviews from the Steam API.

    Pagination is handled via the 'cursor' field returned in the response.
    """
    params = {
        "json": 1,
        "num_per_page": min(num_per_page, 100),
        "filter": filter_,
        "language": language,
        "cursor": cursor,
    }

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


async def fetch_all_reviews(appid: int, max_reviews: int = 1000) -> list[dict]:
    """Fetch up to max_reviews for a given AppID, paginating automatically."""
    all_reviews = []
    cursor = "*"

    while len(all_reviews) < max_reviews:
        data = await fetch_reviews(
            appid,
            num_per_page=min(100, max_reviews - len(all_reviews)),
            cursor=cursor,
        )
        reviews = data.get("reviews", [])
        if not reviews:
            break

        all_reviews.extend(reviews)
        cursor = data.get("cursor", "*")

        # If cursor didn't advance, we've hit the end
        if cursor == "*":
            break

        # Safety: don't loop forever
        if data["query_summary"].get("total_reviews", 0) <= len(all_reviews):
            break

    return all_reviews


async def get_game_info(appid: int) -> dict | None:
    """Get basic game info (name, etc.) from Steam Store API."""
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    app_data = data.get(str(appid), {})
    if app_data.get("success"):
        return app_data.get("data", {})
    return None
