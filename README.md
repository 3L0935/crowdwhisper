# CrowdWhisper

Monitor, analyze, and act on Steam player feedback — automatically.

## Stack

- Python + FastAPI
- Steam Web API
- Jinja2 frontend (prototype)
- VPS deploy with Caddy

## Development

```bash
uv venv
uv pip install -e ".[dev]"
uv run uvicorn app.main:app --reload
```
