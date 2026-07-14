# Research Summary: Hospital Health Management System (HMS)

**Domain:** Healthcare IT / Hospital Management System
**Researched:** 2026-07-13
**Scale:** Large hospital chain (500+ doctors), multiple departments
**Deployment:** Hybrid (on-premise + cloud)
**Compliance:** HIPAA + PDPA
**Overall confidence:** HIGH

---

## Executive Summary

This research covers the complete domain landscape for building a greenfield Hospital Health Management System serving 500+ doctors with hybrid deployment and multi-standard compliance. The research spans 60+ sources from 2025-2026, including production implementations, academic studies, government audit reports (GAO, VA OIG), and practitioner post-mortems.

**The core finding:** Modern hospital HMS architecture has converged on **event-driven microservices** as the dominant pattern, but the recommended starting point is a **modular monolith with strategic microservice extraction** (Strangler Fig pattern). A "big bang" microservices rewrite has a high failure rate in healthcare due to transaction integrity requirements and zero-downtime constraints.

**The #1 risk:** Physician adoption failure. Every other module can work perfectly, but if the documentation layer is difficult, clinicians work around it. No doctor usage = no data = no HMS value proposition. The system must be built for the physician first, not the CIO.

**The #1 compliance risk:** Deferring HIPAA compliance to "Version 2." Building compliance into the architecture from sprint one costs 15-25% of the project. Retrofitting costs 2-3x more and is the most common reason healthcare IT projects fail at compliance, not code.

**The #1 integration risk:** Underestimating HL7/FHIR integration complexity. Hospitals run 20-50 specialized systems. Every integration is a project. Total integration effort often exceeds core HMS development effort.

---

## Key Findings

**Stack:** React 19 + Next.js 15 (web), React Native (mobile), NestJS 11 (backend), PostgreSQL 17 + TimescaleDB, HAPI FHIR 8.x, Redis 7.x, Elasticsearch 8.x, Keycloak 26.x, AWS S3, Mirth Connect 4.x, Grafana stack, GitHub Actions + ArgoCD + Terraform. TypeScript across the full stack. Microservices on Kubernetes with modular monolith starting point.

**Architecture:** Modular monolith → strategic microservice extraction. Schema-per-module (not database-per-service). Event-driven for non-critical paths. CQRS for EHR/Clinical Service. Saga pattern for distributed transactions (billing). API Gateway (Kong/APISIX) for routing, rate limiting, and FHIR-aware routing.

**Critical pitfall:** HIPAA compliance deferred to "Version 2" — costs 2-3x to retrofit, most common cause of healthcare IT project failure.

---

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Foundation & Compliance (Months 1-3)
**Goal:** Core infrastructure with HIPAA compliance built in from day one

**Deliverables:**
- Auth Service (Keycloak, RBAC, MFA, audit logging)
- Patient Service (registration, MRN, demographics)
- Doctor/Department Service (profiles, availability)
- API Gateway (Kong/APISIX)
- Database Infrastructure (PostgreSQL + schemas)
- Audit Logging Pipeline (append-only, tamper-evident)
- Kubernetes Cluster (EKS + on-premise RKE2)

**Rationale:** Addresses table stakes features (Auth, Patient Management, Doctor/Dept) and avoids the #1 compliance risk (deferring HIPAA). Phase 1 must be stable before clinical modules.

**Features from FEATURES.md:** Authentication & Access Control, Patient Management (core), Doctor & Department Management

**Pitfall avoided:** PITFALLS.md #1 (Deferring HIPAA Compliance), #4 (Scope Maximalism)

---

### Phase 2: Core Clinical (Months 3-6)
**Goal:** EHR, scheduling, and clinical workflow that physicians actually want to use

**Deliverables:**
- EHR/Clinical Service (SOAP notes, prescriptions, diagnoses, vitals)
- Scheduling Service (appointment booking, availability, conflict detection)
- Notification Service (SMS, email, push)
- File Storage Service (clinical documents)
- FHIR R4 Server (HAPI FHIR)
- Mirth Connect Integration Engine (on-premise)
- Clinical workflow validation with actual physicians

**Rationale:** This is where physician adoption is won or lost. Every screen must be faster than paper. Clinical validation at every sprint (every 2 weeks).

**Features from FEATURES.md:** EHR (SOAP Notes, eRx, ICD-10, Lab Results, Vitals), Scheduling (booking, availability, calendar views)

**Pitfall avoided:** PITFALLS.md #3 (Skipping Clinical Workflow Validation), #7 (Physician Adoption Failure)

---

### Phase 3: Revenue Cycle (Months 6-9)
**Goal:** Billing and insurance claims processing

**Deliverables:**
- Billing Service (invoices, payments, insurance claims)
- Insurance Claims Management (CPT/ICD coding, claim scrubbing)
- Outstanding Balance Tracking
- Financial Reporting
- HL7 v2 Interfaces (ADT, ORM, ORU) for internal hospital messaging

**Rationale:** Billing is the revenue backbone. Must be stable before Phase 4 integrations. HL7 v2 interfaces enable internal hospital messaging.

**Features from FEATURES.md:** Billing (invoices, payment tracking, insurance claims), Reporting (operational dashboards, financial reports)

**Pitfall avoided:** PITFALLS.md #2 (Underestimating Integration Complexity), #9 (Shared Database)

---

### Phase 4: Integration & Operations (Months 9-12)
**Goal:** External system integration and operational modules

