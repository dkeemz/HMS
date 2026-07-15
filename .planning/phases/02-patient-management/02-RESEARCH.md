# Phase 2: Patient Management - Research

**Researched:** 2026-07-15
**Domain:** Patient registration, medical records, insurance management, clinical search
**Confidence:** HIGH

## Summary

Phase 2 builds the patient management layer on top of Phase 1's auth infrastructure. The core challenge is designing ~15 new database tables (Patient, Allergy, Condition, Surgery, FamilyHistory, InsuranceProvider, InsurancePolicy, Visit, VisitSummary, PatientNote, PatientDepartment, EmergencyContact, NextOfKin, Consent, PatientDepartmentHistory) while following the exact patterns established in Phase 1. The MRN generation uses a PostgreSQL sequence per facility for guaranteed uniqueness and immutability. Patient search uses PostgreSQL `pg_trgm` for sub-2-second fuzzy search across name, MRN, phone, and DOB — no external search engine needed at this scale. The HTMX UI follows the existing split-view clinical pattern with multi-step registration wizard.

**Primary recommendation:** Use database-level PostgreSQL sequences for MRN generation (simplest, most reliable, ACID-compliant), `pg_trgm` GIN indexes for search, and follow the exact Phase 1 model/service/API/schema patterns for all new code.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Patient demographics CRUD | API / Backend | Browser / Client | Business logic and validation in service layer; UI is form-driven HTMX |
| MRN auto-generation | Database / Storage | API / Backend | PostgreSQL sequence guarantees uniqueness at DB level; service calls nextval |
| Medical history recording | API / Backend | Database / Storage | Append-only immutability enforced in service; DB stores structured data |
| Insurance management | API / Backend | Browser / Client | Policy lifecycle (pending→verified→active→expired) managed in service |
| Patient search (<2s) | Database / Storage | API / Backend | pg_trgm GIN indexes do the heavy lifting; API just queries |
| Visit history tracking | API / Backend | Database / Storage | Visits created from appointments (Phase 4) + manual; chronological display |
| Data export (PDF/CSV) | API / Backend | — | Server-side generation using reportlab/stdlib csv |
| Bulk CSV import | API / Backend | — | Server-side validation with preview and error reporting |
| Patient registration UI | Browser / Client | API / Backend | Multi-step wizard, HTMX-driven, inline validation |

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PAT-01 | Patient registration with demographics (name, DOB, gender, contact, address, emergency contacts) | Multi-step wizard model (D-40), comprehensive field set (D-41–D-58), Nigerian phone format validation (D-47) |
| PAT-02 | System assigns unique MRN on registration | PostgreSQL sequence strategy (D-01–D-05), facility-prefixed sequential MRN |
| PAT-03 | Medical history recorded (allergies, conditions, surgeries, family history) | Separate tables per type (D-06–D-14), append-only immutability (D-11), clinical-grade fields |
| PAT-04 | Patient insurance information managed (policy, provider, coverage) | Multiple policies per patient (D-21), verification workflow (D-24), Nigerian NHIS + HMO landscape (D-22, D-25) |
| PAT-05 | Patient search by name, MRN, phone, DOB under 2 seconds | PostgreSQL pg_trgm with GIN indexes (D-15), 300ms debounce typeahead (D-16), 4-char minimum (D-19) |
| PAT-06 | Patient visit history tracked chronologically | Visit lifecycle (D-35), auto-calculated duration (D-36), standardized visit reasons (D-37) |
</phase_requirements>

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** MRN format is sequential with configurable prefix (e.g., LAG-000001 for Lagos branch). Prefix is configurable per facility via settings.
- **D-02:** No check digit — simpler, hospital staff rarely type MRNs manually.
- **D-03:** Sequence continues indefinitely (no yearly reset). Stored in database with facility-specific sequence table.
- **D-04:** MRN is globally unique across all facilities.
- **D-05:** MRN is never reused — permanent once assigned.
- **D-06:** Separate tables per medical history type (Allergy, Condition, Surgery, FamilyHistory).
- **D-11:** All medical history entries are append-only (immutable). Corrections create new entries with status 'corrected' and link to original.
- **D-15:** PostgreSQL full-text search with pg_trgm for Phase 2. Elasticsearch available for upgrade later.
- **D-21:** Multiple policies per patient (primary, secondary, dependent).
- **D-24:** Insurance verification workflow: pending → verified → active → expired.
- **D-34:** Visits auto-created from appointments (Phase 4) + manual walk-in creation by front desk.
- **D-35:** 5-state lifecycle: scheduled → checked-in → in-progress → completed → cancelled.
- **D-40:** Multi-step wizard: Step 1 (Demographics), Step 2 (Emergency contacts + Next of kin), Step 3 (Insurance), Step 4 (Medical history).
- **D-61:** Reuse existing Phase 1 components (sidebar, header, toasts, skeletons, pagination, modal).
- **D-62:** Split view layout: patient list/search on left, patient details on right.
- **D-67:** Full audit via existing AuditService for all patient data access and mutations.
- **D-68:** Full search audit — log every patient search with who, what query, when.

### the agent's Discretion
- MRN sequence implementation (database sequence vs application-level)
- Elasticsearch migration criteria (when to upgrade from PostgreSQL search)
- Specific Nigerian provider seed data (NHIS, Hygeia, Leadway, etc.)
- Consent form template content and structure
- Visit summary PDF template design
- CSV import column mapping and validation rules

