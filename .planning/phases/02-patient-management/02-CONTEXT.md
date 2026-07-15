# Phase 2: Patient Management - Context

**Gathered:** 2026-07-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Patient registration, MRN auto-generation, demographics, medical history recording, insurance management, patient search (<2s), and visit history tracking. Delivers a complete patient onboarding and record management capability for front desk and clinical staff.

</domain>

<decisions>
## Implementation Decisions

### MRN Generation Strategy
- **D-01:** MRN format is sequential with configurable prefix (e.g., LAG-000001 for Lagos branch). Prefix is configurable per facility via settings.
- **D-02:** No check digit — simpler, hospital staff rarely type MRNs manually.
- **D-03:** Sequence continues indefinitely (no yearly reset). Stored in database with facility-specific sequence table.
- **D-04:** MRN is globally unique across all facilities. Facility prefix + sequence number combination ensures uniqueness.
- **D-05:** MRN is never reused — permanent once assigned. HIPAA best practice.

### Medical History Model
- **D-06:** Separate tables per type (Allergy, Condition, Surgery, FamilyHistory). Each has type-specific fields.
- **D-07:** Allergies are clinical grade: name, severity (mild/moderate/severe/life-threatening), reaction, onset date, status, ICD-10 code, cross-reactivity flags, verification status.
- **D-08:** Conditions are structured: name, ICD-10 code, onset date, status (active/resolved/chronic), treating department.
- **D-09:** Surgeries are detailed: procedure name, date, surgeon, hospital, CPT code, anesthesia type, duration, complications, outcome.
- **D-10:** Family history is extended: relationship, condition, age of onset, deceased, hereditary flag, genetic conditions, cause of death.
- **D-11:** All medical history entries are append-only (immutable). Corrections create new entries with status 'corrected' and link to original.
- **D-12:** Doctors, nurses, and custom permission users can enter medical history.
- **D-13:** Each entry tracks source: patient-reported, clinical, or imported.
- **D-14:** Medical history can be entered during registration AND during visits.

### Patient Search Strategy
- **D-15:** PostgreSQL full-text search with pg_trgm for Phase 2. Elasticsearch available for upgrade later.
- **D-16:** Instant search (typeahead) with 300ms debounce.
- **D-17:** Unified search box + advanced filter panel. Quick search for regular users, advanced for power users.
- **D-18:** Toggleable table/card view for search results.
- **D-19:** 4 characters minimum before search triggers.
- **D-20:** 50 results per page with pagination.

### Insurance Data Model
- **D-21:** Multiple policies per patient (primary, secondary, dependent). Most realistic for Nigerian NHIS + private insurance landscape.
- **D-22:** Insurance providers pre-seeded with common Nigerian providers (NHIS, Hygeia, Leadway, etc.) + ability to add new ones.
- **D-23:** Per-visit policy selection — patient selects which insurance to use at check-in.
- **D-24:** Insurance verification workflow: pending → verified → active → expired. Full lifecycle tracking.
- **D-25:** Extended coverage types: NHIS, HMO, Private, Corporate/Group, Military/Paramilitary, Tertiary institution.
- **D-26:** Dependents tracked as separate patient records with FK links to both primary holder AND policy.
- **D-27:** Self-pay is implicit — no insurance record = self-pay.
- **D-28:** No policy number validation — accepts any text.
- **D-29:** Track coverage limits, copay, and coinsurance per policy.
- **D-30:** Automated renewal reminders configurable by admin.
- **D-31:** Insurance card image upload supported.
- **D-32:** Reception and billing staff manage insurance policies.
- **D-33:** Expired policies show warning badge but don't block billing.

### Visit History Structure
- **D-34:** Visits auto-created from appointments (Phase 4) + manual walk-in creation by front desk.
- **D-35:** 5-state lifecycle: scheduled → checked-in → in-progress → completed → cancelled.
- **D-36:** Visit duration auto-calculated from check-in to completion timestamps.
- **D-37:** Visit reasons: standardized categories + free text (e.g., consultation, follow-up, procedure, emergency, lab, vaccination).
- **D-38:** Visit summaries auto-generated (configurable by admin) with date, doctor, diagnosis, prescriptions.
- **D-39:** Patient referrals tracked with referring doctor, destination department, reason, status.

### Patient Registration Workflow
- **D-40:** Multi-step wizard: Step 1 (Demographics), Step 2 (Emergency contacts + Next of kin), Step 3 (Insurance), Step 4 (Medical history).
- **D-41:** Comprehensive required fields: name, DOB, gender, phone, address, emergency contact all mandatory.
- **D-42:** 1 emergency contact required, up to 3. Fields: name, phone, relationship.
- **D-43:** Next of kin tracked separately from emergency contacts (legal designation).
- **D-44:** Optional patient photo capture during registration.
- **D-45:** Gender options: Male, Female (binary — standard for Nigerian healthcare context).
- **D-46:** Address: structured fields (street, city, state, LGA, postal code) + free text landmark/directions.
- **D-47:** Phone validation: Nigerian format (+234XXXXXXXXXX or 0XXXXXXXXXX).
- **D-48:** Email validation: format + MX record check.
- **D-49:** Optional NIN (National Identification Number) field.
- **D-50:** Optional blood group capture.
- **D-51:** Optional preferred language (English, Yoruba, Igbo, Hausa, Pidgin).
- **D-52:** Patient status: active, inactive, deceased. Inactive = no visit in 2+ years.
- **D-53:** Duplicate detection: warn if name + DOB match existing patient.
- **D-54:** Manual print option for registration summary (MRN, name, DOB, emergency contact).
- **D-55:** Consent: optional digital consent or paper upload — must do one. Configurable consent form templates.
- **D-56:** CSV bulk patient import with validation, preview, and error reporting.
- **D-57:** Patient portal login credentials sent immediately during registration.
- **D-58:** Registration fee tracking linked to billing (Phase 7).

