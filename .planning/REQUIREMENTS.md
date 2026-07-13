# Requirements: Health Management System (HMS)

**Defined:** 2026-07-13
**Core Value:** One unified system that replaces all fragmented hospital tools — doctors must access complete patient records and manage appointments from a single place.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Authentication & Access Control

- [ ] **AUTH-01**: User can create account with unique user ID (HIPAA-compliant)
- [ ] **AUTH-02**: User can log in with email/password and MFA (push/biometric)
- [ ] **AUTH-03**: System enforces role-based access control (doctor, nurse, admin, patient)
- [ ] **AUTH-04**: System auto-logs out inactive sessions (HIPAA requirement)
- [ ] **AUTH-05**: All patient record access is logged with who, what, when, why
- [ ] **AUTH-06**: Break-glass emergency access with time-bound override and full audit trail
- [ ] **AUTH-07**: User can log out from any page

### Patient Management

- [ ] **PAT-01**: Patient can register with demographics (name, DOB, gender, contact, address, emergency contacts)
- [ ] **PAT-02**: System assigns unique Medical Record Number (MRN) on registration
- [ ] **PAT-03**: Patient can have medical history recorded (allergies, conditions, surgeries, family history)
- [ ] **PAT-04**: Patient insurance information can be added and managed (policy, provider, coverage)
- [ ] **PAT-05**: Front desk can search patients by name, MRN, phone, DOB (under 2 seconds)
- [ ] **PAT-06**: Patient visit history is tracked chronologically (date, department, doctor, reason, outcome)

### Doctor & Department Management

- [ ] **DOC-01**: Doctor profile can be created (name, specialty, qualifications, department, consultation hours)
- [ ] **DOC-02**: Department structure can be defined hierarchically (Cardiology > Interventional Cardiology)
- [ ] **DOC-03**: Doctor specialties and qualifications can be tracked
- [ ] **DOC-04**: Doctor availability status can be set (available, on-leave, in-surgery, on-duty)

### Scheduling

- [ ] **SCH-01**: Patient can book appointment (online + front-desk)
- [ ] **SCH-02**: Doctor availability calendar shows real-time available slots
- [ ] **SCH-03**: Appointment types supported (consultation 15min, follow-up 10min, procedure 30min, emergency walk-in)
- [ ] **SCH-04**: Calendar views available (day/week/month) for doctors, departments, admin
- [ ] **SCH-05**: System prevents double-booking of doctor or room
- [ ] **SCH-06**: Walk-in/queue management with priority triage for ER/OPD
- [ ] **SCH-07**: Patient can reschedule or cancel appointment

### Electronic Health Records (EHR)

- [ ] **EHR-01**: Doctor can create clinical documentation (SOAP notes — Subjective, Objective, Assessment, Plan)
- [ ] **EHR-02**: Doctor can write prescriptions electronically (eRx) with drug interaction checking
- [ ] **EHR-03**: Diagnosis can be recorded with ICD-10/ICD-11 codes
- [ ] **EHR-04**: Lab results can be viewed within patient chart with normal/abnormal flagging
- [ ] **EHR-05**: Vitals can be recorded (BP, temperature, heart rate, weight, height, SpO2)
- [ ] **EHR-06**: Clinical documents can be uploaded and attached to patient chart (scans, images, reports)
- [ ] **EHR-07**: Active problem list maintained per patient
- [ ] **EHR-08**: Current medication list maintained per patient
- [ ] **EHR-09**: Known allergies with severity levels tracked per patient

### Billing

- [ ] **BIL-01**: Invoice auto-generated from services rendered (consultations, lab tests, procedures, medications)
- [ ] **BIL-02**: Payment can be recorded (cash, card, bank transfer, insurance)
- [ ] **BIL-03**: Insurance claims can be generated with CPT/ICD codes
- [ ] **BIL-04**: Price master configurable per service, per department, with effective dates
- [ ] **BIL-05**: Payment receipts can be generated
- [ ] **BIL-06**: Outstanding balance tracking with aging reports
- [ ] **BIL-07**: Basic financial reports (daily collections, outstanding payments, department-wise revenue)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Inpatient Management (IPD)

- **IPD-01**: Bed management with real-time occupancy view by ward/room/bed
- **IPD-02**: Admission/Discharge/Transfer (ADT) workflows
- **IPD-03**: Ward/nurse station dashboard (current patients, vitals due, medications due)
- **IPD-04**: Auto-generated discharge summary from clinical notes

### Pharmacy

- **PHA-01**: Prescription dispensing workflow (verify, dispense, record)
- **PHA-02**: Drug inventory management (stock levels, expiry dates, batch numbers)
- **PHA-03**: Drug interaction checking against patient medications and allergies
- **PHA-04**: Controlled substance tracking with audit trails

### Laboratory & Diagnostics

- **LAB-01**: Lab test ordering from within EHR
- **LAB-02**: Sample tracking with barcode-based chain of custody
- **LAB-03**: Result entry with normal/abnormal flagging and validation
- **LAB-04**: Results delivery to patient chart automatically

### Notifications

- **NOT-01**: Appointment reminders via SMS/email (configurable intervals)
- **NOT-02**: Lab results ready notification to patients
- **NOT-03**: Billing alerts (payment due, payment confirmations, claim status)
- **NOT-04**: Internal task notifications (pending approvals, shift changes)

### Patient Portal

- **PRT-01**: Patient can self-schedule appointments online 24/7
- **PRT-02**: Patient can view medical records and lab results
- **PRT-03**: Patient can view and pay bills online
- **PRT-04**: Patient can message doctors through secure channel

