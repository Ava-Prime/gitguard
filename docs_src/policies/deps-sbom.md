# Dependency Security & SBOM Policy

**Policy ID:** POL-003
**Status:** Active
**Last Updated:** 2024-12-19

## Overview

This policy ensures that all dependency changes undergo proper security scanning and version pinning to maintain supply chain security. This includes special considerations for org-brain features like Graph API, policy transparency, Mermaid graph generation, and SLO monitoring dependencies.

## Policy Statement

Any pull request labeled with `dependencies` must:
1. Pass Software Bill of Materials (SBOM) security scanning
2. Use pinned versions in `requirements.txt` (no loose version constraints)
3. Include Graph API dependency impact assessment for org-brain features
4. Validate policy transparency engine compatibility
5. Ensure Mermaid graph generation library security

## Rationale

Dependency management is critical for:
- **Supply Chain Security**: Preventing malicious packages from entering our codebase
- **Reproducible Builds**: Ensuring consistent behavior across environments
- **Vulnerability Management**: Tracking and addressing known security issues
- **Compliance**: Meeting regulatory requirements for software composition analysis
- **Graph API Stability**: Ensuring knowledge graph dependencies are secure and stable
- **Policy Engine Integrity**: Maintaining OPA and policy evaluation dependency security
- **Visualization Security**: Securing Mermaid and graph rendering dependencies
- **SLO Monitoring Reliability**: Ensuring metrics and monitoring dependencies are trustworthy

## Implementation

### SBOM Scanning Requirements

#### Tools Used
- **Trivy**: Vulnerability scanning for known CVEs
- **Grype**: Additional vulnerability detection
- **SBOM Generation**: Complete software bill of materials

#### CI Integration
The CI pipeline automatically:
1. Generates SBOM for all dependencies
2. Scans for known vulnerabilities
3. Sets `sbom_ok` check status based on results
4. Blocks merge if critical vulnerabilities are found
5. Validates Graph API dependency compatibility
6. Checks policy transparency engine dependencies
7. Scans Mermaid and visualization library security
8. Verifies SLO monitoring dependency integrity

### Version Pinning Requirements

#### Allowed Formats
```python
# ✅ GOOD: Exact version pinning
django==4.2.7
requests==2.31.0
numpy==1.24.3

# ❌ BAD: Loose constraints
django>=4.0
requests~=2.30
numpy>=1.20,<2.0
```

#### Rationale for Pinning
- **Security**: Prevents automatic updates to vulnerable versions
- **Stability**: Avoids breaking changes from minor/patch updates
- **Auditability**: Clear record of exact versions in use
- **Reproducibility**: Identical builds across all environments

## Enforcement

### Automatic Checks

1. **SBOM Scan Check**
   - **OPA Policy:** `repo.guard.deny[msg]` (SBOM rule)
   - **Trigger:** PR with `dependencies` label
   - **Requirement:** `sbom_ok` check must be true

2. **Version Pinning Check**
   - **OPA Policy:** `repo.guard.deny[msg]` (unpinned versions rule)
   - **Trigger:** PR modifying `requirements.txt`
   - **Requirement:** `diff_unpinned_versions` must be false

### Workflow

1. **Developer** updates dependencies and creates PR
2. **Dependabot/Developer** adds `dependencies` label
3. **CI Pipeline** runs SBOM scanning
4. **GitGuard** checks for version pinning compliance
5. **Merge** allowed only if both checks pass

## Security Scanning Details

### Vulnerability Severity Levels

| Severity | Action |
|----------|--------|
| **Critical** | ❌ Block merge immediately |
| **High** | ⚠️ Require security team review |
| **Medium** | ℹ️ Log for tracking, allow merge |
| **Low** | ℹ️ Log for tracking, allow merge |

### SBOM Contents

The generated SBOM includes:
- Package names and exact versions
- License information
- Dependency tree relationships
- Graph API dependency mappings
- Policy engine dependency chains
- Mermaid rendering library versions
- SLO monitoring tool dependencies
- Chaos engineering test framework versions
- Known vulnerability mappings
- Supply chain provenance data

## Exceptions

### Emergency Patches
For critical security patches, the security team can:
1. Add `security-override` label
2. Temporarily bypass SBOM requirements
3. Must be followed by proper SBOM scan within 24 hours

### Development Dependencies
Development-only dependencies (in `requirements-dev.txt`) have relaxed pinning requirements but still require SBOM scanning.

## Best Practices

### For Developers
1. **Regular Updates**: Update dependencies monthly during maintenance windows
2. **Security Monitoring**: Subscribe to security advisories for key dependencies
3. **Testing**: Thoroughly test after dependency updates
4. **Documentation**: Document reasons for specific version choices

### For Security Team
1. **Review Process**: Weekly review of dependency scan results
2. **Policy Updates**: Quarterly review of scanning tools and policies
3. **Incident Response**: Defined process for critical vulnerability disclosure

## Org-Brain Specific Requirements

### Graph API Dependencies
- **Neo4j Driver**: Pinned version for graph database connectivity
- **GraphQL Libraries**: Security-scanned GraphQL processing libraries
- **API Framework**: Validated web framework versions for Graph API endpoints

### Policy Transparency Dependencies
- **OPA Runtime**: Pinned Open Policy Agent version
- **Policy Parsers**: Security-validated policy parsing libraries
- **Source Code Renderers**: Secure syntax highlighting and rendering libraries

### Mermaid Graph Dependencies
- **Mermaid.js**: Pinned version for diagram generation
- **SVG Processors**: Security-scanned SVG generation libraries
- **Graph Layout**: Validated graph layout and rendering dependencies

### SLO Monitoring Dependencies
- **Prometheus Client**: Pinned metrics collection library
- **Grafana SDK**: Security-validated dashboard generation libraries
- **Alerting Libraries**: Secure notification and alerting dependencies

## Related Policies

- [Infrastructure Owner Review](infra-owners.md) - Owner approval for infrastructure changes
- [Release Windows](release-windows.md) - Timing restrictions for deployments
- [Security Posture](../security.md) - Comprehensive security practices

## Tools & Resources

- **Trivy Documentation**: https://trivy.dev/
- **Grype Documentation**: https://github.com/anchore/grype
- **NIST SBOM Guidelines**: https://www.nist.gov/itl/executive-order-improving-nations-cybersecurity/software-bill-materials
- **Python Security Best Practices**: https://python.org/dev/security/

## Contact

For questions about this policy:
- **Security Team**: security@company.com
- **Platform Engineering**: platform@company.com
- **Emergency Security Issues**: security-emergency@company.com
