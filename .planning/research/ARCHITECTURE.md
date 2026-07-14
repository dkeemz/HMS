# Architecture Patterns: Hospital Health Management System (HMS)

**Domain:** Healthcare IT — Hospital Management System
**Researched:** 2026-07-12
**Scale:** 500+ doctors, multi-hospital chain
**Deployment:** Hybrid (on-premise + cloud)
**Compliance:** HIPAA + PDPA (Thailand/Malaysia)
**Overall confidence:** HIGH — based on 15+ production architectures, academic papers, and real-world case studies from 2025-2026

---

## Executive Summary

Modern hospital HMS architecture has converged on **event-driven microservices** as the dominant pattern. Research across 15+ production implementations (including Frontiers systematic review 2025, CloudEHR architecture 2026, and real-world hospital automation platforms) confirms this approach delivers the scalability, fault isolation, and independent deployment cycles that clinical environments demand.

**Critical finding:** For a 500+ doctor hospital chain, a **modular monolith with strategic microservice extraction** (Strangler Fig pattern) is the safest starting point. A "big bang" microservices rewrite has a high failure rate in healthcare due to transaction integrity requirements and zero-downtime constraints.

---

## 1. System Architecture: Monolith vs Microservices

### Recommendation: Modular Monolith → Strategic Microservice Extraction

Based on research from multiple production hospital systems, the recommended approach is a **modular monolith** with clear domain boundaries, progressively extracting services as the system matures.

**Why not pure microservices from day one:**
- Healthcare workflows have tight transactional dependencies (admission → billing → pharmacy → lab)
- "Big bang" migration from monolith to microservices in healthcare has documented failure patterns (E-hir.org 2026 case study)
- 500+ doctors require immediate stability; microservices operational overhead is significant
- HIPAA/PDPA compliance is harder to verify across dozens of independently deployed services

**Why not pure monolith:**
- Scaling bottlenecks during peak clinical hours (morning rounds)
- Single point of failure risks patient safety
- Independent team deployment impossible
- Regulatory compliance becomes a single-team bottleneck

### Hybrid Architecture (Recommended)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Web App  │  │Mobile App│  │  Kiosk   │  │ Third-Party Apps │   │
│  │ (React)  │  │(React N) │  │ (React)  │  │   (FHIR API)     │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘   │
│       └──────────────┼─────────────┼──────────────────┘              │
└──────────────────────┼─────────────┼────────────────────────────────┘
                       ▼             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    API GATEWAY LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐     │
│  │  Kong/APISIX │  │  Rate Limiter│  │  OAuth2/JWT Validator │     │
│  │  (Routing)   │  │  (Per-Role)  │  │  (SMART on FHIR)     │     │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬───────────┘     │
└─────────┼─────────────────┼──────────────────────┼──────────────────┘
          ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  APPLICATION LAYER (Modular Monolith)                │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐  │
│  │ Patient │ │ Doctor  │ │Scheduling│ │  EHR    │ │  Billing    │  │
│  │ Module  │ │ Module  │ │ Module  │ │ Module  │ │   Module    │  │
│  ├─────────┤ ├─────────┤ ├─────────┤ ├─────────┤ ├─────────────┤  │
│  │ Clinical│ │Pharmacy │ │  Lab    │ │Radiology│ │ Notification│  │
│  │ Module  │ │ Module  │ │ Module  │ │ Module  │ │   Module    │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────────┘  │
│                                                                     │
│  Each module has:                                                   │
│  - Internal API (function calls)                                    │
│  - Dedicated database schema                                        │
│  - Event publishers (for future extraction)                         │
│  - Clear domain boundaries (DDD Bounded Contexts)                   │
└─────────────────────────────────────────────────────────────────────┘
          │                 │                      │
          ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      EVENT BUS (Kafka/RabbitMQ)                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Domain Events: patient.admitted, order.placed, bill.created │   │
│  │  Integration Events: lab.result.ready, pharmacy.dispensed    │   │
│  │  Compliance Events: record.accessed, data.exported           │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
          │                 │                      │
          ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │PostgreSQL│  │ MongoDB  │  │  Redis   │  │    MinIO/S3      │   │
│  │ (ACID)   │  │(Flexible)│  │ (Cache)  │  │  (File Storage)  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Boundaries

