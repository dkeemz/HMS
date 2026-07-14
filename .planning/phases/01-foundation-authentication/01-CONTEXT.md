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

### Area 5: UI/UX Design

- **Design System:** Material UI (MUI)
- **Navigation:** Collapsible sidebar with icons + labels
- **Color Scheme:** Medical blue primary (#1565C0), clean whites/grays
- **Theme:** Light mode default + dark mode toggle (MUI native)
- **Dashboard:** Card grid layout (KPI cards, charts, recent activity)
- **Mobile:** Responsive web (3 breakpoints: mobile <768px, tablet 768-1024px, desktop >1024px)
- **Forms:** Multi-step forms with progress indicators
- **Data Display:** MUI DataGrid with sort, filter, pagination
- **Notifications:** Toast notifications for actions + bell icon for alerts
- **Loading States:** Skeleton loaders
- **Error States:** Inline field errors + toast for server errors
- **Empty States:** Illustration + CTA button
- **Typography:** Roboto font family
- **Icons:** MUI Icons (Material Design)
- **Search:** Global search bar + module-specific search
- **Breadcrumbs:** Displayed for nested pages
- **Confirmations:** Modal dialog for destructive actions
- **Charts:** Recharts library
- **Date Pickers:** MUI Date Pickers (dayjs)
- **Tabs:** MUI Tabs for switching views
- **Page Transitions:** Animated (fade/slide)
- **Table Mobile:** Horizontal scroll
- **Sidebar Mobile:** Slide-in drawer from left
- **Accessibility:** WCAG AAA, full keyboard navigation, full ARIA support, 7:1 contrast ratio
- **Print Styles:** Print-optimized styles for reports, prescriptions, invoices
- **Localization:** English + Nigerian languages (Hausa, Yoruba, Igbo) + i18n framework

### Area 6: Staff Attendance

- **Clock In/Out:** Web-based with IP/location verification
- **Shift Tracking:** Schedule-based (clock-in validates against schedule)
- **Overtime:** Auto-calculate based on hours worked beyond standard shift
- **Breaks:** Auto-deduct based on shift length
- **Reports:** Daily, weekly, monthly summaries with export
- **Leave Management:** Staff request leave, manager approve (annual, sick, etc. with balances)
- **Attendance Alerts:** Auto-alert manager for late, absent, early departure
- **Shift Swaps:** Staff request swap, manager approve (both staff must agree)
- **History Visibility:** Role-based (staff see own, managers see department, admin sees all)

### Area 7: Servicom & Customer Feedback

- **Scope:** Full Servicom (complaints, service requests, feedback tracking, resolution workflow)
- **Channels:** Multi-channel (web form, SMS, email, phone manual entry)
- **Categories:** Predefined + admin can add custom categories later
- **Workflow:** Full (Complaint → Assigned → Investigating → Resolved → Closed)
- **SLA:** Auto-escalation for complaints not resolved within SLA (24h urgent, 72h normal)
- **Surveys:** Post-visit survey (1-5 stars + comments) via SMS/email + in-app feedback button
- **Analytics:** Trend analysis, category breakdown, sentiment scoring, department comparison
- **Anonymous:** Allow anonymous complaints
- **Notifications:** Auto-notify patient at each stage (assigned, investigating, resolved)
- **Priority:** 4 levels (Low, Medium, High, Critical) based on category and severity
- **Reporting:** Dashboard + scheduled monthly reports with export

### Area 8: Data Entities & Models

**People & Organization:**
- User, Patient, Doctor, Nurse, Staff, Department, Role, Permission

**Scheduling & Resources:**
- Appointment, Schedule, Shift, Bed, Ward, Room

**Clinical (EHR):**
- Encounter, Vitals, Diagnosis, Prescription, Lab Order, Lab Result, Allergy, Problem, Imaging, Referral, Immunization, Procedure

**Billing:**
- Invoice, Line Item, Payment, Insurance, Claim, Tariff, Payment Method, Contract, Payment Plan, Collection

**Servicom:**
- Complaint, Feedback, Survey, Resolution, SLA

**Staff Attendance:**
- Attendance Record, Shift Swap, Leave Request, Overtime

**Relationships:**
- Standard: Patient has many Appointments/Encounters/Invoices, Doctor has many Appointments/Encounters, Department has many Doctors/Patients
- Complex: Patient-Doctor assignment, Care teams, Referral chains
