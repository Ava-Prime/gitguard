# Secrets Hygiene

GitGuard Org-Brain implements comprehensive secrets hygiene to prevent accidental exposure of sensitive information in documentation, generated content, and Graph API responses.

## Overview

The secrets hygiene system provides two layers of protection:

1. **Runtime Redaction**: Automatically redacts secrets from generated documentation content
2. **CI Scanning**: Scans the `docs` folder for any secrets that might have been committed

## Supported Secret Types

The system currently detects and redacts the following types of secrets:

### AWS Access Keys
- **Pattern**: `AKIA[0-9A-Z]{16}`
- **Replacement**: `‹AWS_KEY_REDACTED›`
- **Example**: `AKIA1234567890ABCDEF` → `‹AWS_KEY_REDACTED›`

### GitHub Personal Access Tokens
- **Pattern**: `ghp_[0-9A-Za-z]{36,40}`
- **Replacement**: `‹GH_TOKEN_REDACTED›`
- **Example**: `ghp_1234567890abcdef1234567890abcdef123456` → `‹GH_TOKEN_REDACTED›`

### SSH Keys
- **Pattern**: `(?:ssh-rsa|ssh-ed25519)\s+[A-Za-z0-9/+]+={0,3}`
- **Replacement**: `‹SSH_KEY_REDACTED›`
- **Example**: `ssh-rsa AAAAB3NzaC1yc2E...` → `‹SSH_KEY_REDACTED›`

### Graph API Keys
- **Pattern**: `gapi_[0-9A-Za-z]{32,48}`
- **Replacement**: `‹GRAPH_API_KEY_REDACTED›`
- **Example**: `gapi_1234567890abcdef1234567890abcdef12345678` → `‹GRAPH_API_KEY_REDACTED›`

### Policy Transparency Tokens
- **Pattern**: `pt_[0-9A-Za-z]{24,36}`
- **Replacement**: `‹POLICY_TOKEN_REDACTED›`
- **Example**: `pt_1234567890abcdef1234567890abcdef` → `‹POLICY_TOKEN_REDACTED›`

### Chaos Engineering Credentials
- **Pattern**: `chaos_[0-9A-Za-z]{20,32}`
- **Replacement**: `‹CHAOS_CRED_REDACTED›`
- **Example**: `chaos_1234567890abcdef12345678` → `‹CHAOS_CRED_REDACTED›`

## Runtime Redaction

### Implementation

The `_scrub()` function in `apps/guard-codex/activities.py` automatically processes all documentation content before writing to files:

```python
def _scrub(text: str) -> str:
    """Redact sensitive information from text content."""
    import re
    for pat, repl in REDACT:
        text = re.sub(pat, repl, text)
    return text
```

### Coverage

Runtime redaction is applied to:
- PR documentation content
- Release documentation content
- Any text content written to the `docs` folder
- Graph API responses and metadata
- Policy transparency source references
- Mermaid graph configurations
- Owners index data
- Chaos engineering drill results

### Testing

Run the test suite to verify redaction functionality:

```bash
python test_secrets_redaction.py
```

## CI Scanning

### Gitleaks Integration

