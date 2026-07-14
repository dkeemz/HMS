# Module Overview

All 10 HMS modules with features, workflows, and role access.

## Module Map

```
┌─────────────────────────────────────────────────────────────┐
│                    HMS MODULES                               │
├─────────────┬─────────────┬─────────────┬──────────────────┤
│   Auth &    │  Patient    │  Scheduling │   EHR            │
│   Security  │  Management │  Core       │   Clinical       │
├─────────────┼─────────────┼─────────────┼──────────────────┤
│   Billing   │  Attendance │  Servicom   │   Analytics      │
│   Revenue   │  & Shifts   │  & Feedback │   & Reports      │
└─────────────┴─────────────┴─────────────┴──────────────────┘
```

## 1. Auth & Security Module

**Purpose:** Authentication, authorization, MFA, session management, audit logging

### Features
- Conditional MFA (push notification primary, TOTP fallback)
- Password policy (HIPAA-aligned, 12+ chars, 90-day rotation)
- Session management (15-min timeout, 3 concurrent sessions)
- RBAC with 15 predefined roles + custom roles
- Break-glass emergency access
- Full audit logging (6-field capture)
- Account lockout (5 failed attempts → 30-min lock)

### Role Access
| Role | Can Access |
|------|-----------|
| Super Admin | Full access to all auth settings |
| Admin | User management, role assignment, audit logs |
| Compliance Officer | Audit logs, security reports |
| All others | Own profile only |

### Key Workflows
1. **Login:** Username/password → MFA → Dashboard
2. **Break-Glass:** Request access → Admin grants → 1-hour window → Compliance review
3. **Password Reset:** Self-service (email) or admin-assisted

---

## 2. Patient Management Module

**Purpose:** Patient registration, demographics, medical history, records

### Features
- Patient registration with unique Patient ID
- Demographics (name, DOB, gender, contact, address)
- Emergency contacts
- Insurance information
- Medical history timeline
- Allergy tracking
- Global patient search (name, ID, phone, email)

### Role Access
| Role | Can Access |
|------|-----------|
| Receptionist | Registration, search, demographics |
| Doctor | Full patient record, medical history |
| Nurse | Vitals, demographics, medical history |
| Billing | Insurance, billing history |
| Patient (Portal) | Own record only |

### Key Workflows
1. **Registration:** Search or create → Fill demographics → Add insurance → Save
2. **Search:** Global search → Filter → Select patient → View record
3. **Update:** Open record → Edit fields → Save (audit logged)

---

## 3. Doctor & Department Module

**Purpose:** Provider directories, department structure, specialties

### Features
- Doctor profiles (specialty, qualifications, schedule)
- Department management (departments, units, wards)
- Room and bed management
- Provider availability calendar
- Department-level reporting

### Role Access
| Role | Can Access |
|------|-----------|
| Admin | Full CRUD on doctors and departments |
| Dept Head | View/manage own department |
| Doctor | View own profile, department info |
| All staff | Provider directory (read-only) |

---

## 4. Scheduling Core Module

**Purpose:** Appointment scheduling, shift management, calendar

### Features
- Appointment booking (patient, provider, time, type)
- Calendar views (daily, weekly, monthly)
- Conflict detection (no double-booking)
- Appointment status tracking (pending, confirmed, completed, cancelled)
- Automated notifications (SMS/email)
- Shift scheduling for staff
- Recurring appointments

### Role Access
| Role | Can Access |
|------|-----------|
| Receptionist | Book, reschedule, cancel appointments |
| Doctor | View own schedule, mark complete |
| Nurse | View assigned appointments |
| Patient (Portal) | Book/view/cancel own appointments |

### Key Workflows
1. **Book Appointment:** Select patient → Select provider → Choose slot → Confirm
2. **Reschedule:** Open appointment → Select new slot → Confirm → Notify
3. **Cancel:** Open appointment → Cancel → Reason → Notify

---

## 5. EHR Clinical Module

**Purpose:** Clinical documentation, encounters, vitals, notes, orders

### Features
- Encounter management (start, document, close)
- Vital signs recording (BP, HR, temp, RR, weight, height, BMI)
- SOAP clinical notes (Subjective, Objective, Assessment, Plan)
- Specialty-specific templates
- Auto-save (every 30 seconds)
- Problem list management (ICD-10)
- Medication prescriptions
- Drug interaction/allergy checking
- Lab test ordering
- Radiology ordering
- Referral management

### Role Access
| Role | Can Access |
|------|-----------|
| Doctor | Full clinical access |
| Nurse | Vitals, clinical notes (limited) |
| Lab Tech | Lab orders, results |
| Radiologist | Imaging orders, results |
| Pharmacist | Prescriptions, dispensing |

