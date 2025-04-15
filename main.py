from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.base import Base, engine, create_tables
from app.api.v1.endpoints import users, insights, health, finance, notifications, calendar

# Initialize database tables
create_tables()

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
app.include_router(health.router, prefix=settings.API_V1_STR + "/health", tags=["health"])
app.include_router(finance.router, prefix=settings.API_V1_STR + "/finance", tags=["finance"])
app.include_router(notifications.router, prefix=settings.API_V1_STR + "/notifications", tags=["notifications"])
app.include_router(calendar.router, prefix=settings.API_V1_STR + "/calendar", tags=["calendar"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)