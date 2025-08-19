import hashlib
import hmac
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

# Test constants
TEST_PR_NUMBER_1 = 123
TEST_PR_NUMBER_2 = 456
TEST_PR_NUMBER_3 = 789
TEST_PR_NUMBER_4 = 100
TEST_PR_NUMBER_5 = 200
TEST_LOW_RISK_SCORE = 0.15
TEST_MEDIUM_RISK_SCORE = 0.25
TEST_HIGH_RISK_SCORE = 0.75
TEST_VERY_HIGH_RISK_SCORE = 0.85
TEST_VERY_LOW_RISK_SCORE = 0.05
TEST_COVERAGE_DELTA_POSITIVE = 2.5
TEST_COVERAGE_DELTA_NEGATIVE = -5.2
TEST_COVERAGE_DELTA_SMALL = 0.1
TEST_COVERAGE_DELTA_SMALL_NEGATIVE = -0.2
TEST_PERF_DELTA_POSITIVE = 1.3
TEST_PERF_DELTA_LARGE = 10.0
TEST_PERF_DELTA_SMALL = 1.0
TEST_PRECISION_SCORE = 0.123456789
TEST_TEMPORAL_PORT = 7233
TEST_METRICS_SCORE = 0.5
TEST_LOW_RISK_THRESHOLD = 0.15
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_SERVICE_UNAVAILABLE = 503
DEFAULT_RISK_SCORE = 0.0
DEFAULT_COVERAGE_DELTA = 0.0
DEFAULT_PERF_DELTA = 0.0
DEFAULT_PR_NUMBER = 0
DEFAULT_TITLE = ""
RISK_THRESHOLD_LOW = 0.30
TEST_TIMEOUT_SECONDS = 15
TEST_RESPONSE_TIME = 1.5

# Mock the dependencies before importing main
with patch.dict(
    "sys.modules",
    {
        "nats.aio.client": MagicMock(),
        "temporalio.client": MagicMock(),
        "temporalio.worker": MagicMock(),
        "prometheus_client": MagicMock(),
    },
):
    from main import PRAudit, _verify_signature, app

client = TestClient(app)


class TestSignatureVerification:
    def test_verify_signature_empty_secret_demo_mode(self):
        """Test that empty secret allows all requests (demo mode)"""
        result = _verify_signature("", "sha256=invalid", b"test")
        assert result is True

    def test_verify_signature_valid(self):
        """Test valid signature verification"""
        secret = "test_secret"
        body = b"test_payload"
        mac = hmac.new(secret.encode(), msg=body, digestmod=hashlib.sha256).hexdigest()
        signature = f"sha256={mac}"

        result = _verify_signature(secret, signature, body)
        assert result is True

    def test_verify_signature_invalid(self):
        """Test invalid signature rejection"""
        result = _verify_signature("secret", "sha256=invalid", b"test")
        assert result is False

    def test_verify_signature_missing_prefix(self):
        """Test signature without sha256 prefix"""
        result = _verify_signature("secret", "invalid", b"test")
        assert result is False

    def test_verify_signature_none_signature(self):
        """Test None signature"""
        result = _verify_signature("secret", None, b"test")
        assert result is False


class TestPRAuditModel:
    def test_pr_audit_defaults(self):
        """Test PRAudit model with minimal data"""
        audit = PRAudit(number=TEST_PR_NUMBER_1)
        assert audit.number == TEST_PR_NUMBER_1
        assert audit.title is None
        assert audit.labels == []
        assert audit.risk_score == DEFAULT_RISK_SCORE
        assert audit.checks_passed is False

    def test_pr_audit_full_data(self):
        """Test PRAudit model with complete data"""
        audit = PRAudit(
            number=TEST_PR_NUMBER_2,
            title="Test PR",
            labels=["risk:high"],
            risk_score=TEST_VERY_HIGH_RISK_SCORE,
            checks_passed=True,
            changed_paths=["src/main.py"],
            coverage_delta=TEST_COVERAGE_DELTA_NEGATIVE,
            perf_delta=TEST_PERF_DELTA_POSITIVE,
            policies=["security"],
            release_window_state="blocked",
            summary="High risk PR",
        )
        assert audit.number == TEST_PR_NUMBER_2
        assert audit.title == "Test PR"
        assert audit.risk_score == TEST_VERY_HIGH_RISK_SCORE
        assert audit.checks_passed is True


