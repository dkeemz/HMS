# Phase 1: Foundation & Authentication — Context

## Decisions Made

### Area 1: MFA & Login Flow

- **Primary MFA:** Push notification
- **MFA Fallback:** TOTP (if push fails)
- **Login Flow:** Conditional MFA — only required on new device
- **Password Policy:** Strong (HIPAA-aligned) — 12+ chars, upper/lower/number/special, 90-day rotation, no reuse of last 12
- **Account Lockout:** 5 failed attempts → 30-minute lockout, admin can unlock
- **Password Reset:** Both self-service (email link, 15-min expiry) + admin-assisted
- **Login Notifications:** All security events (new device, failed attempts, MFA changes)

### Area 2: Session & Audit Config

- **Session Timeout:** 15 minutes (HIPAA strict)
- **Session Refresh:** Silent refresh before expiry (no re-login during active use)
- **Token Expiry:** Access token 15 min, Refresh token 8 hours
- **Token Storage:** HttpOnly, Secure, SameSite=Strict cookies
- **Multi-Device:** Max 3 concurrent sessions; role-based limits (doctors: 5 sessions, staff: 3)
- **Logout Behavior:** Full logout — immediate token invalidation, clear all device tokens, redirect to login
- **Password Change:** Invalidate all sessions across all devices

- **Audit Fields:** Full 6-field capture — Who, What, When, Where (IP/device), Why (reason), Patient affected, Action result
- **Audit Storage:** Separate audit service (e.g., Elasticsearch)
- **Audit Integrity:** Hash chain — each log entry includes hash of previous entry
- **Audit Access:** Admin dashboard with search, filter, export
- **Audit Alerting:** Pattern-based alerts (multiple failed logins, off-hours access, bulk data exports)
- **Log Retention:** 6 years (HIPAA minimum)

### Area 3: RBAC Role Design

- **Role Count:** 15 roles total
  - Super Admin, Admin, Dept Head, Doctor, Nurse, Pharmacist, Lab Tech, Radiologist, Receptionist, Billing, Compliance Officer, System Auditor, Chief Medical Director, Medical Director, Minister of Health
- **Role Hierarchy:** Hierarchical inheritance (roles inherit permissions from parent roles)
- **Permission Granularity:** Feature-level (e.g., "Patient Records: View Vitals", "Patient Records: Edit Notes")
- **Custom Permissions:** Role + custom overrides — admin can grant/revoke individual permissions beyond role
- **Custom Roles:** Admin can create custom roles with custom permission sets
- **Department Roles:** Assigned by department admin and admin
- **Temporary Role Elevation:** Supported — time-limited, audited (e.g., covering for absent colleague)
- **Doctor Access Scope:** Department-scoped — doctors see all patients in their department
- **Role Assignment:** Admin requests → Department Head approves
- **Permission Changes:** Notify user + compliance officer
- **Audit Trail:** Full audit trail for all role/permission changes (who, what, when, why)

### Area 4: Break-Glass Workflow

- **Trigger:** Admin-granted access (doctor requests, admin approves)
- **Access Duration:** 1 hour (HIPAA strict)
- **Notifications:** Admin + compliance officer + department head (immediate)
- **Post-Access Review:** 24-hour compliance review (every break-glass access)
- **Audit Trail:** Full — who requested, who approved, reason, time accessed, data viewed, review outcome
- **Abuse Prevention:** Frequency alerts (if same user requests >3 times/week)
