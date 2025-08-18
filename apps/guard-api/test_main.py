import pytest
import json
import hmac
import hashlib
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app, _verify_signature, PRAudit

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
        audit = PRAudit(number=123)
        assert audit.number == 123
        assert audit.title is None
        assert audit.labels == []
        assert audit.risk_score == 0.0
        assert audit.checks_passed is False

    def test_pr_audit_full_data(self):
        """Test PRAudit model with complete data"""
        audit = PRAudit(
            number=456,
            title="Test PR",
            labels=["risk:high"],
            risk_score=0.85,
            checks_passed=True,
            changed_paths=["src/main.py"],
            coverage_delta=-5.2,
            perf_delta=1.3,
            policies=["security"],
            release_window_state="blocked",
            summary="High risk PR"
        )
        assert audit.number == 456
        assert audit.title == "Test PR"
        assert audit.risk_score == 0.85
        assert audit.checks_passed is True

class TestWebhookEndpoint:
    @patch('main.httpx.AsyncClient')
    def test_webhook_success(self, mock_client):
        """Test successful webhook processing"""
        # Mock the async client
        mock_async_client = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_async_client
        mock_async_client.post = AsyncMock()

        payload = {
            "pull_request": {
                "number": 123,
                "title": "Fix bug in authentication"
            },
            "analysis": {
                "risk_score": 0.25,
                "checks_passed": True,
                "coverage_delta": 2.5
            },
            "changes": {
                "files": ["auth.py", "test_auth.py"]
            }
        }

        response = client.post(
            "/webhook/github",
            json=payload,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-GitHub-Delivery": "test-delivery-123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["codex"] == 123
        assert data["delivery"] == "test-delivery-123"
        
        # Verify codex was called
        mock_async_client.post.assert_called_once()
        call_args = mock_async_client.post.call_args
        assert "codex/pr-digest" in call_args[0][0]

    @patch('main.httpx.AsyncClient')
    def test_webhook_codex_failure(self, mock_client):
        """Test webhook when codex service is unreachable"""
        # Mock the async client to raise an exception
        mock_async_client = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_async_client
        mock_async_client.post.side_effect = Exception("Connection refused")

        payload = {
            "pull_request": {"number": 456, "title": "Test PR"},
            "analysis": {"risk_score": 0.1},
            "changes": {"files": []}
        }

        response = client.post("/webhook/github", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert "codex_unreachable" in data["reason"]

    def test_webhook_invalid_json(self):
        """Test webhook with invalid JSON"""
        response = client.post(
            "/webhook/github",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 400
        assert "invalid json" in response.json()["detail"]

    @patch('main.WEBHOOK_SECRET', 'test_secret')
    def test_webhook_invalid_signature(self):
        """Test webhook with invalid signature when secret is set"""
        payload = {"pull_request": {"number": 789}}
        
        response = client.post(
            "/webhook/github",
            json=payload,
            headers={"X-Hub-Signature-256": "sha256=invalid"}
        )
        
        assert response.status_code == 401
        assert "invalid signature" in response.json()["detail"]

    def test_webhook_missing_data(self):
        """Test webhook with minimal/missing data"""
        payload = {}  # Empty payload
        
        with patch('main.httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_async_client
            mock_async_client.post = AsyncMock()
            
            response = client.post("/webhook/github", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["ok"] is True
            
            # Verify the payload sent to codex has defaults
            call_args = mock_async_client.post.call_args
            sent_payload = call_args[1]["json"]
            assert sent_payload["number"] == 0  # Default when no PR number
            assert sent_payload["title"] == ""  # Default when no title
            assert sent_payload["risk_score"] == 0.0  # Default risk score

class TestHealthEndpoint:
    def test_health_check(self):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

class TestRiskLabeling:
    @patch('main.httpx.AsyncClient')
    def test_low_risk_labeling(self, mock_client):
        """Test that low risk scores get risk:low label"""
        mock_async_client = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_async_client
        mock_async_client.post = AsyncMock()

        payload = {
            "pull_request": {"number": 100},
            "analysis": {"risk_score": 0.15}  # Low risk
        }

        response = client.post("/webhook/github", json=payload)
        assert response.status_code == 200
        
        # Check the payload sent to codex
        call_args = mock_async_client.post.call_args
        sent_payload = call_args[1]["json"]
        assert "risk:low" in sent_payload["labels"]

    @patch('main.httpx.AsyncClient')
    def test_medium_risk_labeling(self, mock_client):
        """Test that medium/high risk scores get risk:med label"""
        mock_async_client = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_async_client
        mock_async_client.post = AsyncMock()

        payload = {
            "pull_request": {"number": 200},
            "analysis": {"risk_score": 0.75}  # High risk
        }

        response = client.post("/webhook/github", json=payload)
        assert response.status_code == 200
        
        # Check the payload sent to codex
        call_args = mock_async_client.post.call_args
        sent_payload = call_args[1]["json"]
        assert "risk:med" in sent_payload["labels"]

# Legacy test for backward compatibility
def test_webhook_minimal_happy_path():
    """Original test maintained for compatibility"""
    with patch('main.httpx.AsyncClient') as mock_client:
        mock_async_client = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_async_client
        mock_async_client.post = AsyncMock()
        
        payload = {
            "pull_request": {"number": 123, "title": "docs: update readme"},
            "analysis": {"risk_score": 0.05, "checks_passed": True},
            "changes": {"files": ["README.md"]},
        }
        
        response = client.post("/webhook/github", json=payload)
        assert response.status_code == 200
        assert response.json()["ok"] is True

def test_webhook_bad_json():
    """Original test for bad JSON"""
    response = client.post("/webhook/github", data="not-json")
    assert response.status_code == 400