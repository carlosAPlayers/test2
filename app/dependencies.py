"""Application dependency management."""

from app.repositories.onboarding_repository import OnboardingRepository
from app.services.onboarding_service import OnboardingService

# Application-level singleton instances.
# In a production application, these would be managed by a
# dependency injection container or FastAPI's Depends system.
_repository = OnboardingRepository()
_service = OnboardingService(repository=_repository)


def get_onboarding_service() -> OnboardingService:
    """Return the application-level onboarding service instance."""
    return _service


def reset_dependencies() -> None:
    """Reset all dependencies. Used for testing purposes."""
    global _repository, _service
    _repository = OnboardingRepository()
    _service = OnboardingService(repository=_repository)
