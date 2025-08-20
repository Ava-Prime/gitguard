# GitHub Actions Billing & Permissions Fix Guide

## Current Status
✅ **Workflow Permissions Fixed**: Added `packages: write` and `id-token: write` to release.yml workflow
❌ **Billing Issue**: GitHub Actions not starting due to billing/spending limit flag
❌ **Repository Permissions**: Need to configure workflow permissions in repository settings

## 🚨 Critical Steps to Fix GitHub Actions

### 1. Fix Billing Issues (URGENT)

**Problem**: GitHub Actions runs aren't starting due to billing/spending-limit flag.

**Solution**:
1. Go to **Settings → Billing & plans** in your GitHub account/organization
2. Update payment method if payment failed
3. Increase spending limit if it's set to $0
4. Verify billing is active and in good standing

**GitHub Error**: This exact error occurs when payments fail or spending limit is 0.

### 2. Configure Repository Workflow Permissions

**Problem**: Release-Please needs permission to create PRs, and workflows need GHCR access.

**Solution**:
1. Go to **Settings → Actions → General → Workflow permissions**
2. Set to **"Read and write permissions"**
3. Enable **"Allow GitHub Actions to create and approve pull requests"**
4. Apply to both repository AND organization settings if applicable

### 3. Verify Workflow Permissions (COMPLETED ✅)

The following permissions have been added to `.github/workflows/release.yml`:
```yaml
permissions:
  contents: write        # For creating releases
  pull-requests: write   # For Release-Please PRs
  packages: write        # For GHCR publishing
  id-token: write        # For keyless signing with Cosign
```

## 🧪 Testing After Fixes

### Manual Workflow Trigger
Once billing is fixed, test the release workflow:

```bash
# Trigger release workflow manually
gh workflow run release.yml
```

## 🚑 Hotfix & Rollback Playbook

### Hotfix Procedure

For critical bugs that need immediate patching:

```powershell
# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-security-fix

# 2. Make the fix and commit with conventional commit
git add .
git commit -m "fix: resolve critical security vulnerability in auth module"

# 3. Push and create PR
git push origin hotfix/critical-security-fix
gh pr create --title "hotfix: critical security fix" --body "Urgent security patch"

# 4. Merge PR - Release-Please will automatically:
#    - Detect the fix: commit
#    - Bump patch version (e.g., 0.1.0 → 0.1.1)
#    - Open release PR
#    - After merge → Phase B publishes new image
```

### Rollback Procedure

**Never delete tags in production.** Instead, publish a superseding patch:

```powershell
# 1. Identify the problematic release merge commit
git log --oneline --merges

# 2. Revert the release merge (use -m 1 for main branch)
git revert -m 1 <merge_commit_of_release_pr>

# 3. Commit the revert
git commit -m "fix: revert problematic release v0.1.1"

# 4. Push to main
git push origin main

# 5. Release-Please will open corrective PR for next patch version
# This creates a new release (e.g., v0.1.2) that supersedes the broken one
```

### Emergency Override Process

For critical production issues requiring immediate bypass:

1. **Add emergency label**: `emergency-override` to PR
2. **Provide justification**: Clear explanation in PR description
3. **Post-incident review**: Schedule within 24 hours
4. **Audit trail**: All emergency overrides logged and reviewed

### Verification Commands

After any hotfix or rollback:

```powershell
# Verify the new image is published and signed
$TAG = "0.1.2"  # Replace with actual version
$IMAGE = "ghcr.io/codessa-platform/gitguard:$TAG"

# Pull and verify
docker pull $IMAGE
cosign verify `
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" `
  --certificate-identity-regexp "github.com/codessa-platform/gitguard/.github/workflows/release.*" `
  $IMAGE

# Check release notes
gh release view $TAG
```
# Check workflow status
gh run list --workflow release.yml

# View detailed logs
gh run view --log
```

### Verify GHCR Access
After successful run, verify container publishing:

```bash
# Check if container was published
docker pull ghcr.io/ava-prime/gitguard:latest

# Verify container signature
cosign verify ghcr.io/ava-prime/gitguard:latest
```

## 📋 Checklist

- [ ] **Fix GitHub billing** (Settings → Billing & plans)
- [ ] **Update payment method** (if payment failed)
- [ ] **Increase spending limit** (if set to $0)
- [ ] **Set workflow permissions** (Settings → Actions → General)
- [ ] **Enable PR creation** (Allow GitHub Actions to create PRs)
- [x] **Add workflow permissions** (packages: write, id-token: write)
- [ ] **Test manual trigger** (`gh workflow run release.yml`)
- [ ] **Verify GHCR publishing** (check container registry)
- [ ] **Verify Release-Please** (check for automated PRs)

## 🔍 Troubleshooting

### If workflows still don't start:
1. Check organization-level billing settings
2. Verify repository isn't archived or disabled
3. Check if Actions are enabled for the repository
4. Review organization security policies

### If GHCR publishing fails:
1. Verify `packages: write` permission is set
2. Check if GHCR is enabled for the organization
3. Ensure container registry visibility settings allow publishing

### If Release-Please doesn't create PRs:
1. Verify `pull-requests: write` permission
2. Check if "Allow GitHub Actions to create PRs" is enabled
3. Ensure branch protection rules allow automated PRs

## 📚 References

- [GitHub Actions Billing](https://docs.github.com/en/billing/managing-billing-for-github-actions)
- [Workflow Permissions](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#permissions)
- [GHCR Publishing](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Release-Please Setup](https://github.com/google-github-actions/release-please-action)
