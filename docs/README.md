# Technical Documentation

This directory contains technical reference documentation, architecture guides, API references, and user guides for the Cedrus certification management platform.

---

## 📁 Directory Structure

### Architecture & Design

- **`ARCHITECTURE.md`** - High-level system architecture overview
- **`ARCHITECTURE_DIAGRAMS.md`** - Visual diagrams of system components
- **`ARCHITECTURE_VISION.md`** - Long-term architectural vision and goals
- **`ARCHITECTURAL_PATTERNS.md`** - Design patterns and principles used
- **`REFACTORING_PROPOSAL.md`** - Proposed architectural improvements

### Technical Reference

- **`MODELS.md`** - Complete data model documentation (all apps)
- **`API_REFERENCE.md`** - API endpoints and usage
- **`DEPLOYMENT.md`** - Deployment procedures and configuration

### Product Documentation

- **`PRODUCT_REQUIREMENTS.md`** - Detailed product requirements and user stories
- **`PRODUCT_INDEX.md`** - Index of all product features
- **`MVP_SCOPE.md`** - Minimum Viable Product scope definition
- **`USER_JOURNEYS.md`** - User journey maps and workflows

### Brand & Design

- **`BRAND_GUIDELINES.md`** - Brand identity and design system
- **`BRAND_QUICK_REFERENCE.md`** - Quick brand reference guide

### Implementation Tracking

- **`IMPLEMENTATION_PROGRESS.md`** - Current implementation status (Priority 2)
- **`BACKLOG.md`** - Feature backlog and prioritization
- **`TASK_BOARD.md`** - Current sprint task board

### Phase 2 Documentation

- **`PHASE_2_QUICK_REFERENCE.md`** - Quick reference for Phase 2 features (Root Cause Analysis, IAF MD1/MD5)

### User Guides

- **`user-guides/`** - End-user documentation directory
  - `AUDIT_WORKFLOW_GUIDE.md` - Step-by-step audit workflow guide
  - `WORKFLOW_DIAGRAMS.md` - Visual workflow diagrams

---

## 🎯 Document Categories

### For Developers

**Getting Started:**

- Read `ARCHITECTURE.md` for system overview
- Review `MODELS.md` for data structure
- Check `API_REFERENCE.md` for endpoint details
- Follow `DEPLOYMENT.md` for setup

**Implementation:**

- Check `IMPLEMENTATION_PROGRESS.md` for current status
- Review `BACKLOG.md` for upcoming work
- Consult `ARCHITECTURAL_PATTERNS.md` for design guidance

### For Product Managers

**Planning:**

- Review `PRODUCT_REQUIREMENTS.md` for feature details
- Check `MVP_SCOPE.md` for scope boundaries
- Track progress in `IMPLEMENTATION_PROGRESS.md`
- Prioritize work in `BACKLOG.md`

**User Experience:**

- Review `USER_JOURNEYS.md` for user flows
- Check brand consistency with `BRAND_GUIDELINES.md`

### For Business Users

**User Documentation:**

- Start with `user-guides/AUDIT_WORKFLOW_GUIDE.md`
- Reference `user-guides/WORKFLOW_DIAGRAMS.md` for visual guides
- Use `PHASE_2_QUICK_REFERENCE.md` for IAF compliance features

---

## 📊 Key Features Documented

### Phase 1 - ISO 17021 Core Compliance

- 7-state audit workflow (draft → closed)
- Technical review (ISO 17021-1 Clause 9.5)
- Certification decision (ISO 17021-1 Clause 9.6)
- Immutable audit trail

### Phase 2 - IAF Mandatory Documents Compliance

- Root cause analysis system
- Finding recurrence tracking
- Auditor competence management
- IAF MD1 multi-site sampling algorithm
- IAF MD5 duration validation

---

## 🔗 Related Directories

- **`.governance/`** - Formal governance documents, board decisions, completion reports
- **`.agents/`** - Multi-agent system configuration and agent definitions
- **`audits/`** - Audit app source code
- **`core/`** - Core app source code (organizations, certifications)
- **`accounts/`** - User management source code

---

## 📝 Documentation Standards

### Markdown Format

- All documentation in Markdown (.md)
- Use clear headings and structure
- Include table of contents for long documents
- Add examples where applicable

### Naming Convention

- Use UPPERCASE for major reference docs (ARCHITECTURE.md, MODELS.md)
- Use Title_Case for specific features (Phase_2_Quick_Reference.md)
- Use lowercase for directories (user-guides/)

### Content Guidelines

- Keep technical docs up-to-date with code
- Include version/date stamps on guides
- Provide code examples in reference docs
- Link related documents

---

## 🔄 Recently Updated

- **PHASE_2_QUICK_REFERENCE.md** - Added Nov 21, 2025 (Phase 2 completion)
- **IMPLEMENTATION_PROGRESS.md** - Updated Nov 20, 2025 (Priority 2 complete)
- **MODELS.md** - Updated with Phase 2 models

---

## 📞 Getting Help

### Documentation Issues

- Missing documentation? Check `.governance/` for completion reports
- Technical questions? See `ARCHITECTURE.md` and `MODELS.md`
- User questions? Check `user-guides/` directory

### Contributing to Documentation

- Follow existing format and style
- Update related documents when making changes
- Keep code examples synchronized with actual code
- Add entries to this README for new major documents

---

## 🎓 Learning Path

### New Developers

1. Start: `ARCHITECTURE.md` - Understand system structure
2. Then: `MODELS.md` - Learn data models
3. Next: `PRODUCT_REQUIREMENTS.md` - Understand features
4. Finally: Check `IMPLEMENTATION_PROGRESS.md` - See current state

### New Product Managers

1. Start: `PRODUCT_INDEX.md` - Feature overview
2. Then: `MVP_SCOPE.md` - Scope understanding
3. Next: `USER_JOURNEYS.md` - User flows
4. Finally: `BACKLOG.md` - Planning priorities

### End Users

1. Start: `user-guides/AUDIT_WORKFLOW_GUIDE.md` - Main workflow
2. Then: `PHASE_2_QUICK_REFERENCE.md` - Advanced features
3. Reference: `user-guides/WORKFLOW_DIAGRAMS.md` - Visual guides

---

**Last Updated:** November 21, 2025  
**Maintained by:** Cedrus Development Team  
**Status:** Active Development
