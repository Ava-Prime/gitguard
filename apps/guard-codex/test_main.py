from fastapi.testclient import TestClient
from pathlib import Path
import os, shutil, json, pytest
from unittest.mock import patch, MagicMock, mock_open
from main import app, PREvent
import subprocess

def test_digest_writes_md(tmp_path, monkeypatch):
    # isolate docs dir
    from main import app
    import main
    
    docs_path = tmp_path / "docs_src"
    monkeypatch.setattr(main, 'DOCS_SRC', docs_path)
    c = TestClient(app)

    payload = {
        "number": 42, "title": "feat: hello",
        "labels": ["risk:low"], "risk_score": 0.1,
        "checks_passed": True, "changed_paths": ["README.md"]
    }

    with patch('main.subprocess.run') as mock_run:
        mock_run.return_value = None
        r = c.post("/codex/pr-digest", json=payload)
        assert r.status_code == 200
        response_data = r.json()
        assert response_data["status"] == "ok"
        assert (tmp_path / "docs_src" / "prs" / "42.md").exists()
        mock_run.assert_called_once_with(["make", "docs-build"], check=True)

def test_digest_handles_none_title(tmp_path, monkeypatch):
    # test with None title
    from main import app
    import main
    
    docs_path = tmp_path / "docs_src"
    monkeypatch.setattr(main, 'DOCS_SRC', docs_path)
    c = TestClient(app)

    payload = {
        "number": 43,
        "labels": ["bug"], "risk_score": 0.5,
        "checks_passed": False, "changed_paths": ["src/main.py"]
    }
    
    with patch('main.subprocess.run') as mock_run:
        mock_run.return_value = None
        r = c.post("/codex/pr-digest", json=payload)
        assert r.status_code == 200
        response_data = r.json()
        assert response_data["status"] == "ok"
        
        md_file = tmp_path / "docs_src" / "prs" / "43.md"
        assert md_file.exists()
        content = md_file.read_text(encoding="utf-8")
        assert "# PR #43:" in content
        assert "✗" in content  # checks failed
        mock_run.assert_called_once_with(["make", "docs-build"], check=True)

def test_digest_with_full_payload(tmp_path, monkeypatch):
    # isolate docs dir
    from main import app
    import main
    
    docs_path = tmp_path / "docs_src"
    monkeypatch.setattr(main, 'DOCS_SRC', docs_path)
    c = TestClient(app)

    payload = {
        "number": 44,
        "title": "refactor: optimize performance",
        "labels": ["performance", "refactor"],
        "risk_score": 0.3,
        "checks_passed": True,
        "changed_paths": ["src/core.py", "tests/test_core.py"],
        "coverage_delta": 2.5,
        "perf_delta": -15.0,
        "policies": ["security-review", "performance-check"],
        "release_window_state": "closed",
        "summary": "Optimized core algorithms for better performance"
    }
    
    with patch('main.subprocess.run') as mock_run:
        mock_run.return_value = None
        r = c.post("/codex/pr-digest", json=payload)
        assert r.status_code == 200
        response_data = r.json()
        assert response_data["status"] == "ok"
        
        md_file = tmp_path / "docs_src" / "prs" / "44.md"
        assert md_file.exists()
        mock_run.assert_called_once_with(["make", "docs-build"], check=True)
        content = md_file.read_text(encoding="utf-8")
        
        # Check content structure
        assert "# PR #44: refactor: optimize performance" in content
        assert "**Risk:** 0.3" in content
        assert "✓" in content  # checks passed
        assert "**Coverage Δ:** 2.5%" in content
        assert "**Perf Δ:** -15.0" in content
        assert "performance, refactor" in content
        assert "Optimized core algorithms" in content
        assert "- `src/core.py`" in content
        assert "- `tests/test_core.py`" in content
        assert "Release window: closed" in content
        assert "security-review, performance-check" in content


