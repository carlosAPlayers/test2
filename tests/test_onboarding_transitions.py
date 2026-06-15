"""Tests for onboarding status transition rules."""

import pytest
from uuid import uuid4

from app.models.onboarding import ALLOWED_TRANSITIONS, OnboardingStatus
from app.repositories.onboarding_repository import OnboardingRepository
from app.services.onboarding_service import (
    CustomerNotFoundError,
    InvalidTransitionError,
    OnboardingService,
)


@pytest.fixture
def repository() -> OnboardingRepository:
    return OnboardingRepository()


@pytest.fixture
def service(repository: OnboardingRepository) -> OnboardingService:
    return OnboardingService(repository=repository)


class TestAllowedTransitions:
    """Test that the allowed transitions map is correctly defined."""

    def test_aguardando_documentos_can_transition_to_em_analise(self) -> None:
        allowed = ALLOWED_TRANSITIONS[OnboardingStatus.AGUARDANDO_DOCUMENTOS]
        assert OnboardingStatus.EM_ANALISE in allowed

    def test_aguardando_documentos_has_only_one_transition(self) -> None:
        allowed = ALLOWED_TRANSITIONS[OnboardingStatus.AGUARDANDO_DOCUMENTOS]
        assert len(allowed) == 1

    def test_em_analise_can_transition_to_acao_necessaria(self) -> None:
        allowed = ALLOWED_TRANSITIONS[OnboardingStatus.EM_ANALISE]
        assert OnboardingStatus.ACAO_NECESSARIA in allowed

    def test_em_analise_can_transition_to_aprovado(self) -> None:
        allowed = ALLOWED_TRANSITIONS[OnboardingStatus.EM_ANALISE]
        assert OnboardingStatus.APROVADO in allowed

    def test_em_analise_can_transition_to_rejeitado(self) -> None:
        allowed = ALLOWED_TRANSITIONS[OnboardingStatus.EM_ANALISE]
        assert OnboardingStatus.REJEITADO in allowed

    def test_em_analise_has_three_transitions(self) -> None:
        allowed = ALLOWED_TRANSITIONS[OnboardingStatus.EM_ANALISE]
        assert len(allowed) == 3

    def test_acao_necessaria_can_transition_to_aguardando_documentos(self) -> None:
        allowed = ALLOWED_TRANSITIONS[OnboardingStatus.ACAO_NECESSARIA]
        assert OnboardingStatus.AGUARDANDO_DOCUMENTOS in allowed

    def test_acao_necessaria_has_only_one_transition(self) -> None:
        allowed = ALLOWED_TRANSITIONS[OnboardingStatus.ACAO_NECESSARIA]
        assert len(allowed) == 1

    def test_aprovado_is_terminal(self) -> None:
        allowed = ALLOWED_TRANSITIONS[OnboardingStatus.APROVADO]
        assert len(allowed) == 0

    def test_rejeitado_is_terminal(self) -> None:
        allowed = ALLOWED_TRANSITIONS[OnboardingStatus.REJEITADO]
        assert len(allowed) == 0

    def test_all_statuses_have_transition_rules(self) -> None:
        for status in OnboardingStatus:
            assert status in ALLOWED_TRANSITIONS