**Deliverables:**
- External Lab Integration (LIS connectivity)
- Pharmacy Integration (prescription dispensing, drug interaction checking)
- IPD Module (bed management, ADT, nurse station)
- Inventory Module (stock management, expiry tracking)
- FHIR R4 APIs for external integrations
- Patient Portal (self-scheduling, records access, bill pay)
- Mobile App (React Native)

**Rationale:** External integrations are the highest-risk phase. Requires stable core modules from Phases 1-3. Patient portal and mobile are Phase 2 features per PROJECT.md.

**Features from FEATURES.md:** Lab Integration, Pharmacy, IPD, Inventory, Patient Portal, Mobile App

**Pitfall avoided:** PITFALLS.md #15 (Over-Customization), #14 (Training as One-Time Event)

---

### Phase 5: Advanced Features (Months 12+)
**Goal:** Analytics, AI, and optimization

**Deliverables:**
- Analytics Engine (operational and clinical KPIs)
- Clinical Decision Support (drug interactions, allergy checking)
- Telemedicine (video consultation)
- Custom Report Builder
- Advanced FHIR capabilities (SMART on FHIR, Bulk Data Export)

**Rationale:** Advanced features require 6-12 months of operational data before being useful. Telemedicine is a separate product vertical per PROJECT.md.

**Features from FEATURES.md:** Telemedicine, Clinical Decision Support, Custom Report Builder, Predictive Analytics

**Pitfall avoided:** PITFALLS.md #4 (Scope Maximalism), #10 (No Post-Launch Maintenance Plan)

---

## Phase Ordering Rationale

1. **Foundation first** — HIPAA compliance must be architectural, not bolted on. Auth, Patient, and Doctor/Department are prerequisites for all other modules.

2. **Clinical core before billing** — Billing depends on clinical documentation. EHR must be stable before charges can be generated accurately.

3. **Billing before integrations** — Revenue cycle is critical for hospital operations. External integrations are highest-risk; they need stable internal modules.

4. **Integrations before advanced features** — External system connectivity (lab, pharmacy, IPD) enables clinical value. Advanced features (AI, analytics) require operational data.

5. **Advanced features last** — Analytics, CDS, and telemedicine require 6-12 months of operational data. Building them before the core is stable wastes resources.

---

## Research Flags for Phases

| Phase | Research Depth Needed | Reason |
|-------|----------------------|--------|
| Phase 1 | Standard patterns | Auth, Patient, Doctor/Department are well-understood. Keycloak + PostgreSQL + RBAC patterns are established. |
| Phase 2 | **Deep research needed** | Clinical documentation workflows, physician UX patterns, FHIR R4 resource mapping, Mirth Connect configuration. Highest-risk phase for adoption. |
| Phase 3 | **Deep research needed** | Insurance claims processing, CPT/ICD coding, claim scrubbing, HL7 v2 message types. Complex business logic. |
| Phase 4 | **Deep research needed** | External system integration (LIS, PACS, pharmacy dispensing), HL7 v2/FHIR coexistence, mobile HIPAA requirements. Highest technical risk. |
| Phase 5 | Standard patterns | Analytics, CDS, and telemedicine are well-understood patterns. Lower risk after core is stable. |

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Multiple production healthcare sources, 2026-dated references, universal consensus on PostgreSQL, React, NestJS |
| Features | HIGH | Comprehensive feature landscape from 20+ HMS sources, clear table stakes vs. differentiators |
| Architecture | HIGH | 15+ production architectures studied, academic papers, real-world case studies, modular monolith pattern validated |
| Pitfalls | HIGH | Drawn from GAO reports, VA OIG audits, academic studies, and practitioner post-mortems. Multiple independent sources confirm same failure patterns |

---

## Gaps to Address

- **Phase-specific FHIR resource mapping** — Detailed mapping of HMS data models to FHIR R4 resources needed for Phase 2
- **Insurance payer-specific requirements** — CPT/ICD coding rules vary by payer and region; needs phase-specific research
- **PDPA jurisdiction-specific requirements** — Thailand vs. Malaysia PDPA differences need clarification
- **Mobile HIPAA requirements** — Detailed mobile-specific compliance controls needed for Phase 4
- **Telehealth video SDK selection** — Twilio vs. Daily.co comparison deferred to Phase 5

---

## Key Decisions for Roadmap

| Decision | Recommendation | Rationale |
|----------|---------------|-----------|
| Architecture pattern | Modular monolith → microservices | Safer starting point, lower operational overhead, cleaner extraction path |
| Database strategy | Schema-per-module | Enforces boundary discipline, enables clean service extraction |
| FHIR server | HAPI FHIR 8.x (self-hosted) | Most deployed open-source FHIR server, best search conformance, full SMART on FHIR |
| Integration engine | Mirth Connect 4.5.x (on-premise) | Industry standard, handles HL7 v2 + FHIR, runs in hospital data center |
| Auth provider | Keycloak 26.x (self-hosted) | Data sovereignty, LDAP/AD federation, zero per-user cost at scale |
| Cloud provider | AWS (HIPAA BAA) | Most HIPAA-eligible services, largest healthcare cloud ecosystem |
| Compliance approach | Built-in from day one | 15-25% incremental cost vs. 2-3x retrofit cost |
| Deployment strategy | Department-by-department | Reduces risk, enables parallel run, allows clinical staff adaptation |

---

*Last updated: 2026-07-13 after ecosystem research*