| Component | Responsibility | Communicates With | Extraction Priority |
|-----------|---------------|-------------------|---------------------|
| **Auth Service** | JWT/OAuth2, RBAC, MFA | All services | High (extract first) |
| **Patient Service** | Demographics, identity, MPI | All clinical services | High |
| **Doctor/Department Service** | Profiles, specializations, availability | Scheduling, Auth | Medium |
| **Scheduling Service** | Appointments, availability, queue management | Patient, Doctor, Notification | Medium |
| **EHR/Clinical Service** | Encounters, notes, orders, results | All clinical services | Low (core, extract last) |
| **Billing Service** | Invoices, payments, insurance claims | EHR, Patient | High (extract early) |
| **Notification Service** | SMS, email, push, in-app | All services (pub/sub) | High (extract first) |
| **File Storage Service** | DICOM, documents, images | EHR, Lab, Radiology | Medium |
| **Integration Service** | HL7/FHIR translation, external system adapters | All services, external systems | High |

### Data Flow: Patient Admission Example

```
1. Patient arrives → Registration (Patient Service)
2. Registration publishes: patient.registered
3. Doctor assigns bed → Admission (EHR Service)
4. Admission publishes: patient.admitted
5. Billing Service receives event → creates encounter record
6. Pharmacy Service receives event → prepares medication profile
7. Lab Service receives event → queues pre-admission tests
8. Notification Service sends: admission confirmation to patient
9. All events logged to audit trail (compliance requirement)
```

---

## 2. Core Components: Detailed Design

### 2.1 Auth Service

**Pattern:** Centralized Identity & Access Management (IAM)

