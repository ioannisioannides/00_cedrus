# 🔌 MCP SERVER SETUP GUIDE

## GitHub MCP Server Configuration for Cedrus

**Date:** November 21, 2025  
**Purpose:** Enable enhanced GitHub integration for 30-day excellence tracking

---

## ✅ INSTALLATION COMPLETE

**Package:** `github-mcp-server` v1.8.7  
**Status:** ✅ Installed globally  
**Location:** `/usr/local/lib/node_modules/github-mcp-server`

---

## 🔑 STEP 1: CREATE GITHUB PERSONAL ACCESS TOKEN

### Generate Token on GitHub

1. Go to: <https://github.com/settings/tokens/new>
2. Token name: `Cedrus MCP Server - Development`
3. Expiration: `90 days` (or custom for MVP period)
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (Update GitHub Action workflows)
   - ✅ `project` (Full control of projects)
   - ✅ `admin:org` (if using organization)
   - ✅ `notifications` (Access notifications)

5. Click **Generate token**
6. **Copy the token immediately** (you won't see it again!)

### Example Token Format

```
ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 🛠️ STEP 2: CONFIGURE VS CODE MCP SETTINGS

### Option A: VS Code Settings UI

1. Open VS Code Settings (`Cmd+,` on macOS)
2. Search for: `mcp`
3. Find: **GitHub Copilot > MCP: Servers**
4. Click **Edit in settings.json**

### Option B: Direct JSON Configuration

Add to your VS Code `settings.json`:

**Location:** `~/Library/Application Support/Code/User/settings.json` (macOS)

```json
{
  "github.copilot.chat.mcp.enabled": true,
  "github.copilot.chat.mcp.servers": {
    "github": {
      "command": "github-mcp-server",
      "args": [],
      "env": {
        "GITHUB_TOKEN": "ghp_YOUR_TOKEN_HERE",
        "GITHUB_OWNER": "ioannisioannides",
        "GITHUB_REPO": "00_cedrus"
      }
    }
  }
}
```

**⚠️ Security Note:** DO NOT commit settings.json with your token!

### Alternative: Environment Variables (More Secure)

```bash
# Add to ~/.zshrc or ~/.bashrc
export GITHUB_TOKEN="ghp_YOUR_TOKEN_HERE"
export GITHUB_OWNER="ioannisioannides"
export GITHUB_REPO="00_cedrus"
```

Then in VS Code settings:

```json
{
  "github.copilot.chat.mcp.servers": {
    "github": {
      "command": "github-mcp-server",
      "args": []
    }
  }
}
```

---

## 🎯 STEP 3: VERIFY CONNECTION

### Test MCP Server Connection

1. **Restart VS Code** (required after config changes)
2. Open GitHub Copilot Chat
3. Try a test command:

**Example Prompts:**

```
@github list open issues
@github create issue "Day 6-7: Monitoring & Observability" with label "week-1"
@github show workflow status
@github create branch "feature/monitoring-observability"
```

### Expected Response

```
✅ Connected to github/00_cedrus
✅ Found X open issues
✅ GitHub Actions: Y workflows
```

---

## 📊 CEDRUS USE CASES

### 1. **30-Day Milestone Tracking**

**Create Issues for Each Day:**

```
Create GitHub issues for Week 2 tasks:
- Day 8-9: Test Suite Overhaul
- Day 10-11: Integration & E2E Testing
- Day 12-13: Performance & Load Testing
- Day 14: Security Penetration Testing
```

**Link Commits to Issues:**

```
When committing Day 6-7 work, include:
git commit -m "feat: Day 6-7 Monitoring (#6)"
```

### 2. **CI/CD Monitoring**

**Check Pipeline Status:**

```
Show me the status of the latest CI/CD run
Did the security scan pass?
What's the test coverage from the last run?
```

### 3. **Pull Request Workflow**

**Create Feature Branches:**

```
Create a new branch "feature/week2-testing" from main
Create PR for Day 6-7 monitoring implementation
Review open PRs and check CI status
```

### 4. **Project Board Integration**

**Track Progress:**

```
Move "Day 5: Docker" to Done column
Add "Day 6-7: Monitoring" to In Progress
Show project board status
```

### 5. **Issue Management**

**Bug Tracking:**

```
Create issue: "76 failing tests need fixtures update"
Label it: bug, week-2, priority-high
Assign to: @ioannisioannides
```

---

## 🚀 IMMEDIATE ACTIONS (Post-Setup)

### Once MCP Server is Connected

1. **Create Week 1 Milestone**
   - Title: "Week 1: Foundation & Security (Days 1-7)"
   - Due date: November 28, 2025
   - Link Days 1-7 issues

2. **Create Week 2-4 Milestones**
   - Week 2: Quality & Testing (Days 8-14)
   - Week 3: Architecture & Optimization (Days 15-21)
   - Week 4: UI/UX & Documentation (Days 22-28)

3. **Generate Issue Template**
   - Day X-Y: `[Task Name]`
   - Assigned to: Elite agent team
   - Labels: week-N, priority-level
   - Checklist: Deliverables from 30-day plan

4. **Setup GitHub Actions Monitoring**
   - Watch for CI/CD failures
   - Monitor security scan results
   - Track test coverage trends

---

## 🔍 TROUBLESHOOTING

### Issue: "MCP Server not found"

**Solution:** Verify installation

```bash
which github-mcp-server
npm list -g github-mcp-server
```

### Issue: "Authentication failed"

**Solution:** Check token

```bash
# Test token with curl
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/user
```

### Issue: "VS Code not detecting MCP"

**Solution:**

1. Restart VS Code completely
2. Check settings.json syntax (valid JSON)
3. Verify Copilot Chat is enabled
4. Check VS Code version (needs latest)

### Issue: "Permission denied"

**Solution:** Token needs correct scopes

- Regenerate token with `repo`, `workflow`, `project`

---

## 📚 AVAILABLE COMMANDS

### Repository Operations

- List files, branches, commits
- Search code, issues, PRs
- Clone, pull, push operations

### Issue Management

- Create, update, close issues
- Add labels, assignees, milestones
- Comment on issues

### Pull Request Workflow

- Create PRs from branches
- Review code changes
- Merge, close PRs
- Check CI status

### GitHub Actions

- List workflows
- Trigger workflow runs
- Check run status
- View logs

### Project Boards

- List projects
- Move cards between columns
- Add issues to projects

---

## 💡 TIPS & BEST PRACTICES

### 1. **Consistent Naming**

```
Branches: feature/day-X-Y-description
Issues: Day X-Y: Task Name
PRs: feat: Day X-Y implementation
```

### 2. **Linking**

```
Commits: "feat: monitoring (#6)"
PRs: "Closes #6, Resolves #7"
```

### 3. **Labels**

```
week-1, week-2, week-3, week-4
priority-high, priority-medium, priority-low
bug, enhancement, documentation
security, performance, testing
```

### 4. **Milestones**

- Group by week (Week 1-4)
- Set realistic due dates
- Track completion percentage

---

## 🎉 NEXT STEPS

1. ✅ Complete this setup guide
2. ✅ Generate GitHub token
3. ✅ Configure VS Code settings
4. ✅ Restart VS Code
5. ✅ Test connection with simple command
6. ✅ Create Week 1 milestone
7. ✅ Create issues for Days 6-30
8. ✅ Continue with Day 6-7 implementation

---

## 📖 RESOURCES

- **GitHub MCP Server:** <https://github.com/github/github-mcp-server>
- **MCP Documentation:** <https://modelcontextprotocol.io/>
- **GitHub API:** <https://docs.github.com/en/rest>
- **Personal Access Tokens:** <https://github.com/settings/tokens>

---

**Setup by:** Dr. Elena Rostova (Orchestrator)  
**Date:** November 21, 2025  
**Status:** Ready for token configuration  
**Next:** Day 6-7 Monitoring & Observability