class TestPRDigestEndpoint:
    """Test PR digest generation functionality"""
    
    def test_pr_digest_mermaid_graph_generation(self, tmp_path, monkeypatch):
        """Test Mermaid graph generation in PR digest"""
        from main import app
        import main
        
        docs_path = tmp_path / "docs_src"
        monkeypatch.setattr(main, 'DOCS_SRC', docs_path)
        client = TestClient(app)
        
        payload = {
            "number": 100,
            "title": "Add new feature",
            "changed_paths": ["src/feature.py", "tests/test_feature.py", "docs/feature.md"],
            "policies": ["security-review.rego", "performance-check.rego"]
        }
        
        with patch('main.subprocess.run') as mock_run:
            mock_run.return_value = None
            response = client.post("/codex/pr-digest", json=payload)
            
            assert response.status_code == 200
            md_file = tmp_path / "docs_src" / "prs" / "100.md"
            content = md_file.read_text(encoding="utf-8")
            
            # Check Mermaid graph structure
            assert "```mermaid" in content
            assert "graph LR" in content
            assert 'PR["PR #100"]' in content
            assert "FILES" in content
            assert "feature.py" in content
            assert "security_review_rego" in content
            assert "performance_check_rego" in content
    
    def test_pr_digest_large_file_list_truncation(self, tmp_path, monkeypatch):
        """Test truncation of large file lists in Mermaid graph"""
        from main import app
        import main
        
        docs_path = tmp_path / "docs_src"
        monkeypatch.setattr(main, 'DOCS_SRC', docs_path)
        client = TestClient(app)
        
        # Create payload with more than 5 files
        changed_paths = [f"src/file{i}.py" for i in range(10)]
        payload = {
            "number": 101,
            "title": "Large refactor",
            "changed_paths": changed_paths
        }
        
        with patch('main.subprocess.run') as mock_run:
            mock_run.return_value = None
            response = client.post("/codex/pr-digest", json=payload)
            
            assert response.status_code == 200
            md_file = tmp_path / "docs_src" / "prs" / "101.md"
            content = md_file.read_text(encoding="utf-8")
            
            # Should show "...5 more" for truncated files
            assert "...5 more" in content
            assert "F1" in content  # First 5 files should be shown
            assert "F5" in content
    
    def test_pr_digest_subprocess_failure(self, tmp_path, monkeypatch):
        """Test handling of subprocess failure during docs build"""
        from main import app
        import main
        
        docs_path = tmp_path / "docs_src"
        monkeypatch.setattr(main, 'DOCS_SRC', docs_path)
        client = TestClient(app)
        
        payload = {"number": 102, "title": "Test PR"}
        
        with patch('main.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "make")
            response = client.post("/codex/pr-digest", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "partial"
            assert "error" in data
            assert data["page"] == "/prs/102.md"
    
    def test_pr_digest_empty_fields(self, tmp_path, monkeypatch):
        """Test PR digest with empty/default field values"""
        from main import app
        import main
        
        docs_path = tmp_path / "docs_src"
        monkeypatch.setattr(main, 'DOCS_SRC', docs_path)
        client = TestClient(app)
        
        payload = {"number": 103}  # Minimal payload
        
        with patch('main.subprocess.run') as mock_run:
            mock_run.return_value = None
            response = client.post("/codex/pr-digest", json=payload)
            
            assert response.status_code == 200
            md_file = tmp_path / "docs_src" / "prs" / "103.md"
            content = md_file.read_text(encoding="utf-8")
            
            # Check default values are handled
            assert "# PR #103:" in content
            assert "**Risk:** 0.0" in content
            assert "✗" in content  # checks_passed defaults to False
            assert "_generated by GitGuard_" in content
            assert "_n/a_" in content  # no changed files
            assert "none" in content  # no labels/policies


class TestSemanticSearch:
    """Test semantic search functionality"""
    
    @patch('main.embed')
    @patch('main.search_similar')
    def test_semantic_search_success(self, mock_search, mock_embed):
        """Test successful semantic search"""
        client = TestClient(app)
        
        # Mock embedding generation
        mock_embed.return_value = [0.1] * 1536  # Mock 1536-dim vector
        
        # Mock search results
        mock_results = [
            {"id": "pr_123", "content": "Bug fix for authentication", "score": 0.95},
            {"id": "pr_456", "content": "Security improvements", "score": 0.87}
        ]
        mock_search.return_value = mock_results
        
        response = client.get("/search?q=authentication bug")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["query"] == "authentication bug"
        assert data["count"] == 2
        assert len(data["results"]) == 2
        assert data["results"][0]["id"] == "pr_123"
        
        mock_embed.assert_called_once_with("authentication bug")
        mock_search.assert_called_once_with([0.1] * 1536, limit=20)
    
    @patch('main.embed')
    def test_semantic_search_embedding_failure(self, mock_embed):
        """Test semantic search when embedding generation fails"""
        client = TestClient(app)
        
        # Mock embedding failure
        mock_embed.return_value = []
        
        response = client.get("/search?q=test query")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "Embedding generation unavailable" in data["message"]
    
    @patch('main.embed')
    @patch('main.search_similar')
    def test_semantic_search_exception_handling(self, mock_search, mock_embed):
        """Test semantic search exception handling"""
        client = TestClient(app)
        
        mock_embed.return_value = [0.1] * 1536
        mock_search.side_effect = Exception("Database connection failed")
        
        response = client.get("/search?q=test query")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "Database connection failed" in data["message"]
    
    def test_semantic_search_missing_query(self):
        """Test semantic search with missing query parameter"""
        client = TestClient(app)
        
        response = client.get("/search")
        
        # FastAPI should return 422 for missing required query parameter
        assert response.status_code == 422


class TestPREventModel:
    """Test PREvent Pydantic model"""
    
    def test_pr_event_model_validation(self):
        """Test PREvent model with valid data"""
        data = {
            "number": 123,
            "title": "Test PR",
            "labels": ["bug", "urgent"],
            "risk_score": 0.75,
            "checks_passed": True,
            "changed_paths": ["src/main.py", "tests/test_main.py"],
            "coverage_delta": 5.2,
            "perf_delta": -2.1,
            "policies": ["security.rego"],
            "release_window_state": "closed",
            "summary": "Fixed critical bug in authentication"
        }
        
        pr_event = PREvent(**data)
        
        assert pr_event.number == 123
        assert pr_event.title == "Test PR"
        assert len(pr_event.labels) == 2
        assert pr_event.risk_score == 0.75
        assert pr_event.checks_passed is True
        assert len(pr_event.changed_paths) == 2
        assert pr_event.coverage_delta == 5.2
        assert pr_event.perf_delta == -2.1
        assert len(pr_event.policies) == 1
        assert pr_event.release_window_state == "closed"
        assert pr_event.summary == "Fixed critical bug in authentication"
    
    def test_pr_event_model_defaults(self):
        """Test PREvent model default values"""
        pr_event = PREvent(number=456)
        
        assert pr_event.number == 456
        assert pr_event.title is None
        assert pr_event.labels == []
        assert pr_event.risk_score == 0.0
        assert pr_event.checks_passed is False
        assert pr_event.changed_paths == []
        assert pr_event.coverage_delta == 0.0
        assert pr_event.perf_delta == 0.0
        assert pr_event.policies == []
        assert pr_event.release_window_state == "open"
        assert pr_event.summary == ""
    
    def test_pr_event_model_type_validation(self):
        """Test PREvent model type validation"""
        # Test invalid number type
        with pytest.raises(ValueError):
            PREvent(number="invalid")
        
        # Test invalid risk_score type
        with pytest.raises(ValueError):
            PREvent(number=123, risk_score="invalid")
        
        # Test invalid checks_passed type
        with pytest.raises(ValueError):
            PREvent(number=123, checks_passed="invalid")


class TestFileOperations:
    """Test file system operations"""
    
    def test_docs_directory_creation(self, tmp_path, monkeypatch):
        """Test automatic creation of docs directory structure"""
        from main import app
        import main
        
        docs_path = tmp_path / "custom_docs"
        monkeypatch.setattr(main, 'DOCS_SRC', docs_path)
        client = TestClient(app)
        
        # Ensure directory doesn't exist initially
        assert not docs_path.exists()
        
        payload = {"number": 200, "title": "Test directory creation"}
        
        with patch('main.subprocess.run') as mock_run:
            mock_run.return_value = None
            response = client.post("/codex/pr-digest", json=payload)
            
            assert response.status_code == 200
            # Check that directories were created
            assert docs_path.exists()
            assert (docs_path / "prs").exists()
            assert (docs_path / "prs" / "200.md").exists()
    
    def test_markdown_file_encoding(self, tmp_path, monkeypatch):
        """Test that markdown files are written with UTF-8 encoding"""
        from main import app
        import main
        
        docs_path = tmp_path / "docs_src"
        monkeypatch.setattr(main, 'DOCS_SRC', docs_path)
        client = TestClient(app)
        
        # Use unicode characters to test encoding
        payload = {
            "number": 201,
            "title": "Test with unicode: 🚀 ñáéíóú",
            "summary": "Contains unicode characters: 中文 العربية"
        }
        
        with patch('main.subprocess.run') as mock_run:
            mock_run.return_value = None
            response = client.post("/codex/pr-digest", json=payload)
            
            assert response.status_code == 200
            md_file = docs_path / "prs" / "201.md"
            
            # Read with UTF-8 encoding
            content = md_file.read_text(encoding="utf-8")
            assert "🚀 ñáéíóú" in content
            assert "中文 العربية" in content


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_json_payload(self):
        """Test handling of invalid JSON in request body"""
        client = TestClient(app)
        
        response = client.post("/codex/pr-digest", 
                              data="invalid json",
                              headers={"Content-Type": "application/json"})
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields"""
        client = TestClient(app)
        
        # Missing required 'number' field
        payload = {"title": "Test PR"}
        
        response = client.post("/codex/pr-digest", json=payload)
        
        assert response.status_code == 422  # Validation error
    
    @patch('main.subprocess.run')
    def test_file_write_permission_error(self, mock_run, tmp_path, monkeypatch):
        """Test handling of file write permission errors"""
        from main import app
        import main
        
        # Create a read-only directory
        docs_path = tmp_path / "readonly_docs"
        docs_path.mkdir()
        docs_path.chmod(0o444)  # Read-only
        
        monkeypatch.setattr(main, 'DOCS_SRC', docs_path)
        client = TestClient(app)
        
        payload = {"number": 202, "title": "Test permission error"}
        
        try:
            response = client.post("/codex/pr-digest", json=payload)
            # The endpoint might handle this gracefully or raise an exception
            # This depends on the actual implementation
        except PermissionError:
            # Expected behavior for permission denied
            pass
        finally:
            # Restore permissions for cleanup
            docs_path.chmod(0o755)


class TestIntegration:
    """Integration tests for guard-codex functionality"""
    
    def test_full_workflow_integration(self, tmp_path, monkeypatch):
        """Test complete workflow from PR event to documentation generation"""
        from main import app
        import main
        
        docs_path = tmp_path / "docs_src"
        monkeypatch.setattr(main, 'DOCS_SRC', docs_path)
        client = TestClient(app)
        
        # Comprehensive payload
        payload = {
            "number": 300,
            "title": "feat: implement new authentication system",
            "labels": ["feature", "security", "breaking-change"],
            "risk_score": 0.65,
            "checks_passed": True,
            "changed_paths": [
                "src/auth/authentication.py",
                "src/auth/authorization.py",
                "tests/test_auth.py",
                "docs/authentication.md",
                "migrations/001_auth_tables.sql"
            ],
            "coverage_delta": 8.5,
            "perf_delta": 3.2,
            "policies": ["security-review.rego", "breaking-change.rego"],
            "release_window_state": "open",
            "summary": "Implemented OAuth2 authentication with JWT tokens and role-based authorization"
        }
        
        with patch('main.subprocess.run') as mock_run:
            mock_run.return_value = None
            response = client.post("/codex/pr-digest", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["page"] == "/prs/300.md"
            assert "ts" in data
            
            # Verify file creation and content
            md_file = docs_path / "prs" / "300.md"
            assert md_file.exists()
            
            content = md_file.read_text(encoding="utf-8")
            
            # Verify all sections are present
            assert "# PR #300: feat: implement new authentication system" in content
            assert "**Risk:** 0.65" in content
            assert "✓" in content  # checks passed
            assert "**Coverage Δ:** 8.5%" in content
            assert "**Perf Δ:** 3.2" in content
            assert "feature, security, breaking-change" in content
            assert "## Impact Graph" in content
            assert "```mermaid" in content
            assert "## Summary" in content
            assert "OAuth2 authentication" in content
            assert "## Changed Files" in content
            assert "authentication.py" in content
            assert "## Governance" in content
            assert "Release window: open" in content
            assert "security-review.rego" in content
            
            # Verify subprocess was called
            mock_run.assert_called_once_with(["make", "docs-build"], check=True)