```
┌─────────────────────────────────────────┐
│              AUTH SERVICE                 │
│                                          │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ JWT Issuer  │  │  RBAC Engine    │   │
│  │ (RS256)     │  │  (Casbin/OPA)   │   │
│  └─────────────┘  └─────────────────┘   │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ MFA Handler │  │  Session Mgr    │   │
│  │ (TOTP/SMS)  │  │  (Redis)        │   │
│  └─────────────┘  └─────────────────┘   │
│  ┌─────────────────────────────────┐    │
│  │  Service-to-Service Auth (mTLS) │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

**Key decisions:**
- **JWT with RS256** for stateless token validation across services
- **Short-lived access tokens** (15 min) + **refresh tokens** (7 days) stored in Redis
- **Service accounts** with mTLS for inter-service authentication
- **SMART on FHIR scopes** for clinical data access (patient/Patient.read, user/Observation.write)

### 2.2 Patient Service

**Pattern:** Master Patient Index (MPI) with domain-driven design

**Responsibilities:**
- Patient registration and demographics
- Cross-system patient identity resolution (MPI)
- Insurance and contact information
- Patient preferences and consents

**Database:** PostgreSQL (ACID transactions for identity data)

**Key entities:**
- `patients` (demographics, identifiers)
- `patient_identifiers` (MRN, national ID, insurance ID)
- `patient_consents` (PDPA/HIPAA consent records)
- `patient_contacts` (emergency contacts, next of kin)

### 2.3 Doctor/Department Service

**Pattern:** Reference data service with caching

**Responsibilities:**
- Doctor profiles, specializations, credentials
- Department structure and hierarchy
- Doctor availability and scheduling preferences
- Credential verification and expiry tracking

**Database:** PostgreSQL with Redis cache for frequently accessed profiles

### 2.4 Scheduling Service

**Pattern:** Event-sourced with optimistic concurrency

**Responsibilities:**
- Appointment booking and management
- Doctor availability management
- Queue management and walk-in handling
- Recurring appointments and follow-ups
- Room/resource allocation

**Database:** PostgreSQL with Redis for real-time availability cache

**Critical constraints:**
- Optimistic locking to prevent double-booking
- Event sourcing for appointment state transitions
- Integration with external calendar systems (Google Calendar, Outlook)

### 2.5 EHR/Clinical Service

**Pattern:** CQRS (Command Query Responsibility Segregation)

**Responsibilities:**
- Clinical encounters and documentation
- Medical history and problem lists
- Orders (lab, radiology, medication)
- Clinical notes (SOAP, progress notes)
- Care plans and protocols

**Database:** PostgreSQL (commands) + Elasticsearch (queries/reports)

**Critical design:**
- **CQRS separation:** Write path optimizes for consistency, read path optimizes for clinical workflow speed
- **Version control:** Every clinical document versioned with immutable history
- **Clinical decision support hooks:** CDS Hooks integration points

### 2.6 Billing Service

**Pattern:** Saga pattern for distributed transactions

**Responsibilities:**
- Invoice generation from clinical encounters
- Payment processing (cash, card, insurance)
- Insurance claim submission and tracking
- Revenue cycle management
- Financial reporting

**Database:** PostgreSQL (ACID for financial transactions)

**Critical design:**
- **Saga orchestration:** Coordinates across EHR (charge capture), Insurance (claim submission), Payment (collection)
- **Idempotency:** Prevent duplicate charges from retries
- **Dual-write prevention:** Use outbox pattern for event publishing

### 2.7 Notification Service

**Pattern:** Pub/sub with channel abstraction

**Responsibilities:**
- Multi-channel delivery (SMS, email, push, in-app)
- Template management and localization
- Delivery tracking and retry logic
- Rate limiting per channel
- HIPAA-compliant messaging (no PHI in notifications)

**Database:** MongoDB (flexible template storage) + Redis (delivery queue)

### 2.8 File Storage Service

**Pattern:** Object storage with metadata indexing

**Responsibilities:**
- DICOM image storage and retrieval
- Clinical document storage (PDF, images)
- Lab result PDFs and reports
- Patient-uploaded files
- Version control and retention management

**Storage:** MinIO (S3-compatible, on-premise) + cloud backup

**Critical design:**
- **Separation of metadata and content:** Metadata in PostgreSQL, files in object storage
- **Lazy loading:** Large files (DICOM) streamed, not loaded entirely into memory
- **Retention enforcement:** Automated lifecycle policies per document type

---

## 3. Data Architecture

### 3.1 Database Strategy: Schema-per-Module (Not Database-per-Service)

For a modular monolith, use **schema-per-module** within a shared PostgreSQL cluster:

```
┌─────────────────────────────────────┐
│         PostgreSQL Cluster           │
│                                      │
│  ┌──────────┐  ┌──────────┐        │
│  │  auth    │  │ patient  │        │
│  │  schema  │  │  schema  │        │
│  └──────────┘  └──────────┘        │
│  ┌──────────┐  ┌──────────┐        │
│  │  ehr     │  │ billing  │        │
│  │  schema  │  │  schema  │        │
│  └──────────┘  └──────────┘        │
│  ┌──────────┐  ┌──────────┐        │
│  │schedule  │  │  lab     │        │
│  │  schema  │  │  schema  │        │
│  └──────────┘  └──────────┘        │
│  ┌──────────────────────────┐      │
│  │   audit_log (append-only)│      │
│  └──────────────────────────┘      │
└─────────────────────────────────────┘
```

**Why schema-per-module, not database-per-service:**
- Easier transaction management across modules during monolith phase
- Simpler backup and recovery
- Lower operational overhead
- Clean extraction path when services are extracted later

**Why not shared schema:**
- Schema-per-module enforces boundary discipline
- Prevents accidental cross-module queries
- Enables clean service extraction without data migration

### 3.2 Data Normalization for Medical Records

Medical data requires careful normalization balancing clinical accuracy with query performance:

**Highly normalized (3NF+):**
- Patient demographics
- Doctor profiles
- Department structure
- Insurance plans
- Reference data (ICD codes, SNOMED, LOINC)

**Denormalized for performance:**
- Clinical encounter summaries (materialized views)
- Billing line items (denormalized from clinical orders)
- Appointment history (denormalized for quick display)
- Lab result trends (pre-computed aggregations)

**Document-style (flexible schema):**
- Clinical notes (variable structure per specialty)
- Radiology reports
- Lab results (different test types have different fields)
- Discharge summaries

### 3.3 Audit Logging Architecture

HIPAA and PDPA both require comprehensive, tamper-evident audit trails.

```
┌─────────────────────────────────────────────────────────────┐
│                    AUDIT LOGGING PIPELINE                     │
│                                                              │
│  Application Layer                                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Every service emits structured audit events:         │   │
│  │  {                                                    │   │
│  │    "timestamp": "2026-07-12T10:30:00Z",              │   │
│  │    "actor": "dr.smith@hospital.com",                 │   │
│  │    "action": "VIEW",                                  │   │
│  │    "resource": "Patient/12345",                      │   │
│  │    "resource_type": "Patient",                       │   │
│  │    "fields_accessed": ["name", "dob", "diagnosis"],  │   │
│  │    "purpose": "clinical_care",                       │   │
│  │    "ip_address": "10.0.1.100",                       │   │
│  │    "session_id": "abc-123",                          │   │
│  │    "correlation_id": "req-xyz-789"                   │   │
│  │  }                                                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Event Bus (Kafka) — audit.audit.log topic            │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│              ┌───────────┼───────────┐                      │
│              ▼           ▼           ▼                      │
│  ┌──────────────┐ ┌──────────┐ ┌──────────────┐           │
│  │ Append-Only  │ │ SIEM     │ │ Compliance   │           │
│  │ Audit Store  │ │ (Splunk/ │ │ Dashboard    │           │
│  │ (Immutable)  │ │ ELK)     │ │ (Grafana)    │           │
│  └──────────────┘ └──────────┘ └──────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

