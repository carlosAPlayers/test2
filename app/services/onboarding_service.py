"""Service layer for onboarding status management."""

from typing import Optional
from uuid import UUID

from app.models.onboarding import (
    ALLOWED_TRANSITIONS,
    OnboardingStatus,
    OnboardingStatusResponse,
    StatusHistoryEntry,
)
from app.repositories.onboarding_repository import OnboardingRepository


class InvalidTransitionError(Exception):
    """Raised when an invalid status transition is attempted."""

    def __init__(
        self,
        current_status: OnboardingStatus,
        new_status: OnboardingStatus,
    ) -> None:
        self.current_status = current_status
        self.new_status = new_status
        allowed = ALLOWED_TRANSITIONS.get(current_status, set())
        allowed_names = [s.value for s in allowed] if allowed else ["nenhum"]
        super().__init__(
            f"Transição inválida de '{current_status.value}' para '{new_status.value}'. "
            f"Transições permitidas: {', '.join(allowed_names)}."
        )


class CustomerNotFoundError(Exception):
    """Raised when the customer onboarding record is not found."""

    def __init__(self, customer_id: UUID) -> None:
        self.customer_id = customer_id
        super().__init__(
            f"Registro de onboarding não encontrado para o cliente {customer_id}."
        )


class OnboardingService:
    """Manages onboarding status lifecycle and transition rules."""

    def __init__(self, repository: OnboardingRepository) -> None:
        self._repository = repository

    def get_onboarding_status(self, customer_id: UUID) -> OnboardingStatusResponse:
        """Get the current onboarding status and history for a customer.

        Raises CustomerNotFoundError if no record exists.
        """
        record = self._repository.get_by_customer_id(customer_id)
        if record is None:
            raise CustomerNotFoundError(customer_id)

        return OnboardingStatusResponse(
            customer_id=record.customer_id,
            current_status=record.current_status,
            updated_at=record.updated_at,
            history=record.history,
        )

    def create_onboarding(self, customer_id: UUID) -> OnboardingStatusResponse:
        """Initialize onboarding for a new customer.

        The initial status is always 'Aguardando documentos'.
        """
        record = self._repository.create(customer_id)
        return OnboardingStatusResponse(
            customer_id=record.customer_id,
            current_status=record.current_status,
            updated_at=record.updated_at,
            history=record.history,
        )

    def transition_status(
        self,
        customer_id: UUID,
        new_status: OnboardingStatus,
        reason: Optional[str] = None,
    ) -> OnboardingStatusResponse:
        """Transition the onboarding status for a customer.

        Validates the transition against the allowed transitions map.

        Raises:
            CustomerNotFoundError: If the customer record does not exist.
            InvalidTransitionError: If the transition is not allowed.
        """
        record = self._repository.get_by_customer_id(customer_id)
        if record is None:
            raise CustomerNotFoundError(customer_id)

        current_status = record.current_status
        self._validate_transition(current_status, new_status)

        updated_record = self._repository.update_status(
            customer_id, new_status, reason
        )

        return OnboardingStatusResponse(
            customer_id=updated_record.customer_id,
            current_status=updated_record.current_status,
            updated_at=updated_record.updated_at,
            history=updated_record.history,
        )

    def get_status_history(self, customer_id: UUID) -> list[StatusHistoryEntry]:
        """Get the full status change history for a customer.

        Raises CustomerNotFoundError if no record exists.
        """
        record = self._repository.get_by_customer_id(customer_id)
        if record is None:
            raise CustomerNotFoundError(customer_id)
        return record.history

    @staticmethod
    def _validate_transition(
        current_status: OnboardingStatus,
        new_status: OnboardingStatus,
    ) -> None:
        """Validate that a status transition is allowed.

        Raises InvalidTransitionError if the transition is not permitted.
        """
        if current_status == new_status:
            raise InvalidTransitionError(current_status, new_status)

        allowed = ALLOWED_TRANSITIONS.get(current_status, set())
        if new_status not in allowed:
            raise InvalidTransitionError(current_status, new_status)
