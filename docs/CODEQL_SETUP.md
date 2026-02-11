# CodeQL Setup

This repository uses a **custom CodeQL workflow** (`.github/workflows/codeql.yml`) for advanced code security scanning.

## Important Configuration Requirement

**GitHub's default CodeQL setup MUST be disabled for the custom workflow to function correctly.**

### Why This Matters

CodeQL analyses from advanced configurations (custom workflows) cannot be processed when the default setup is enabled. You'll encounter the following error if both are active:

```
CodeQL analyses from advanced configurations cannot be processed when the default setup is enabled
```

### How to Disable Default Setup

1. Navigate to your repository on GitHub
2. Go to **Settings** → **Code security and analysis**
3. Under the "Code scanning" section, locate **CodeQL analysis**
4. If it shows as "Enabled" with default setup:
   - Click **"Disable"** to turn off default setup, OR
   - Click **"Configure"** → Switch to **"Advanced"** mode

### Custom Workflow Benefits

Our custom CodeQL workflow (`.github/workflows/codeql.yml`) provides:

- **Multi-language scanning**: Python and JavaScript
- **Scheduled scans**: Daily security checks (10:00 UTC)
- **PR integration**: Automatic scanning on pull requests
- **Flexible configuration**: Customizable security rules and patterns
- **Manual triggers**: On-demand security scans via workflow_dispatch

### Workflow Schedule

The CodeQL workflow runs:

- On every push to the `main` branch
- On every pull request to the `main` branch
- Daily at 10:00 UTC (scheduled scan)
- Manually via the Actions tab (workflow_dispatch)

### Troubleshooting

#### Error: "CodeQL analyses from advanced configurations cannot be processed"

**Solution**: Disable GitHub's default CodeQL setup following the steps above.

#### Workflow Not Running

1. Verify the workflow file exists at `.github/workflows/codeql.yml`
2. Check that GitHub Actions are enabled for the repository
3. Ensure you have the required permissions (`security-events: write`)

#### Results Not Appearing in Security Tab

1. Verify the workflow completed successfully in the Actions tab
2. Check that `security-events: write` permission is granted
3. Wait a few minutes - results may take time to process

## Additional Resources

- [GitHub CodeQL Documentation](https://docs.github.com/en/code-security/code-scanning/introduction-to-code-scanning/about-code-scanning-with-codeql)
- [CodeQL CLI Reference](https://codeql.github.com/docs/codeql-cli/)
- [Security Policy](../SECURITY.md)
