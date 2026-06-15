"""In-memory repository for onboarding status persistence."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from app.models.onboarding import (
    OnboardingStatus,
    StatusHistoryEntry,
)


class CustomerOnboardingRecord:
    """Internal record representing a customer's onboarding state."""

    def __init__(self, customer_id: UUID) -> None:
        self.customer_id = customer_id
        self.current_status = OnboardingStatus.AGUARDANDO_DOCUMENTOS
        self.updated_at = datetime.utcnow()
        self.history: list[StatusHistoryEntry] = []


class OnboardingRepository:
    """In-memory repository for customer onboarding data.

    This implementation stores data in memory. In a production environment,
    this would be replaced with a database-backed implementation.
    """

    def __init__(self) -> None:
        self._records: dict[UUID, CustomerOnboardingRecord] = {}

    def get_by_customer_id(
        self, customer_id: UUID
    ) -> Optional[CustomerOnboardingRecord]:
        """Retrieve onboarding record by customer ID."""
        return self._records.get(customer_id)

    def create(self, customer_id: UUID) -> CustomerOnboardingRecord:
        """Create a new onboarding record for a customer.

        Raises ValueError if a record already exists for the customer.
        """
        if customer_id in self._records:
            raise ValueError(
                f"Onboarding record already exists for customer {customer_id}"
            )
        record = CustomerOnboardingRecord(customer_id)
        # Record the initial status in history
        initial_entry = StatusHistoryEntry(
            customer_id=customer_id,
            previous_status=None,
            new_status=OnboardingStatus.AGUARDANDO_DOCUMENTOS,
            changed_at=record.updated_at,
            reason="Onboarding iniciado",
        )
        record.history.append(initial_entry)
        self._records[customer_id] = record
        return record

    def update_status(
        self,
        customer_id: UUID,
        new_status: OnboardingStatus,
        reason: Optional[str] = None,
    ) -> CustomerOnboardingRecord:
        """Update the onboarding status for a customer.

        This method only persists the change; validation of
        transition rules should be done in the service layer.

        Raises KeyError if the customer record does not exist.
        """
        record = self._records.get(customer_id)
        if record is None:
            raise KeyError(f"No onboarding record found for customer {customer_id}")

        previous_status = record.current_status
        now = datetime.utcnow()

        history_entry = StatusHistoryEntry(
            customer_id=customer_id,
            previous_status=previous_status,
            new_status=new_status,
            changed_at=now,
            reason=reason,
        )

        record.current_status = new_status
        record.updated_at = now
        record.history.append(history_entry)

        return record

    def exists(self, customer_id: UUID) -> bool:
        """Check if an onboarding record exists for a customer."""
        return customer_id in self._records
