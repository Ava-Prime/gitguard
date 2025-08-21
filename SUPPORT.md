# GitGuard Support

Welcome to GitGuard support! This document outlines how to get help, report issues, and contribute to the project.

## 🆘 Getting Help

### Quick Start Resources

- **📖 Documentation**: Start with our [README](README.md) and [Self-Dogfooding Guide](SELF_DOGFOOD.md)
- **🍳 Policy Cookbook**: Check our [Policy Examples](docs/policy-cookbook.md) for common use cases
- **🔧 Troubleshooting**: See [Common Issues](#common-issues) below
- **💬 Discussions**: Join conversations in [GitHub Discussions](https://github.com/Ava-Prime/gitguard/discussions)

### Support Channels

| Channel | Best For | Response Time |
|---------|----------|---------------|
| [GitHub Issues](https://github.com/Ava-Prime/gitguard/issues) | Bug reports, feature requests | 1-3 business days |
| [GitHub Discussions](https://github.com/Ava-Prime/gitguard/discussions) | Questions, ideas, community help | Community-driven |
| [Security Issues](SECURITY.md) | Security vulnerabilities | 24-48 hours |

## 🐛 Reporting Issues

### Before Reporting

1. **Search existing issues**: Check if your issue has already been reported
2. **Check documentation**: Review our docs and troubleshooting guides
3. **Test with latest version**: Ensure you're using the most recent GitGuard release
4. **Gather information**: Collect logs, configuration, and reproduction steps

### Issue Types

- **🐛 Bug Report**: Something isn't working as expected
- **✨ Feature Request**: Suggest new functionality
- **📚 Documentation**: Improvements to docs or examples
- **🔒 Security**: Use our [security vulnerability template](.github/ISSUE_TEMPLATE/security-vulnerability.yml)

### What to Include

**For Bug Reports:**
- GitGuard version and deployment method
- Operating system and environment details
- Complete error messages and logs
- Steps to reproduce the issue
- Expected vs. actual behavior
- Policy configuration (sanitized)

**For Feature Requests:**
- Clear description of the desired functionality
- Use case and business justification
- Proposed implementation approach (if any)
- Examples of similar features in other tools

## 🔧 Common Issues

### Installation & Setup

**Issue**: Docker containers won't start
```bash
# Check container logs
docker-compose logs gitguard
docker-compose logs temporal

# Verify port availability
netstat -tulpn | grep :8080
netstat -tulpn | grep :7233
```

**Issue**: GitHub App webhook not receiving events
- Verify webhook URL is accessible from GitHub
- Check webhook secret configuration
- Ensure ngrok/cloudflared tunnel is active
- Review GitHub App permissions

**Issue**: Policy evaluation failures
```bash
# Check policy syntax
make dryrun

# Review evaluation logs
docker-compose logs gitguard | grep "policy"

# Test policy in isolation
curl -X POST http://localhost:8080/api/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{"policy": "your-policy-here", "input": {}}'
```

### Configuration Issues

**Issue**: Environment variables not loading
- Verify `.env` file exists and is properly formatted
- Check for trailing spaces or special characters
- Ensure Docker Compose is reading the correct `.env` file

**Issue**: GitHub App authentication failures
- Verify `GITHUB_APP_ID` matches your GitHub App
- Check `GITHUB_APP_PRIVATE_KEY` is properly formatted (with newlines)
- Ensure `GITHUB_WEBHOOK_SECRET` matches GitHub App configuration

### Performance Issues

**Issue**: Slow policy evaluation
- Review policy complexity and optimize logic
- Check for infinite loops or expensive operations
- Monitor resource usage: `docker stats`
- Consider policy caching strategies

**Issue**: High memory usage
- Review Temporal workflow retention settings
- Check for memory leaks in custom policies
- Monitor container resource limits

## 🚀 Self-Service Debugging

### Health Checks

```bash
# Check GitGuard health
curl http://localhost:8080/health

# Check Temporal health
curl http://localhost:7233/api/v1/namespaces

# Verify all services
make status
```

### Log Analysis

```bash
# GitGuard application logs
docker-compose logs -f gitguard

# Temporal workflow logs
docker-compose logs -f temporal

# All services with timestamps
docker-compose logs -f -t

# Filter for errors
docker-compose logs gitguard | grep -i error
```

### Configuration Validation

```bash
# Validate policy syntax
make dryrun

# Test webhook endpoint
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: ping" \
  -d '{"zen": "test"}'

# Check environment configuration
docker-compose config
```

## 📋 Diagnostic Information

When reporting issues, please include:

### System Information
```bash
# GitGuard version
git describe --tags --always

# Docker version
docker --version
docker-compose --version

# System resources
df -h
free -h
```

### Configuration (Sanitized)
```bash
# Environment variables (remove secrets)
env | grep -E '^(GITHUB_|GITGUARD_)' | sed 's/=.*/=***REDACTED***/'

# Docker Compose configuration
docker-compose config --services
```

### Recent Logs
```bash
# Last 100 lines from each service
docker-compose logs --tail=100 gitguard
docker-compose logs --tail=100 temporal
```

## 🤝 Contributing

We welcome contributions! See our [Contributing Guidelines](CONTRIBUTING.md) for:

- Code contribution process
- Development environment setup
- Testing requirements
- Code style guidelines

### Quick Contribution Checklist

- [ ] Fork the repository
- [ ] Create a feature branch
- [ ] Write tests for new functionality
- [ ] Ensure all tests pass
- [ ] Update documentation
- [ ] Submit a pull request

## 📞 Emergency Support

### Security Issues

For security vulnerabilities:
1. **DO NOT** create a public GitHub issue
2. Email: security@gitguard.dev
3. Use our [security policy](SECURITY.md) guidelines
4. Expect acknowledgment within 24-48 hours

### Critical Production Issues

For production outages or critical issues:
1. Check our [incident runbook](INCIDENT_RUNBOOK.md)
2. Create a GitHub issue with "[URGENT]" prefix
3. Include full diagnostic information
4. Tag @maintainers in the issue

## 📚 Additional Resources

- **🏠 Homepage**: [GitGuard Project](https://github.com/Ava-Prime/gitguard)
- **📖 Documentation**: [Wiki](https://github.com/Ava-Prime/gitguard/wiki)
- **🎯 Roadmap**: [Project Board](https://github.com/Ava-Prime/gitguard/projects)
- **📊 Status**: [Service Status](https://status.gitguard.dev) (if applicable)
- **💬 Community**: [Discord/Slack](https://discord.gg/gitguard) (if applicable)

## 🙏 Community Guidelines

When seeking support:

- **Be respectful**: Treat all community members with kindness
- **Be specific**: Provide detailed information about your issue
- **Be patient**: Maintainers and community members volunteer their time
- **Be helpful**: Share solutions that work for you
- **Search first**: Check existing issues and discussions

---

**Need immediate help?** Start with our [troubleshooting guide](#common-issues) or create a [GitHub issue](https://github.com/Ava-Prime/gitguard/issues/new/choose).

**Found this helpful?** ⭐ Star the project and share it with others!
