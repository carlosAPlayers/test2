"""Tests for onboarding status API endpoints."""

import pytest
from uuid import uuid4, UUID

from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import reset_dependencies
from app.models.onboarding import OnboardingStatus


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    """Reset application state before each test."""
    reset_dependencies()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def customer_id() -> UUID:
    return uuid4()


@pytest.fixture
def onboarded_customer(client: TestClient, customer_id: UUID) -> UUID:
    """Create an onboarding record and return the customer ID."""
    client.post(f"/customers/{customer_id}/onboarding-status")
    return customer_id


class TestGetOnboardingStatus:
    """Tests for GET /customers/{id}/onboarding-status."""

    def test_get_status_returns_current_status(
        self, client: TestClient, onboarded_customer: UUID
    ) -> None:
        response = client.get(
            f"/customers/{onboarded_customer}/onboarding-status"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["current_status"] == OnboardingStatus.AGUARDANDO_DOCUMENTOS.value

    def test_get_status_returns_customer_id(
        self, client: TestClient, onboarded_customer: UUID
    ) -> None:
        response = client.get(
            f"/customers/{onboarded_customer}/onboarding-status"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["customer_id"] == str(onboarded_customer)

    def test_get_status_returns_history(
        self, client: TestClient, onboarded_customer: UUID
    ) -> None:
        response = client.get(
            f"/customers/{onboarded_customer}/onboarding-status"
        )
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert len(data["history"]) == 1

    def test_get_status_returns_updated_at(
        self, client: TestClient, onboarded_customer: UUID
    ) -> None:
        response = client.get(
            f"/customers/{onboarded_customer}/onboarding-status"
        )
        assert response.status_code == 200
        data = response.json()
        assert "updated_at" in data

    def test_get_status_nonexistent_customer_returns_404(
        self, client: TestClient
    ) -> None:
        response = client.get(
            f"/customers/{uuid4()}/onboarding-status"
        )
        assert response.status_code == 404

    def test_get_status_invalid_uuid_returns_422(
        self, client: TestClient
    ) -> None:
        response = client.get("/customers/invalid-uuid/onboarding-status")
        assert response.status_code == 422


class TestCreateOnboarding:
    """Tests for POST /customers/{id}/onboarding-status."""

    def test_create_returns_201(
        self, client: TestClient, customer_id: UUID
    ) -> None:
        response = client.post(
            f"/customers/{customer_id}/onboarding-status"
        )
        assert response.status_code == 201

    def test_create_sets_initial_status(
        self, client: TestClient, customer_id: UUID
    ) -> None:
        response = client.post(
            f"/customers/{customer_id}/onboarding-status"
        )
        data = response.json()
        assert data["current_status"] == OnboardingStatus.AGUARDANDO_DOCUMENTOS.value

    def test_create_duplicate_returns_409(
        self, client: TestClient, onboarded_customer: UUID
    ) -> None:
        response = client.post(
            f"/customers/{onboarded_customer}/onboarding-status"
        )
        assert response.status_code == 409


class TestTransitionOnboardingStatus:
    """Tests for PATCH /customers/{id}/onboarding-status."""

    def test_valid_transition_returns_200(
        self, client: TestClient, onboarded_customer: UUID
    ) -> None:
        response = client.patch(
            f"/customers/{onboarded_customer}/onboarding-status",
            json={"new_status": OnboardingStatus.EM_ANALISE.value},
        )
        assert response.status_code == 200

    def test_valid_transition_updates_status(
        self, client: TestClient, onboarded_customer: UUID
    ) -> None:
        response = client.patch(
            f"/customers/{onboarded_customer}/onboarding-status",
            json={"new_status": OnboardingStatus.EM_ANALISE.value},
        )
        data = response.json()
        assert data["current_status"] == OnboardingStatus.EM_ANALISE.value

    def test_valid_transition_adds_history_entry(
        self, client: TestClient, onboarded_customer: UUID
    ) -> None:
        client.patch(
            f"/customers/{onboarded_customer}/onboarding-status",
            json={"new_status": OnboardingStatus.EM_ANALISE.value},
        )
        response = client.get(
            f"/customers/{onboarded_customer}/onboarding-status"
        )
        data = response.json()
        assert len(data["history"]) == 2

    def test_invalid_transition_returns_422(
        self, client: TestClient, onboarded_customer: UUID
    ) -> None:
        response = client.patch(
            f"/customers/{onboarded_customer}/onboarding-status",
            json={"new_status": OnboardingStatus.APROVADO.value},
        )
        assert response.status_code == 422

    def test_transition_nonexistent_customer_returns_404(
        self, client: TestClient
    ) -> None:
        response = client.patch(
            f"/customers/{uuid4()}/onboarding-status",
            json={"new_status": OnboardingStatus.EM_ANALISE.value},
        )
        assert response.status_code == 404

    def test_transition_with_reason(
        self, client: TestClient, onboarded_customer: UUID
    ) -> None:
        reason = "Todos os documentos enviados"
        response = client.patch(
            f"/customers/{onboarded_customer}/onboarding-status",
            json={
                "new_status": OnboardingStatus.EM_ANALISE.value,
                "reason": reason,
            },
        )
        data = response.json()
        last_entry = data["history"][-1]
        assert last_entry["reason"] == reason

    def test_transition_without_reason(
        self, client: TestClient, onboarded_customer: UUID
    ) -> None:
        response = client.patch(
            f"/customers/{onboarded_customer}/onboarding-status",
            json={"new_status": OnboardingStatus.EM_ANALISE.value},
        )
        data = response.json()
        last_entry = data["history"][-1]
        assert last_entry["reason"] is None

    def test_transition_with_invalid_status_returns_422(
        self, client: TestClient, onboarded_customer: UUID
    ) -> None:
        response = client.patch(
            f"/customers/{onboarded_customer}/onboarding-status",
            json={"new_status": "Status Inválido"},
        )
        assert response.status_code == 422

    def test_transition_missing_body_returns_422(
        self, client: TestClient, onboarded_customer: UUID
    ) -> None:
        response = client.patch(
            f"/customers/{onboarded_customer}/onboarding-status",
            json={},
        )
        assert response.status_code == 422

    def test_reason_max_length_validation(
        self, client: TestClient, onboarded_customer: UUID
    ) -> None:
        long_reason = "x" * 501
        response = client.patch(
            f"/customers/{onboarded_customer}/onboarding-status",
            json={
                "new_status": OnboardingStatus.EM_ANALISE.value,
                "reason": long_reason,
            },
        )
        assert response.status_code == 422


class TestGetOnboardingHistory:
    """Tests for GET /customers/{id}/onboarding-status/history."""

    def test_get_history_returns_list(
        self, client: TestClient, onboarded_customer: UUID
    ) -> None:
        response = client.get(
            f"/customers/{onboarded_customer}/onboarding-status/history"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_history_nonexistent_customer_returns_404(
        self, client: TestClient
    ) -> None:
        response = client.get(
            f"/customers/{uuid4()}/onboarding-status/history"
        )
        assert response.status_code == 404

    def test_history_tracks_multiple_transitions(
        self, client: TestClient, onboarded_customer: UUID
    ) -> None:
        client.patch(
            f"/customers/{onboarded_customer}/onboarding-status",
            json={"new_status": OnboardingStatus.EM_ANALISE.value},
        )
        client.patch(
            f"/customers/{onboarded_customer}/onboarding-status",
            json={"new_status": OnboardingStatus.APROVADO.value},
        )
        response = client.get(
            f"/customers/{onboarded_customer}/onboarding-status/history"
        )
        data = response.json()
        assert len(data) == 3  # initial + 2 transitions

    def test_history_entries_have_expected_fields(
        self, client: TestClient, onboarded_customer: UUID
    ) -> None:
        response = client.get(
            f"/customers/{onboarded_customer}/onboarding-status/history"
        )
        data = response.json()
        entry = data[0]
        assert "id" in entry
        assert "customer_id" in entry
        assert "previous_status" in entry
        assert "new_status" in entry
        assert "changed_at" in entry
        assert "reason" in entry
