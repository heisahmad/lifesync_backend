from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import users, insights, sync, health
from app.core.config import settings
from app.db.base import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix=settings.API_V1_STR + "/users", tags=["users"])
app.include_router(insights.router, prefix=settings.API_V1_STR + "/insights", tags=["insights"])
app.include_router(sync.router, prefix=settings.API_V1_STR + "/sync", tags=["sync"])
app.include_router(health.router, prefix=settings.API_V1_STR + "/health", tags=["health"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)