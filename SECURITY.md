# Security Policy

## Supported Versions

We actively support the following versions of GitGuard with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 2.1.x   | :white_check_mark: |
| 2.0.x   | :white_check_mark: |
| 1.9.x   | :x:                |
| < 1.9   | :x:                |

## Reporting a Vulnerability

### Security Contact

For security vulnerabilities, please contact our security team:

- **Primary Contact**: security@gitguard.dev
- **Backup Contact**: security-team@example.org
- **PGP Key**: [Download Public Key](https://gitguard.dev/security/pgp-key.asc)
- **Security Advisory**: [GitHub Security Advisories](https://github.com/gitguard/gitguard/security/advisories)

### Disclosure Process

1. **Initial Report**: Send a detailed report to security@gitguard.dev
   - Include steps to reproduce the vulnerability
   - Provide proof-of-concept if available
   - Specify affected versions and components
   - Use PGP encryption for sensitive details

2. **Acknowledgment**: We will acknowledge receipt within **24 hours**

3. **Initial Assessment**: Security team will provide initial assessment within **72 hours**
   - Confirm vulnerability validity
   - Assign severity level (Critical, High, Medium, Low)
   - Provide estimated timeline for resolution

4. **Investigation & Fix**: Development of security patch
   - Critical: 7 days
   - High: 14 days
   - Medium: 30 days
   - Low: 60 days

5. **Coordinated Disclosure**: Public disclosure after fix is available
   - Security advisory published
   - CVE assigned if applicable
   - Credit given to reporter (unless anonymity requested)

### Service Level Agreement (SLA)

| Severity | Response Time | Resolution Target |
|----------|---------------|-------------------|
| Critical | 4 hours       | 7 days           |
| High     | 24 hours      | 14 days          |
| Medium   | 72 hours      | 30 days          |
| Low      | 1 week        | 60 days          |

**Critical Vulnerabilities** include:
- Remote code execution
- Authentication bypass
- Privilege escalation
- Data exfiltration
- Supply chain attacks

**High Vulnerabilities** include:
- Cross-site scripting (XSS)
- SQL injection
- Insecure direct object references
- Security misconfigurations

### Security Features

GitGuard implements multiple security layers:

- **Secret Scanning**: Automated detection of exposed credentials
- **Policy Enforcement**: OPA-based security policies
- **Container Security**: Image scanning and signing with Cosign
- **Supply Chain Security**: SBOM generation and attestation
- **Access Controls**: RBAC with principle of least privilege
- **Audit Logging**: Comprehensive security event logging
- **Encryption**: TLS 1.3 for data in transit, AES-256 for data at rest

### Security Best Practices

When deploying GitGuard:

1. **Environment Security**:
   - Use dedicated service accounts with minimal permissions
   - Enable audit logging for all security events
   - Regularly rotate API keys and tokens
   - Implement network segmentation

2. **Configuration Security**:
   - Review and customize OPA policies for your environment
   - Enable all security scanning features
   - Configure proper backup and disaster recovery
   - Use secrets management systems (not environment variables)

3. **Monitoring & Alerting**:
   - Monitor security events and policy violations
   - Set up alerts for critical security events
   - Regularly review access logs and user activities
   - Implement incident response procedures

### Security Updates

Security updates are distributed through:

- **GitHub Releases**: Tagged releases with security patches
- **Container Images**: Updated images in container registry
- **Security Advisories**: Detailed vulnerability information
- **Mailing List**: security-announce@gitguard.dev (low-volume)

### Bug Bounty Program

We operate a responsible disclosure program with recognition for security researchers:

- **Scope**: GitGuard core application and official extensions
- **Rewards**: Recognition in security advisories and contributor list
- **Hall of Fame**: [Security Researchers](https://gitguard.dev/security/hall-of-fame)

### Compliance & Certifications

GitGuard is designed to support compliance with:

- **SOC 2 Type II**: Security, availability, and confidentiality
- **ISO 27001**: Information security management
- **NIST Cybersecurity Framework**: Risk management
- **GDPR**: Data protection and privacy
- **HIPAA**: Healthcare data security (when configured appropriately)

### Security Architecture

For detailed security architecture information, see:

- [Security Architecture Document](docs/security-architecture.md)
- [Threat Model](docs/threat-model.md)
- [Security Controls Matrix](docs/security-controls.md)
- [Incident Response Plan](docs/incident-response.md)

---

**Last Updated**: December 2024  
**Next Review**: March 2025  
**Document Version**: 2.1.0