The GitHub Actions workflow includes a `secrets-scan` job that uses [Gitleaks](https://github.com/gitleaks/gitleaks) to scan the `docs` folder and org-brain data:

```yaml
secrets-scan:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Scan docs for secrets
      uses: gitleaks/gitleaks-action@v2
      with:
        scan-path: docs
        redact: true
        log-level: error
    - name: Scan Graph API configs
      uses: gitleaks/gitleaks-action@v2
      with:
        scan-path: apps/guard-brain/config
        redact: true
        log-level: error
```

### Configuration

- **Scan Path**: `docs` folder only
- **Redaction**: Enabled (secrets are redacted in logs)
- **Log Level**: Error (only shows actual findings)
- **Blocking**: The build job depends on successful secrets scan

## Security Benefits

### Defense in Depth

1. **Prevention**: Runtime redaction prevents secrets from being written to files
2. **Detection**: CI scanning catches any secrets that bypass runtime redaction
3. **Remediation**: Automated redaction in CI logs prevents exposure in build outputs

### Zero False Positives

The regex patterns are designed to be highly specific to minimize false positives while maintaining comprehensive coverage of common secret formats.

## Best Practices

### For Developers

1. **Never commit secrets**: Use environment variables and secure secret management
2. **Review PR content**: Check generated documentation for any sensitive information
3. **Use test data**: When creating examples, use obviously fake credentials

### For Operations

1. **Monitor CI logs**: Review secrets scan results regularly
2. **Update patterns**: Add new secret patterns as needed
3. **Rotate exposed secrets**: If a secret is detected, rotate it immediately

## Extending the System

### Adding New Secret Types

To add support for new secret types, update the `REDACT` list in `activities.py`:

```python
REDACT = [
    # AWS Access Keys
    (r'AKIA[0-9A-Z]{16}', '‹AWS_KEY_REDACTED›'),
    # GitHub Personal Access Tokens
    (r'ghp_[0-9A-Za-z]{36,40}', '‹GH_TOKEN_REDACTED›'),
    # SSH Keys
    (r'(?:ssh-rsa|ssh-ed25519)\s+[A-Za-z0-9/+]+={0,3}', '‹SSH_KEY_REDACTED›'),
    # Graph API Keys
    (r'gapi_[0-9A-Za-z]{32,48}', '‹GRAPH_API_KEY_REDACTED›'),
    # Policy Transparency Tokens
    (r'pt_[0-9A-Za-z]{24,36}', '‹POLICY_TOKEN_REDACTED›'),
    # Chaos Engineering Credentials
    (r'chaos_[0-9A-Za-z]{20,32}', '‹CHAOS_CRED_REDACTED›'),
    # Your new pattern
    (r'your-new-pattern', '‹YOUR_SECRET_REDACTED›'),
]
```

### Custom Redaction Logic

For more complex redaction needs, extend the `_scrub()` function:

```python
def _scrub(text: str) -> str:
    import re
    # Standard pattern matching
    for pat, repl in REDACT:
        text = re.sub(pat, repl, text)
    
    # Custom logic here
    # ...
    
    return text
```

## Troubleshooting

### Common Issues

**Q: Secrets scan is failing in CI**
- Check the Gitleaks action logs for specific findings
- Verify that the `docs` folder doesn't contain committed secrets
- Consider updating `.gitleaksignore` if needed

**Q: Legitimate content is being redacted**
- Review the regex patterns for overly broad matching
- Consider adding negative lookahead/lookbehind assertions
- Update test cases to cover edge cases

**Q: New secret type not being caught**
- Add the pattern to the `REDACT` list
- Test with `test_secrets_redaction.py`
- Update documentation and CI configuration
- Consider Graph API, policy transparency, or chaos engineering contexts

**Q: Graph API responses contain sensitive data**
- Verify Graph API key redaction is working
- Check policy transparency token patterns
- Review owners index data for exposed credentials

**Q: Mermaid graphs showing sensitive information**
- Update Mermaid graph generation to use redacted data
- Check chaos engineering drill configurations
- Verify SLO monitoring doesn't expose secrets

### Testing Changes

After modifying redaction patterns:

1. Run the test suite: `python test_secrets_redaction.py`
2. Test with real examples (use fake secrets)
3. Verify CI scanning still works
4. Update documentation

## Metrics and Monitoring

### CI Integration

- Secrets scan results are visible in GitHub Actions logs
- Failed scans block the documentation build process
- Scan duration and results are tracked per workflow run

### Runtime Metrics

- Document generation metrics include redaction operations
- No sensitive information is logged in metrics
- Performance impact is minimal (regex operations are fast)

## Compliance

This secrets hygiene system helps maintain compliance with:

- **SOC 2**: Systematic protection of sensitive information
- **PCI DSS**: Prevention of payment card data exposure
- **GDPR**: Protection of personal data in documentation
- **Internal Security Policies**: Automated enforcement of secrets management

## Future Enhancements

- **Machine Learning**: Advanced pattern detection using ML models
- **Custom Dictionaries**: Organization-specific secret patterns
- **Real-time Scanning**: IDE integration for immediate feedback
- **Audit Logging**: Detailed logs of redaction operations
- **Integration Testing**: Automated testing with secret detection tools
- **Graph API Security**: Enhanced redaction for relationship data
- **Policy Transparency**: Dynamic secret detection in policy sources
- **Chaos Engineering**: Secure credential management for drill execution
- **SLO Monitoring**: Protected metrics and alerting configurations