"""API router for onboarding status endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.models.onboarding import (
    OnboardingStatusResponse,
    StatusHistoryEntry,
    StatusTransitionRequest,
)
from app.services.onboarding_service import (
    CustomerNotFoundError,
    InvalidTransitionError,
)
from app.dependencies import get_onboarding_service

router = APIRouter(
    prefix="/customers",
    tags=["onboarding"],
)


@router.get(
    "/{customer_id}/onboarding-status",
    response_model=OnboardingStatusResponse,
    summary="Obter status do onboarding",
    description="Retorna o status atual do onboarding e o histórico de alterações do cliente.",
    responses={
        404: {"description": "Cliente não encontrado"},
    },
)
def get_onboarding_status(customer_id: UUID) -> OnboardingStatusResponse:
    """Get the current onboarding status and history for a customer."""
    service = get_onboarding_service()
    try:
        return service.get_onboarding_status(customer_id)
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/{customer_id}/onboarding-status",
    response_model=OnboardingStatusResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Iniciar onboarding",
    description="Cria um novo registro de onboarding para o cliente com status inicial 'Aguardando documentos'.",
    responses={
        409: {"description": "Onboarding já iniciado para o cliente"},
    },
)
def create_onboarding(customer_id: UUID) -> OnboardingStatusResponse:
    """Initialize onboarding for a new customer."""
    service = get_onboarding_service()
    try:
        return service.create_onboarding(customer_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{customer_id}/onboarding-status",
    response_model=OnboardingStatusResponse,
    summary="Transicionar status do onboarding",
    description="Atualiza o status do onboarding do cliente, validando as regras de transição.",
    responses={
        404: {"description": "Cliente não encontrado"},
        422: {"description": "Transição de status inválida"},
    },
)
def transition_onboarding_status(
    customer_id: UUID,
    request: StatusTransitionRequest,
) -> OnboardingStatusResponse:
    """Transition the onboarding status for a customer."""
    service = get_onboarding_service()
    try:
        return service.transition_status(
            customer_id, request.new_status, request.reason
        )
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get(
    "/{customer_id}/onboarding-status/history",
    response_model=list[StatusHistoryEntry],
    summary="Obter histórico de alterações do onboarding",
    description="Retorna o histórico completo de alterações de status do onboarding do cliente.",
    responses={
        404: {"description": "Cliente não encontrado"},
    },
)
def get_onboarding_history(customer_id: UUID) -> list[StatusHistoryEntry]:
    """Get the full status change history for a customer."""
    service = get_onboarding_service()
    try:
        return service.get_status_history(customer_id)
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
