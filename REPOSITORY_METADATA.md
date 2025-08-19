# Repository Metadata Configuration

This file contains the recommended metadata for the GitGuard repository to improve discoverability and community onboarding.

## Repository Description

**Recommended Description:**
```
Policy-driven Git repository governance and compliance automation with AI-powered code review, supply chain security, and transparent decision-making through OPA rules and SBOM generation.
```

## Repository Topics

**Recommended Topics:**
```
git-automation
policy-engine
opa-policies
code-review
supply-chain-security
sbom
compliance
governance
ci-cd
security-scanning
vulnerability-management
infrastructure-as-code
devops
gitops
repository-management
workflow-automation
open-policy-agent
cosign
sigstore
transparency
```

## How to Apply These Settings

### Via GitHub Web Interface:
1. Go to your repository on GitHub
2. Click the ⚙️ gear icon next to "About" on the right sidebar
3. Add the description in the "Description" field
4. Add topics in the "Topics" field (separate with spaces or commas)
5. Click "Save changes"

### Via GitHub CLI:
```bash
# Set repository description
gh repo edit --description "Policy-driven Git repository governance and compliance automation with AI-powered code review, supply chain security, and transparent decision-making through OPA rules and SBOM generation."

# Add topics (GitHub CLI doesn't support topics directly, use web interface)
```

### Via GitHub API:
```bash
curl -X PATCH \
  -H "Authorization: token YOUR_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/YOUR_ORG/gitguard \
  -d '{
    "description": "Policy-driven Git repository governance and compliance automation with AI-powered code review, supply chain security, and transparent decision-making through OPA rules and SBOM generation.",
    "topics": ["git-automation", "policy-engine", "opa-policies", "code-review", "supply-chain-security", "sbom", "compliance", "governance", "ci-cd", "security-scanning", "vulnerability-management", "infrastructure-as-code", "devops", "gitops", "repository-management", "workflow-automation", "open-policy-agent", "cosign", "sigstore", "transparency"]
  }'
```

## Additional Repository Settings

### Recommended Settings:
- ✅ **Issues**: Enabled (for community contributions)
- ✅ **Wiki**: Disabled (use docs/ folder instead)
- ✅ **Discussions**: Enabled (for community Q&A)
- ✅ **Projects**: Enabled (for roadmap tracking)
- ✅ **Security**: Enable security advisories
- ✅ **Insights**: Enable dependency graph and Dependabot alerts

### Branch Protection Rules:
- Require pull request reviews before merging
- Require status checks to pass before merging
- Require branches to be up to date before merging
- Include administrators in restrictions

### Labels to Add:
- `good first issue` (for newcomer-friendly issues)
- `help wanted` (for issues seeking contributors)
- `documentation` (for docs-related issues)
- `installation` (for setup-related issues)
- `visuals` (for screenshot/diagram issues)
- `developer-experience` (for DX improvements)

## Community Health Files

The following files help with community onboarding:
- ✅ `README.md` - Project overview and quick start
- ✅ `CONTRIBUTING.md` - Contribution guidelines
- ✅ `CODE_OF_CONDUCT.md` - Community standards
- ✅ `SECURITY.md` - Security policy
- ✅ `.github/ISSUE_TEMPLATE/` - Issue templates
- ✅ `.github/PULL_REQUEST_TEMPLATE.md` - PR template
- ✅ `LICENSE` - License information

## SEO and Discoverability

These topics help with discoverability in GitHub search and topic pages:
- **Primary**: `git-automation`, `policy-engine`, `opa-policies`
- **Security**: `supply-chain-security`, `sbom`, `security-scanning`
- **DevOps**: `ci-cd`, `devops`, `gitops`, `workflow-automation`
- **Compliance**: `compliance`, `governance`, `transparency`
- **Technology**: `open-policy-agent`, `cosign`, `sigstore`
