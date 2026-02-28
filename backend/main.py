"""
FormWhisper Backend — FastAPI entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import session, tts, security, upload

app = FastAPI(
    title="FormWhisper API",
    description=(
        "Accessible voice-driven form filling for government aid, housing, "
        "and medical intake forms."
    ),
    version="0.1.0",
)

# ── CORS (allow all origins for dev) ─────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ────────────────────────────────────────
app.include_router(session.router)
app.include_router(tts.router)
app.include_router(security.router)
app.include_router(upload.router)


# ── Health check ─────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok", "service": "formwhisper-api", "version": "0.1.0"}
