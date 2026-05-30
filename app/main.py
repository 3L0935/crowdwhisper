"""CrowdWhisper — FastAPI application."""

import jinja2
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.steam import (
    fetch_all_reviews,
    fetch_recent_reviews,
    get_game_info,
    fetch_forum_topics,
)
from app.analyzer import analyze_reviews

app = FastAPI(title="CrowdWhisper", version="0.1.0")

HERE = Path(__file__).parent

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(HERE / "templates")),
    autoescape=jinja2.select_autoescape(["html", "xml"]),
    cache_size=0,
)

app.mount("/static", StaticFiles(directory=str(HERE / "static")), name="static")


def tpl(name: str, **kwargs):
    return HTMLResponse(jinja_env.get_template(name).render(**kwargs))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return tpl("index.html", request=request, result=None, appid="")


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(request: Request, appid: str = Form(...)):
    if not appid.strip() or not appid.strip().isdigit():
        return tpl(
            "index.html",
            request=request,
            result={"error": "Enter a valid Steam AppID (numbers only)."},
            appid=appid,
        )

    appid_int = int(appid.strip())

    try:
        game_info = await get_game_info(appid_int)

        # Fetch all reviews (gets real totals from query_summary)
        all_reviews, query_summary = await fetch_all_reviews(
            appid_int, max_reviews=500
        )

        # Fetch recent (30 days) with Steam's day_range filter
        recent_reviews, recent_summary = await fetch_recent_reviews(
            appid_int, day_range=30, max_reviews=500
        )

        # Fetch forum topics
        forum_topics = await fetch_forum_topics(appid_int)

        analysis = analyze_reviews(all_reviews)

        # Use REAL Steam totals from query_summary
        total_positive = query_summary.get("total_positive", 0)
        total_negative = query_summary.get("total_negative", 0)
        total_steam = total_positive + total_negative

        analysis["game_name"] = (
            game_info.get("name", f"AppID {appid_int}")
            if game_info
            else f"AppID {appid_int}"
        )
        analysis["game_img"] = (
            game_info.get("header_image", "") if game_info else ""
        )

        # Override with REAL Steam totals
        analysis["total_steam"] = total_steam
        analysis["positive_steam"] = total_positive
        analysis["negative_steam"] = total_negative
        analysis["positive_steam_pct"] = (
            round(total_positive / total_steam * 100, 1) if total_steam else 0
        )
        analysis["negative_steam_pct"] = (
            round(total_negative / total_steam * 100, 1) if total_steam else 0
        )

        # Recent reviews (filtered by Steam's API directly)
        analysis_recent = analyze_reviews(recent_reviews)
        analysis["recent"] = {
            "count": recent_summary.get("total_reviews", len(recent_reviews)),
            "positive": recent_summary.get("total_positive", 0),
            "negative": recent_summary.get("total_negative", 0),
        }
        analysis["recent_reviews"] = analysis_recent["top_reviews"]["negative"][
            :5
        ] + analysis_recent["top_reviews"]["positive"][:5]

        # Forum data
        analysis["forum_topics"] = forum_topics

    except ValueError as e:
        return tpl(
            "index.html",
            request=request,
            result={"error": str(e)},
            appid=appid,
        )
    except Exception as e:
        return tpl(
            "index.html",
            request=request,
            result={"error": f"API error: {e}"},
            appid=appid,
        )

    return tpl("index.html", request=request, result=analysis, appid=appid)


@app.get("/api/analyze/{appid}")
async def api_analyze(appid: int):
    """JSON API endpoint for programmatic access."""
    try:
        game_info = await get_game_info(appid)
        all_reviews, query_summary = await fetch_all_reviews(appid, max_reviews=500)
        analysis = analyze_reviews(all_reviews)
        analysis["game_name"] = (
            game_info.get("name", f"AppID {appid}")
            if game_info
            else f"AppID {appid}"
        )
        analysis["steam_totals"] = {
            "total": query_summary.get("total_reviews", 0),
            "positive": query_summary.get("total_positive", 0),
            "negative": query_summary.get("total_negative", 0),
        }
        return analysis
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