### Patient Notes
- **D-59:** Categorized free-text notes on patient profile (clinical, administrative, preference).

### Patient Department Management
- **D-60:** Patient can be associated with multiple departments + track department history.

### UI Design
- **D-61:** Reuse existing Phase 1 components (sidebar, header, toasts, skeletons, pagination, modal).
- **D-62:** Split view layout: patient list/search on left, patient details on right. Standard clinical layout.
- **D-63:** Inline validation with green checkmarks for valid fields, red borders for errors.
- **D-64:** Allergy alert: red banner at top of patient profile with allergy count, click to expand details.
- **D-65:** Patient photo in top-left of profile header. Standard clinical layout.

### Data Export
- **D-66:** Patient profile, medical history, and visit history exportable as PDF and CSV.

### Audit & Compliance
- **D-67:** Full audit via existing AuditService for all patient data access and mutations.
- **D-68:** Full search audit — log every patient search with who, what query, when. Critical for HIPAA compliance.

### Claude's Discretion
- MRN sequence implementation (database sequence vs application-level)
- Elasticsearch migration criteria (when to upgrade from PostgreSQL search)
- Specific Nigerian provider seed data (NHIS, Hygeia, Leadway, etc.)
- Consent form template content and structure
- Visit summary PDF template design
- CSV import column mapping and validation rules

### Folded Todos
None — no pending todos matched Phase 2 scope.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — PAT-01 through PAT-06 (Patient Management requirements)
- `.planning/ROADMAP.md` — Phase 2 details, success criteria, plan breakdown

### Architecture & Decisions
- `.planning/PROJECT.md` — Core value, constraints, key decisions (FastAPI + HTMX stack)

### Existing Code (patterns to follow)
- `app/models/user.py` — User model pattern (UUID PKs, timestamps, relationships)
- `app/api/v1/auth.py` — API endpoint pattern (router, deps, error handling)
- `app/services/rbac.py` — Service pattern (staticmethod, async, flush, audit)
- `app/schemas/auth.py` — Schema pattern (Pydantic BaseModel, validation)
- `app/core/database.py` — Database setup (async SQLAlchemy, get_db)
- `app/seeds/roles.py` — Seed pattern (idempotent, dataclass specs)
- `tests/conftest.py` — Test infrastructure (SQLite in-memory, mocked Keycloak)

### Compliance
- `app/models/audit_log.py` — AuditLog model (patient_id column, hash chain)
- `app/services/audit.py` — AuditService (tamper-evident logging)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **AuditLog model**: Already has `patient_id` UUID column — just needs FK constraint to new Patient model
- **BreakGlassAccess model**: Already has `patient_id` UUID column — same FK treatment
- **Patient permissions**: `patient:create`, `patient:read`, `patient:update`, `patient:delete` seeded in 15 roles
- **Phase 1 components**: sidebar.html, header.html, toast.html, skeleton.html, pagination.html, modal.html
- **Rate limiting**: slowapi limiter already configured (can apply to patient search)
- **Audit middleware**: Already extracts `patient_id` from query params

### Established Patterns
- **Model layer**: SQLAlchemy 2.0 `Mapped[T]` style, UUID PKs, `created_at`/`updated_at` timestamps
- **Service layer**: All `@staticmethod`, async, accept `db: AsyncSession`, call `flush()` not `commit()`
- **API layer**: FastAPI routers with dependency injection, `require_permission()`, `CurrentUser`
- **Schema layer**: Pydantic BaseModel, `{Entity}Create`/`{Entity}Response` naming
- **Test layer**: SQLite in-memory, `StaticPool`, mocked Keycloak/notifications, factory fixtures
- **Migration layer**: Alembic async, PostgreSQL-specific types, 12-char hex revision IDs

### Integration Points
- `app/api/v1/router.py` — Add patient router here
- `app/models/__init__.py` — Register new patient models
- `app/seeds/roles.py` — Patient permissions already seeded
- `tests/conftest.py` — Add patient fixtures (create_patient factory)

</code_context>

<specifics>
## Specific Ideas

- MAUTH research (https://mauth.gov.ng/) — existing EHR has 22 clinical departments, IP-based patient tracking, 50+ bed wards. Potential improvements: unified login, telemedicine, bed management, patient portal, NHIS integration
- Nigerian hospital context: NHIS + private insurance common, dependents under parent policy, paper-first workflows being digitized
- Split view is standard in clinical systems (Epic, Cerner, OpenMRS all use it)

</specifics>

<deferred>
## Deferred Ideas

- **Attendance tracking** (staff or patient) — new capability, belongs in separate phase
- **SERVICOM** (patient complaints/satisfaction tracking) — new capability, belongs in separate phase
- **Patient portal features** (self-scheduling, bill payment, secure messaging) — v2 requirements (PRT-01 through PRT-04)
- **Multi-location patient transfers** — v2 requirement (ML-02)
- **Telemedicine integration** — v3 requirement (TEL-01 through TEL-03)

</deferred>

---

*Phase: 2-Patient Management*
*Context gathered: 2026-07-15*