### Key Workflows
1. **Start Encounter:** Select patient → Start Encounter → Record vitals → Write notes → Orders
2. **Prescribe:** Search medication → Dosage/frequency → Check interactions → Send to pharmacy
3. **Order Labs:** Select tests → Add clinical notes → Submit → Results delivered

---

## 6. Billing Foundation Module

**Purpose:** Charge capture, invoicing, payments, insurance claims

### Features
- Automatic charge capture from clinical documentation
- Invoice generation
- Payment processing (cash, card, bank transfer, insurance)
- Receipt generation
- Insurance claim submission
- Claim status tracking
- Tariff/service price management
- Payment plans
- Outstanding balance tracking

### Role Access
| Role | Can Access |
|------|-----------|
| Billing Staff | Full billing operations |
| Doctor | View patient billing (read-only) |
| Admin | Reports, tariff management |
| Patient (Portal) | Own billing, make payments |

### Key Workflows
1. **Generate Invoice:** Review charges → Add items → Calculate total → Generate
2. **Process Payment:** Select invoice → Choose method → Process → Receipt
3. **Insurance Claim:** Create claim → Submit → Track → Resubmit if denied

---

## 7. Staff Attendance Module

**Purpose:** Clock-in/out, shift tracking, overtime, leave, shift swaps

### Features
- Web clock-in with IP/location tracking
- Schedule-based shift tracking
- Automatic overtime calculation
- Break auto-deduction (30 min for >6hr shifts)
- Leave request/approval workflow
- Shift swap request/approval
- Role-based history visibility
- Auto-alerts for managers (late, absent, overtime)

### Role Access
| Role | Can Access |
|------|-----------|
| All Staff | Clock in/out, own schedule, leave requests |
| Manager | Team attendance dashboard, approve leave/swaps |
| Admin | All attendance records, reports |

### Key Workflows
1. **Clock In:** Navigate to Attendance → Clock In → Confirm
2. **Request Leave:** Select type → Dates → Reason → Submit → Await approval
3. **Shift Swap:** Select shift → Choose colleague → Submit → Both managers approve

---

## 8. Servicom (Customer Service) Module

**Purpose:** Complaints, feedback, surveys, SLA management

### Features
- Multi-channel intake (web, SMS, email, phone)
- Complaint lifecycle tracking (7 statuses)
- Category management (10 predefined + custom)
- Priority levels (Low, Medium, High, Critical)
- SLA tracking with auto-escalation
- Post-visit surveys (auto-triggered)
- In-app feedback (1-5 stars + comments)
- Anonymous complaint option
- Resolution tracking
- Reporting dashboard

### Role Access
| Role | Can Access |
|------|-----------|
| All Staff/Patients | Submit complaints, provide feedback |
| Servicom Officer | Full complaint management |
| Manager | Team complaints, escalation |
| Admin | Reports, SLA config |

### Key Workflows
1. **File Complaint:** Select category → Priority → Description → Submit
2. **Track Status:** View complaints → Check status → View history
3. **Resolve:** Investigate → Document resolution → Close → Survey sent

---

## 9. Analytics & Reports Module

**Purpose:** Dashboards, operational insights, compliance reporting

### Features
- Real-time dashboards (role-specific)
- Operational reports (appointments, admissions, discharges)
- Financial reports (revenue, outstanding, claims)
- Clinical reports (patient outcomes, diagnoses)
- Compliance reports (audit logs, HIPAA)
- Staff performance reports
- Export (PDF, Excel, CSV)
- Scheduled report delivery

### Role Access
| Role | Can Access |
|------|-----------|
| Admin | All reports |
| Dept Head | Department reports |
| Doctor | Patient-level analytics |
| Compliance | Compliance reports |
| All staff | Own performance dashboard |

---

## 10. Integration Hub Module

**Purpose:** External system connections, FHIR, NHIS, SMS/email

### Features
- HAPI FHIR R4 server
- NHIS claims integration
- SMS gateway (Twilio)
- Email service (SendGrid)
- LDAP/AD user federation
- HL7v2 message support
- Bulk FHIR export
- API key management

### Status: V2+ (planned)

---

## Cross-Module Data Flow

```
Patient Registration → Scheduling → EHR → Billing
        ↓                ↓          ↓       ↓
    Audit Log        Audit Log   Audit Log  Audit Log
        ↓                ↓          ↓       ↓
    Notification     Notification  —    Receipt/Claim
```

## Module Dependencies

| Module | Depends On |
|--------|-----------|
| Auth | None (foundation) |
| Patient | Auth |
| Doctor/Dept | Auth, Patient |
| Scheduling | Auth, Patient, Doctor |
| EHR | Auth, Patient, Doctor, Scheduling |
| Billing | Auth, Patient, EHR |
| Attendance | Auth, Doctor/Dept |
| Servicom | Auth, Patient (optional) |
| Analytics | All modules |
| Integration | Auth, all clinical modules |
