# Phase 2: Patient Management - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-15
**Phase:** 2-Patient Management
**Areas discussed:** MRN Generation Strategy, Medical History Model, Patient Search Strategy, Insurance Data Model, Visit History Structure, Registration Workflow, Duplicate Detection, Patient Status, Emergency Contacts, Patient Photo, Gender Options, Address Structure, Audit Trail for Patient Data, Phone Validation, Patient Registration Printout, Consent & Privacy, Visit Status Tracking, National ID (NIN), Blood Group, Bulk Patient Import, Language Preference, Email Validation, Next of Kin, Patient Notes, Patient Portal Access, Visit Reason Categorization, Patient Transfer, Registration Fee, Consent Form Template, Patient Search Audit, Patient Referral, Visit Duration Tracking, Patient Visit Summary, Allergy Alert Display, Patient Data Export, Patient Photo Display, UI Style, UI Layout, Form Design

---

## MRN Generation Strategy

### MRN Format
| Option | Description | Selected |
|--------|-------------|----------|
| Sequential with prefix | MRN-000001, MRN-000002, etc. Simple, human-readable | ✓ |
| Date-based with sequence | MRN-2026-000001. Embeds registration year | |
| UUID-derived (short) | First 8-10 chars of UUID. No sequence to predict | |

**User's choice:** Sequential with prefix (Recommended)

### MRN Prefix
| Option | Description | Selected |
|--------|-------------|----------|
| HMS- | Hospital Management System — generic | |
| Configurable per facility | Each hospital location gets its own prefix | ✓ |
| You decide | Let Claude choose | |

**User's choice:** Configurable per facility

### Check Digit
| Option | Description | Selected |
|--------|-------------|----------|
| No check digit | Simpler. MRN-000001 | ✓ |
| Luhn check digit | MRN-0000017 (last digit validates) | |

**User's choice:** No check digit (Recommended)

### MRN Reset
| Option | Description | Selected |
|--------|-------------|----------|
| Continue indefinitely | MRN-000001, 000002, ... forever | ✓ |
| Reset per year | MRN-2026-000001, then MRN-2027-000001 | |

**User's choice:** Continue indefinitely (Recommended)

### Uniqueness
| Option | Description | Selected |
|--------|-------------|----------|
| Unique per facility | Each facility has its own sequence | |
| Globally unique | MRN is globally unique across all facilities | ✓ |

**User's choice:** Globally unique

### MRN Reuse
| Option | Description | Selected |
|--------|-------------|----------|
| Never reuse | MRN is permanent once assigned | ✓ |
| Reuse after grace period | Allow reassignment after configurable period | |

**User's choice:** Never reuse (Recommended)

---

## Medical History Model

### Data Structure
| Option | Description | Selected |
|--------|-------------|----------|
| Separate tables per type | Allergy, Condition, Surgery, FamilyHistory as separate models | ✓ |
| Single flexible model | Single model with type ENUM and JSONB | |
| Hybrid (columns + JSONB) | Core fields in columns, extended data in JSONB | |

**User's choice:** Separate tables per type (Recommended)

### Allergy Detail Level
| Option | Description | Selected |
|--------|-------------|----------|
| Basic | Name, severity, reaction, onset, status | |
| Clinical grade | Basic + ICD-10, cross-reactivity, verification status | ✓ |

**User's choice:** Clinical grade

### Condition Structure
| Option | Description | Selected |
|--------|-------------|----------|
| Structured | Name, ICD-10, onset, status, treating dept | ✓ |
| Free text | Just name and notes | |

**User's choice:** Structured (Recommended)

### Surgery Detail Level
| Option | Description | Selected |
|--------|-------------|----------|
| Standard | Procedure, date, surgeon, hospital, outcome, notes | |
| Detailed | Standard + CPT code, anesthesia, duration, complications | ✓ |

**User's choice:** Detailed

### Family History Detail Level
| Option | Description | Selected |
|--------|-------------|----------|
| Basic | Relationship, condition, age of onset, deceased | |
| Extended | Basic + hereditary flag, genetic conditions, cause of death | ✓ |

**User's choice:** Extended

### Editability
| Option | Description | Selected |
|--------|-------------|----------|
| Editable with audit trail | Staff can edit, changes tracked via audit log | |
| Append-only (immutable) | Entries are append-only, corrections create new entries | ✓ |

**User's choice:** Append-only (immutable)

### Entry Permissions
| Option | Description | Selected |
|--------|-------------|----------|
| Doctors + nurses | Most flexible for clinical workflow | |
| Doctors only | More controlled but slower | |
| Any clinical staff | Maximum flexibility but less oversight | |

