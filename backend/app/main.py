import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db.database import engine, Base
from .api.routes import health, upload, claims

# Auto bootstrap SQLite tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Plum Adjudicate API",
    description="Automated Claim Adjudication rules and AI processing engine",
    version="1.0.0"
)

# Enable CORS for Next.js client access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Link routing blueprints
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(upload.router, prefix="/api/docs", tags=["documents"])
app.include_router(claims.router, prefix="/api/claims", tags=["claims"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
