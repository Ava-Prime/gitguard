# GitGuard Demo

🚀 **Experience GitGuard instantly without any local setup required!**

## 🌐 Live Demo

Try GitGuard right now in your browser:

**👉 [Launch Interactive Demo](https://codessa-platform.github.io/gitguard/demo/)**

## 🎯 What You Can Experience

### 🎮 Interactive Playground
- **Full GitGuard Interface**: Explore the complete dashboard with sample data
- **Policy Management**: Create, edit, and test policies in real-time
- **Repository Simulation**: See how GitGuard handles different repository scenarios
- **Real-time Monitoring**: Watch policy evaluations and decisions as they happen

### 📊 Live Dashboard
- **Policy Evaluations**: See approved, rejected, and pending decisions
- **Compliance Monitoring**: Track regulatory compliance across repositories
- **Performance Metrics**: View deployment success rates and review times
- **Risk Assessment**: Understand how GitGuard identifies and mitigates risks

### 🔗 API Explorer
- **Interactive Documentation**: Test all API endpoints with live examples
- **Authentication Flow**: Understand how to integrate with GitGuard
- **Webhook Simulation**: See how GitGuard responds to GitHub events
- **Response Examples**: View real API responses with sample data

## 🚀 Quick Deployment Options

### Option 1: One-Click Cloud Deployment

#### Railway
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/gitguard)

#### Render
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/codessa-platform/gitguard)

#### Fly.io
```bash
flyctl launch --from https://github.com/codessa-platform/gitguard
```

### Option 2: Local Docker Deployment

#### Linux/macOS
```bash
# Quick deploy script
curl -fsSL https://raw.githubusercontent.com/codessa-platform/gitguard/main/scripts/quick-deploy.sh | bash

# Or manual Docker Compose
git clone https://github.com/codessa-platform/gitguard.git
cd gitguard
docker-compose up -d
```

#### Windows
```powershell
# Download and run PowerShell script
iwr -useb https://raw.githubusercontent.com/codessa-platform/gitguard/main/scripts/quick-deploy.ps1 | iex

# Or manual Docker Compose
git clone https://github.com/codessa-platform/gitguard.git
cd gitguard
docker-compose up -d
```

### Option 3: Binary Installation

#### Linux
```bash
# Download latest release
wget https://github.com/codessa-platform/gitguard/releases/latest/download/gitguard-linux
chmod +x gitguard-linux
./gitguard-linux serve --demo
```

#### Windows
```powershell
# Download latest release
Invoke-WebRequest -Uri "https://github.com/codessa-platform/gitguard/releases/latest/download/gitguard-windows.exe" -OutFile "gitguard.exe"
.\gitguard.exe serve --demo
```

#### macOS
```bash
# Download latest release
wget https://github.com/codessa-platform/gitguard/releases/latest/download/gitguard-darwin
chmod +x gitguard-darwin
./gitguard-darwin serve --demo
```

## 🎭 Demo Scenarios

Once you have GitGuard running, try these scenarios:

### 1. Policy Evaluation Workflow
1. **Visit the Dashboard** → See active policies and recent evaluations
2. **Create a Test Policy** → Use the policy editor to define rules
3. **Simulate a Pull Request** → Watch GitGuard evaluate your policy
4. **Review the Decision** → Understand the reasoning behind approvals/rejections

### 2. Compliance Monitoring
1. **Check Compliance Dashboard** → View regulatory compliance status
2. **Review Audit Logs** → See detailed compliance tracking
3. **Test Compliance Policies** → Create policies for SOX, GDPR, etc.
4. **Generate Reports** → Export compliance reports

### 3. Risk Assessment
1. **View Risk Dashboard** → See risk scores for repositories
2. **Analyze Breaking Changes** → Understand impact assessment
3. **Review Security Scans** → See vulnerability detection in action
4. **Test Risk Policies** → Create custom risk evaluation rules

