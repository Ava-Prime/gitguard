# GitGuard GitHub Integration

This document describes the GitHub integration features for GitGuard, including automated PR comments with org-brain preview links, policy transparency, and Graph API access.

## 🔗 PR Comment Integration

GitGuard automatically comments on pull requests with a direct link to the Codex preview portal, providing instant developer value.

### Features

- **Instant Preview Links**: Every PR gets a comment with a direct link to its org-brain analysis
- **Policy Transparency**: Comments include policy decisions with source code references
- **Mermaid Graphs**: Visual relationship diagrams embedded in PR pages
- **Owners Index**: Dynamic ownership tracking and file-level responsibility
- **Graph API Access**: Real-time relationship data via REST endpoints
- **Portal Integration**: Links point to the generated static portal pages
- **Developer Experience**: No need to navigate to external tools - everything is linked directly in the PR

### Setup

#### 1. Configure Repository Variables

Set the `CODEX_BASE_URL` variable in your GitHub repository or organization settings:

**For GitHub Pages:**
```
CODEX_BASE_URL=https://your-org.github.io/your-repo
```

**For Custom CDN:**
```
CODEX_BASE_URL=https://your-cdn.example.com
```

**Steps to set the variable:**
1. Go to your repository Settings
2. Navigate to "Secrets and variables" → "Actions"
3. Click "Variables" tab
4. Click "New repository variable"
5. Name: `CODEX_BASE_URL`
6. Value: Your portal base URL (without trailing slash)

#### 2. Workflow Configuration

The `.github/workflows/codex-docs.yml` workflow includes:

```yaml
comment:
  if: github.event_name == 'pull_request'
  needs: build
  runs-on: ubuntu-latest
  permissions:
    pull-requests: write
  steps:
    - name: Comment PR with org-brain link
      uses: thollander/actions-comment-pull-request@v3
      with:
        message: |
          🧭 **Org-Brain Analysis**: `${{ vars.CODEX_BASE_URL }}/prs/${{ github.event.pull_request.number }}.html`
          
          📊 **Features Available:**
          - Policy transparency with source references
          - Mermaid relationship graphs
          - Dynamic owners index
          - Graph API: `${{ vars.CODEX_BASE_URL }}/graph/pr/${{ github.event.pull_request.number }}`
```

### How It Works

1. **PR Creation/Update**: When a PR is opened or updated on the `docs` branch
2. **Org-Brain Analysis**: The workflow builds comprehensive analysis including:
   - Policy transparency with source code references
   - Mermaid graphs showing relationships
   - Dynamic owners index updates
   - Graph API endpoints for real-time data
3. **Portal Build**: The workflow builds the org-brain portal with PR-specific analysis
4. **Comment Generation**: A comment is automatically posted with preview and API links
5. **Developer Access**: Developers can immediately access visual analysis and programmatic data

### Comment Format

The automated comment appears as:

> 🧭 **Org-Brain Analysis**: `https://your-domain.com/prs/123.html`
> 
> 📊 **Features Available:**
> - Policy transparency with source references
> - Mermaid relationship graphs
> - Dynamic owners index
> - Graph API: `https://your-domain.com/graph/pr/123`

Where `123` is the PR number, creating direct links to visual analysis and programmatic access.

### Permissions

The workflow requires:
- `pull-requests: write` - To post comments on PRs
- `contents: read` - To access repository content

### Troubleshooting

#### Comment Not Appearing

1. **Check Variable**: Ensure `CODEX_BASE_URL` is set correctly
2. **Workflow Permissions**: Verify the workflow has `pull-requests: write` permission
3. **Branch Targeting**: Confirm the PR targets the `docs` branch
4. **Action Logs**: Check the workflow run logs for errors

#### Wrong URL in Comment

1. **Variable Value**: Double-check the `CODEX_BASE_URL` variable value
2. **No Trailing Slash**: Ensure the base URL doesn't end with `/`
3. **Protocol**: Include `https://` in the base URL

#### Portal Page Not Found

1. **Build Success**: Verify the org-brain portal build completed successfully
2. **Deployment**: Check that the portal was deployed to the correct location
3. **File Generation**: Confirm the PR-specific HTML file was created
4. **Graph API**: Verify Graph API endpoints are accessible at port 8002
5. **Mermaid Rendering**: Check that Mermaid graphs are properly generated
6. **Policy Sources**: Ensure policy transparency includes source references

### Integration with Other Tools

#### Slack/Teams Integration

You can extend this pattern to post links in team channels:

```yaml
- name: Notify Slack
  uses: 8398a7/action-slack@v3
  with:
    status: success
    text: |
      🧭 Org-Brain analysis ready: ${{ vars.CODEX_BASE_URL }}/prs/${{ github.event.pull_request.number }}.html
      📊 Graph API: ${{ vars.CODEX_BASE_URL }}/graph/pr/${{ github.event.pull_request.number }}
      🔍 Features: Policy transparency, Mermaid graphs, dynamic ownership
```

#### Email Notifications

For email integration, the preview link can be included in notification templates.

### Security Considerations

- **Public Repositories**: Links will be publicly accessible if using GitHub Pages
- **Private Repositories**: Ensure your CDN/hosting respects repository privacy settings
- **Access Control**: Consider implementing authentication for sensitive codebases

### Best Practices

1. **Consistent Base URL**: Use the same `CODEX_BASE_URL` across all repositories in your organization
2. **CDN Usage**: Consider using a CDN for better performance and reliability
3. **Link Testing**: Regularly verify that generated links work correctly
4. **Documentation**: Keep this documentation updated when changing the setup

## 📊 Metrics and Monitoring

Track the effectiveness of PR comments and org-brain features:

- **Comment Success Rate**: Monitor workflow success/failure rates
- **Link Click-through**: Use analytics to track portal usage from PR comments
- **Graph API Usage**: Monitor API endpoint access and response times
- **Policy Transparency**: Track coverage of policy decisions with source references
- **Mermaid Graph Rendering**: Monitor graph generation success rates
- **Owners Index Updates**: Track dynamic ownership accuracy and freshness
- **Developer Feedback**: Gather feedback on the usefulness of visual analysis and API access

## 🔄 Future Enhancements

Potential improvements to consider:

- **Status Checks**: Add GitHub status checks with portal and API links
- **Rich Comments**: Include policy summary and ownership changes directly in comments
- **Interactive Graphs**: Embed interactive Mermaid graphs in PR comments
- **Real-time Updates**: Live updates via Graph API WebSocket connections
- **Multi-format Support**: Support different output formats (PDF, JSON, GraphQL)
- **Conditional Comments**: Only comment when significant policy or ownership changes are detected
- **CORS Integration**: Enable cross-origin access for external tools
- **Chaos Engineering**: Include chaos drill results in PR analysis
- **SLO Monitoring**: Display freshness and performance SLOs in comments