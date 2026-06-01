# Security Policy — Cedrus Next.js GRC Platform

Cedrus takes security and trust very seriously. As a GRC (Governance, Risk, Compliance) platform managing ISO 17021 external audit management, the confidentiality, integrity, and availability of our users' systems and data are paramount.

## Supported Versions

We actively maintain and support the current major version of the Cedrus platform.

| Version | Supported          | Notes |
| ------- | ------------------ | ----- |
| 1.x.x (Next.js 15) | :white_check_mark: | Active Development & Security Updates |
| < 1.0.x  | :x:                | Deprecated / Draft Baselines |

## Multi-Tenant Security Scope
Cedrus is designed with strict multi-organization and multi-role tenancy boundaries. Key focus security areas include:
- Cross-tenant data isolation: Ensure `cbOrgId` and `clientOrgId` scope limitations are enforced on every database query.
- Server Action authentication and role validation: Every mutation action must run user verification and redirect on authorization failure.
- NextAuth v5 session integrity.

## Reporting a Vulnerability

If you discover a security vulnerability, please do NOT open a public GitHub issue. Instead, report it responsibly through our secure disclosure channel:

1. **Email:** Send a detailed report to [security@cedrus.example](mailto:security@cedrus.example).
2. **Encrypted Communication:** (Optional) Encrypt your email using our PGP key (available upon request).
3. **What to Include:**
   - A descriptive title indicating the nature of the vulnerability.
   - Steps to reproduce, including any proof of concept (PoC) scripts or requests.
   - The potential impact (e.g., cross-tenant exposure, privilege escalation).
   - Your name and how you would like to be credited.

### Our Response Pipeline
- **Acknowledgement:** We will acknowledge receipt of your vulnerability report within 24 hours.
- **Triage & Evaluation:** Our security team will investigate and confirm the issue within 3 business days.
- **Remediation:** If validated, we aim to provide a security patch or workaround within 7 to 14 days, depending on severity.
- **Disclosure:** We follow coordinated vulnerability disclosure practices. We will publish an advisory once a patch is successfully verified and rolled out.

Thank you for helping keep Cedrus secure!
