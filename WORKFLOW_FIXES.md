# GitHub Actions Workflow Fixes

This document summarizes the fixes applied to resolve "Startup failure" issues in GitHub Actions workflows.

## Changes Made

### 1. Added Manual Triggers (`workflow_dispatch`)

Both workflows now support manual triggering for isolation and testing:

**Files Updated:**
- `.github/workflows/codex-docs.yml`
- `gitguard/.github/workflows/ci.yml`

**New Trigger Configuration:**
```yaml
on:
  workflow_dispatch:  # ← Added manual trigger
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
  push:
    branches: [main]
```

### 2. Fixed Missing Test File

**Issue:** The CI workflow referenced a missing test file `tests/test_policy_integration.py`

**Solution:** Created the missing test file with comprehensive policy integration tests:
- Policy file existence validation
- Sample policy evaluation tests
- Policy decision structure validation
- High-risk file detection tests
- Policy transparency data tests

### 3. Updated Repository Variable Usage

**Issue:** The codex-docs workflow was using hardcoded GitHub Pages URL instead of the configurable `CODEX_BASE_URL` variable.

**Solution:** Updated the PR comment template to use `${{ vars.CODEX_BASE_URL }}` for:
- Codex preview links
- Graph API endpoints

## Required Repository Configuration

### Repository Variables (Required)

Set these in your GitHub repository settings under **Settings > Secrets and variables > Actions > Variables**:

| Variable Name | Description | Example Value |
|---------------|-------------|---------------|
| `CODEX_BASE_URL` | Base URL for Codex documentation portal | `https://your-org.github.io/gitguard` |

### Repository Secrets (Already Configured)

These secrets are automatically available and properly configured:

| Secret Name | Usage | Status |
|-------------|-------|--------|
| `GITHUB_TOKEN` | GitHub Pages deployment, API access | ✅ Auto-configured |

### Optional Secrets (Not Currently Used)

| Secret Name | Purpose | Status |
|-------------|---------|--------|
| `DOCS_BOT_PAT` | Alternative to GITHUB_TOKEN for docs deployment | ⚠️ Mentioned in docs but not used |

## Verification Steps

### 1. Test Manual Triggers

1. Go to **Actions** tab in your repository
2. Select "Codex Documentation" or "GitGuard CI" workflow
3. Click "Run workflow" button
4. Verify the workflow starts successfully

### 2. Verify Repository Variables

1. Go to **Settings > Secrets and variables > Actions > Variables**
2. Ensure `CODEX_BASE_URL` is set to your documentation base URL
3. Test with a PR to verify the comment links work correctly

### 3. Test Policy Integration

Run the new policy integration tests:
```bash
cd gitguard
pytest tests/test_policy_integration.py -v
```

### 4. Validate OPA Policies

Ensure all referenced policy files exist:
```bash
cd gitguard
opa test policies/ -v
opa fmt --diff policies/
```

## Troubleshooting

### Workflow Still Fails?

1. **Check Variables**: Ensure `CODEX_BASE_URL` is set in repository variables
2. **Check Permissions**: Verify the repository has Pages enabled if using GitHub Pages
3. **Check Policy Files**: Ensure all `.rego` files in `policies/` directory are valid
4. **Check Test Files**: Verify all test files referenced in workflows exist

### Missing Dependencies?

If pytest or OPA tests fail:
```bash
# Install Python dependencies
pip install -r requirements-dev.txt

# Install OPA (Linux/macOS)
curl -L -o opa https://openpolicyagent.org/downloads/v0.58.0/opa_linux_amd64_static
chmod +x opa
sudo mv opa /usr/local/bin/
```

## Next Steps

1. **Set Repository Variables**: Configure `CODEX_BASE_URL` in your repository settings
2. **Test Workflows**: Create a test PR to verify both workflows run successfully
3. **Monitor**: Check the Actions tab for any remaining issues
4. **Clean Up**: Remove this file once everything is working properly

---

**Note**: All changes maintain backward compatibility and follow GitHub Actions best practices.
