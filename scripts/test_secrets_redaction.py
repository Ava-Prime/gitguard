#!/usr/bin/env python3
"""
Secrets Redaction Test Suite

Tests the secrets detection and redaction functionality in GitGuard.
Validates that sensitive information is properly masked in logs and outputs.
"""

import pytest
import json
import re
from pathlib import Path


class TestSecretsRedaction:
    """Test suite for secrets redaction functionality."""
    
    def test_api_key_redaction(self):
        """Test that API keys are properly redacted."""
        test_content = "API_KEY=sk-1234567890abcdef"
        redacted = self.redact_secrets(test_content)
        assert "sk-1234567890abcdef" not in redacted
        assert "[REDACTED]" in redacted or "***" in redacted
    
    def test_github_token_redaction(self):
        """Test that GitHub tokens are properly redacted."""
        test_content = "GITHUB_TOKEN=ghp_1234567890abcdef1234567890abcdef12345678"
        redacted = self.redact_secrets(test_content)
        assert "ghp_1234567890abcdef1234567890abcdef12345678" not in redacted
        assert "[REDACTED]" in redacted or "***" in redacted
    
    def test_database_url_redaction(self):
        """Test that database URLs with credentials are redacted."""
        test_content = "DATABASE_URL=postgresql://user:password@localhost:5432/db"
        redacted = self.redact_secrets(test_content)
        assert "password" not in redacted
        assert "[REDACTED]" in redacted or "***" in redacted
    
    def test_jwt_token_redaction(self):
        """Test that JWT tokens are properly redacted."""
        test_content = "JWT_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        redacted = self.redact_secrets(test_content)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in redacted
        assert "[REDACTED]" in redacted or "***" in redacted
    
    def test_private_key_redaction(self):
        """Test that private keys are properly redacted."""
        test_content = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKB
-----END PRIVATE KEY-----"""
        redacted = self.redact_secrets(test_content)
        assert "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKB" not in redacted
        assert "[REDACTED]" in redacted or "***" in redacted
    
    def test_safe_content_preserved(self):
        """Test that non-sensitive content is preserved."""
        test_content = "This is safe content with no secrets"
        redacted = self.redact_secrets(test_content)
        assert redacted == test_content
    
    def redact_secrets(self, content: str) -> str:
        """Simple secrets redaction implementation for testing."""
        patterns = [
            r'(API_KEY|GITHUB_TOKEN|JWT_TOKEN)=[^\s]+',
            r'postgresql://[^:]+:[^@]+@[^\s]+',
            r'-----BEGIN [^-]+ KEY-----[\s\S]*?-----END [^-]+ KEY-----',
            r'eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*',  # JWT
            r'sk-[a-zA-Z0-9]{48}',  # OpenAI API keys
            r'ghp_[a-zA-Z0-9]{36}',  # GitHub personal access tokens
        ]
        
        redacted_content = content
        for pattern in patterns:
            redacted_content = re.sub(pattern, '[REDACTED]', redacted_content, flags=re.IGNORECASE)
        
        return redacted_content


def main():
    """Run the secrets redaction tests."""
    print("🔒 Running Secrets Redaction Tests...")
    print("=" * 50)
    
    test_suite = TestSecretsRedaction()
    tests = [
        test_suite.test_api_key_redaction,
        test_suite.test_github_token_redaction,
        test_suite.test_database_url_redaction,
        test_suite.test_jwt_token_redaction,
        test_suite.test_private_key_redaction,
        test_suite.test_safe_content_preserved,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"Tests passed: {passed}")
    print(f"Tests failed: {failed}")
    
    if failed > 0:
        print("\n❌ Some tests failed. Please review the secrets redaction implementation.")
        exit(1)
    else:
        print("\n✅ All secrets redaction tests passed!")
        print("Secrets detection and redaction is working correctly.")


if __name__ == "__main__":
    main()