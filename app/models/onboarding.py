"""Domain models for onboarding status tracking."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class OnboardingStatus(str, Enum):
    """Possible onboarding statuses as defined in the acceptance criteria."""

    AGUARDANDO_DOCUMENTOS = "Aguardando documentos"
    EM_ANALISE = "Em análise"
    ACAO_NECESSARIA = "Ação necessária"
    APROVADO = "Aprovado"
    REJEITADO = "Rejeitado"


# Allowed status transitions mapping.
# Each key maps to the set of statuses it can transition to.
ALLOWED_TRANSITIONS: dict[OnboardingStatus, set[OnboardingStatus]] = {
    OnboardingStatus.AGUARDANDO_DOCUMENTOS: {
        OnboardingStatus.EM_ANALISE,
    },
    OnboardingStatus.EM_ANALISE: {
        OnboardingStatus.ACAO_NECESSARIA,
        OnboardingStatus.APROVADO,
        OnboardingStatus.REJEITADO,
    },
    OnboardingStatus.ACAO_NECESSARIA: {
        OnboardingStatus.AGUARDANDO_DOCUMENTOS,
    },
    OnboardingStatus.APROVADO: set(),
    OnboardingStatus.REJEITADO: set(),
}


class StatusHistoryEntry(BaseModel):
    """A single record in the onboarding status change history."""

    id: UUID = Field(default_factory=uuid4)
    customer_id: UUID
    previous_status: Optional[OnboardingStatus] = None
    new_status: OnboardingStatus
    changed_at: datetime = Field(default_factory=datetime.utcnow)
    reason: Optional[str] = None


class OnboardingStatusResponse(BaseModel):
    """Response schema for the onboarding status endpoint."""

    customer_id: UUID
    current_status: OnboardingStatus
    updated_at: datetime
    history: list[StatusHistoryEntry] = Field(default_factory=list)


class StatusTransitionRequest(BaseModel):
    """Request schema for transitioning the onboarding status."""

    new_status: OnboardingStatus
    reason: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional reason for the status change.",
    )