### Deferred Ideas (OUT OF SCOPE)
- Attendance tracking (staff or patient)
- SERVICOM (patient complaints/satisfaction tracking)
- Patient portal features (self-scheduling, bill payment, secure messaging) — v2
- Multi-location patient transfers — v2
- Telemedicine integration — v3
</user_constraints>

## Standard Stack

### Core (already installed — no new packages needed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy | 2.0.49 | ORM with async support | Already in use, project standard |
| FastAPI | 0.136.1 | API framework | Already in use, project standard |
| Pydantic | 2.13.3 | Request/response validation | Already in use, project standard |
| Alembic | 1.18.4 | Database migrations | Already in use, project standard |
| Jinja2 | 3.1.3 | Template engine for HTMX pages | Already in use, project standard |
| asyncpg | 0.31.0 | PostgreSQL async driver | Already in use, project standard |

### Supporting (for Phase 2-specific features)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| reportlab | 4.5.1 | PDF generation for patient exports, visit summaries | Patient profile export, visit summary PDF |
| stdlib csv | — | CSV import/export | Bulk patient import, data export |
| PostgreSQL pg_trgm | (extension) | Fuzzy text search | Patient search by name, MRN |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pg_trgm | Elasticsearch | Elasticsearch is overkill for Phase 2 scale; pg_trgm handles <100K patients fine. Elasticsearch upgrade path preserved for later (D-15). |
| Database sequences for MRN | Application-level counter | DB sequences are ACID-compliant, survive crashes, no race conditions. Application-level needs distributed locking. |
| reportlab for PDF | weasyprint | weasyprint needs system-level Cairo/Pango libs. reportlab is pure Python, simpler deployment. |
| Separate tables per medical history | Single polymorphic table | Separate tables allow type-specific fields without NULL columns. Better query performance for type-specific views. |

