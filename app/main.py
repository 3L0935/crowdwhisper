"""CrowdWhisper — FastAPI application."""

import jinja2
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.steam import fetch_all_reviews, get_game_info
from app.analyzer import analyze_reviews

app = FastAPI(title="CrowdWhisper", version="0.1.0")

HERE = Path(__file__).parent

# Build Jinja2 env directly with a noop cache to avoid starlette conflicts
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(HERE / "templates")),
    autoescape=jinja2.select_autoescape(["html", "xml"]),
    cache_size=0,  # disable cache to avoid starlette cache-key conflict
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
            result={"error": "Please enter a valid Steam AppID (numbers only)."},
            appid=appid,
        )

    appid_int = int(appid.strip())

    try:
        game_info = await get_game_info(appid_int)
        reviews = await fetch_all_reviews(appid_int, max_reviews=500)
        analysis = analyze_reviews(reviews)
        analysis["game_name"] = (
            game_info.get("name", f"AppID {appid_int}")
            if game_info
            else f"AppID {appid_int}"
        )
        analysis["game_img"] = (
            game_info.get("header_image", "") if game_info else ""
        )
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
        reviews = await fetch_all_reviews(appid, max_reviews=500)
        analysis = analyze_reviews(reviews)
        analysis["game_name"] = (
            game_info.get("name", f"AppID {appid}")
            if game_info
            else f"AppID {appid}"
        )
        return analysis
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
