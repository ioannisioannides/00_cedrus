# Phase 3 Implementation Plan: Operational Excellence & Expansion

**Status:** DRAFT
**Start Date:** 25 November 2025
**Target Completion:** Sprint 12

---

## 1. Executive Summary

Phase 3 focuses on transforming Cedrus from a data capture system into a full-service certification platform. The primary goals are to generate professional, legally binding documentation (PDFs) and expand the market addressable by the platform to include Internal Audit departments (ISO 19011).

## 2. Key Deliverables

### 2.1 Reporting Engine (Priority 1)

**Objective:** Automate the generation of formal documents.

- **Features:**
  - **Audit Report PDF:** A comprehensive document including scope, team, findings, and conclusions.
  - **Certificate PDF:** A formal ISO certificate with QR code validation.
  - **Audit Plan PDF:** A schedule document for clients.
- **Technology:** `WeasyPrint` (HTML-to-PDF) + Django Templates.

### 2.2 Internal Audit Module (Priority 2)

**Objective:** Support ISO 19011 internal audit workflows.

- **Features:**
  - **Audit Program:** Annual schedule of internal audits.
  - **Self-Assessment:** Checklists for internal auditors.
  - **Gap Analysis:** Tools for pre-assessment.
- **Architecture:** Extension of `audits` app or new `internal_audits` app.

### 2.3 Notification System (Priority 3)

**Objective:** Keep stakeholders informed.

- **Features:**
  - Email triggers on status changes (e.g., "Audit Submitted").
  - In-app notifications for assigned tasks.

---

## 3. Technical Architecture

### 3.1 New Application: `reporting`

We will create a dedicated Django app `reporting` to handle:

- PDF Generation Logic.
- Template Management.
- Document Versioning.

### 3.2 Dependencies

- `WeasyPrint`: For high-fidelity PDF generation.
- `qrcode`: For certificate validation links.

---

## 4. Sprint Plan

### Sprint 11: The Reporting Engine

- **Goal:** Generate Audit Report and Certificate PDFs.
- **Tasks:**
  1. Initialize `reporting` app.
  2. Design HTML templates for Reports and Certificates.
  3. Implement PDF generation service.
  4. Add "Download PDF" buttons to Audit Detail view.

### Sprint 12: Internal Audit & Notifications

- **Goal:** Internal Audit workflows and Email alerts.
- **Tasks:**
  1. Model `AuditProgram` for internal scheduling.
  2. Implement Email Service.
  3. Create Internal Audit specific views.

---

## 5. Success Metrics

- **PDF Generation Time:** < 2 seconds per document.
- **Visual Fidelity:** PDFs must match Cedrus Brand Guidelines.
- **Code Quality:** Maintain 10/10 Pylint score.