**User's choice:** Doctors + nurses + custom permission users

### Source Tracking
| Option | Description | Selected |
|--------|-------------|----------|
| Source tracking | Each entry has source field (patient-reported, clinical, imported) | ✓ |
| No source tracking | All entries treated equally | |

**User's choice:** Source tracking (Recommended)

### Entry Timing
| Option | Description | Selected |
|--------|-------------|----------|
| Standalone entry | Separate Medical History page, outside visit context | |
| During registration + visits | Both entry points update same patient record | ✓ |
| During visits only | Forces clinical context but delays initial capture | |

**User's choice:** During registration + visits (Recommended)

---

## Patient Search Strategy

### Search Backend
| Option | Description | Selected |
|--------|-------------|----------|
| PostgreSQL full-text | Use pg_trgm extension, no additional infra | |
| Elasticsearch | Use Elasticsearch 8 in Docker Compose | |
| PostgreSQL first, Elasticsearch later | Start simple, upgrade if needed | ✓ |

**User's choice:** PostgreSQL first, Elasticsearch later

### Search Behavior
| Option | Description | Selected |
|--------|-------------|----------|
| Instant search (typeahead) | Results appear as you type | ✓ |
| Search on submit | Press Enter or click Search | |

**User's choice:** Instant search (Recommended)

### Search UI
| Option | Description | Selected |
|--------|-------------|----------|
| Single unified search box | One box searches across all fields | |
| Multi-field search form | Separate fields with AND/OR logic | |
| Unified + advanced filters | Quick box + advanced filter panel | ✓ |

**User's choice:** Unified + advanced filters

### Search Results Display
| Option | Description | Selected |
|--------|-------------|----------|
| Table view | Compact, scannable | |
| Card view | Visual, takes more space | |
| Toggleable view | User can toggle between table and card | ✓ |

**User's choice:** Toggleable view

### Minimum Characters
| Option | Description | Selected |
|--------|-------------|----------|
| 2 characters | Balances speed with precision | |
| 1 character | Maximum responsiveness | |
| 3 characters | Fewer false positives | |

**User's choice:** 4 characters

### Results Limit
| Option | Description | Selected |
|--------|-------------|----------|
| 20 + load more | Fast initial load | |
| 50 + pagination | More results upfront | ✓ |
| No limit | Risky for large datasets | |

**User's choice:** 50 + pagination

---

## Insurance Data Model

### Policy Count
| Option | Description | Selected |
|--------|-------------|----------|
| Multiple policies per patient | Primary, secondary, dependent | ✓ |
| Single active policy | One at a time | |
| Multiple with primary/secondary | Claims go to primary first | |

**User's choice:** Multiple policies per patient (Recommended)

### Provider Management
| Option | Description | Selected |
|--------|-------------|----------|
| Lookup table | Separate InsuranceProvider table | |
| Free text on policy | Provider name as free text | |
| Seeded + extensible | Pre-seeded common providers + ability to add | ✓ |

**User's choice:** Seeded + extensible (Recommended)

### Visit-Insurance Link
| Option | Description | Selected |
|--------|-------------|----------|
| Per-visit policy selection | Patient selects which insurance at check-in | ✓ |
| Default policy per patient | Default unless overridden | |
| No visit linkage | Insurance is just patient-level data | |

**User's choice:** Per-visit policy selection (Recommended)

### Insurance Detail Level
| Option | Description | Selected |
|--------|-------------|----------|
| Basic data entry | Policy number, provider, plan type, dates | |
| Data + card upload | Basic + insurance card image | |
| Data + verification workflow | Basic + verification status | ✓ |

**User's choice:** Data + verification workflow

### Coverage Types
| Option | Description | Selected |
|--------|-------------|----------|
| Standard types | NHIS, HMO, Private, Self-pay | |
| Extended types | Standard + Tertiary, Corporate, Military | ✓ |
| Free text | Maximum flexibility | |

**User's choice:** Extended types

### Dependent Tracking
| Option | Description | Selected |
|--------|-------------|----------|
| Dependents as separate patients | Each dependent gets own patient record | ✓ |
| Dependents as policy metadata | Stored as JSON/list on policy | |
| No dependent tracking (v1) | Each person registers independently | |

**User's choice:** Dependents as separate patients (Recommended)

### Policy Expiration
| Option | Description | Selected |
|--------|-------------|----------|
| Warn but allow | Show warning badge, no blocking | ✓ |
| Block on expired | Force renewal before visit | |
| No expiration tracking (v1) | Just record coverage dates | |

**User's choice:** Warn but allow (Recommended)

