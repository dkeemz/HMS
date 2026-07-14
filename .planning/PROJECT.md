# Health Management System (HMS)

## What This Is

An all-in-one Health Management System for large hospital chains, serving doctors, nurses, admin staff, and registered patients. Replaces fragmented hospital tools with a unified platform covering patient management, clinical records, scheduling, and billing — accessible via web and mobile, deployed hybrid (on-premise + cloud), compliant with international and Nigerian healthcare standards (HIPAA, PDPA, NDPA, NHIS, NAFDAC, etc.).

## Core Value

One unified system that replaces all fragmented hospital tools — if everything else fails, doctors must be able to access complete patient records and manage appointments from a single place.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Authentication & role-based access control (doctors, nurses, admin, patients)
- [ ] Patient management (registration, profiles, medical history)
- [ ] Doctor & department management (profiles, specialties, department structure)
- [ ] Appointment scheduling (patient bookings, doctor availability, calendar views)
- [ ] Basic Electronic Health Records (medical records, prescriptions, diagnoses, lab results)
- [ ] Billing foundation (invoices, payment tracking, insurance)

### Out of Scope

- Shift/roster management — complex scheduling logic, deferred to v2
- Multi-location/hospital chain features — v1 focuses on single location
- Advanced analytics & reporting — defer to v2 after core modules stable
- Mobile apps — web-first approach, native mobile in v2+
- Pharmacy integration — deep pharmacy hooks deferred
- Lab integration — deep lab system hooks deferred
- Telemedicine — separate product vertical, not in v1

## Context

- **Target scale:** Large hospital chain (500+ doctors, multiple departments)
- **Deployment:** Hybrid — hospital on-premise servers + cloud for scalability
- **Compliance:** International standards (HIPAA, PDPA) + Nigerian standards (NDPA, NHIS, NAFDAC, Cybercrimes Act 2015)
- **Platform:** Web application (primary) + mobile (v2+)
- **Users:** Full hospital staff (doctors, nurses, admin, reception) + registered patients
- **Problem:** Hospitals currently juggle multiple disconnected tools for records, scheduling, billing — leading to inefficiency and poor patient continuity

## Constraints

- **Compliance**: Must meet HIPAA + PDPA + NDPA (Nigeria Data Protection Act 2023) + NHIS + NAFDAC + Cybercrimes Act 2015 — affects data storage, encryption, audit logging
- **Deployment**: Hybrid architecture — data residency requirements mean some data stays on-premise
- **Scale**: Must support 500+ concurrent doctors across departments
- **Security**: Patient health data requires encryption at rest and in transit, role-based access, audit trails
- **Integration**: Must eventually integrate with existing hospital systems (lab equipment, pharmacy, insurance portals)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Web-first approach | Largest reach, no install needed, faster iteration | — Pending |
| Hybrid deployment | Data residency requirements + scalability needs | — Pending |
| Full EHR from v1 | Core clinical value, doctors need complete patient view | — Pending |
| Billing in v1 | Revenue cycle management is critical for hospital operations | — Pending |
| Multiple compliance standards | International hospital chain requires HIPAA + PDPA + Nigerian standards (NDPA, NHIS, NAFDAC) | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-13 after initialization*
