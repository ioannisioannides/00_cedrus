# Board Meeting Minutes — Cedrus

Date: 26 November 2025
Attendees: Project Owner, DevOps Lead, Product Owner, Security Lead, QA Lead, Accreditation Lead, Release Manager, UI/UX Lead, Orchestrator (PM)
Location: Remote
Facilitator: Orchestrator

## 1. Objectives

- Review current project status (tests, coverage, recent fixes)
- Prioritize critical production-readiness work
- Assign owners and target dates for top actions
- Agree next meeting and cadence

## 2. Executive Summary

- Test suite: 483 passing tests; coverage 80.5%.
- Recent work: Pylint fixes, logging improvements, markdown fixes, passed full test suite and pushed to `main`.
- Key gaps: Production hardening, CI/CD, monitoring, backup strategy, workflow unit tests, accreditation modules.

## 3. Decisions & Assignments

Below are the agreed owners and target dates for each action item (owners are suggested from prior planning and available team roles):

1. Apply Production Settings & Secrets
   - Owner: DevOps Lead (Primary), Security Lead (Advisor)
   - Start: 2025-11-26
   - Target: 2025-11-28
   - Acceptance: `python manage.py check --deploy` passes; no hardcoded secrets.

2. Implement CI/CD Pipeline
   - Owner: Release Manager
   - Start: 2025-11-26
   - Target: 2025-12-03
   - Acceptance: GitHub Actions workflow runs tests/lint, blocks merges on failure.

3. Dockerize Application and Compose
   - Owner: DevOps Lead
   - Start: 2025-11-26
   - Target: 2025-11-30
   - Acceptance: `docker-compose up` starts app + db locally; CI builds image.

4. Monitoring, Error Tracking & Logging
   - Owner: SRE / DevOps
   - Start: 2025-11-27
   - Target: 2025-12-01
   - Acceptance: Sentry receives a test event; uptime monitor configured.

5. Backups & Disaster Recovery
   - Owner: DevOps Lead
   - Start: 2025-11-27
   - Target: 2025-12-02
   - Acceptance: Successful restore of a test backup.

6. Fix Test Coverage Gaps & Add Workflow Unit Tests
   - Owner: QA Lead, Engineers
   - Start: 2025-11-26
   - Target: 2025-12-07
   - Acceptance: Coverage > 85% and `trunk/workflows/audit_workflow.py` covered by unit tests.

7. Security Hardening & Pen-testing Prep
   - Owner: Security Lead
   - Start: 2025-11-26
   - Target: 2025-12-04
   - Acceptance: `check --deploy` passes and Bandit report generated with no critical findings.

8. Add CI Caching & Performance Benchmarks
   - Owner: Performance Engineer
   - Start: 2025-11-28
   - Target: 2025-12-10
   - Acceptance: Redis configured; Locust script provided and run.

9. Complete Service Layer & Refactor Business Logic
   - Owner: Engineering Lead
   - Start: 2025-12-01
   - Target: 2025-12-14
   - Acceptance: Business logic moved to services and unit-tested.

10. API (Django REST Framework) & API Docs
    - Owner: Product Owner, Backend Engineer
    - Start: 2025-12-03
    - Target: 2025-12-17
    - Acceptance: Basic API endpoints with OpenAPI docs at `/api/docs/`.

11. Accessibility & UI/UX Polish
    - Owner: UI/UX Lead
    - Start: 2025-11-28
    - Target: 2025-12-10
    - Acceptance: Axe audit passes high-priority issues; design tokens follow brand guide.

12. Documentation: User Guides & Runbooks
    - Owner: Tech Writer
    - Start: 2025-11-27
    - Target: 2025-12-05
    - Acceptance: `docs/user-guides/` contains Auditor, Client, CB Admin guides.

13. Accreditation & Compliance Tasks
    - Owner: Accreditation Lead
    - Start: 2025-11-26
    - Target: 2025-12-14
    - Acceptance: Competence & complaints modules implemented; docs updated.

14. Legal, Contracts & GDPR Compliance
    - Owner: Legal Counsel
    - Start: 2025-11-27
    - Target: 2025-12-04
    - Acceptance: Documented retention policy and privacy controls.

15. Manual QA & Release Preparation
    - Owner: QA Lead & Release Manager
    - Start: 2025-12-05
    - Target: 2025-12-09
    - Acceptance: Manual QA checklist completed and release tag created.

16. Stakeholder Advisory Reviews
    - Owner: Project Manager
    - Start: 2025-11-29
    - Target: 2025-12-03
    - Acceptance: Advisory meetings with notes and action items captured.

17. Training & Enablement
    - Owner: Training Lead
    - Start: 2025-12-07
    - Target: 2025-12-21
    - Acceptance: Training deck uploaded and sessions scheduled.

18. Legal & Licensing Review
    - Owner: Legal Counsel
    - Start: 2025-11-27
    - Target: 2025-12-04
    - Acceptance: SPDX list of dependencies and license review complete.

19. CI: Add Pre-merge Linting and Security Checks
    - Owner: Release Manager / DevOps
    - Start: 2025-11-27
    - Target: 2025-12-03
    - Acceptance: `pylint`, `bandit`, `mypy` jobs run on PRs.

20. Roadmap & Prioritization Workshop
    - Owner: Project Manager / Orchestrator
    - Start: 2025-11-26
    - Target: 2025-11-28
    - Acceptance: 30-day plan in `.governance/ENTERPRISE_EXCELLENCE_30DAY_PLAN.md`.

21. Facilitated Board Meeting Minutes
    - Owner: Orchestrator
    - Completed: 2025-11-26

22. Create ELI5 Environment Secrets Guide (Private)
    - Owner: DevOps Lead (Author), Security Lead (Reviewer)
    - Completed: 2025-11-26

## 4. Action Items (Immediate / Next 48 hours)

- DevOps: Apply production settings and run `python manage.py check --deploy` (Due 2025-11-28).
- Release Manager: Open PR with CI skeleton (tests + lint) and block merges until passing (Due 2025-12-03).
- QA & Engineering: Identify top 10 coverage gaps and assign tickets (Due 2025-11-28).
- Security: Run Bandit and prepare pen-test checklist (Due 2025-12-04).

## 5. Risks Reviewed

- Production secrets and settings not applied — HIGH priority.
- No monitoring / backups yet — HIGH priority.
- Accreditation deliverables require feature additions — MEDIUM priority.

## 6. Next Meeting

- Date: 03 December 2025
- Focus: CI rollout, production settings verification, and coverage progress.

## 7. Minutes prepared by

Orchestrator (Project Manager)

---

*File created: `docs/board_meeting_minutes_2025-11-26.md`*