**Key requirements:**
- **Append-only:** Audit logs cannot be modified or deleted (HIPAA §164.312(b))
- **Tamper-evident:** Hash chain or blockchain-style integrity verification
- **PHI-free shipping:** Audit logs shipped to SIEM without PHI (only metadata)
- **Retention:** Minimum 6 years (HIPAA) / varies by PDPA jurisdiction
- **Real-time alerting:** Anomalous access patterns trigger immediate alerts

### 3.4 Data Retention and Archival

| Data Type | Active Retention | Archive Retention | Destruction Method |
|-----------|-----------------|-------------------|-------------------|
| Patient Demographics | Until patient inactive + 10 years | 10-25 years | Anonymize after legal period |
| Clinical Records | 10 years from last visit | 25 years | Certified digital destruction |
| Lab Results | 10 years | 25 years | Certified digital destruction |
| Billing Records | 7 years | 10 years | Certified digital destruction |
| Audit Logs | 6 years (HIPAA minimum) | 10 years | Immutable archive |
| CCTV Footage | 30 days | None | Auto-overwrite |
| Consent Records | Duration of consent + 5 years | 10 years | Certified destruction |
| Staff Records | Duration of employment + 7 years | 10 years | Certified destruction |

**Archival strategy:**
- **Hot tier (0-2 years):** Primary database, full query capability
- **Warm tier (2-10 years):** Compressed archive, query-on-demand
- **Cold tier (10+ years):** Object storage (MinIO/S3), read-only
- **Destruction:** Automated lifecycle policies with manual approval gates

---

## 4. Security Architecture

### 4.1 Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   AUTHENTICATION FLOW                         │
│                                                              │
│  User Login                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ Username │───▶│  Auth    │───▶│   MFA    │              │
│  │ + Pass   │    │ Service  │    │ (TOTP/   │              │
│  └──────────┘    │ (Verify) │    │  SMS)    │              │
│                  └──────────┘    └────┬─────┘              │
│                                       │                      │
│                                       ▼                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  JWT Token Issued (RS256)                             │   │
│  │  {                                                    │   │
│  │    "sub": "dr.smith@hospital.com",                   │   │
│  │    "role": "doctor",                                  │   │
│  │    "department": "cardiology",                        │   │
│  │    "scopes": ["patient:read", "order:write"],        │   │
│  │    "hospital": "hospital-main",                       │   │
│  │    "exp": 1689184200,                                │   │
│  │    "iat": 1689183300                                 │   │
│  │  }                                                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Token Validation (Every Request)                     │   │
│  │  1. API Gateway validates signature (RS256 public)   │   │
│  │  2. Check expiration                                  │   │
│  │  3. Extract scopes and roles                          │   │
│  │  4. Forward to service with X-Auth headers            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Authorization Model (RBAC for Hospital Roles)

```
┌─────────────────────────────────────────────────────────────┐
│                    RBAC HIERARCHY                             │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  super_admin                                        │    │
│  │  └── hospital_admin                                 │    │
│  │      ├── department_head                            │    │
│  │      │   ├── doctor                                 │    │
│  │      │   │   └── resident                           │    │
│  │      │   ├── nurse_manager                          │    │
│  │      │   │   └── nurse                              │    │
│  │      │   └── lab_technician                         │    │
│  │      ├── billing_manager                            │    │
│  │      │   └── billing_clerk                          │    │
│  │      ├── pharmacist                                 │    │
│  │      └── receptionist                               │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Permission Matrix (Examples):                               │
│  ┌──────────────┬─────────┬─────────┬─────────┬──────────┐ │
│  │ Role         │ Patient │ EHR     │ Billing │ Pharmacy │ │
│  ├──────────────┼─────────┼─────────┼─────────┼──────────┤ │
│  │ Doctor       │ R/W     │ R/W     │ R       │ R        │ │
│  │ Nurse        │ R       │ R/W     │ -       │ R        │ │
│  │ Receptionist │ R/W     │ R       │ R       │ -        │ │
│  │ Billing      │ R       │ R       │ R/W     │ -        │ │
│  │ Pharmacist   │ R       │ R       │ -       │ R/W      │ │
│  │ Lab Tech     │ R       │ R/W     │ -       │ -        │ │
│  │ Admin        │ R       │ R       │ R       │ R        │ │
│  └──────────────┴─────────┴─────────┴─────────┴──────────┘ │
│                                                              │
│  R = Read, W = Write, - = No Access                         │
└─────────────────────────────────────────────────────────────┘
```

