# Roadmap: Health Management System (HMS)

## Overview

This roadmap delivers a unified Hospital Health Management System through 8 phases, building from a secure foundation with HIPAA-compliant authentication, through patient/doctor management, clinical EHR documentation, appointment scheduling, and finally revenue cycle billing. Each phase delivers an end-to-end user capability using the MVP vertical slice approach. The system is built for a single hospital location first, with hybrid deployment (on-premise + cloud), and compliance baked into the architecture from day one — not bolted on later.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation & Authentication** - HIPAA-compliant auth, RBAC, and audit logging
- [ ] **Phase 2: Patient Management** - Patient registration, MRN, demographics, and medical history
- [ ] **Phase 3: Doctor & Department Management** - Doctor profiles, specialties, department hierarchy, availability
- [ ] **Phase 4: Scheduling Core** - Appointment booking, availability, calendar views, conflict prevention
- [ ] **Phase 5: EHR Documentation** - Clinical notes (SOAP), vitals, diagnoses, lab results, document uploads
- [ ] **Phase 6: EHR Clinical Lists** - Active problem list, medication list, allergies with severity tracking
- [ ] **Phase 7: Billing Foundation** - Invoice generation, payment recording, price master, receipts
- [ ] **Phase 8: Billing & Revenue** - Insurance claims, outstanding balance tracking, financial reports

## Phase Details

### Phase 1: Foundation & Authentication
**Goal**: Users can securely access the system with HIPAA-compliant authentication, role-based permissions, and complete audit trails for all patient data access
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, AUTH-06, AUTH-07
**Success Criteria** (what must be TRUE):
  1. User can create an account with a unique ID and log in using email/password with MFA
  2. Each user role (doctor, nurse, admin, patient) sees only the screens and data permitted for their role
  3. Inactive sessions are automatically terminated after the configured timeout period
  4. Every access to a patient record is logged with who accessed it, what was viewed, when, and the clinical reason
  5. Emergency break-glass access overrides role restrictions with a time-bound window and full audit trail
**Plans**: 7 plans

Plans:
- [ ] 01-01: Project scaffolding — Next.js 15 frontend, NestJS 11 backend, PostgreSQL 17, TypeScript, monorepo structure
- [ ] 01-02: Database infrastructure — Schema-per-module strategy, migrations, connection pooling, initial compliance tables
- [ ] 01-03: Keycloak 26.x integration — Self-hosted IdP, user registration, email/password login, MFA enrollment
- [ ] 01-04: Role-based access control — Doctor, nurse, admin, patient roles with permission matrices and middleware enforcement
- [ ] 01-05: Session management — Auto-logout for inactive sessions, global logout from any page
- [ ] 01-06: Audit logging pipeline — Append-only, tamper-evident audit trail for all patient record access (who, what, when, why)
- [ ] 01-07: Break-glass emergency access — Time-bound override with full audit trail and admin notification

### Phase 2: Patient Management
**Goal**: Front desk and clinical staff can register patients, manage demographics, track medical history, and retrieve any patient in under 2 seconds
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: PAT-01, PAT-02, PAT-03, PAT-04, PAT-05, PAT-06
**Success Criteria** (what must be TRUE):
  1. Patient can be registered with full demographics (name, DOB, gender, contact, address, emergency contacts) and receives a unique MRN
  2. Patient medical history (allergies, conditions, surgeries, family history) is recorded and viewable in the patient chart
  3. Patient insurance information (policy, provider, coverage) can be added and managed per visit
  4. Front desk can search patients by name, MRN, phone, or DOB with results returning in under 2 seconds
  5. Patient visit history is tracked chronologically showing date, department, doctor, reason, and outcome
**Plans**: 6 plans

Plans:
- [ ] 02-01: Patient registration service — Demographics intake, MRN auto-generation, validation rules
- [ ] 02-02: Patient profile UI — Registration forms, profile views, demographic editing
- [ ] 02-03: Medical history recording — Allergies, conditions, surgeries, family history entry and display
- [ ] 02-04: Insurance management — Policy entry, provider lookup, coverage tracking per patient
- [ ] 02-05: Patient search — Multi-field search (name, MRN, phone, DOB) with <2s response, indexed queries
- [ ] 02-06: Visit history tracking — Chronological visit log with department, doctor, reason, outcome

