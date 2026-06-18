"""FastAPI application entry point."""

from fastapi import FastAPI

from app.routers.onboarding_router import router as onboarding_router

app = FastAPI(
    title="Onboarding Service",
    description="Serviço para gerenciamento de status do onboarding de clientes.",
    version="1.0.0",
)

app.include_router(onboarding_router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
