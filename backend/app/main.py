import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import ask, dashboard, inventory, listing, ml, profit, upload, usage

app = FastAPI(title="AI Seller Copilot API")

frontend_origins = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(upload.router)
app.include_router(dashboard.router)
app.include_router(listing.router)
app.include_router(inventory.router)
app.include_router(usage.router)
app.include_router(ask.router)
app.include_router(ml.router)
app.include_router(profit.router)
