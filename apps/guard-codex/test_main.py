from fastapi.testclient import TestClient
from pathlib import Path
import os, shutil
from unittest.mock import patch

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