### Phase 3: Doctor & Department Management
**Goal**: Admin can set up the hospital's organizational structure and doctors can manage their profiles and availability status
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: DOC-01, DOC-02, DOC-03, DOC-04
**Success Criteria** (what must be TRUE):
  1. Doctor profiles are creatable with name, specialty, qualifications, department assignment, and consultation hours
  2. Department structure is defined hierarchically (e.g., Cardiology > Interventional Cardiology)
  3. Doctor specialties and qualifications are tracked and visible in the doctor directory
  4. Doctor availability status can be set to available, on-leave, in-surgery, or on-duty in real time
**Plans**: 4 plans

Plans:
- [ ] 03-01: Department service — Hierarchical department CRUD, parent-child relationships, department directory
- [ ] 03-02: Doctor profile service — Profile creation, specialty/qualification tracking, department assignment
- [ ] 03-03: Doctor directory UI — Doctor listing, search by specialty/department, profile views
- [ ] 03-04: Availability status management — Real-time status toggle (available, on-leave, in-surgery, on-duty)

### Phase 4: Scheduling Core
**Goal**: Patients and front desk can book, reschedule, or cancel appointments with real-time availability visibility and automatic conflict prevention
**Mode:** mvp
**Depends on**: Phase 2, Phase 3
**Requirements**: SCH-01, SCH-02, SCH-03, SCH-04, SCH-05, SCH-06, SCH-07
**Success Criteria** (what must be TRUE):
  1. Patient can book an appointment online or via front desk with real-time slot availability shown
  2. Appointment types are supported with correct durations (consultation 15min, follow-up 10min, procedure 30min, emergency walk-in)
  3. Calendar views (day/week/month) are available for doctors, departments, and admin with real-time slot display
  4. System prevents double-booking of the same doctor or room for overlapping time slots
  5. Walk-in/queue management with priority triage works for ER and OPD patients
  6. Patient can reschedule or cancel an existing appointment
**Plans**: 7 plans

Plans:
- [ ] 04-01: Scheduling service — Appointment CRUD, time slot generation from doctor availability rules
- [ ] 04-02: Availability calendar service — Real-time available slots computed from doctor profiles and existing bookings
- [ ] 04-03: Appointment type management — Configurable types with durations (consultation, follow-up, procedure, walk-in)
- [ ] 04-04: Calendar views UI — Day/week/month views for doctors, departments, and admin with drag-to-book
- [ ] 04-05: Conflict prevention — Double-booking detection for doctor and room with validation and user-friendly error
- [ ] 04-06: Walk-in & queue management — ER/OPD queue with priority triage, queue position tracking, estimated wait
- [ ] 04-07: Reschedule & cancel flows — Patient-initiated reschedule/cancel with policy enforcement and confirmation

### Phase 5: EHR Documentation
**Goal**: Doctors can document patient encounters using SOAP notes, record vitals, attach diagnoses with ICD codes, view lab results, and upload clinical documents — all within a unified patient chart
**Mode:** mvp
**Depends on**: Phase 2, Phase 3
**Requirements**: EHR-01, EHR-02, EHR-03, EHR-04, EHR-05, EHR-06
**Success Criteria** (what must be TRUE):
  1. Doctor can create SOAP notes (Subjective, Objective, Assessment, Plan) linked to a patient encounter
  2. Doctor can write electronic prescriptions with drug interaction checking against patient medications
  3. Diagnoses can be recorded with ICD-10/ICD-11 code selection and search
  4. Lab results can be viewed within the patient chart with automatic normal/abnormal flagging
  5. Vitals (BP, temperature, heart rate, weight, height, SpO2) can be recorded and displayed as a trend over time
  6. Clinical documents (scans, images, reports) can be uploaded and attached to the patient chart
**Plans**: 6 plans

