# Code Ownership

This page shows the current code ownership structure based on the CODEOWNERS file and recent activity.

## Current Owners

<!-- This content is generated from the knowledge graph -->

| Owner | Type | Files Owned | Recent Activity |
|-------|------|-------------|----------------|

*This table is automatically updated based on CODEOWNERS patterns and file changes in pull requests.*

## Ownership Model

GitGuard implements a hierarchical ownership model that defines:

### Repository Owners
- **Primary Owners**: Full administrative access and final decision authority
- **Secondary Owners**: Backup decision makers and escalation contacts
- **Domain Experts**: Subject matter experts for specific areas

### Component Ownership
- **Service Owners**: Responsible for individual microservices and components
- **Infrastructure Owners**: Platform and deployment infrastructure responsibility
- **Security Owners**: Security policy and vulnerability management

## Ownership Responsibilities

### Code Review
- Owners are automatically assigned as reviewers for their areas
- Required approvals based on change risk and scope
- Escalation procedures for owner unavailability

### Incident Response
- On-call rotation and escalation procedures
- Incident ownership and resolution tracking
- Post-incident review and improvement processes

### Policy Compliance
- Owners ensure their areas comply with governance policies
- Regular compliance audits and remediation
- Training and knowledge transfer responsibilities

## CODEOWNERS Integration

### How It Works
Code ownership is automatically parsed from the `.github/CODEOWNERS` file and integrated into the GitGuard knowledge graph:

- **Pattern Matching**: Files are matched against CODEOWNERS patterns
- **Owner Nodes**: Teams and users are created as Owner entities
- **Ownership Edges**: Relationships link owners to their files
- **Activity Tracking**: PR changes update ownership activity

### Pattern Examples
```
# Global owners
* @org/core-team

# Documentation
/docs/ @org/docs-team @technical-writer

# Security-sensitive files
/security/ @org/security-team
*.yml @org/devops-team

# Specific components
/apps/guard-api/ @org/backend-team
/apps/guard-codex/ @org/ai-team
```

### Owner Types
- **Teams**: `@org/team-name` - GitHub teams with multiple members
- **Users**: `@username` - Individual GitHub users

## Ownership Assignment

Ownership is defined through:
- **CODEOWNERS files**: GitHub-native ownership definitions (primary)
- **Team assignments**: Organizational team structure mapping
- **Policy rules**: OPA-based dynamic ownership assignment

## Contact Information

Ownership contact information is maintained in:
- Team directories and organizational charts
- On-call rotation schedules
- Emergency escalation procedures