### Self-Pay Handling
| Option | Description | Selected |
|--------|-------------|----------|
| Implicit (no record = self-pay) | No insurance record = self-pay | ✓ |
| Explicit self-pay record | Create 'Self-Pay' insurance record | |
| Self-pay + payment plan | More billing complexity | |

**User's choice:** Implicit (no record = self-pay) (Recommended)

### Policy Number Validation
| Option | Description | Selected |
|--------|-------------|----------|
| No validation | Accept any text | ✓ |
| Per-provider format validation | Validate format per provider | |
| Basic format validation | Alphanumeric, 6-20 chars | |

**User's choice:** No validation (Recommended)

### Coverage Details
| Option | Description | Selected |
|--------|-------------|----------|
| Track limits + copay | Record coverage limits, copay, coinsurance | ✓ |
| Minimal (provider + dates only) | No financial details | |
| Limits only, no copay | Track limits but defer copay | |

**User's choice:** Track limits + copay (Recommended)

### Renewal Reminders
| Option | Description | Selected |
|--------|-------------|----------|
| Visual indicator only | Show expiration date prominently | |
| Automated reminders | Send email/SMS before expiry | ✓ |
| Start date only | No expiration tracking | |

**User's choice:** Automated reminders, configurable by admin

### Card Upload
| Option | Description | Selected |
|--------|-------------|----------|
| Yes, upload card | Store in patient attachments | ✓ |
| No image upload (v1) | Just text data | |
| Upload + OCR auto-fill | Advanced AI complexity | |

**User's choice:** Yes, upload card (Recommended)

### Insurance Management Permissions
| Option | Description | Selected |
|--------|-------------|----------|
| Reception + billing | Most realistic role separation | ✓ |
| Any staff with patient:update | Maximum flexibility | |
| Reception only | Most controlled | |

**User's choice:** Reception + billing (Recommended)

### Dependent Link
| Option | Description | Selected |
|--------|-------------|----------|
| FK to primary holder | Dependent links to holder | |
| FK to insurance policy | Dependent links to policy | |
| Both links | Dependent links to holder AND policy | ✓ |

**User's choice:** Both links

---

## Visit History Structure

### Visit Creation
| Option | Description | Selected |
|--------|-------------|----------|
| Auto from appointments + manual walk-in | Vises auto-created when appointments booked + manual | ✓ |
| Manual only | All visits created manually | |
| Auto at check-in | Created when patient arrives | |

**User's choice:** Auto from appointments + manual walk-in (Recommended)

### Visit Status
| Option | Description | Selected |
|--------|-------------|----------|
| 5-state lifecycle | Scheduled, checked-in, in-progress, completed, cancelled | ✓ |
| 4-state lifecycle | Scheduled, in-progress, completed, cancelled | |
| 6-state lifecycle | Created, waiting, with-doctor, completed, cancelled | |

**User's choice:** 5-state lifecycle (Recommended)

### Visit Duration
| Option | Description | Selected |
|--------|-------------|----------|
| Auto-calculate from timestamps | Calculate from check-in to completion | ✓ |
| Manual entry | Staff manually enter duration | |
| No duration (v1) | Just status timestamps | |

**User's choice:** Auto-calculate from timestamps (Recommended)

### Visit Reason
| Option | Description | Selected |
|--------|-------------|----------|
| Standardized categories | consultation, follow-up, procedure, etc. | |
| Free text only | Simple, flexible, inconsistent | |
| Categories + free text | Best of both worlds | ✓ |

**User's choice:** Categories + free text

### Visit Summary
| Option | Description | Selected |
|--------|-------------|----------|
| Auto-generate + print/email | Auto-generate with date, doctor, diagnosis, prescriptions | |
| Screen only | Summary available on screen | |
| No summary (v1) | Focus on clinical data entry | |

**User's choice:** Configurable by admin

---

## Patient Registration Workflow

### Registration Form
| Option | Description | Selected |
|--------|-------------|----------|
| Multi-step wizard | Step 1: Demographics, Step 2: Emergency, Step 3: Insurance, Step 4: History | ✓ |
| Single page with sections | All fields on one page with collapsible sections | |
| Two-page split | Demographics + emergency on page 1, insurance + history on page 2 | |

**User's choice:** Multi-step wizard (Recommended)

### Required Fields
| Option | Description | Selected |
|--------|-------------|----------|
| Minimal required | Name, DOB, gender, phone mandatory | |
| Comprehensive required | Name, DOB, gender, phone, address, emergency all mandatory | ✓ |
| Very minimal | Name, DOB, gender mandatory | |

**User's choice:** Comprehensive required