**Key authorization patterns:**
- **Attribute-Based Access Control (ABAC):** Patient data access scoped by department, shift, and patient assignment
- **Break-the-glass:** Emergency access with mandatory justification logging
- **Time-based:** Access restricted to active shifts only
- **Location-based:** On-premise access for clinical data, VPN for remote

### 4.3 Data Encryption

**At Rest:**
- **Database:** AES-256 encryption (PostgreSQL Transparent Data Encryption)
- **File Storage:** AES-256 server-side encryption (MinIO/S3 SSE)
- **Backups:** AES-256 encrypted before storage
- **Key Management:** Centralized KMS (HashiCorp Vault or cloud KMS)
- **Column-level:** Sensitive fields (SSN, diagnosis codes) use application-level encryption

**In Transit:**
- **Client → Gateway:** TLS 1.3 mandatory
- **Gateway → Services:** mTLS (mutual TLS) via service mesh
- **Service → Database:** TLS 1.2+ with certificate pinning
- **External Integrations:** TLS 1.3 with certificate validation
- **Message Broker:** TLS encryption for Kafka/RabbitMQ connections

### 4.4 Audit Trail Implementation

**Immutable audit log with hash chain:**

```
Event N:
  data: { ... }
  previous_hash: hash(Event N-1)
  hash: SHA256(data + previous_hash + timestamp)

This creates a tamper-evident chain. Any modification to historical
events breaks the chain and is detectable.
```

**Storage strategy:**
- **Primary:** Dedicated append-only PostgreSQL table (audit_log)
- **Replication:** Real-time replication to separate audit database
- **Archive:** Periodic export to immutable object storage (WORM)
- **Retention:** 6-10 years depending on jurisdiction

### 4.5 HIPAA + PDPA Compliance Patterns

| Requirement | HIPAA | PDPA | Implementation |
|-------------|-------|------|----------------|
| Consent | BAA + patient authorization | Explicit consent (Section 26) | Consent management module with granular consent tracking |
| Access Control | §164.312(a) - Minimum necessary | Section 37 - Appropriate security | RBAC + ABAC with break-the-glass logging |
| Audit | §164.312(b) - Audit controls | Section 39 - Record keeping | Immutable audit log with hash chain |
| Encryption | §164.312(a)(2)(iv) - Encryption | Section 37 - Technical safeguards | AES-256 at rest, TLS 1.3 in transit |
| Breach Notification | 60 days to HHS | 72 hours to PDPC | Automated breach detection with notification workflow |
| Data Retention | 6 years minimum | Purpose-limited retention | Automated lifecycle with manual approval gates |
| Cross-border | BAA required | Section 28-29 - Transfer rules | Data residency controls with transfer impact assessment |
| Right to Access | §164.524 - Access rights | Section 30 - Access rights | Self-service patient portal with data export |
| Right to Deletion | Limited (state laws) | Section 33 - Erasure rights | Anonymization pipeline with legal hold checks |

---

## 5. Integration Architecture

