# API Reference - Priority 2 Endpoints

**Version:** 1.0  
**Last Updated:** 20 November 2025  
**Base URL:** `http://your-domain.com` or `http://127.0.0.1:8000` (development)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Documentation Endpoints](#documentation-endpoints)
3. [Recommendation & Decision Endpoints](#recommendation--decision-endpoints)
4. [File Management Endpoints](#file-management-endpoints)
5. [Status Transition Endpoints](#status-transition-endpoints)
6. [Response Codes](#response-codes)
7. [Error Handling](#error-handling)

---

## Authentication

All endpoints require user authentication via Django session cookies.

**Authentication Method:** Session-based (cookie)

**Required Headers:**

```http
Cookie: sessionid=<session_token>
X-CSRFToken: <csrf_token>
```

**Login Endpoint:**

```http
POST /accounts/login/
Content-Type: application/x-www-form-urlencoded

username=<username>&password=<password>
```

---

## Documentation Endpoints

### Edit Organization Changes

Update organization changes documentation for an audit.

**Endpoint:** `GET/POST /audits/audit/<int:audit_id>/edit-organization-changes/`

**Method:** `GET` (display form) or `POST` (submit form)

**Permissions:** Lead Auditor or CB Admin

**URL Parameters:**

- `audit_id` (integer, required): The audit ID

**Form Fields (POST):**

```json
{
  "has_org_changes": boolean,
  "org_changes_details": string (required if has_org_changes=true),
  "changes_affect_scope": boolean (required if has_org_changes=true),
  "scope_impact_details": string (optional)
}
```

**Example Request:**

```http
POST /audits/audit/123/edit-organization-changes/
Content-Type: application/x-www-form-urlencoded
X-CSRFToken: <token>

has_org_changes=true&org_changes_details=New+production+line+added&changes_affect_scope=false
```

**Success Response:**

```http
HTTP/1.1 302 Found
Location: /audits/audit/123/

Set-Cookie: messages=Organization+changes+updated+successfully
```

**Error Response:**

```http
HTTP/1.1 200 OK
Content-Type: text/html

<!-- Form with validation errors -->
```

---

### Edit Audit Plan Review

Update audit plan review documentation.

**Endpoint:** `GET/POST /audits/audit/<int:audit_id>/edit-plan-review/`

**Method:** `GET` (display form) or `POST` (submit form)

**Permissions:** Lead Auditor or CB Admin

**URL Parameters:**

- `audit_id` (integer, required): The audit ID

**Form Fields (POST):**

```json
{
  "plan_reviewed": boolean,
  "plan_adequate": boolean (required if plan_reviewed=true),
  "plan_changes_required": string (optional),
  "team_qualified": boolean (required if plan_reviewed=true),
  "qualification_notes": string (optional),
  "plan_approved": boolean
}
```

**Example Request:**

```http
POST /audits/audit/123/edit-plan-review/
Content-Type: application/x-www-form-urlencoded
X-CSRFToken: <token>

plan_reviewed=true&plan_adequate=true&team_qualified=true&plan_approved=true
```

**Success Response:**

```http
HTTP/1.1 302 Found
Location: /audits/audit/123/
```

---

### Edit Audit Summary

Update audit summary and conclusions.

**Endpoint:** `GET/POST /audits/audit/<int:audit_id>/edit-summary/`

**Method:** `GET` (display form) or `POST` (submit form)

**Permissions:** Lead Auditor or CB Admin

**URL Parameters:**

- `audit_id` (integer, required): The audit ID

**Form Fields (POST):**

```json
{
  "summary_completed": boolean,
  "audit_objectives_met": boolean (required if summary_completed=true),
  "system_effectiveness": string (optional),
  "key_findings_summary": string (required if summary_completed=true),
  "outstanding_issues": string (optional)
}
```

**Example Request:**

```http
POST /audits/audit/123/edit-summary/
Content-Type: application/x-www-form-urlencoded
X-CSRFToken: <token>

summary_completed=true&audit_objectives_met=true&key_findings_summary=All+requirements+met
```

**Success Response:**

```http
HTTP/1.1 302 Found
Location: /audits/audit/123/
```

---

## Recommendation & Decision Endpoints

### Create/Edit Recommendation

Lead Auditor creates or updates certification recommendation.

**Endpoint:** `GET/POST /audits/audit/<int:audit_id>/recommendation/`

**Method:** `GET` (display form) or `POST` (submit form)

**Permissions:** Lead Auditor (assigned to audit) only

**URL Parameters:**

- `audit_id` (integer, required): The audit ID

**Form Fields (POST):**

```json
{
  "recommendation": string,  // "certify" | "certify_conditions" | "deny"
  "justification": string (required),
  "stage_2_date": date (required for Stage 1 audits),
  "conditions": string (required if recommendation="certify_conditions")
}
```

**Example Request:**

```http
POST /audits/audit/123/recommendation/
Content-Type: application/x-www-form-urlencoded
X-CSRFToken: <token>

recommendation=certify&justification=All+requirements+met.+No+major+NCs.
```

**Success Response:**

```http
HTTP/1.1 302 Found
Location: /audits/audit/123/

Set-Cookie: messages=Recommendation+saved+successfully
```

**Error Response (Permission Denied):**

```http
HTTP/1.1 403 Forbidden
Content-Type: text/html

<!-- Error page: Only lead auditor can create recommendations -->
```

**Error Response (Validation):**

```http
HTTP/1.1 200 OK
Content-Type: text/html

<!-- Form with validation errors -->
```

---

### Make Certification Decision

CB Admin makes final certification decision.

**Endpoint:** `GET/POST /audits/audit/<int:audit_id>/decision/`

**Method:** `GET` (display form) or `POST` (submit form)

**Permissions:** CB Admin only

**URL Parameters:**

- `audit_id` (integer, required): The audit ID

**Prerequisites:**

- Audit must be in `submitted_to_cb` status
- Lead Auditor recommendation must exist

**Form Fields (POST):**

```json
{
  "decision": string,  // "certify" | "certify_conditions" | "deny"
  "decision_date": date (required),
  "certificate_number": string (required if decision="certify" or "certify_conditions"),
  "validity_period_years": integer (required if certifying),
  "special_conditions": string (optional),
  "internal_notes": string (optional)
}
```

**Example Request:**

```http
POST /audits/audit/123/decision/
Content-Type: application/x-www-form-urlencoded
X-CSRFToken: <token>

decision=certify&decision_date=2025-11-20&certificate_number=CERT-2025-123&validity_period_years=3
```

**Success Response:**

```http
HTTP/1.1 302 Found
Location: /audits/audit/123/

Set-Cookie: messages=Decision+saved+successfully.+Audit+status+updated+to+decided.
```

**Error Response (No Recommendation):**

```http
HTTP/1.1 403 Forbidden
Content-Type: text/html

<!-- Error page: Recommendation required before decision -->
```

**Error Response (Wrong Status):**

```http
HTTP/1.1 403 Forbidden
Content-Type: text/html

<!-- Error page: Audit must be in submitted_to_cb status -->
```

---

## File Management Endpoints

### Upload Evidence File

Upload evidence file for an audit.

**Endpoint:** `GET/POST /audits/audit/<int:audit_id>/upload-file/`

**Method:** `GET` (display form) or `POST` (submit file)

**Permissions:** Auditor, Lead Auditor, or CB Admin

**URL Parameters:**

- `audit_id` (integer, required): The audit ID

**Form Fields (POST - multipart/form-data):**

```json
{
  "file": file (required),
  "description": string (required),
  "related_nonconformity": integer (optional, NC ID)
}
```

**File Validation:**

- **Maximum Size:** 10 MB
- **Allowed Types:**
  - PDF (`.pdf`)
  - Word (`.doc`, `.docx`)
  - Excel (`.xls`, `.xlsx`)
  - Images (`.jpg`, `.jpeg`, `.png`, `.gif`)

**Example Request:**

```http
POST /audits/audit/123/upload-file/
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary
X-CSRFToken: <token>

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="audit_evidence.pdf"
Content-Type: application/pdf

<binary file data>
------WebKitFormBoundary
Content-Disposition: form-data; name="description"

Quality manual review evidence
------WebKitFormBoundary
Content-Disposition: form-data; name="related_nonconformity"

45
------WebKitFormBoundary--
```

**Success Response:**

```http
HTTP/1.1 302 Found
Location: /audits/audit/123/

Set-Cookie: messages=File+uploaded+successfully
```

**Error Response (File Too Large):**

```http
HTTP/1.1 200 OK
Content-Type: text/html

<!-- Form with error: File size exceeds 10MB limit -->
```

**Error Response (Invalid Type):**

```http
HTTP/1.1 200 OK
Content-Type: text/html

<!-- Form with error: File type not allowed -->
```

---

### Download Evidence File

Download an evidence file.

**Endpoint:** `GET /audits/file/<int:file_id>/download/`

**Method:** `GET`

**Permissions:** Auditor, Lead Auditor, or CB Admin

**URL Parameters:**

- `file_id` (integer, required): The file ID

**Example Request:**

```http
GET /audits/file/456/download/
Cookie: sessionid=<token>
```

**Success Response:**

```http
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename="audit_evidence.pdf"
Content-Length: 1234567

<binary file data>
```

**Error Response (Not Found):**

```http
HTTP/1.1 404 Not Found
Content-Type: text/html

<!-- 404 page: File not found -->
```

**Error Response (Permission Denied):**

```http
HTTP/1.1 403 Forbidden
Content-Type: text/html

<!-- 403 page: You do not have permission to download this file -->
```

---

### Delete Evidence File

Delete an evidence file (with confirmation).

**Endpoint:** `GET/POST /audits/file/<int:file_id>/delete/`

**Method:** `GET` (show confirmation) or `POST` (confirm deletion)

**Permissions:** File uploader or CB Admin

**URL Parameters:**

- `file_id` (integer, required): The file ID

**Example Request (Show Confirmation):**

```http
GET /audits/file/456/delete/
Cookie: sessionid=<token>
```

**Example Request (Confirm Deletion):**

```http
POST /audits/file/456/delete/
Content-Type: application/x-www-form-urlencoded
X-CSRFToken: <token>

confirm=yes
```

**Success Response:**

```http
HTTP/1.1 302 Found
Location: /audits/audit/123/

Set-Cookie: messages=File+deleted+successfully
```

**Error Response (Permission Denied):**

```http
HTTP/1.1 403 Forbidden
Content-Type: text/html

<!-- 403 page: Only uploader or CB Admin can delete files -->
```

---

## Status Transition Endpoints

### Transition Audit Status

Change audit status (workflow transition).

**Endpoint:** `POST /audits/audit/<int:audit_id>/transition-status/`

**Method:** `POST`

**Permissions:** Role-dependent (see workflow rules)

**URL Parameters:**

- `audit_id` (integer, required): The audit ID

**Form Fields (POST):**

```json
{
  "next_status": string,  // "client_review" | "submitted_to_cb" | "decided"
  "notes": string (optional)
}
```

**Workflow Rules:**

| From Status | To Status | Required Role | Validation |
|-------------|-----------|---------------|------------|
| `draft` | `client_review` | Lead Auditor | Documentation complete |
| `client_review` | `submitted_to_cb` | Lead Auditor or CB Admin | All major NCs responded |
| `submitted_to_cb` | `decided` | CB Admin | Recommendation exists |

**Example Request:**

```http
POST /audits/audit/123/transition-status/
Content-Type: application/x-www-form-urlencoded
X-CSRFToken: <token>

next_status=client_review&notes=Audit+ready+for+client+review
```

**Success Response:**

```http
HTTP/1.1 302 Found
Location: /audits/audit/123/

Set-Cookie: messages=Audit+status+changed+to+client_review
```

**Error Response (Permission Denied):**

```http
HTTP/1.1 302 Found
Location: /audits/audit/123/

Set-Cookie: messages=You+do+not+have+permission+to+perform+this+transition
```

**Error Response (Validation Failed):**

```http
HTTP/1.1 302 Found
Location: /audits/audit/123/

Set-Cookie: messages=Major+nonconformity+(Clause+7.5)+has+not+been+responded+to
```

**Error Response (Invalid Transition):**

```http
HTTP/1.1 302 Found
Location: /audits/audit/123/

Set-Cookie: messages=Invalid+transition+from+'draft'+to+'decided'
```

---

## Response Codes

### HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| `200 OK` | Success | GET requests, form display with errors |
| `302 Found` | Redirect | Successful POST, redirects to audit detail |
| `403 Forbidden` | Permission Denied | User lacks required permissions |
| `404 Not Found` | Not Found | Audit or file doesn't exist |
| `500 Internal Server Error` | Server Error | Unexpected server error |

### Django Messages Framework

Success and error messages are stored in Django's messages framework and displayed after redirect.

**Message Levels:**

- `success`: Green banner (successful operations)
- `error`: Red banner (validation errors, permission denied)
- `warning`: Yellow banner (warnings)
- `info`: Blue banner (informational)

**Example HTML Template:**

```html
{% if messages %}
  {% for message in messages %}
    <div class="alert alert-{{ message.tags }}">
      {{ message }}
    </div>
  {% endfor %}
{% endif %}
```

---

## Error Handling

### Validation Errors

Validation errors are displayed in the form with field-specific messages.

**Example Response:**

```html
<form method="post">
  <div class="field-group">
    <label>Organization Changes Details</label>
    <textarea name="org_changes_details"></textarea>
    <span class="error">This field is required when organization changes exist.</span>
  </div>
</form>
```

### Permission Errors

**403 Forbidden** page with explanatory message:

- "Only lead auditor can create recommendations"
- "Only CB Admin can make decisions"
- "You do not have permission to upload files"

### Not Found Errors

**404 Not Found** page when:

- Audit doesn't exist
- File doesn't exist
- User doesn't have access to view audit

### Workflow Validation Errors

Displayed as Django messages after redirect:

- "Invalid transition from 'draft' to 'decided'"
- "Major nonconformity (Clause 7.5) has not been responded to"
- "You do not have permission to perform this transition"

---

## Testing Endpoints

### Using cURL

**Login:**

```bash
curl -c cookies.txt -X POST http://127.0.0.1:8000/accounts/login/ \
  -d "username=testuser&password=testpass" \
  -d "csrfmiddlewaretoken=<token>"
```

**Upload File:**

```bash
curl -b cookies.txt -X POST http://127.0.0.1:8000/audits/audit/123/upload-file/ \
  -H "X-CSRFToken: <token>" \
  -F "file=@/path/to/file.pdf" \
  -F "description=Test evidence" \
  -F "csrfmiddlewaretoken=<token>"
```

**Transition Status:**

```bash
curl -b cookies.txt -X POST http://127.0.0.1:8000/audits/audit/123/transition-status/ \
  -H "X-CSRFToken: <token>" \
  -d "next_status=client_review" \
  -d "csrfmiddlewaretoken=<token>"
```

### Using Postman

1. **Authentication:**
   - POST to `/accounts/login/`
   - Save cookies automatically
   - Extract CSRF token from cookies

2. **Subsequent Requests:**
   - Include saved cookies
   - Add `X-CSRFToken` header
   - Set appropriate `Content-Type`

---

## Related Documentation

- **User Guide:** See `user-guides/AUDIT_WORKFLOW_GUIDE.md`
- **Workflow Diagrams:** See `user-guides/WORKFLOW_DIAGRAMS.md`
- **Architecture:** See `ARCHITECTURE.md`
- **Models:** See `MODELS.md`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-20 | Initial API reference for Priority 2 endpoints |

---

*This API reference documents the Priority 2 implementation as of November 2025. These are web endpoints for HTML forms, not REST API endpoints.*