class TestServiceTransitions:
    """Test status transitions through the service layer."""

    def test_initial_status_is_aguardando_documentos(
        self, service: OnboardingService
    ) -> None:
        customer_id = uuid4()
        result = service.create_onboarding(customer_id)
        assert result.current_status == OnboardingStatus.AGUARDANDO_DOCUMENTOS

    def test_valid_transition_aguardando_to_em_analise(
        self, service: OnboardingService
    ) -> None:
        customer_id = uuid4()
        service.create_onboarding(customer_id)
        result = service.transition_status(
            customer_id, OnboardingStatus.EM_ANALISE
        )
        assert result.current_status == OnboardingStatus.EM_ANALISE

    def test_valid_transition_em_analise_to_aprovado(
        self, service: OnboardingService
    ) -> None:
        customer_id = uuid4()
        service.create_onboarding(customer_id)
        service.transition_status(customer_id, OnboardingStatus.EM_ANALISE)
        result = service.transition_status(
            customer_id, OnboardingStatus.APROVADO
        )
        assert result.current_status == OnboardingStatus.APROVADO

    def test_valid_transition_em_analise_to_rejeitado(
        self, service: OnboardingService
    ) -> None:
        customer_id = uuid4()
        service.create_onboarding(customer_id)
        service.transition_status(customer_id, OnboardingStatus.EM_ANALISE)
        result = service.transition_status(
            customer_id, OnboardingStatus.REJEITADO
        )
        assert result.current_status == OnboardingStatus.REJEITADO

    def test_valid_transition_em_analise_to_acao_necessaria(
        self, service: OnboardingService
    ) -> None:
        customer_id = uuid4()
        service.create_onboarding(customer_id)
        service.transition_status(customer_id, OnboardingStatus.EM_ANALISE)
        result = service.transition_status(
            customer_id, OnboardingStatus.ACAO_NECESSARIA
        )
        assert result.current_status == OnboardingStatus.ACAO_NECESSARIA

    def test_valid_transition_acao_necessaria_to_aguardando(
        self, service: OnboardingService
    ) -> None:
        customer_id = uuid4()
        service.create_onboarding(customer_id)
        service.transition_status(customer_id, OnboardingStatus.EM_ANALISE)
        service.transition_status(customer_id, OnboardingStatus.ACAO_NECESSARIA)
        result = service.transition_status(
            customer_id, OnboardingStatus.AGUARDANDO_DOCUMENTOS
        )
        assert result.current_status == OnboardingStatus.AGUARDANDO_DOCUMENTOS

    def test_full_happy_path_cycle(
        self, service: OnboardingService
    ) -> None:
        """Test a complete onboarding cycle:
        Aguardando -> Em análise -> Ação necessária -> Aguardando -> Em análise -> Aprovado
        """
        customer_id = uuid4()
        service.create_onboarding(customer_id)

        service.transition_status(customer_id, OnboardingStatus.EM_ANALISE)
        service.transition_status(customer_id, OnboardingStatus.ACAO_NECESSARIA)
        service.transition_status(customer_id, OnboardingStatus.AGUARDANDO_DOCUMENTOS)
        service.transition_status(customer_id, OnboardingStatus.EM_ANALISE)
        result = service.transition_status(
            customer_id, OnboardingStatus.APROVADO
        )

        assert result.current_status == OnboardingStatus.APROVADO
        # Initial + 5 transitions = 6 history entries
        assert len(result.history) == 6

    def test_invalid_transition_aguardando_to_aprovado(
        self, service: OnboardingService
    ) -> None:
        customer_id = uuid4()
        service.create_onboarding(customer_id)
        with pytest.raises(InvalidTransitionError):
            service.transition_status(customer_id, OnboardingStatus.APROVADO)

    def test_invalid_transition_aguardando_to_rejeitado(
        self, service: OnboardingService
    ) -> None:
        customer_id = uuid4()
        service.create_onboarding(customer_id)
        with pytest.raises(InvalidTransitionError):
            service.transition_status(customer_id, OnboardingStatus.REJEITADO)

    def test_invalid_transition_aguardando_to_acao_necessaria(
        self, service: OnboardingService
    ) -> None:
        customer_id = uuid4()
        service.create_onboarding(customer_id)
        with pytest.raises(InvalidTransitionError):
            service.transition_status(
                customer_id, OnboardingStatus.ACAO_NECESSARIA
            )

    def test_invalid_transition_from_aprovado(
        self, service: OnboardingService
    ) -> None:
        customer_id = uuid4()
        service.create_onboarding(customer_id)
        service.transition_status(customer_id, OnboardingStatus.EM_ANALISE)
        service.transition_status(customer_id, OnboardingStatus.APROVADO)

        for target_status in OnboardingStatus:
            with pytest.raises(InvalidTransitionError):
                service.transition_status(customer_id, target_status)

    def test_invalid_transition_from_rejeitado(
        self, service: OnboardingService
    ) -> None:
        customer_id = uuid4()
        service.create_onboarding(customer_id)
        service.transition_status(customer_id, OnboardingStatus.EM_ANALISE)
        service.transition_status(customer_id, OnboardingStatus.REJEITADO)

        for target_status in OnboardingStatus:
            with pytest.raises(InvalidTransitionError):
                service.transition_status(customer_id, target_status)

    def test_transition_same_status_raises_error(
        self, service: OnboardingService
    ) -> None:
        customer_id = uuid4()
        service.create_onboarding(customer_id)
        with pytest.raises(InvalidTransitionError):
            service.transition_status(
                customer_id, OnboardingStatus.AGUARDANDO_DOCUMENTOS
            )

    def test_transition_nonexistent_customer_raises_error(
        self, service: OnboardingService
    ) -> None:
        with pytest.raises(CustomerNotFoundError):
            service.transition_status(uuid4(), OnboardingStatus.EM_ANALISE)

    def test_transition_with_reason(
        self, service: OnboardingService
    ) -> None:
        customer_id = uuid4()
        service.create_onboarding(customer_id)
        reason = "Documentos recebidos com sucesso"
        result = service.transition_status(
            customer_id, OnboardingStatus.EM_ANALISE, reason=reason
        )
        last_entry = result.history[-1]
        assert last_entry.reason == reason