## v3 Requirements

Deferred to future release.

### Telemedicine

- **TEL-01**: Secure video consultation between doctor and patient
- **TEL-02**: Virtual waiting room with queue management
- **TEL-03**: E-prescriptions from virtual visits

### Nurse Workflow

- **NRS-01**: Mobile bedside vitals recording
- **NRS-02**: Medication administration record (MAR) with barcode scanning
- **NRS-03**: Nursing notes documentation
- **NRS-04**: Task/worklist management (medications due, vitals due, discharges pending)

### Inventory & Supply Chain

- **INV-01**: Stock management across departments
- **INV-02**: Purchase order management
- **INV-03**: Stock alerts (min/max thresholds)
- **INV-04**: Expiry tracking with alerts

### Advanced Reporting

- **RPT-01**: Custom report builder (drag-and-drop)
- **RPT-02**: Predictive analytics (patient volume, bed demand, staffing)
- **RPT-03**: Clinical quality metrics (CMS measures, infection rates, mortality)

### AI Features

- **AI-01**: Clinical decision support (drug interactions, allergy alerts, dosing)
- **AI-02**: Voice-to-text clinical documentation
- **AI-03**: Discharge summary automation

### Multi-Location

- **ML-01**: Cross-facility appointment scheduling
- **ML-02**: Inter-hospital patient transfers
- **ML-03**: Chain-wide analytics and reporting

## v4 Requirements

Enterprise-grade features.

### Enterprise Analytics

- **ENT-01**: Data warehouse with cross-chain business intelligence
- **ENT-02**: Executive dashboards with KPI tracking

### Compliance Automation

- **CMP-01**: Automated HIPAA/PDPA/NDPA compliance reporting
- **CMP-02**: Risk assessment and audit automation

### Interoperability Hub

- **INT-01**: Full HL7/FHIR integration engine
- **INT-02**: External system marketplace

### Advanced Security

- **SEC-01**: Zero-trust architecture implementation
- **SEC-02**: Advanced threat detection and security analytics

### Patient Engagement

- **ENG-01**: Patient satisfaction surveys
- **ENG-02**: Health education content delivery
- **ENG-03**: Chronic disease management programs

### Clinical Trials

- **TRL-01**: Clinical trial management
- **TRL-02**: Research data export

### Revenue Optimization

- **REV-01**: Advanced denial management and appeals
- **REV-02**: Predictive claim scoring

### Custom Integrations

- **CST-01**: API marketplace for third-party integrations
- **CST-02**: Custom workflow builder

## Out of Scope

| Feature | Reason |
|---------|--------|
| Social media integration | PHI leakage risk, HIPAA/NDPA nightmare |
| Patient rating/scoring | Discrimination risk, ethical concerns |
| AI autonomous diagnosis | Liability and patient safety nightmare |
| Online drug sales/e-commerce | Massive regulatory burden, licensing requirements |
| Cryptocurrency payments | Regulatory uncertainty, no patient demand |
| Public-facing hospital statistics | Competitive and legal liability |
| Custom identity provider from scratch | Multi-year effort, massive liability |
| Password-only authentication | Unacceptable for healthcare, violates compliance |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Pending |
| AUTH-02 | Phase 1 | Pending |
| AUTH-03 | Phase 1 | Pending |
| AUTH-04 | Phase 1 | Pending |
| AUTH-05 | Phase 1 | Pending |
| AUTH-06 | Phase 1 | Pending |
| AUTH-07 | Phase 1 | Pending |
| PAT-01 | Phase 2 | Pending |
| PAT-02 | Phase 2 | Pending |
| PAT-03 | Phase 2 | Pending |
| PAT-04 | Phase 2 | Pending |
| PAT-05 | Phase 2 | Pending |
| PAT-06 | Phase 2 | Pending |
| DOC-01 | Phase 3 | Pending |
| DOC-02 | Phase 3 | Pending |
| DOC-03 | Phase 3 | Pending |
| DOC-04 | Phase 3 | Pending |
| SCH-01 | Phase 4 | Pending |
| SCH-02 | Phase 4 | Pending |
| SCH-03 | Phase 4 | Pending |
| SCH-04 | Phase 4 | Pending |
| SCH-05 | Phase 4 | Pending |
| SCH-06 | Phase 4 | Pending |
| SCH-07 | Phase 4 | Pending |
| EHR-01 | Phase 5 | Pending |
| EHR-02 | Phase 5 | Pending |
| EHR-03 | Phase 5 | Pending |
| EHR-04 | Phase 5 | Pending |
| EHR-05 | Phase 5 | Pending |
| EHR-06 | Phase 5 | Pending |
| EHR-07 | Phase 6 | Pending |
| EHR-08 | Phase 6 | Pending |
| EHR-09 | Phase 6 | Pending |
| BIL-01 | Phase 7 | Pending |
| BIL-02 | Phase 7 | Pending |
| BIL-03 | Phase 8 | Pending |
| BIL-04 | Phase 7 | Pending |
| BIL-05 | Phase 7 | Pending |
| BIL-06 | Phase 8 | Pending |
| BIL-07 | Phase 8 | Pending |

**Coverage:**
- v1 requirements: 37 total
- Mapped to phases: 37 ✓
- Unmapped: 0 ✓

---
*Requirements defined: 2026-07-13*
*Last updated: 2026-07-13 after roadmap creation — traceability mapped*