### 4. API Integration
1. **Explore API Docs** → Interactive Swagger/OpenAPI interface
2. **Test Endpoints** → Make real API calls with sample data
3. **Webhook Simulation** → See how GitGuard handles GitHub events
4. **Authentication** → Understand API key and OAuth flows

## 🔧 Configuration Options

### Environment Variables

```bash
# Demo Configuration
DEMO_MODE=true                    # Enable demo mode with sample data
GENERATE_SAMPLE_DATA=true         # Create sample repositories and policies
SAMPLE_REPOS=5                    # Number of sample repositories
SAMPLE_POLICIES=10                # Number of sample policies

# Service Ports
GITGUARD_PORT=8080                # Main GitGuard API port
GRAFANA_PORT=3000                 # Grafana dashboard port
PROMETHEUS_PORT=9090              # Prometheus metrics port

# Database (Demo)
POSTGRES_DB=gitguard_demo         # Demo database name
POSTGRES_USER=gitguard            # Database user
POSTGRES_PASSWORD=demo_password   # Database password (auto-generated)

# GitHub Integration (Optional)
GITHUB_APP_ID=your_app_id         # GitHub App ID
GITHUB_APP_PRIVATE_KEY=your_key   # GitHub App private key
GITHUB_WEBHOOK_SECRET=your_secret # Webhook secret
```

### Custom Deployment

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  gitguard-api:
    environment:
      - CUSTOM_POLICY_PATH=/custom/policies
      - ENABLE_ADVANCED_FEATURES=true
    volumes:
      - ./custom-policies:/custom/policies
    ports:
      - "9000:8080"  # Custom port mapping
```

## 📊 Monitoring & Observability

### Access Points
- **GitGuard Dashboard**: `http://localhost:8080`
- **Grafana Monitoring**: `http://localhost:3000`
- **Prometheus Metrics**: `http://localhost:9090`
- **Temporal Web UI**: `http://localhost:8088`
- **API Documentation**: `http://localhost:8080/docs`

### Key Metrics
- Policy evaluation success rate
- Average review time
- Deployment frequency
- Security scan results
- Compliance score trends

## 🛠️ Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check Docker status
docker ps
docker-compose logs

# Restart services
docker-compose restart
```

#### Port Conflicts
```bash
# Use custom ports
PORT=9000 GRAFANA_PORT=4000 docker-compose up -d
```

#### Database Connection Issues
```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

### Getting Help

- 📚 **Documentation**: [https://codessa-platform.github.io/gitguard/](https://codessa-platform.github.io/gitguard/)
- 🐛 **Issues**: [GitHub Issues](https://github.com/codessa-platform/gitguard/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/codessa-platform/gitguard/discussions)
- 📧 **Email**: support@codessa-platform.com

## 🎯 Next Steps

After exploring the demo:

1. **⭐ Star the Repository** → Show your support
2. **🔗 Connect Your GitHub** → Set up real integration
3. **📝 Create Custom Policies** → Define your governance rules
4. **🚀 Deploy to Production** → Use our production deployment guides
5. **🤝 Join the Community** → Contribute and get support

## 🏗️ Architecture Overview

The demo includes:

- **GitGuard API**: Core policy engine and REST API
- **PostgreSQL**: Policy and evaluation data storage
- **Redis**: Caching and session management
- **Temporal**: Workflow orchestration
- **OPA**: Policy decision engine
- **Prometheus**: Metrics collection
- **Grafana**: Monitoring dashboards

## 🔒 Security Note

**⚠️ Demo Environment Only**: The demo uses simplified security settings for ease of use. For production deployments:

- Use strong, unique passwords
- Enable TLS/SSL encryption
- Configure proper authentication
- Set up network security
- Review security best practices

---

**Ready to experience GitGuard?** 🚀

👉 **[Launch Demo Now](https://codessa-platform.github.io/gitguard/demo/)**