class TestServiceHistory:
    """Test status change history tracking."""

    def test_initial_history_has_one_entry(
        self, service: OnboardingService
    ) -> None:
        customer_id = uuid4()
        result = service.create_onboarding(customer_id)
        assert len(result.history) == 1

    def test_initial_history_entry_has_no_previous_status(
        self, service: OnboardingService
    ) -> None:
        customer_id = uuid4()
        result = service.create_onboarding(customer_id)
        assert result.history[0].previous_status is None
        assert result.history[0].new_status == OnboardingStatus.AGUARDANDO_DOCUMENTOS

    def test_history_records_previous_and_new_status(
        self, service: OnboardingService
    ) -> None:
        customer_id = uuid4()
        service.create_onboarding(customer_id)
        service.transition_status(customer_id, OnboardingStatus.EM_ANALISE)
        history = service.get_status_history(customer_id)

        assert len(history) == 2
        last = history[-1]
        assert last.previous_status == OnboardingStatus.AGUARDANDO_DOCUMENTOS
        assert last.new_status == OnboardingStatus.EM_ANALISE

    def test_history_entries_have_timestamps(
        self, service: OnboardingService
    ) -> None:
        customer_id = uuid4()
        service.create_onboarding(customer_id)
        service.transition_status(customer_id, OnboardingStatus.EM_ANALISE)
        history = service.get_status_history(customer_id)

        for entry in history:
            assert entry.changed_at is not None

    def test_history_preserves_chronological_order(
        self, service: OnboardingService
    ) -> None:
        customer_id = uuid4()
        service.create_onboarding(customer_id)
        service.transition_status(customer_id, OnboardingStatus.EM_ANALISE)
        service.transition_status(customer_id, OnboardingStatus.ACAO_NECESSARIA)
        history = service.get_status_history(customer_id)

        for i in range(1, len(history)):
            assert history[i].changed_at >= history[i - 1].changed_at

    def test_history_for_nonexistent_customer_raises_error(
        self, service: OnboardingService
    ) -> None:
        with pytest.raises(CustomerNotFoundError):
            service.get_status_history(uuid4())

    def test_history_entries_have_customer_id(
        self, service: OnboardingService
    ) -> None:
        customer_id = uuid4()
        service.create_onboarding(customer_id)
        service.transition_status(customer_id, OnboardingStatus.EM_ANALISE)
        history = service.get_status_history(customer_id)

        for entry in history:
            assert entry.customer_id == customer_id