### Emergency Contacts
| Option | Description | Selected |
|--------|-------------|----------|
| 1 required, up to 3 | Sufficient for emergencies | ✓ |
| 2 required | More reliable reach | |
| Optional | Fastest registration | |

**User's choice:** 1 required, up to 3 (Recommended)

### Next of Kin
| Option | Description | Selected |
|--------|-------------|----------|
| Separate from emergency contacts | Legal designation separate from emergency | ✓ |
| Same as first emergency contact | Simpler, less data entry | |
| No next of kin (v1) | Rely on emergency contacts only | |

**User's choice:** Separate from emergency contacts (Recommended)

### Patient Photo
| Option | Description | Selected |
|--------|-------------|----------|
| Yes, capture photo | Stored as file attachment | |
| No photo (v1) | Just text data | |
| Optional | Staff can upload if they want | ✓ |

**User's choice:** Optional

### Gender Options
| Option | Description | Selected |
|--------|-------------|----------|
| Binary (M/F) | Standard for Nigerian healthcare | ✓ |
| Inclusive options | Male, Female, Other, Prefer not to say | |
| Three options | Male, Female, Other | |

**User's choice:** Binary (M/F) (Recommended)

### Address Structure
| Option | Description | Selected |
|--------|-------------|----------|
| Structured fields | Street, city, state, LGA, postal code | |
| Free text | Single textarea | |
| Structured + landmark text | Structured + free text for landmark/directions | ✓ |

**User's choice:** Structured + landmark text

### Phone Validation
| Option | Description | Selected |
|--------|-------------|----------|
| Nigerian format validation | +234XXXXXXXXXX or 0XXXXXXXXXX | ✓ |
| Basic digit validation | Any 10-15 digit number | |
| No validation | Accept any text | |

**User's choice:** Nigerian format validation (Recommended)

### Email Validation
| Option | Description | Selected |
|--------|-------------|----------|
| Validate format | Regex validation | |
| No validation | Accept any text | |
| Validate + MX check | Format + domain exists | ✓ |

**User's choice:** Validate + MX check

### National ID (NIN)
| Option | Description | Selected |
|--------|-------------|----------|
| Yes, capture NIN | Required by Nigerian law | |
| Optional NIN | Enter if patient has it | ✓ |
| No NIN (v1) | Too much friction | |

**User's choice:** Optional NIN

### Blood Group
| Option | Description | Selected |
|--------|-------------|----------|
| Yes, capture blood group | Important for clinical safety | |
| Optional | Enter during first clinical visit if known | ✓ |
| No blood group (v1) | Enter during clinical encounters only | |

**User's choice:** Optional

### Language Preference
| Option | Description | Selected |
|--------|-------------|----------|
| Yes, track language | English, Yoruba, Igbo, Hausa, Pidgin | |
| Default English (v1) | No language tracking | |
| Optional | Enter if patient specifies | ✓ |

**User's choice:** Optional

### Patient Status
| Option | Description | Selected |
|--------|-------------|----------|
| Active/inactive/deceased | Simple lifecycle | ✓ |
| Extended states | Active, inactive, deceased, transferred, archived | |
| Active/inactive only | No deceased tracking | |

**User's choice:** Active/inactive/deceased (Recommended)

### Duplicate Detection
| Option | Description | Selected |
|--------|-------------|----------|
| Warn on potential match | Warn if name + DOB match | ✓ |
| Block on exact match | Reject if name + DOB + phone match | |
| No detection | Staff responsible for searching | |

**User's choice:** Warn on potential match (Recommended)

### Registration Printout
| Option | Description | Selected |
|--------|-------------|----------|
| Auto-print | Auto-print registration summary | |
| Manual print option | Staff can print if patient requests | ✓ |
| No printout (v1) | MRN displayed on screen only | |

**User's choice:** Manual print option

### Consent & Privacy
| Option | Description | Selected |
|--------|-------------|----------|
| Digital consent capture | Capture digital consent for NDPA compliance | |
| Paper consent + upload | Traditional paper form | |
| No digital consent (v1) | Rely on paper consent | |

**User's choice:** Optional both, must do one

### Bulk Import
| Option | Description | Selected |
|--------|-------------|----------|
| Yes, CSV import | With validation, preview, error reporting | ✓ |
| API-only import | Developer-driven migration | |
| No bulk import (v1) | Manual registration only | |

**User's choice:** Yes, CSV import (Recommended)

### Portal Access
| Option | Description | Selected |
|--------|-------------|----------|
| Yes, immediate access | Patients receive login credentials immediately | ✓ |
| Delayed activation | Portal access activated later | |
| No portal (v1) | Staff-only access | |

**User's choice:** Yes, immediate access (Recommended)