Plans:
- [ ] 05-01: Clinical documentation service — SOAP note CRUD, encounter linking, note versioning
- [ ] 05-02: Prescription service (eRx) — Electronic prescriptions with drug interaction checking, dose validation
- [ ] 05-03: Diagnosis service — ICD-10/ICD-11 code lookup, diagnosis recording per encounter
- [ ] 05-04: Lab results viewer — Lab result display within patient chart, normal/abnormal flagging, result history
- [ ] 05-05: Vitals recording & trending — Vitals entry form, trend charts over time, vital sign ranges
- [ ] 05-06: Clinical document upload — File upload to patient chart (scans, images, reports), document viewer

### Phase 6: EHR Clinical Lists
**Goal**: Doctors maintain accurate per-patient clinical lists (problems, medications, allergies) that are always current and visible across encounters
**Mode:** mvp
**Depends on**: Phase 5
**Requirements**: EHR-07, EHR-08, EHR-09
**Success Criteria** (what must be TRUE):
  1. Active problem list is maintained per patient with add/resolve/close status tracking
  2. Current medication list is maintained per patient with dosage, frequency, and prescribing doctor
  3. Known allergies with severity levels (mild, moderate, severe, life-threatening) are tracked per patient and flagged during prescribing
**Plans**: 3 plans

Plans:
- [ ] 06-01: Active problem list — Problem tracking per patient (add, resolve, close), chronological history
- [ ] 06-02: Medication list — Current medications with dosage, frequency, prescriber, status tracking
- [ ] 06-03: Allergy tracking — Allergies with severity levels, cross-reference with prescribing and drug interaction checking

### Phase 7: Billing Foundation
**Goal**: Charges are auto-generated from services rendered, payments are recorded across multiple methods, and receipts are produced — giving the revenue cycle its foundation
**Mode:** mvp
**Depends on**: Phase 4, Phase 5
**Requirements**: BIL-01, BIL-02, BIL-04, BIL-05
**Success Criteria** (what must be TRUE):
  1. Invoices are auto-generated from services rendered (consultations, lab tests, procedures, medications) with line-item detail
  2. Payments can be recorded in cash, card, bank transfer, or insurance with proper allocation to invoices
  3. Price master is configurable per service, per department, with effective dates for price changes
  4. Payment receipts are generated automatically and can be printed or emailed
**Plans**: 4 plans

Plans:
- [ ] 07-01: Invoice generation service — Auto-invoice from clinical encounters, line-item creation, invoice CRUD
- [ ] 07-02: Payment recording — Multi-method payment recording (cash, card, transfer, insurance), allocation to invoices
- [ ] 07-03: Price master — Service pricing per department with effective dates, price versioning
- [ ] 07-04: Receipt generation — Auto-generated receipts, PDF rendering, print/email delivery

### Phase 8: Billing & Revenue
**Goal**: Insurance claims are processed with proper coding, outstanding balances are tracked with aging visibility, and financial reports provide revenue visibility across departments
**Mode:** mvp
**Depends on**: Phase 7
**Requirements**: BIL-03, BIL-06, BIL-07
**Success Criteria** (what must be TRUE):
  1. Insurance claims can be generated with CPT/ICD code mapping and submitted for processing
  2. Outstanding balance tracking shows per-patient and per-invoice aging (current, 30, 60, 90+ days)
  3. Basic financial reports are available: daily collections, outstanding payments, department-wise revenue breakdown
**Plans**: 3 plans

Plans:
- [ ] 08-01: Insurance claims service — CPT/ICD code mapping, claim generation, claim status tracking
- [ ] 08-02: Outstanding balance & aging — Per-patient and per-invoice aging buckets, balance dashboard
- [ ] 08-03: Financial reports — Daily collections, outstanding payments, department-wise revenue reports

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Authentication | 0/7 | Not started | - |
| 2. Patient Management | 0/6 | Not started | - |
| 3. Doctor & Department Management | 0/4 | Not started | - |
| 4. Scheduling Core | 0/7 | Not started | - |
| 5. EHR Documentation | 0/6 | Not started | - |
| 6. EHR Clinical Lists | 0/3 | Not started | - |
| 7. Billing Foundation | 0/4 | Not started | - |
| 8. Billing & Revenue | 0/3 | Not started | - |