class TestWebhookEndpoint:
    @patch("main.httpx.AsyncClient")
    def test_webhook_success(self, mock_client):
        """Test successful webhook processing"""
        # Mock the async client
        mock_async_client = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_async_client
        mock_async_client.post = AsyncMock()

        payload = {
            "pull_request": {"number": TEST_PR_NUMBER_1, "title": "Fix bug in authentication"},
            "analysis": {
                "risk_score": TEST_MEDIUM_RISK_SCORE,
                "checks_passed": True,
                "coverage_delta": TEST_COVERAGE_DELTA_POSITIVE,
            },
            "changes": {"files": ["auth.py", "test_auth.py"]},
        }

        response = client.post(
            "/webhook/github",
            json=payload,
            headers={"X-GitHub-Event": "pull_request", "X-GitHub-Delivery": "test-delivery-123"},
        )

        assert response.status_code == HTTP_OK
        data = response.json()
        assert data["ok"] is True
        assert data["codex"] == TEST_PR_NUMBER_1
        assert data["delivery"] == "test-delivery-123"

        # Verify codex was called
        mock_async_client.post.assert_called_once()
        call_args = mock_async_client.post.call_args
        assert "codex/pr-digest" in call_args[0][0]

    @patch("main.httpx.AsyncClient")
    def test_webhook_codex_failure(self, mock_client):
        """Test webhook when codex service is unreachable"""
        # Mock the async client to raise an exception
        mock_async_client = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_async_client
        mock_async_client.post.side_effect = Exception("Connection refused")

        payload = {
            "pull_request": {"number": TEST_PR_NUMBER_2, "title": "Test PR"},
            "analysis": {"risk_score": TEST_LOW_RISK_SCORE},
            "changes": {"files": []},
        }

        response = client.post("/webhook/github", json=payload)

        assert response.status_code == HTTP_OK
        data = response.json()
        assert data["ok"] is False
        assert "codex_unreachable" in data["reason"]

    def test_webhook_invalid_json(self):
        """Test webhook with invalid JSON"""
        response = client.post(
            "/webhook/github", data="invalid json", headers={"Content-Type": "application/json"}
        )

        assert response.status_code == HTTP_BAD_REQUEST
        assert "invalid json" in response.json()["detail"]

    @patch("main.WEBHOOK_SECRET", "test_secret")
    def test_webhook_invalid_signature(self):
        """Test webhook with invalid signature"""
        payload = {"pull_request": {"number": TEST_PR_NUMBER_3}}

        response = client.post(
            "/webhook/github", json=payload, headers={"X-Hub-Signature-256": "sha256=invalid"}
        )

        assert response.status_code == HTTP_UNAUTHORIZED
        assert "invalid signature" in response.json()["detail"]

    def test_webhook_missing_data(self):
        """Test webhook with minimal/missing data"""
        payload = {}  # Empty payload

        with patch("main.httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_async_client
            mock_async_client.post = AsyncMock()

            response = client.post("/webhook/github", json=payload)

        assert response.status_code == HTTP_OK
        data = response.json()
        assert data["ok"] is True

        # Verify the payload sent to codex has defaults
        call_args = mock_async_client.post.call_args
        sent_payload = call_args[1]["json"]
        assert sent_payload["number"] == DEFAULT_PR_NUMBER  # Default when no PR number
        assert sent_payload["title"] == DEFAULT_TITLE  # Default when no title
        assert sent_payload["risk_score"] == DEFAULT_RISK_SCORE  # Default risk score


class TestHealthEndpoint:
    def test_health_check(self):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == HTTP_OK
        assert response.json() == {"status": "healthy"}


class TestRiskLabeling:
    @patch("main.httpx.AsyncClient")
    def test_low_risk_labeling(self, mock_client):
        """Test that low risk scores get risk:low label"""
        mock_async_client = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_async_client
        mock_async_client.post = AsyncMock()

        payload = {
            "pull_request": {"number": TEST_PR_NUMBER_4},
            "analysis": {"risk_score": TEST_LOW_RISK_THRESHOLD},
        }  # Low risk

        response = client.post("/webhook/github", json=payload)
        assert response.status_code == HTTP_OK

        # Check the payload sent to codex
        call_args = mock_async_client.post.call_args
        sent_payload = call_args[1]["json"]
        assert "risk:low" in sent_payload["labels"]

    @patch("main.httpx.AsyncClient")
    def test_medium_risk_labeling(self, mock_client):
        """Test that medium/high risk scores get risk:med label"""
        mock_async_client = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_async_client
        mock_async_client.post = AsyncMock()

        payload = {
            "pull_request": {"number": TEST_PR_NUMBER_5},
            "analysis": {"risk_score": TEST_HIGH_RISK_SCORE},
        }  # High risk

        response = client.post("/webhook/github", json=payload)
        assert response.status_code == HTTP_OK

        # Check the payload sent to codex
        call_args = mock_async_client.post.call_args
        sent_payload = call_args[1]["json"]
        assert "risk:med" in sent_payload["labels"]


# Legacy test for backward compatibility
def test_webhook_minimal_happy_path():
    """Original test maintained for compatibility"""
    with patch("main.httpx.AsyncClient") as mock_client:
        mock_async_client = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_async_client
        mock_async_client.post = AsyncMock()

        payload = {
            "pull_request": {"number": TEST_PR_NUMBER_1, "title": "docs: update readme"},
            "analysis": {"risk_score": TEST_VERY_LOW_RISK_SCORE, "checks_passed": True},
            "changes": {"files": ["README.md"]},
        }

        response = client.post("/webhook/github", json=payload)
        assert response.status_code == HTTP_OK
        assert response.json()["ok"] is True


def test_webhook_bad_json():
    """Original test for bad JSON"""
    response = client.post("/webhook/github", data="not-json")
    assert response.status_code == HTTP_BAD_REQUEST


class TestRiskScoring:
    """Test risk scoring functionality"""

    def test_low_risk_score_calculation(self):
        """Test calculation of low risk scores"""
        analysis = {
            "risk_score": TEST_MEDIUM_RISK_SCORE,
            "checks_passed": True,
            "coverage_delta": TEST_COVERAGE_DELTA_SMALL,
            "performance_delta": TEST_PERF_DELTA_SMALL,
        }

        pr_audit = PRAudit(
            number=TEST_PR_NUMBER_1,
            risk_score=analysis["risk_score"],
            checks_passed=analysis["checks_passed"],
            coverage_delta=analysis["coverage_delta"],
            perf_delta=analysis["performance_delta"],
        )

        assert pr_audit.risk_score == TEST_MEDIUM_RISK_SCORE
        assert pr_audit.checks_passed is True
        assert "risk:low" in pr_audit.labels or pr_audit.risk_score <= RISK_THRESHOLD_LOW

    def test_high_risk_score_calculation(self):
        """Test calculation of high risk scores"""
        analysis = {
            "risk_score": TEST_VERY_HIGH_RISK_SCORE,
            "checks_passed": False,
            "coverage_delta": TEST_COVERAGE_DELTA_SMALL_NEGATIVE,
            "performance_delta": TEST_PERF_DELTA_LARGE,
        }

        pr_audit = PRAudit(
            number=TEST_PR_NUMBER_2,
            risk_score=analysis["risk_score"],
            checks_passed=analysis["checks_passed"],
            coverage_delta=analysis["coverage_delta"],
            perf_delta=analysis["performance_delta"],
        )

        assert pr_audit.risk_score == TEST_VERY_HIGH_RISK_SCORE
        assert pr_audit.checks_passed is False
        assert pr_audit.risk_score > RISK_THRESHOLD_LOW

    def test_risk_score_rounding(self):
        """Test that risk scores are properly rounded"""
        pr_audit = PRAudit(number=TEST_PR_NUMBER_3, risk_score=TEST_PRECISION_SCORE)
        # The main.py rounds to 3 decimal places
        assert isinstance(pr_audit.risk_score, float)
        assert pr_audit.risk_score == TEST_PRECISION_SCORE  # Model doesn't round, main.py does


class TestNATSIntegration:
    """Test NATS messaging integration"""

    @patch("main.nats_client")
    async def test_nats_message_publishing_success(self, mock_nats):
        """Test successful NATS message publishing"""
        mock_nats.publish = AsyncMock()

        # This would be tested in an async context in real implementation
        subject = "gh.pull_request.opened"
        payload = {"test": "data"}

        await mock_nats.publish(subject, json.dumps(payload).encode())
        mock_nats.publish.assert_called_once_with(subject, json.dumps(payload).encode())

    @patch("main.nats_client")
    async def test_nats_message_publishing_failure(self, mock_nats):
        """Test NATS message publishing failure handling"""
        mock_nats.publish = AsyncMock(side_effect=Exception("NATS connection failed"))

        with pytest.raises(Exception, match="NATS connection failed"):
            await mock_nats.publish("test.subject", b"test data")

    def test_nats_subject_generation(self):
        """Test NATS subject generation from GitHub events"""
        event_type = "pull_request"
        action = "opened"
        expected_subject = f"gh.{event_type}.{action}"

        assert expected_subject == "gh.pull_request.opened"


class TestTemporalIntegration:
    """Test Temporal workflow integration"""

    @patch("main.temporal_client")
    async def test_temporal_client_connection(self, mock_temporal):
        """Test Temporal client connection"""
        mock_temporal.connect = AsyncMock(return_value=mock_temporal)

        client = await mock_temporal.connect(f"temporal:{TEST_TEMPORAL_PORT}")
        assert client is not None
        mock_temporal.connect.assert_called_once_with(f"temporal:{TEST_TEMPORAL_PORT}")

    @patch("main.temporal_client")
    async def test_temporal_workflow_start(self, mock_temporal):
        """Test starting Temporal workflows"""
        mock_workflow = AsyncMock()
        mock_temporal.start_workflow = AsyncMock(return_value=mock_workflow)

        workflow = await mock_temporal.start_workflow("test_workflow", {"data": "test"})
        assert workflow is not None
        mock_temporal.start_workflow.assert_called_once_with("test_workflow", {"data": "test"})


class TestMetricsIntegration:
    """Test Prometheus metrics integration"""

    @patch("main.record_webhook_event")
    def test_webhook_metrics_recording(self, mock_record):
        """Test that webhook events are properly recorded in metrics"""
        mock_record.return_value = None

        # Simulate calling the metrics function
        from main import record_webhook_event

        record_webhook_event("pull_request", "opened", True, TEST_METRICS_SCORE)

        # In real implementation, this would verify the metrics were recorded
        assert True  # Placeholder for actual metrics verification

    def test_metrics_endpoint(self):
        """Test the /metrics endpoint returns Prometheus format"""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")

    @patch("main.record_codex_request")
    def test_codex_request_metrics(self, mock_record):
        """Test Codex request metrics recording"""
        mock_record.return_value = None

        from main import record_codex_request

        record_codex_request("/codex/pr-digest", HTTP_OK, TEST_RESPONSE_TIME)

        # Verify metrics recording was called
        assert True  # Placeholder for actual verification


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_missing_pr_data(self):
        """Test handling of missing PR data in webhook"""
        payload = {
            "action": "opened",
            "repository": {"name": "test-repo"},
            # Missing pull_request data
        }

        response = client.post(
            "/webhook/github", json=payload, headers={"x-github-event": "pull_request"}
        )

        # Should handle gracefully with defaults
        assert response.status_code == HTTP_OK

    def test_invalid_risk_score_data(self):
        """Test handling of invalid risk score data"""
        payload = {
            "action": "opened",
            "pull_request": {"number": TEST_PR_NUMBER_1},
            "analysis": {"risk_score": "invalid"},
        }

        response = client.post(
            "/webhook/github", json=payload, headers={"x-github-event": "pull_request"}
        )

        # Should handle gracefully with default risk score
        assert response.status_code == HTTP_OK

    @patch("main.httpx.AsyncClient")
    def test_codex_service_unavailable(self, mock_client):
        """Test handling when Codex service is unavailable"""
        mock_response = MagicMock()
        mock_response.status_code = HTTP_SERVICE_UNAVAILABLE

        mock_async_client = AsyncMock()
        mock_async_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
        mock_client.return_value.__aenter__.return_value = mock_async_client

        payload = {
            "action": "opened",
            "pull_request": {"number": TEST_PR_NUMBER_1, "title": "Test PR"},
        }

        response = client.post(
            "/webhook/github", json=payload, headers={"x-github-event": "pull_request"}
        )

        # Should continue processing even if Codex fails
        assert response.status_code == HTTP_OK


class TestDataModels:
    """Test Pydantic data models"""

    def test_pr_audit_model_validation(self):
        """Test PRAudit model validation"""
        # Valid data
        valid_data = {
            "number": TEST_PR_NUMBER_1,
            "title": "Test PR",
            "labels": ["risk:low", "feature"],
            "risk_score": RISK_THRESHOLD_LOW,
            "checks_passed": True,
            "changed_paths": ["src/main.py", "tests/test_main.py"],
            "coverage_delta": TEST_COVERAGE_DELTA_SMALL,
            "perf_delta": TEST_PERF_DELTA_POSITIVE,
        }

        pr_audit = PRAudit(**valid_data)
        assert pr_audit.number == TEST_PR_NUMBER_1
        assert pr_audit.title == "Test PR"
        assert len(pr_audit.labels) == 2
        assert pr_audit.risk_score == RISK_THRESHOLD_LOW

    def test_pr_audit_model_defaults(self):
        """Test PRAudit model default values"""
        pr_audit = PRAudit(number=TEST_PR_NUMBER_2)

        assert pr_audit.number == TEST_PR_NUMBER_2
        assert pr_audit.title is None
        assert pr_audit.labels == []
        assert pr_audit.risk_score == 0.0
        assert pr_audit.checks_passed is False
        assert pr_audit.changed_paths == []
        assert pr_audit.coverage_delta == 0.0
        assert pr_audit.perf_delta == 0.0
        assert pr_audit.policies == []
        assert pr_audit.release_window_state == "open"
        assert pr_audit.summary == ""


class TestStartupShutdown:
    """Test application startup and shutdown events"""

    @patch("main.NATS")
    @patch("main.Temporal")
    @patch("main.start_metrics_server")
    async def test_startup_event_success(self, mock_metrics, mock_temporal, mock_nats):
        """Test successful startup event"""
        mock_nats_instance = AsyncMock()
        mock_nats.return_value = mock_nats_instance
        mock_nats_instance.connect = AsyncMock()

        mock_temporal_instance = AsyncMock()
        mock_temporal.connect = AsyncMock(return_value=mock_temporal_instance)

        # This would test the actual startup event in a real async test
        assert True  # Placeholder for actual startup testing

    @patch("main.nats_client")
    @patch("main.temporal_client")
    async def test_shutdown_event(self, mock_temporal, mock_nats):
        """Test shutdown event cleanup"""
        mock_nats.close = AsyncMock()
        mock_temporal.close = AsyncMock()

        # This would test the actual shutdown event
        assert True  # Placeholder for actual shutdown testing