### Registration Fee
| Option | Description | Selected |
|--------|-------------|----------|
| Track fee + payment | Record fee amount and payment status | ✓ |
| Fee exists, no tracking | Tracked separately in billing | |
| No fee tracking (v1) | Focus on patient data | |

**User's choice:** Track fee + payment (Recommended)

---

## Patient Notes

### Notes Style
| Option | Description | Selected |
|--------|-------------|----------|
| Yes, free-text notes | Quick notes on patient profile | |
| Categorized notes | Clinical, administrative, preference | ✓ |
| No free-text notes (v1) | All structured fields | |

**User's choice:** Categorized notes

---

## Patient Department Management

### Department Tracking
| Option | Description | Selected |
|--------|-------------|----------|
| Track transfers | Patient belongs to one department at a time | |
| Multi-department (no transfer) | Patient can be in multiple departments simultaneously | ✓ |
| No department tracking (v1) | Department is just a label | |

**User's choice:** Can have both — append patient department and track

---

## Consent Form Templates

### Template Management
| Option | Description | Selected |
|--------|-------------|----------|
| Configurable templates | Admin-configurable consent form templates | ✓ |
| Single hardcoded form | Simpler but less flexible | |
| No templates (v1) | Just record consent status | |

**User's choice:** Configurable templates (Recommended)

---

## Patient Search Audit

### Search Logging
| Option | Description | Selected |
|--------|-------------|----------|
| Full search audit | Log every patient search with who, what, when | ✓ |
| Log detail views only | Log searches that access patient details | |
| No search audit (v1) | Rely on general audit logging | |

**User's choice:** Full search audit (Recommended)

---

## Patient Referral

### Referral Tracking
| Option | Description | Selected |
|--------|-------------|----------|
| Track referrals | Referring doctor, destination dept, reason, status | ✓ |
| No referrals (v1) | Focus on core patient management | |
| Simple referral link | Between departments, no full workflow | |

**User's choice:** Track referrals (Recommended)

---

## Allergy Alert Display

### Display Style
| Option | Description | Selected |
|--------|-------------|----------|
| Red banner + expandable details | Always visible at top of profile | ✓ |
| Sidebar with color coding | Always visible in sidebar | |
| Badge icon + modal | Click to view details | |

**User's choice:** Red banner + expandable details (Recommended)

---

## Patient Data Export

### Export Format
| Option | Description | Selected |
|--------|-------------|----------|
| PDF export | Patient profile, history, visits | |
| PDF + CSV | PDF + CSV for data portability | ✓ |
| No export (v1) | Data stays in system | |

**User's choice:** PDF + CSV

---

## Patient Photo Display

### Photo Location
| Option | Description | Selected |
|--------|-------------|----------|
| Profile header | Top-left of patient profile | ✓ |
| Sidebar | Next to patient name | |
| Modal only | Click to view | |

**User's choice:** Profile header (Recommended)

---

## UI Design

### Component Reuse
| Option | Description | Selected |
|--------|-------------|----------|
| Reuse Phase 1 components | Sidebar, header, toasts, skeletons | ✓ |
| New patient-specific components | Different layout for different context | |
| Mixed approach | Use existing where possible, new where needed | |

**User's choice:** Reuse Phase 1 components (Recommended)

### Page Layout
| Option | Description | Selected |
|--------|-------------|----------|
| Split view | Patient list on left, details on right | ✓ |
| Full-page views | List on one page, profile on another | |
| Dashboard + separate pages | Dashboard with recent patients | |

**User's choice:** Split view (Recommended)

### Form Validation Display
| Option | Description | Selected |
|--------|-------------|----------|
| Inline validation | Green checkmarks, red borders, real-time | ✓ |
| Submit-time validation | Validation on submit only | |
| Inline + help text | Inline + field-level help text | |

**User's choice:** Inline validation (Recommended)

---

## Claude's Discretion

- MRN sequence implementation (database sequence vs application-level)
- Elasticsearch migration criteria (when to upgrade from PostgreSQL search)
- Specific Nigerian provider seed data (NHIS, Hygeia, Leadway, etc.)
- Consent form template content and structure
- Visit summary PDF template design
- CSV import column mapping and validation rules

## Deferred Ideas

- **Attendance tracking** (staff or patient) — new capability, belongs in separate phase
- **SERVICOM** (patient complaints/satisfaction tracking) — new capability, belongs in separate phase
- **Patient portal features** (self-scheduling, bill payment, secure messaging) — v2 requirements (PRT-01 through PRT-04)
- **Multi-location patient transfers** — v2 requirement (ML-02)
- **Telemedicine integration** — v3 requirement (TEL-01 through TEL-03)
