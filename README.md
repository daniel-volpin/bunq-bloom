# bunq Bloom

bunq Bloom is a kid economy engine for the bunq Hackathon.

Current baseline:

```text
parent posts gig -> kid claims it -> kid uploads before/after photos -> backend verifies -> payment/fallback result is shown in the UI
```

## Quick Start

Run the backend and frontend in separate terminals.

### 1. Start the backend

```bash
cd apps/api
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Recommended local backend mode for the current baseline:

```text
BLOOM_AI_PROVIDER=lmstudio
BLOOM_LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1
BLOOM_LMSTUDIO_MODEL=qwen3.5-9b-mlx
BLOOM_USE_FAKE_BUNQ=true
```

Backend health check:

```text
http://127.0.0.1:8000/api/health
```

### 2. Start the frontend

```bash
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

Frontend app:

```text
http://127.0.0.1:3000/
```

Useful routes:

```text
http://127.0.0.1:3000/
http://127.0.0.1:3000/gigs
http://127.0.0.1:3000/wallet
http://127.0.0.1:3000/profile
```

## Verification

Backend tests:

```bash
cd apps/api
pytest tests
```

Frontend checks:

```bash
cd apps/web
npm run typecheck
npm run lint
```

## Notes

- The frontend proxies `/api/*` requests to the FastAPI backend through `API_BASE_URL`.
- `.env`, `bunq_context.json`, and secrets should stay local only.
- The current recommended local setup keeps bunq in fake mode while frontend/backend integration is hardened.
- Image upload is the next area to tighten after this baseline.

## More Docs

- Detailed setup and smoke tests: `docs/runbook.md`
- Product and architecture docs: `docs/README.md`