**Installation:** No new packages to install — all dependencies are already in the project. reportlab is already available (v4.5.1).

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| reportlab | PyPI | 24+ years | 50M+ | [github.com/ReportLab/reportlab](https://github.com/ReportLab/reportlab) | [OK] | Approved |
| weasyprint | PyPI | 12+ years | 20M+ | [github.com/Kozea/WeasyPrint](https://github.com/Kozea/WeasyPrint) | [OK] | Approved (backup only) |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

*Note: Phase 2 requires no new pip packages. reportlab and weasyprint are already installed. The primary search technology (pg_trgm) is a PostgreSQL extension, not a Python package.*

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Browser (HTMX)                              │
│  ┌──────────────┐  ┌─────────────────────────────────────────────┐ │
│  │ Patient List  │  │ Patient Detail / Registration Wizard       │ │
│  │ (Search)      │→ │ (Demographics, Medical Hx, Insurance,     │ │
│  │ pg_trgm       │  │  Visits, Notes, Allergy Banner)           │ │
│  └──────┬───────┘  └──────────────────┬──────────────────────────┘ │
│         │ hx-get / hx-post            │                            │
└─────────┼─────────────────────────────┼────────────────────────────┘
          │                             │
┌─────────▼─────────────────────────────▼────────────────────────────┐
│                    FastAPI Router Layer                             │
│  /api/v1/patients/*     /api/v1/patients/{id}/medical-history/*   │
│  /api/v1/patients/{id}/insurance/*     /api/v1/patients/{id}/visits│
│  require_permission("patient", "create|read|update|delete")        │
│  AuditService.log_event() for every mutation                       │
└─────────┬─────────────────────────────┬────────────────────────────┘
          │                             │
┌─────────▼─────────────────────────────▼────────────────────────────┐
│                    Service Layer (all @staticmethod, async)         │
│  PatientService   MedicalHistoryService   InsuranceService          │
│  VisitService     PatientSearchService    MRNService               │
│  All methods accept db: AsyncSession, call flush() not commit()    │
└─────────┬─────────────────────────────┬────────────────────────────┘
          │                             │
┌─────────▼─────────────────────────────▼────────────────────────────┐
│                    PostgreSQL 17                                    │
│  patients │ allergies │ conditions │ surgeries │ family_history    │
│  insurance_providers │ insurance_policies │ visits │ visit_summaries│
│  patient_notes │ emergency_contacts │ next_of_kin │ consents       │
│  mrn_sequences (facility prefix + next value)                      │
│  pg_trgm GIN indexes on patients (name, mrn, phone, dob)          │
│  AuditLog.patient_id FK ───────────────────────────────────────┘  │
│  BreakGlassAccess.patient_id FK ───────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure

```
app/
├── models/
│   ├── patient.py              # Patient model (core entity)
│   ├── mrn_sequence.py         # MRN sequence table (facility prefix tracking)
│   ├── emergency_contact.py    # EmergencyContact (1-3 per patient)
│   ├── next_of_kin.py          # NextOfKin (separate legal designation)
│   ├── allergy.py              # Allergy (clinical-grade fields)
│   ├── condition.py            # Condition (ICD-10, status tracking)
│   ├── surgery.py              # Surgery (detailed procedure records)
│   ├── family_history.py       # FamilyHistory (extended family data)
│   ├── insurance_provider.py   # InsuranceProvider (pre-seeded)
│   ├── insurance_policy.py     # InsurancePolicy (per-patient, lifecycle)
│   ├── visit.py                # Visit (5-state lifecycle)
│   ├── visit_summary.py        # VisitSummary (auto-generated)
│   ├── patient_note.py         # PatientNote (categorized free-text)
│   ├── patient_department.py   # PatientDepartment (many-to-many + history)
│   └── consent.py              # Consent (digital or paper upload)
├── schemas/
│   ├── patient.py              # PatientCreate, PatientResponse, PatientUpdate
│   ├── medical_history.py      # AllergyCreate, ConditionCreate, etc.
│   ├── insurance.py            # InsurancePolicyCreate, InsuranceProviderResponse
│   ├── visit.py                # VisitCreate, VisitResponse
│   └── search.py               # PatientSearchParams, PatientSearchResponse
├── services/
│   ├── patient.py              # PatientService (registration, CRUD, search)
│   ├── mrn.py                  # MRNService (generation, validation)
│   ├── medical_history.py      # MedicalHistoryService (all types)
│   ├── insurance.py            # InsuranceService (policy lifecycle)
│   ├── visit.py                # VisitService (lifecycle management)
│   └── patient_search.py       # PatientSearchService (pg_trgm queries)
├── api/v1/
│   ├── patients.py             # Patient CRUD + registration endpoints
│   ├── medical_history.py      # Medical history endpoints per patient
│   ├── insurance.py            # Insurance endpoints per patient
│   ├── visits.py               # Visit history endpoints
│   └── patient_search.py       # Search endpoint (unified + advanced)
├── templates/
│   ├── patients/
│   │   ├── list.html           # Split view: search + list left, detail right
│   │   ├── register.html       # Multi-step registration wizard
│   │   ├── profile.html        # Patient profile view
│   │   ├── medical_history.html # Allergies, conditions, surgeries, family hx
│   │   ├── insurance.html      # Insurance policies management
│   │   └── visits.html         # Visit history timeline
│   └── components/
│       ├── allergy_banner.html # Red allergy alert banner (D-64)
│       ├── patient_card.html   # Patient result card (toggleable view)
│       ├── search_filters.html # Advanced filter panel
│       └── visit_timeline.html # Chronological visit display
└── seeds/
    └── insurance_providers.py  # Pre-seed Nigerian insurance providers
```

### Pattern 1: Patient Model (UUID PK, timestamps, soft status)

```python
# Source: Following app/models/user.py pattern exactly
# Pattern: SQLAlchemy 2.0 Mapped[T], UUID PK, created_at/updated_at

class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'deceased')",
            name="ck_patient_status",
        ),
        Index("ix_patient_mrn_trgm", "mrn", postgresql_using="gin",
              postgresql_ops={"mrn": "gin_trgm_ops"}),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    mrn: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)  # Male/Female
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    blood_group: Mapped[str | None] = mapped_column(String(5), nullable=True)
    nin: Mapped[str | None] = mapped_column(String(11), nullable=True)  # National ID
    preferred_language: Mapped[str | None] = mapped_column(String(20), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    # Address (structured per D-46)
    address_street: Mapped[str] = mapped_column(String(255), nullable=False)
    address_city: Mapped[str] = mapped_column(String(100), nullable=False)
    address_state: Mapped[str] = mapped_column(String(100), nullable=False)
    address_lga: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address_postal_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    address_landmark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

### Pattern 2: Service Layer (all @staticmethod, async, flush not commit)

```python
# Source: Following app/services/rbac.py pattern exactly

class PatientService:
    @staticmethod
    async def register_patient(
        db: AsyncSession,
        data: PatientCreate,
        created_by: uuid.UUID,
    ) -> Patient:
        """Register a new patient with MRN auto-generation."""
        # 1. Duplicate detection (D-53)
        existing = await PatientService._check_duplicate(db, data)
        if existing:
            raise ValueError(f"Possible duplicate: {existing.first_name} {existing.last_name} (DOB: {existing.date_of_birth})")

        # 2. Generate MRN
        mrn = await MRNService.generate_mrn(db)

        # 3. Create patient
        patient = Patient(mrn=mrn, **data.model_dump())
        db.add(patient)
        await db.flush()

        # 4. Audit log
        await AuditService.log_event(
            db, user_id=created_by, action="patient_registered",
            resource="patient", resource_id=str(patient.id),
            patient_id=patient.id, why="New patient registration",
        )
        await db.flush()
        return patient
```

### Pattern 3: API Router with Permission + Audit

```python
# Source: Following app/api/v1/auth.py pattern exactly

router = APIRouter(prefix="/patients", tags=["patients"])

@router.post("/", response_model=PatientResponse, status_code=201)
async def register_patient(
    body: PatientCreate,
    current_user: CurrentUser = Depends(require_permission("patient", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Register a new patient with demographics and auto-generated MRN."""
    try:
        patient = await PatientService.register_patient(db, body, current_user.id)
        await db.commit()
        return PatientResponse.model_validate(patient)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
```

### Pattern 4: Pydantic Schema with Validation

```python
# Source: Following app/schemas/auth.py pattern exactly

class PatientCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    gender: Literal["Male", "Female"]  # D-45: binary for Nigerian context
    phone: str = Field(..., pattern=r"^(\+234|0)[789]\d{9}$")  # D-47: Nigerian format
    email: EmailStr | None = None
    # ... structured address fields per D-46
    address_street: str
    address_city: str
    address_state: str
    address_lga: str | None = None
    address_postal_code: str | None = None
    address_landmark: str | None = None

class PatientResponse(BaseModel):
    id: str
    mrn: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    phone: str
    email: str | None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

### Anti-Patterns to Avoid
- **Hand-rolling MRN generation:** Don't use application-level counters or UUID-based MRNs. PostgreSQL sequences are ACID-compliant and survive crashes. Application counters lose state on restart.
- **Mutable medical history:** Never update allergy/condition/surgery records in place. Always create new entries and link to originals (D-11 append-only).
- **Committing in services:** Services must call `flush()` not `commit()`. The API layer owns the transaction boundary.
- **Building search from scratch:** Don't implement custom fuzzy matching. PostgreSQL pg_trgm with GIN indexes handles this natively.
- **Skipping audit logs:** Every patient data access and mutation must go through AuditService. The middleware handles generic HTTP logging; service-level logging captures clinical context (who accessed what patient record and why).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MRN uniqueness | Application UUID or random ID | PostgreSQL `nextval()` sequence | ACID guarantees, survives crashes, no race conditions, sequential for human readability |
| Fuzzy text search | Custom Levenshtein distance | PostgreSQL `pg_trgm` + GIN index | Built-in trigram similarity, GiST/GIN indexed, <50ms on 100K rows |
| PDF generation | HTML-to-image hack | reportlab (already installed) | Production-grade PDF with tables, headers, barcodes. Pure Python, no system deps |
| CSV parsing | Manual string splitting | Python stdlib `csv` + Pydantic validation | Handles quoting, encoding, edge cases. Pydantic validates each row |
| Date validation | Manual date parsing | Pydantic `date` type + custom validators | Handles ISO format, leap years, range validation automatically |
| Phone validation | Regex from memory | Pydantic `Field(pattern=...)` with Nigerian regex | D-47 specifies exact format (+234XXXXXXXXXX or 0XXXXXXXXXX) |
| Insurance lifecycle state machine | Manual status tracking | Enum + service method per transition | Prevents invalid transitions, makes state explicit, easier to audit |

**Key insight:** This phase adds ~15 new tables but zero new infrastructure. PostgreSQL pg_trgm replaces the need for Elasticsearch. reportlab replaces the need for a PDF microservice. The existing AuditService handles all compliance logging. Focus effort on data modeling correctness, not infrastructure.

## Common Pitfalls

### Pitfall 1: MRN Generation Race Condition
**What goes wrong:** Two concurrent registrations get the same MRN if using application-level counters.
**Why it happens:** SELECT MAX(mrn) + 1 is not atomic under concurrency.
**How to avoid:** Use PostgreSQL `nextval()` on a sequence. The database guarantees uniqueness even under thousands of concurrent registrations.
**Warning signs:** Tests pass sequentially but fail under concurrent load.

### Pitfall 2: Medical History Mutation Instead of Append
**What goes wrong:** Doctor "corrects" an allergy by updating the existing record, losing audit history.
**Why it happens:** Natural CRUD instinct — UPDATE feels correct.
**How to avoid:** Service layer enforces append-only. `update_allergy()` creates a new record with `status='corrected'` and `corrected_by` FK to original. Original record is never modified.
**Warning signs:** Any UPDATE on allergy/condition/surgery tables outside of status changes.

### Pitfall 3: Search Performance Degradation
**What goes wrong:** Patient search takes >2 seconds as patient count grows.
**Why it happens:** Missing GIN index on pg_trgm columns, or using LIKE '%term%' instead of similarity search.
**How to avoid:** Create GIN indexes on name, MRN, phone columns. Use `similarity()` function from pg_trgm extension. Test with 100K+ synthetic patient records.
**Warning signs:** EXPLAIN ANALYZE shows sequential scan instead of index scan.

### Pitfall 4: Transaction Boundary Leaks
**What goes wrong:** Partial patient registration data committed — demographics saved but emergency contacts lost.
**Why it happens:** Service calls `commit()` mid-transaction, or `flush()` is missing before reading back data.
**How to avoid:** Services always `flush()`. Only the API endpoint calls `commit()` after all operations succeed. Wrap multi-step operations in a single transaction.
**Warning signs:** Tests that create patients with contacts but contacts are sometimes NULL.

### Pitfall 5: SQLite Test vs PostgreSQL Search Mismatch
**What goes wrong:** pg_trgm search tests pass in development but fail in production because SQLite doesn't support pg_trgm.
**Why it happens:** SQLite in-memory tests can't replicate PostgreSQL-specific features.
**How to avoid:** Mark pg_trgm search tests as `@pytest.mark.postgresql` and run them against a real PostgreSQL test database. Use `pytest-postgresql` or Docker-based test runner for search tests. Keep non-search tests on SQLite.
**Warning signs:** Tests using `similarity()` function fail with "no such function" on SQLite.

### Pitfall 6: Missing Audit Log for Search Queries
**What goes wrong:** HIPAA audit trail is incomplete — patient mutations are logged but searches are not.
**Why it happens:** Focus on mutation auditing (create/update/delete) but forget that search itself is a PHI access event.
**How to avoid:** Log every patient search query with: who searched, what query terms, how many results returned, timestamp. D-68 explicitly requires this.
**Warning signs:** Audit logs show patient updates but no search events.

### Pitfall 7: Emergency Contact / Next of Kin Confusion
**What goes wrong:** Emergency contacts and next of kin are modeled as the same thing.
**Why it happens:** They seem similar but have different legal meanings (D-42 vs D-43).
**How to avoid:** Separate tables. Emergency contacts: up to 3, for medical emergencies. Next of kin: single legal designation, for legal/financial decisions. Different fields, different relationships.
**Warning signs:** Single "contacts" table with a type discriminator instead of two separate tables.

## Code Examples

### MRN Generation Service

```python
# Source: PostgreSQL sequence pattern, [ASSUMED] based on standard PostgreSQL sequence usage

class MRNService:
    """Generate unique MRNs using PostgreSQL sequences.

    Each facility has its own sequence (e.g., LAG_SEQ for Lagos).
    MRN format: {PREFIX}-{000001} (D-01, D-02).
    """

    @staticmethod
    async def generate_mrn(
        db: AsyncSession,
        facility_prefix: str = "LAG",
    ) -> str:
        """Generate next MRN for the given facility.

        Uses PostgreSQL nextval() for ACID-compliant sequence generation.
        No check digit (D-02). Never reused (D-05).
        """
        # Ensure sequence exists for this facility
        seq_name = f"mrn_seq_{facility_prefix.lower()}"
        await db.execute(
            text(f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = '{seq_name}') THEN
                        CREATE SEQUENCE {seq_name} START 1;
                    END IF;
                END
                $$;
            """)
        )

        # Get next value
        result = await db.execute(text(f"SELECT nextval('{seq_name}')"))
        next_val = result.scalar()

        # Format: PREFIX-NNNNNN (6 digits, zero-padded)
        return f"{facility_prefix}-{next_val:06d}"

    @staticmethod
    async def validate_mrn_format(mrn: str) -> bool:
        """Validate MRN format: PREFIX-NNNNNN where PREFIX is alphabetic."""
        import re
        return bool(re.match(r"^[A-Z]{2,5}-\d{6}$", mrn))
```

### pg_trgm Patient Search

```python
# Source: PostgreSQL pg_trgm extension, [ASSUMED] standard usage pattern

class PatientSearchService:
    """Full-text patient search using PostgreSQL pg_trgm.

    D-15: pg_trgm for Phase 2 (Elasticsearch upgrade path later).
    D-16: 300ms debounce on frontend.
    D-19: 4 characters minimum before search triggers.
    D-20: 50 results per page.
    D-68: Log every search for HIPAA audit.
    """

    @staticmethod
    async def search_patients(
        db: AsyncSession,
        query: str,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Patient], int]:
        """Search patients by name, MRN, phone, or DOB.

        Uses pg_trgm similarity for fuzzy matching.
        Returns (patients, total_count) for pagination.
        """
        if len(query) < 4:
            raise ValueError("Search query must be at least 4 characters")

        # Build search condition using pg_trgm similarity
        search_pattern = f"%{query}%"
        stmt = (
            select(Patient)
            .where(
                or_(
                    Patient.mrn.ilike(search_pattern),
                    func.similarity(Patient.first_name, query) > 0.3,
                    func.similarity(Patient.last_name, query) > 0.3,
                    Patient.phone.ilike(search_pattern),
                    Patient.first_name.ilike(search_pattern),
                    Patient.last_name.ilike(search_pattern),
                )
            )
            .order_by(
                func.greatest(
                    func.similarity(Patient.first_name, query),
                    func.similarity(Patient.last_name, query),
                ).desc()
            )
        )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar()

        # Paginate
        offset = (page - 1) * page_size
        result = await db.execute(stmt.offset(offset).limit(page_size))
        patients = list(result.scalars().all())

        # D-68: Audit every search
        await AuditService.log_event(
            db,
            user_id=user_id,
            action="patient_search",
            resource="patient",
            extra_data={"query": query, "results_count": total, "page": page},
            why="Patient search",
        )

        return patients, total
```

### Multi-Step Registration Wizard (HTMX)

```html
<!-- Source: Following app/templates/admin/roles.html HTMX pattern -->
<!-- D-40: Multi-step wizard — Step 1 (Demographics), Step 2 (Contacts), Step 3 (Insurance), Step 4 (Medical History) -->

<!-- Step indicator -->
<div class="steps">
  <div class="step active" id="step-indicator-1">1. Demographics</div>
  <div class="step" id="step-indicator-2">2. Contacts</div>
  <div class="step" id="step-indicator-3">3. Insurance</div>
  <div class="step" id="step-indicator-4">4. Medical History</div>
</div>

<!-- Step 1: Demographics -->
<div id="step-1" class="step-content">
  <form hx-post="/api/v1/patients/register/step1"
        hx-target="#step-2"
        hx-swap="innerHTML"
        hx-indicator="#step1-indicator">
    <!-- Name fields -->
    <div class="form-row">
      <div class="form-group">
        <label for="first_name">First Name *</label>
        <input type="text" id="first_name" name="first_name" required maxlength="100">
      </div>
      <div class="form-group">
        <label for="last_name">Last Name *</label>
        <input type="text" id="last_name" name="last_name" required maxlength="100">
      </div>
    </div>
    <!-- DOB, Gender, Phone, Address... -->
    <button type="submit" class="btn btn-primary">Next: Contacts →</button>
  </form>
</div>

<!-- Step container for HTMX swap -->
<div id="step-2"></div>
<div id="step-3"></div>
<div id="step-4"></div>
```

### Insurance Policy Lifecycle

```python
# Source: [ASSUMED] standard state machine pattern for insurance lifecycle
# D-24: pending → verified → active → expired

class InsuranceService:
    VALID_TRANSITIONS = {
        "pending": ["verified", "expired"],
        "verified": ["active", "expired"],
        "active": ["expired"],
        "expired": [],  # Terminal state
    }

    @staticmethod
    async def transition_status(
        db: AsyncSession,
        policy_id: uuid.UUID,
        new_status: str,
        changed_by: uuid.UUID,
    ) -> InsurancePolicy:
        """Transition insurance policy status with validation."""
        policy = await db.get(InsurancePolicy, policy_id)
        if policy is None:
            raise ValueError("Policy not found")

        valid = InsuranceService.VALID_TRANSITIONS.get(policy.status, [])
        if new_status not in valid:
            raise ValueError(
                f"Cannot transition from '{policy.status}' to '{new_status}'. "
                f"Valid transitions: {valid}"
            )

        old_status = policy.status
        policy.status = new_status
        if new_status == "verified":
            policy.verified_at = datetime.now(UTC)
            policy.verified_by = changed_by
        elif new_status == "active":
            policy.activated_at = datetime.now(UTC)
        elif new_status == "expired":
            policy.expired_at = datetime.now(UTC)

        await AuditService.log_event(
            db, user_id=changed_by,
            action="insurance_status_changed",
            resource="insurance_policy",
            resource_id=str(policy.id),
            patient_id=policy.patient_id,
            extra_data={"old_status": old_status, "new_status": new_status},
        )
        await db.flush()
        return policy
```

### Visit History Timeline

```python
# Source: [ASSUMED] standard chronological display pattern
# D-35: 5-state lifecycle, D-36: auto-calculated duration, D-37: standardized reasons

class VisitService:
    VALID_TRANSITIONS = {
        "scheduled": ["checked-in", "cancelled"],
        "checked-in": ["in-progress", "cancelled"],
        "in-progress": ["completed"],
        "completed": [],  # Terminal state
        "cancelled": [],  # Terminal state
    }

    VISIT_REASONS = [
        "consultation", "follow-up", "procedure",
        "emergency", "lab", "vaccination", "other",
    ]

    @staticmethod
    async def create_walkin_visit(
        db: AsyncSession,
        patient_id: uuid.UUID,
        department_id: uuid.UUID,
        reason: str,
        created_by: uuid.UUID,
    ) -> Visit:
        """Create a walk-in visit for front desk (D-34: manual creation)."""
        if reason not in VisitService.VISIT_REASONS:
            raise ValueError(f"Invalid reason: {reason}. Must be one of {VisitService.VISIT_REASONS}")

        visit = Visit(
            patient_id=patient_id,
            department_id=department_id,
            reason=reason,
            status="scheduled",  # Will transition to checked-in immediately
            created_by=created_by,
        )
        db.add(visit)
        await db.flush()

        # Auto check-in for walk-ins
        visit.status = "checked-in"
        visit.checked_in_at = datetime.now(UTC)

        await AuditService.log_event(
            db, user_id=created_by,
            action="walkin_visit_created",
            resource="visit",
            resource_id=str(visit.id),
            patient_id=patient_id,
            why="Walk-in patient registration",
        )
        await db.flush()
        return visit
```

### Bulk CSV Import Validation

```python
# Source: [ASSUMED] standard CSV import pattern with validation preview
# D-56: CSV bulk patient import with validation, preview, and error reporting

class PatientImportService:
    REQUIRED_COLUMNS = [
        "first_name", "last_name", "date_of_birth", "gender",
        "phone", "address_street", "address_city", "address_state",
    ]

    @staticmethod
    async def preview_import(
        db: AsyncSession,
        csv_content: str,
        user_id: uuid.UUID,
    ) -> dict:
        """Parse CSV, validate rows, return preview with errors.

        Returns: {
            "total_rows": int,
            "valid_rows": int,
            "error_rows": int,
            "preview": [...first 10 valid rows...],
            "errors": [...first 10 error rows with reasons...],
            "duplicate_warnings": [...name+DOB matches...],
        }
        """
        import csv
        import io

        reader = csv.DictReader(io.StringIO(csv_content))
        errors = []
        preview = []
        duplicates = []
        valid_count = 0

        for i, row in enumerate(reader):
            # Validate required columns
            missing = [col for col in PatientImportService.REQUIRED_COLUMNS if not row.get(col)]
            if missing:
                errors.append({"row": i + 1, "errors": [f"Missing: {', '.join(missing)}"]})
                continue

            # Validate with Pydantic
            try:
                PatientCreate(**row)
                valid_count += 1
                if len(preview) < 10:
                    preview.append(row)
                # Check for duplicates (D-53)
                dup = await PatientService._check_duplicate_by_name_dob(
                    db, row["first_name"], row["last_name"], row["date_of_birth"]
                )
                if dup:
                    duplicates.append({"row": i + 1, "existing_patient_id": str(dup.id)})
            except ValidationError as e:
                errors.append({"row": i + 1, "errors": [str(err) for err in e.errors()]})

        return {
            "total_rows": i + 1,
            "valid_rows": valid_count,
            "error_rows": len(errors),
            "preview": preview,
            "errors": errors[:10],
            "duplicate_warnings": duplicates[:10],
        }
```

### Alembic Migration Pattern

```python
# Source: Following alembic/versions/e1250935c5f1_initial_auth_tables.py pattern

"""add_patient_management_tables

Revision ID: a3b4c5d6e7f8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-15
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a3b4c5d6e7f8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pg_trgm extension
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Create patients table
    op.create_table(
        "patients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("mrn", sa.String(20), unique=True, nullable=False, index=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("date_of_birth", sa.Date, nullable=False),
        sa.Column("gender", sa.String(10), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        # ... more columns
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create GIN indexes for pg_trgm search
    op.execute("""
        CREATE INDEX ix_patient_name_trgm ON patients
        USING gin ((first_name || ' ' || last_name) gin_trgm_ops)
    """)
    op.execute("""
        CREATE INDEX ix_patient_mrn_trgm ON patients
        USING gin (mrn gin_trgm_ops)
    """)
    op.execute("""
        CREATE INDEX ix_patient_phone_trgm ON patients
        USING gin (phone gin_trgm_ops)
    """)

    # Add FK constraints to existing tables
    op.alter_column(
        "audit_logs", "patient_id",
        sa.ForeignKey("patients.id", ondelete="SET NULL"),
    )
    op.alter_column(
        "break_glass_access", "patient_id",
        sa.ForeignKey("patients.id", ondelete="CASCADE"),
    )

    # Create remaining tables...
    # (allergies, conditions, surgeries, family_history, etc.)


def downgrade() -> None:
    op.drop_table("patients")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| LIKE '%term%' for search | pg_trgm GIN indexes with similarity() | PostgreSQL 9.1+ (2011) | 10-100x faster fuzzy search |
| Application-level ID generation | Database sequences | Always standard | ACID guarantees, no race conditions |
| Mutable records with UPDATE | Append-only with version linking | Healthcare compliance standard | Full audit trail, never lose data |
| Separate search services (Solr/ES) | pg_trgm for <100K records | PostgreSQL 9.1+ | No infrastructure overhead, one database |

**Deprecated/outdated:**
- UUID-based MRNs: Not human-readable, not sequential, not suitable for hospital staff (D-02: no check digit either)
- Single-table medical history with type discriminator: Wasteful NULLs, poor type-specific queries
- Application-level fuzzy matching: Slow, no index support, doesn't scale

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | pg_trgm GIN indexes provide <50ms search on 100K patients | Patient Search | May need Elasticsearch upgrade sooner than planned |
| A2 | reportlab 4.5.1 is sufficient for patient profile PDF exports | Data Export | May need weasyprint if complex layouts required |
| A3 | SQLite in-memory tests can use mock for pg_trgm search tests | Testing | Search tests need PostgreSQL test database |
| A4 | PostgreSQL sequences survive server restarts without data loss | MRN Generation | Would need sequence recreation logic |
| A5 | Nigerian phone format regex `^(\+234|0)[789]\d{9}$` covers all valid numbers | Validation | Some edge cases may be rejected |
| A6 | Walk-in visits start in "scheduled" status then immediately transition to "checked-in" | Visit Lifecycle | Could instead start directly in "checked-in" |
| A7 | Medical history append-only means no DELETE permission for clinical data | Medical History | Soft-delete with status='deleted' may be needed for admin override |

## Open Questions

1. **Facility prefix configuration:** Where does the facility prefix mapping live? Is it in the database (facility table), environment variable, or settings file?
   - What we know: D-01 says "configurable per facility via settings"
   - What's unclear: Is "settings" a database table, .env file, or Pydantic Settings?
   - Recommendation: Create a simple `facilities` table with `id`, `name`, `prefix`, `is_active` columns. Seed with Lagos facility. This allows admin UI for adding new facilities later.

2. **Consent form templates:** D-55 mentions "configurable consent form templates" — what's the template content?
   - What we know: Digital consent or paper upload required
   - What's unclear: What templates exist, what fields they contain
   - Recommendation: Start with a simple `consent_templates` table (name, content_json, is_active). Default template is a standard Nigerian healthcare consent. Paper upload stored as file reference.

3. **Visit summary auto-generation:** D-38 says "auto-generated (configurable by admin)" — what triggers generation?
   - What we know: Summary includes date, doctor, diagnosis, prescriptions
   - What's unclear: Is it generated at visit completion? On demand? Template-driven?
   - Recommendation: Generate on visit status → "completed". Use a Jinja2 template for the summary content. Store as JSONB in visit_summaries table.

4. **Photo upload storage:** D-44 mentions patient photo capture — where are photos stored?
   - What we know: Optional photo during registration
   - What's unclear: Local filesystem vs S3 vs database blob
   - Recommendation: Local filesystem in `uploads/patients/` directory for Phase 2. URL stored in `photo_url` column. S3 migration later.

## Validation Architecture

> Note: No `.planning/config.json` found — treating nyquist_validation as enabled.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (async) |
| Config file | pytest.ini / pyproject.toml (none detected — configure in Wave 0) |
| Quick run command | `pytest tests/test_patient*.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PAT-01 | Patient registration with full demographics | integration | `pytest tests/test_patient.py::test_register_patient -x` | ❌ Wave 0 |
| PAT-01 | Nigerian phone validation | unit | `pytest tests/test_patient.py::test_phone_validation -x` | ❌ Wave 0 |
| PAT-01 | Duplicate detection (name+DOB) | integration | `pytest tests/test_patient.py::test_duplicate_detection -x` | ❌ Wave 0 |
| PAT-02 | MRN auto-generation (unique, sequential) | integration | `pytest tests/test_patient.py::test_mrn_generation -x` | ❌ Wave 0 |
| PAT-02 | MRN never reused | unit | `pytest tests/test_patient.py::test_mrn_no_reuse -x` | ❌ Wave 0 |
| PAT-03 | Allergy creation (clinical-grade) | integration | `pytest test_medical_history.py::test_create_allergy -x` | ❌ Wave 0 |
| PAT-03 | Medical history append-only | integration | `pytest test_medical_history.py::test_append_only -x` | ❌ Wave 0 |
| PAT-04 | Insurance policy lifecycle | integration | `pytest test_insurance.py::test_policy_lifecycle -x` | ❌ Wave 0 |
| PAT-04 | Expired policy warning (no billing block) | unit | `pytest test_insurance.py::test_expired_policy_warning -x` | ❌ Wave 0 |
| PAT-05 | Search returns <2 seconds on 10K records | integration | `pytest test_search.py::test_search_performance -x` | ❌ Wave 0 |
| PAT-05 | 4-char minimum enforcement | unit | `pytest test_search.py::test_minimum_query_length -x` | ❌ Wave 0 |
| PAT-05 | Search audit logging | integration | `pytest test_search.py::test_search_audit_log -x` | ❌ Wave 0 |
| PAT-06 | Visit lifecycle transitions | integration | `pytest test_visit.py::test_visit_lifecycle -x` | ❌ Wave 0 |
| PAT-06 | Visit duration auto-calculation | unit | `pytest test_visit.py::test_duration_calculation -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_patient*.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_patient.py` — covers PAT-01, PAT-02 (registration, MRN)
- [ ] `tests/test_medical_history.py` — covers PAT-03 (allergies, conditions, surgeries, family history)
- [ ] `tests/test_insurance.py` — covers PAT-04 (policy lifecycle, providers)
- [ ] `tests/test_search.py` — covers PAT-05 (search performance, audit)
- [ ] `tests/test_visit.py` — covers PAT-06 (visit lifecycle, duration)
- [ ] `tests/conftest.py` — add `create_patient` factory fixture, patient-related model imports
- [ ] Alembic migration `add_patient_management_tables` — new tables + pg_trgm extension
- [ ] `app/seeds/insurance_providers.py` — seed Nigerian insurance providers (NHIS, Hygeia, Leadway, etc.)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Existing Keycloak auth from Phase 1 |
| V3 Session Management | yes | Existing session timeout from Phase 1 |
| V4 Access Control | yes | require_permission("patient", "create|read|update|delete") per endpoint |
| V5 Input Validation | yes | Pydantic models with Field validators for all patient data |
| V6 Cryptography | no | No new crypto in this phase (existing TLS for data in transit) |

### Known Threat Patterns for FastAPI + PostgreSQL Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SQL injection via search query | Tampering | SQLAlchemy ORM parameterized queries — never raw SQL with user input |
| Unauthorized patient record access | Information Disclosure | require_permission() dependency on every patient endpoint |
| PHI exposure in search results | Information Disclosure | Log every search (D-68), return only necessary fields in list view |
| MRN enumeration attack | Information Disclosure | MRN is not a secret (staff use it), but search is audit-logged |
| Bulk patient data export | Information Disclosure | Rate limiting on export endpoints, audit log with export counts |
| Patient photo path traversal | Tampering | Store photos with UUID filenames, validate file type, no user-controlled paths |
| CSV import injection | Tampering | Validate all CSV fields through Pydantic, reject suspicious content |

## Sources

### Primary (HIGH confidence)
- Existing codebase patterns (app/models/user.py, app/services/rbac.py, app/api/v1/auth.py) — direct code inspection
- Phase 1 CONTEXT.md and REQUIREMENTS.md — direct file read
- PostgreSQL pg_trgm documentation — [CITED: postgresql.org/docs/current/pgtrgm.html]

### Secondary (MEDIUM confidence)
- SQLAlchemy 2.0 documentation — [CITED: docs.sqlalchemy.org/en/20/orm/declarative_config.html]
- FastAPI dependency injection patterns — [CITED: fastapi.tiangolo.com/tutorial/dependencies/]
- Alembic migration patterns — [CITED: alembic.sqlalchemy.org/en/latest/tutorial.html]
- reportlab for PDF generation — [CITED: reportlab.com/docs/reportlab-docbook/]

### Tertiary (LOW confidence)
- Nigerian phone number format specification — [ASSUMED] based on D-47 decision context
- Nigerian insurance provider names (NHIS, Hygeia, Leadway) — [ASSUMED] from D-22 decision, should verify current providers

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages already in use, no new dependencies needed
- Architecture: HIGH — following exact Phase 1 patterns, well-understood clinical domain
- Pitfalls: HIGH — common database patterns with known solutions

**Research date:** 2026-07-15
**Valid until:** 2026-08-15 (stable — project stack is mature, no rapidly-moving dependencies)
