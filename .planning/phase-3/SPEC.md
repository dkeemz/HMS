# Phase 3 SPEC: Doctor & Department Management

## Goal
Admin can set up the hospital's organizational structure and doctors can manage their profiles and availability status.

## Success Criteria
1. Doctor profiles are creatable with name, specialty, qualifications, department assignment, and consultation hours
2. Department structure is defined hierarchically (e.g., Cardiology > Interventional Cardiology)
3. Doctor specialties and qualifications are tracked and visible in the doctor directory
4. Doctor availability status can be set to available, on-leave, in-surgery, or on-duty in real time

## Plans
- 03-01: Department service — Hierarchical department CRUD, parent-child relationships, department directory
- 03-02: Doctor profile service — Profile creation, specialty/qualification tracking, department assignment
- 03-03: Doctor directory UI — Doctor listing, search by specialty/department, profile views
- 03-04: Availability status management — Real-time status toggle (available, on-leave, in-surgery, on-duty)

## Key Design Decisions
1. Doctor = User + DoctorProfile (1:1 extension, not separate entity)
2. Department is self-referential (parent_id -> id) for hierarchy
3. Availability status on DoctorProfile (not separate table)
4. Consultation hours as JSONB for flexibility
5. Page routes in app/main.py, HTMX fragments in v1 API routes

## Dependencies
- Phase 1 (Auth, RBAC, Audit) — COMPLETE
- Phase 2 (Patient Management) — COMPLETE
