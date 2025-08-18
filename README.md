# GitGuard 🛡️
*The Autonomous Repository Steward*

GitGuard is an intelligent Git workflow automation platform that enforces quality, prevents incidents, and accelerates delivery through AI-powered code review and autonomous repository management. It features an organizational knowledge system ("org-brain") that provides judgment with receipts - every decision shows its source code and reasoning with full transparency and traceability.

## Quickstart

```bash
make setup && make up && make demo-quick
# Docs: http://localhost:8001  Grafana: http://localhost:3000  API: http://localhost:8000
```

### What you'll see

✅ **Auto-merge for low-risk PRs** - Safe changes merge automatically  
🚫 **Policy transparency with source code** - See exact OPA rules and inputs that made decisions  
📊 **Visual relationship graphs** - Mermaid diagrams show file touches and governance connections  
👥 **Always-current ownership index** - Dynamic owners list from live graph data  
📚 **Docs portal updating in real-time** - Live documentation with policy explanations  
🔥 **Chaos engineering drills** - Automated failure testing validates alert systems  
📈 **SLO monitoring with P99 alerts** - Performance tracking ensures system health  

### Demo Commands

```bash
make demo-quick     # 2-min flow: low-risk + security scenarios
make demo-investor  # 5-min flow: low-risk + release-window + dashboard
make demo-customer  # 10-min flow: comprehensive governance demo
```

### What happens on merge?

1. **🎯 Risk Assessment** - AI analyzes code complexity, test coverage, and security impact
2. **🚪 Policy Gate** - OPA enforces governance rules with full transparency (see exact rules & inputs)
3. **📊 Visual Mapping** - Mermaid graphs show file relationships and governance connections (≤20 nodes)
4. **👥 Ownership Tracking** - Dynamic owners index updates from graph data
5. **📖 Documentation** - Codex generates human-readable PR digest with policy explanations
6. **🔍 Monitoring** - SLO alerts track freshness P99 and system health

## Documentation

- [🚀 Getting Started Guide](GETTING_STARTED.md) - Complete user onboarding
- [🏗️ Architecture Overview](ARCHITECTURE.md) - System design and data flows
- [👩‍💻 Developer Guide](DEVELOPER_GUIDE.md) - Local setup and development
- [🤝 Contributing Guidelines](CONTRIBUTING.md) - How to contribute
- [🔗 GitHub Integration](docs/GITHUB_INTEGRATION.md) - PR comments with instant Codex preview links
- [📊 Prometheus Alerts](docs/PROMETHEUS_ALERTS.md) - Monitoring and SLO configuration
- [🔐 Secrets Hygiene](docs/SECRETS_HYGIENE.md) - Automated secrets redaction and scanning
- [📋 Operations Runbook](RUNBOOK.md) - Troubleshooting and done-done validation checklist
- [🌪️ Chaos Engineering](tests/CHAOS_ENGINEERING.md) - Failure testing and resilience validation
- [📚 Live Documentation Portal](http://localhost:8001) - Policies and PR digests (when running)
- [🔌 API Reference](http://localhost:8000/docs) - Interactive API docs (when running)
- [📊 Graph API](http://localhost:8000/graph/pr/{number}) - Read-only graph data endpoint

## Architecture

GitGuard consists of several components working together:

- **guard-api**: Receives GitHub webhooks, normalizes events, forwards to Codex
- **codex**: Writes PR digests to `docs_src/`, triggers MkDocs build
- **OPA**: Policy decisions for merge/tag (release windows, infra reviews, deps)
- **Temporal/NATS**: Workflow orchestration and event streaming
- **Prometheus/Grafana**: Observability - scrapes services, shows merge rates, block reasons, revert rate
- **CI**: Lint, tests, SBOM; sets `checks` signals for OPA input

**Flow**: PR → CI artifacts → risk compute → OPA gate → (merge|block) → Codex doc → dashboards

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design and data flows.

## Contributing

- **Branch from `main`**, name `feat|fix|chore/<scope>-<slug>`
- **Conventional Commits**; squash merge only
- **Run locally**: `make setup && make up`
- **Tests**: `pytest -q` (aim for coverage deltas ≥ -0.2%)
- **Policy changes** require a docs page under `docs_src/policies/`

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines and [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for setup instructions.

## Support

- 💬 [Discord Community](https://discord.gg/gitguard)
- 📧 [Enterprise Support](mailto:enterprise@gitguard.io)
- 🐛 [GitHub Issues](https://github.com/your-org/gitguard/issues)

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**GitGuard** - Your repositories, under guard. 🛡️