### 5.1 API Gateway Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                    API GATEWAY (Kong/APISIX)                  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Layer 1: Security                                    │   │
│  │  - JWT validation (RS256)                             │   │
│  │  - Rate limiting (per-role, per-tenant)               │   │
│  │  - IP whitelisting                                    │   │
│  │  - DDoS protection                                    │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Layer 2: Routing                                     │   │
│  │  - Path-based routing (/api/patient/* → PatientSvc)   │   │
│  │  - FHIR-aware routing (/fhir/* → FHIR Facade)        │   │
│  │  - Load balancing (round-robin, least-connections)    │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Layer 3: Transformation                              │   │
│  │  - Request/response logging                           │   │
│  │  - Header injection (X-Request-ID, X-Tenant-ID)      │   │
│  │  - Protocol translation (REST ↔ HL7/FHIR)            │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Layer 4: Observability                               │   │
│  │  - Request metrics (latency, error rate)              │   │
│  │  - Audit logging (PHI-safe)                           │   │
│  │  - Distributed tracing (OpenTelemetry)                │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Event-Driven vs Request-Response

**Use synchronous (REST/gRPC) when:**
- Real-time response needed (patient lookup, authentication)
- Simple CRUD operations
- Clinical workflow requires immediate confirmation
- Transaction integrity is critical (billing, orders)

**Use asynchronous (Kafka/events) when:**
- Fan-out to multiple consumers (patient admitted → billing, pharmacy, lab)
- Decoupling services for resilience
- Audit logging (non-blocking)
- Notification delivery (email, SMS, push)
- Data synchronization between systems

**Saga pattern for distributed transactions:**

```
Patient Admission Saga:
1. Patient Service: Create admission record
2. Billing Service: Create encounter (compensate: cancel encounter)
3. Pharmacy Service: Create medication profile (compensate: remove profile)
4. Notification Service: Send admission alert (compensate: send cancellation)
5. Lab Service: Queue pre-admission tests (compensate: cancel tests)

If step 3 fails:
- Compensate step 2: Cancel encounter
- Compensate step 1: Cancel admission
- Retry with error handling
```

### 5.3 External System Integration

```
┌─────────────────────────────────────────────────────────────┐
│                EXTERNAL INTEGRATION LAYER                     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  HL7/FHIR Integration Service                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │ HL7 v2      │  │ FHIR R4     │  │ C-CDA       │  │   │
│  │  │ Adapter     │  │ Facade      │  │ Adapter     │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  External Systems:                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Lab     │  │Pharmacy  │  │Insurance │  │  Other   │   │
│  │  (LIS)   │  │  (PIS)   │  │  (HMO)   │  │ Hospitals│   │
│  │ HL7 v2   │  │ HL7 v2   │  │ X12/EDI  │  │ FHIR R4  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Integration Patterns                                 │   │
│  │  - Adapter Pattern: Each external system has adapter  │   │
│  │  - Circuit Breaker: Prevent cascading failures        │   │
│  │  - Retry with Backoff: Handle transient failures      │   │
│  │  - Dead Letter Queue: Capture failed messages         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 5.4 HL7/FHIR Standards Implementation

**FHIR R4 as primary API standard:**

| Resource | Usage | Notes |
|----------|-------|-------|
| Patient | Patient demographics and identity | Core resource, always FHIR |
| Encounter | Clinical encounters | Maps to ADT messages |
| Observation | Lab results, vital signs | Maps to HL7 v2 OBX segments |
| Condition | Diagnoses, problem lists | SNOMED/ICD coded |
| MedicationRequest | Prescriptions | Maps to HL7 v2 ORM messages |
| ServiceRequest | Lab/radiology orders | Maps to HL7 v2 ORM messages |
| DiagnosticReport | Lab/radiology reports | Maps to HL7 v2 ORU messages |
| Appointment | Scheduling | Maps to HL7 v2 SIU messages |
| Claim | Insurance claims | X12 837/835 mapping |

**HL7 v2 to FHIR mapping strategy:**
- **FHIR Facade pattern:** Expose FHIR R4 API on top of existing HL7 v2 systems
- **Translation engine:** Map HL7 v2 segments to FHIR resources
- **Terminology service:** Centralized code system translation (SNOMED, LOINC, ICD)
- **Validation pipeline:** Validate FHIR resources against US Core profiles

**Key FHIR capabilities to implement:**
- **REST API:** CRUD + Search for all clinical resources
- **SMART on FHIR:** OAuth2 authorization for third-party apps
- **FHIR Subscriptions:** Real-time notifications for resource changes
- **Bulk Data Export:** Nightly analytics and reporting
- **CDS Hooks:** Clinical decision support integration

---

## 6. Deployment Architecture: Hybrid (On-Premise + Cloud)

```
┌─────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT TOPOLOGY                        │
│                                                              │
│  ON-PREMISE (Hospital)                                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │Kubernetes│  │PostgreSQL│  │  Redis   │          │   │
│  │  │Cluster   │  │Primary   │  │  Cache   │          │   │
│  │  │(26 pods) │  │(Primary) │  │          │          │   │
│  │  └──────────┘  └──────────┘  └──────────┘          │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │  Kafka   │  │  MinIO   │  │  Kong    │          │   │
│  │  │ (Events) │  │ (Files)  │  │ (Gateway)│          │   │
│  │  └──────────┘  └──────────┘  └──────────┘          │   │
│  │                                                      │   │
│  │  All PHI stays on-premise (data sovereignty)        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  CLOUD (AWS/Azure/GCP)                                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │Kubernetes│  │PostgreSQL│  │  Redis   │          │   │
│  │  │Cluster   │  │(Read     │  │  (Dista- │          │   │
│  │  │(DR/Front)│  │ Replica) │  │  nced)   │          │   │
│  │  └──────────┘  └──────────┘  └──────────┘          │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │Patient   │  │Analytics │  │ Backup   │          │   │
│  │  │Portal    │  │Engine    │  │ Storage  │          │   │
│  │  └──────────┘  └──────────┘  └──────────┘          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Network: VPN/Direct Connect between on-premise and cloud   │
│  Replication: Async replication for DR, sync for reads       │
└─────────────────────────────────────────────────────────────┘
```

**Why this hybrid approach:**
- **Data sovereignty:** PHI stays on-premise (PDPA/HIPAA requirement)
- **Disaster recovery:** Cloud provides geo-redundant backup
- **Patient portal:** Cloud-hosted for external access without VPN
- **Analytics:** Cloud provides elastic compute for reporting
- **Scalability:** Cloud handles peak loads (annual checkup seasons)

---

## 7. Observability Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY STACK                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Metrics (Prometheus + Grafana)                       │   │
│  │  - Request rate, latency, error rate per service      │   │
│  │  - Database connection pool utilization               │   │
│  │  - Kafka consumer lag                                 │   │
│  │  - Clinical workflow KPIs (avg wait time, etc.)       │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Logging (ELK/Seq)                                    │   │
│  │  - Structured JSON logs with correlation IDs          │   │
│  │  - PHI-safe logging (no patient data in logs)         │   │
│  │  - Audit log aggregation                              │   │
│  │  - Error pattern detection                            │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Tracing (Jaeger/Zipkin)                              │   │
│  │  - Distributed tracing across services                │   │
│  │  - Request flow visualization                         │   │
│  │  - Performance bottleneck identification              │   │
│  │  - Clinical workflow tracing                          │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Alerting (PagerDuty/Opsgenie)                        │   │
│  │  - Service health alerts                              │   │
│  │  - Database replication lag                           │   │
│  │  - Security event alerts                              │   │
│  │  - Clinical system downtime alerts                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Suggested Build Order

### Phase 1: Foundation (Months 1-3)
**Goal:** Core infrastructure and authentication

| Component | Priority | Dependencies | Parallel? |
|-----------|----------|--------------|-----------|
| Auth Service | Critical | None | Yes |
| Patient Service | Critical | Auth | Yes |
| API Gateway | Critical | Auth | Yes |
| Database Infrastructure | Critical | None | Yes |
| Audit Logging | Critical | None | Yes |
| Kubernetes Cluster | Critical | None | Yes |

**Critical path:** Auth → Patient Service → API Gateway

### Phase 2: Clinical Core (Months 3-6)
**Goal:** Core clinical workflow

| Component | Priority | Dependencies | Parallel? |
|-----------|----------|--------------|-----------|
| EHR/Clinical Service | Critical | Patient, Auth | No (sequential) |
| Doctor/Department Service | High | Auth | Yes |
| Scheduling Service | High | Patient, Doctor | Yes |
| Notification Service | High | Auth | Yes |
| File Storage Service | High | Auth | Yes |

**Critical path:** EHR Service (blocks all clinical workflows)

### Phase 3: Operations (Months 6-9)
**Goal:** Billing and operational features

| Component | Priority | Dependencies | Parallel? |
|-----------|----------|--------------|-----------|
| Billing Service | Critical | EHR, Patient | No |
| Lab Integration | High | EHR, File Storage | Yes |
| Pharmacy Integration | High | EHR | Yes |
| Radiology Integration | High | EHR, File Storage | Yes |
| Reporting Engine | Medium | All services | Yes |

**Critical path:** Billing Service (revenue cycle)

### Phase 4: Integration (Months 9-12)
**Goal:** External system integration

| Component | Priority | Dependencies | Parallel? |
|-----------|----------|--------------|-----------|
| HL7/FHIR Integration | High | All services | No |
| External Lab Systems | High | Integration Service | Yes |
| Insurance/Claims | High | Billing, Integration | Yes |
| Patient Portal (Cloud) | Medium | Patient, Auth | Yes |
| Mobile App | Medium | All services | Yes |

**Critical path:** HL7/FHIR Integration (enables all external connectivity)

### Phase 5: Advanced Features (Months 12+)
**Goal:** Analytics, AI, and optimization

| Component | Priority | Dependencies | Parallel? |
|-----------|----------|--------------|-----------|
| Analytics Engine | Medium | All services | Yes |
| Clinical Decision Support | Medium | EHR | Yes |
| Population Health | Low | Analytics | Yes |
| Telehealth Integration | Medium | EHR, Notification | Yes |
| AI/ML Pipeline | Low | Analytics | Yes |

---

## 9. Technology Stack Summary

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend** | React + TypeScript + Tailwind | Component-based, strong typing, rapid UI development |
| **API Gateway** | Kong or Apache APISIX | Healthcare-specific features, FHIR-aware routing |
| **Backend** | Node.js (NestJS) or .NET | Type safety, strong enterprise patterns, healthcare SDK support |
| **Database** | PostgreSQL 16 | ACID compliance, JSON support, proven in healthcare |
| **Document Store** | MongoDB 7 | Flexible schema for clinical documents |
| **Cache** | Redis 7 | Session management, real-time data caching |
| **Message Broker** | Apache Kafka | Event sourcing, audit trail, high throughput |
| **File Storage** | MinIO (S3-compatible) | DICOM, documents, on-premise control |
| **Container Orchestration** | Kubernetes | Auto-scaling, self-healing, rolling deployments |
| **Service Mesh** | Istio or Linkerd | mTLS, traffic management, observability |
| **CI/CD** | GitHub Actions + ArgoCD | GitOps workflow, automated deployments |
| **Monitoring** | Prometheus + Grafana | Metrics and dashboards |
| **Logging** | ELK Stack or Seq | Centralized logging with audit support |
| **Tracing** | Jaeger + OpenTelemetry | Distributed tracing across services |
| **Secrets** | HashiCorp Vault | Centralized secrets management |
| **FHIR Server** | HAPI FHIR or Azure Health Data Services | FHIR R4 compliance |

---

## 10. Anti-Patterns to Avoid

| Anti-Pattern | Why It Fails | Instead |
|--------------|-------------|---------|
| **Big Bang Microservices** | Operational overhead overwhelms team; transaction integrity issues | Start modular monolith, extract services gradually |
| **Shared Database Across Services** | Tight coupling, scaling bottlenecks, single point of failure | Schema-per-module with clear boundaries |
| **PHI in Logs** | HIPAA/PDPA violation, audit risk | PHI-free structured logging with correlation IDs |
| **Synchronous Everything** | Cascading failures, poor performance | Event-driven for non-critical paths |
| **No Circuit Breakers** | External system failure cascades internally | Polly/Resilience4j for all external calls |
| **Manual Deployments** | Human error, audit trail gaps | GitOps with ArgoCD, automated pipelines |
| **Skip Audit Logging** | Compliance failure, undetectable breaches | Audit logging as first-class concern |
| **Encryption Afterthought** | Retrofitting encryption is expensive | Encrypt at rest and in transit from day one |

---

## Sources

- Frontiers in Digital Health (2025): "Architectural patterns for health information systems: a systematic review"
- E-hir.org (2026): "Transferable Migration Framework Derived from a Large-scale Tertiary Hospital EHR System"
- Kagga (2025): "Migrating Legacy Healthcare Systems to Cloud-Native Microservices with AI"
- Reid & Jacob (2026): "A Cloud-Based Architecture for Scalable EHR Management System"
- Rahim (2026): "Architecting a Real-World Hospital Automation Platform with Kubernetes & GitOps"
- MedFlow GitHub Repository (2026): Cloud-native healthcare microservices platform
- SmartCare GitHub Repository (2026): Enterprise-grade microservices HMS
- ANI Solutions (2026): "HIPAA-Compliant EHR Architecture Design Guide"
- TactionSoft (2026): "Healthcare Microservices Architecture: Complete Guide"
- Konfirmity (2026): "HIPAA Microservices Security: A Walkthrough"
- Peerbits (2026): "Healthcare API Gateway Architecture Guide" & "FHIR Integration Architecture Guide"
- VE3 Global (2026): "A Practical Guide to HL7/FHIR API Integration"
- Nirmitee.io (2026): "FHIR Facade Architecture for Legacy Healthcare Systems"
- 6B Health (2026): "Secondary care EPR integration: Architecting HL7 v2 and FHIR coexistence"
- DataA.dev (2025): "Enterprise Healthcare Integration Case Study"
- Thailand PDPA (2019): Personal Data Protection Act BE 2562
- Thailand PDPC (2026): Healthcare-specific data protection guideline consultation
- Malaysia PDPA (2010): Code of Practice for Private Hospitals (APHM)
- Singapore PDPA: Retention Limitation Obligation Guidelines
