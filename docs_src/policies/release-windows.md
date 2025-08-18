# Release Windows Policy

**Policy ID:** POL-001  
**Status:** Active  
**Last Updated:** 2024-12-19

## Overview

To protect production stability, deployments are blocked outside of standard business hours. This policy applies to all GitGuard components including org-brain features like Graph API, policy transparency services, and SLO monitoring systems.

## Policy Statement

Deployments to production environments are restricted to business hours to ensure:
1. Engineering team availability for incident response
2. Reduced risk of unattended deployment issues
3. Proper monitoring and validation of org-brain feature deployments
4. Coordination with dependent systems and services

## Release Window Schedule

**Standard Release Window:**
- **Days:** Monday through Friday
- **Hours:** 08:00 to 16:00 (Africa/Johannesburg timezone)
- **Exclusions:** Public holidays and company closure days

**Emergency Release Window:**
- **Availability:** 24/7 for critical security fixes
- **Approval:** Requires security team and on-call engineer approval
- **Scope:** Limited to security patches and critical bug fixes

## Org-Brain Specific Considerations

### Graph API Deployments
- **Database Migrations:** Neo4j schema changes require extended monitoring
- **API Compatibility:** GraphQL schema changes need backward compatibility validation
- **Performance Impact:** Graph query performance must be validated post-deployment

### Policy Transparency Deployments
- **OPA Updates:** Policy engine updates require validation of all existing policies
- **Policy Compatibility:** Ensure policy evaluation remains consistent
- **Source Code Serving:** Verify policy transparency API remains functional

### SLO Monitoring Deployments
- **Metrics Continuity:** Ensure SLO metrics collection remains uninterrupted
- **Dashboard Updates:** Validate Grafana dashboards after monitoring changes
- **Alert Functionality:** Test alert delivery after alerting system updates

### Chaos Engineering Deployments
- **Test Environment:** Chaos testing infrastructure updates require validation
- **Safety Controls:** Verify emergency stop mechanisms after updates
- **Test Scheduling:** Ensure chaos test scheduling remains functional

## Exceptions

### Security Emergencies
- **Critical vulnerabilities:** Immediate deployment allowed with security team approval
- **Active security incidents:** Emergency patches can be deployed outside windows
- **Supply chain compromises:** Dependency updates for security issues

### System Outages
- **Production down:** Emergency fixes allowed to restore service
- **Data loss prevention:** Immediate deployment to prevent data corruption
- **Cascading failures:** Fixes to prevent system-wide outages

## Enforcement

**OPA Policy:** `repo.guard.blocks_merge`  
**Trigger:** Pull request merge attempt outside release window  
**Action:** Block merge with clear explanation and next available window

### Override Process
1. **Emergency Declaration:** On-call engineer declares emergency
2. **Approval Chain:** Security team or engineering manager approval
3. **Documentation:** Emergency deployment must be documented with justification
4. **Post-Deployment:** Immediate monitoring and validation required

## Monitoring and Validation

### Pre-Deployment Checks
- All automated tests must pass
- Security scans must complete successfully
- Org-brain feature compatibility validated
- Rollback plan documented and tested

### Post-Deployment Monitoring
- **First 30 minutes:** Intensive monitoring of all systems
- **Graph API:** Query performance and response time validation
- **Policy Engine:** Policy evaluation success rate monitoring
- **SLO Metrics:** Verify SLO compliance remains within targets
- **Chaos Tests:** Run smoke tests to ensure chaos engineering functionality

## Related Policies

- [Infrastructure Owner Review](infra-owners.md) - Owner approval for infrastructure changes
- [Dependency Security & SBOM](deps-sbom.md) - Security scanning for dependencies
- [Security Posture](../security.md) - Security requirements for deployments

## Contact

For questions about release windows or emergency deployment approval:
- **Engineering Team:** engineering@company.com
- **On-Call Engineer:** Use PagerDuty escalation
- **Security Team:** security@company.com