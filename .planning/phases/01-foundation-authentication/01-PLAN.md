# Phase 1: Foundation & Authentication — Plan

## Goal
Build the core application infrastructure: Next.js frontend, NestJS backend, PostgreSQL database, Keycloak integration, RBAC, MFA, audit logging, and break-glass workflow. All subsequent phases depend on this foundation.

## Requirements Coverage

| Requirement | Description | Status |
|-------------|-------------|--------|
| AUTH-01 | User can create account with unique user ID (HIPAA-compliant) | In Scope |
| AUTH-02 | User can log in with email/password and MFA (push/biometric) | In Scope |
| AUTH-03 | System enforces role-based access control (15 roles) | In Scope |
| AUTH-04 | System auto-logs out inactive sessions (15-min timeout) | In Scope |
| AUTH-05 | All patient record access is logged (6-field audit) | In Scope |
| AUTH-06 | Break-glass emergency access with time-bound override | In Scope |
| AUTH-07 | User can log out from any page | In Scope |

## Tasks

### Task 1: Project Scaffolding
**Estimated effort:** Small
**Depends on:** None

- [ ] Initialize Next.js 15 project with TypeScript, App Router
- [ ] Initialize NestJS 11 project with TypeScript
- [ ] Set up Prisma ORM with PostgreSQL provider
- [ ] Configure ESLint + Prettier (shared config)
- [ ] Create monorepo structure (apps/web, apps/api, packages/shared)
- [ ] Add .env.example with all required variables
- [ ] Add Docker Compose for local dev (PostgreSQL, Redis, Keycloak, Elasticsearch)
- [ ] Verify: `npm run dev` starts both frontend and backend

**Acceptance criteria:**
- Frontend runs on port 3000
- Backend runs on port 3001
- Database connects successfully
- Linting passes with zero errors

---

### Task 2: Database Schema — Core Auth Tables
**Estimated effort:** Medium
**Depends on:** Task 1

- [ ] Design Prisma schema for: User, Role, Permission, UserRole, RolePermission
- [ ] Add User model fields: id (UUID), email (unique), firstName, lastName, passwordHash, status, lastLoginAt, createdAt, updatedAt
- [ ] Add Role model: id, name (unique), description, isSystem (for predefined), createdAt
- [ ] Add Permission model: id, resource, action, description
- [ ] Add UserRole junction: userId, roleId, assignedBy, assignedAt
- [ ] Add RolePermission junction: roleId, permissionId
- [ ] Add AuditLog model: id, userId, action, resource, resourceId, metadata (JSONB), ipAddress, userAgent, timestamp, previousHash, hash (for chain integrity)
- [ ] Create database migration
- [ ] Seed 15 predefined roles with permission hierarchy

**Acceptance criteria:**
- Migration runs cleanly on fresh database
- All 15 roles seeded: Super Admin, Admin, Dept Head, Doctor, Nurse, Pharmacist, Lab Tech, Radiologist, Receptionist, Billing, Compliance Officer, System Auditor, Chief Medical Director, Medical Director, Minister of Health
- Permission hierarchy established (Super Admin inherits all)

---

### Task 3: Keycloak Integration
**Estimated effort:** Large
**Depends on:** Task 2

- [ ] Install @nestjs-keycloak-connect and keycloak-connect packages
- [ ] Configure Keycloak admin client for user/role sync
- [ ] Create Keycloak realm configuration (HMS realm)
- [ ] Set up JWT validation middleware (verify Keycloak tokens)
- [ ] Implement user sync: Keycloak user → HMS User record
- [ ] Implement role sync: Keycloak roles ↔ HMS Roles
- [ ] Configure MFA policies in Keycloak (push notification + TOTP)
- [ ] Add conditional MFA logic: new device detection → require MFA
- [ ] Implement session management (15-min timeout, silent refresh)
- [ ] Configure token storage (HttpOnly, Secure, SameSite=Strict cookies)

**Acceptance criteria:**
- User can log in via Keycloak with email/password
- MFA prompt appears on new device login
- JWT token validates on backend
- Session expires after 15 minutes of inactivity
- Silent refresh works during active use

---

### Task 4: Password Policy & Account Security
**Estimated effort:** Medium
**Depends on:** Task 3

- [ ] Implement password validation: 12+ chars, upper/lower/number/special
- [ ] Add password rotation enforcement (90-day max age)
- [ ] Implement password history check (no reuse of last 12)
- [ ] Add account lockout: 5 failed attempts → 30-minute lockout
- [ ] Implement self-service password reset (email link, 15-min expiry)
- [ ] Implement admin-assisted password reset
- [ ] Add login notifications (new device, failed attempts)
- [ ] Invalidate all sessions on password change

**Acceptance criteria:**
- Weak passwords rejected with clear error message
- Locked account cannot login for 30 minutes
- Password reset email sends within 60 seconds
- Password change invalidates all other sessions

---

### Task 5: RBAC System
**Estimated effort:** Large
**Depends on:** Task 2, Task 3

- [ ] Create RBAC guard for NestJS (role-based route protection)
- [ ] Implement permission checking middleware
- [ ] Create role assignment API: admin assigns → dept head approves
- [ ] Add custom role creation (admin + dept head approval)
- [ ] Implement permission overrides (grant/revoke individual permissions)
- [ ] Add temporary role elevation (time-limited, audited)
- [ ] Create department-scoped access for doctors
- [ ] Add permission change notifications (user + compliance officer)
- [ ] Build admin RBAC management UI (role list, permission matrix)
- [ ] Add full audit trail for all role/permission changes

**Acceptance criteria:**
- User with role X can only access permitted resources
- Role assignment requires two approvals (admin + dept head)
- Custom roles can be created with specific permissions
- All role changes are audit logged
- Permission changes trigger notifications

---

### Task 6: Audit Logging System
**Estimated effort:** Large
**Depends on:** Task 2

- [ ] Create audit service (separate from main DB)
- [ ] Implement 6-field capture: Who, What, When, Where, Why, Patient
- [ ] Add hash chain integrity (each entry includes hash of previous)
- [ ] Store audit logs in Elasticsearch (or PostgreSQL with partitioning)
- [ ] Create audit log API (search, filter, export)
- [ ] Build audit log admin dashboard (search, filter, export)
- [ ] Implement pattern-based alerting (failed logins, off-hours, bulk exports)
- [ ] Set up 6-year retention policy
- [ ] Add audit log integrity verification tool

**Acceptance criteria:**
- Every API call generates audit log entry
- Hash chain is verifiable (tamper-evident)
- Audit logs searchable by user, action, date, patient
- Export to CSV/PDF works
- Alert fires on 5+ failed logins in 5 minutes

---

### Task 7: Break-Glass Workflow
**Estimated effort:** Medium
**Depends on:** Task 5, Task 6

- [ ] Create break-glass request API (doctor requests access)
- [ ] Implement admin approval workflow
- [ ] Add 1-hour access window enforcement
- [ ] Send notifications: admin + compliance officer + dept head (immediate)
- [ ] Implement 24-hour compliance review workflow
- [ ] Add full audit trail (who requested, who approved, reason, time accessed, data viewed)
- [ ] Implement frequency alerts (>3 requests/week per user)
- [ ] Build break-glass admin dashboard

**Acceptance criteria:**
- Doctor can request emergency access to specific patient
- Admin can approve with reason
- Access expires automatically after 1 hour
- Compliance officer notified immediately
- 24-hour review is mandatory (blocks further break-glass if missed)
- All break-glass events fully audited

---

### Task 8: Frontend — Auth & Layout
**Estimated effort:** Large
**Depends on:** Task 1, Task 3

- [ ] Build login page (email, password, MFA prompt)
- [ ] Build password reset flow pages
- [ ] Create main layout: collapsible sidebar + header + content area
- [ ] Implement sidebar navigation with icons + labels
- [ ] Add header: global search, notifications bell, user menu
- [ ] Build light/dark theme toggle (MUI native)
- [ ] Implement responsive breakpoints (mobile <768px, tablet 768-1024px, desktop >1024px)
- [ ] Add skeleton loaders for all pages
- [ ] Add toast notification system
- [ ] Implement print styles for reports
- [ ] Add keyboard navigation (Tab, Enter, Escape, Arrow keys)
- [ ] Add ARIA labels for screen readers

**Acceptance criteria:**
- Login page matches design (medical blue, clean layout)
- Sidebar collapses to icons on tablet, drawer on mobile
- Dark mode toggle works across all components
- All pages have skeleton loaders
- Keyboard navigation works for all interactive elements
- WCAG AAA contrast ratios met (7:1)

---

### Task 9: Frontend — Admin Dashboard
**Estimated effort:** Medium
**Depends on:** Task 8

- [ ] Build user management page (list, create, edit, deactivate)
- [ ] Build role management page (list, create, assign)
- [ ] Build permission matrix view
- [ ] Build audit log viewer (search, filter, export)
- [ ] Build break-glass management page
- [ ] Add dashboard cards (user count, recent activity, security alerts)
- [ ] Implement MUI DataGrid for all tables (sort, filter, pagination)

**Acceptance criteria:**
- Admin can create user in < 2 minutes
- Role assignment UI shows permission matrix
- Audit logs searchable with < 2 second response
- All tables support sort, filter, pagination

---

### Task 10: Backend API — Auth Endpoints
**Estimated effort:** Medium
**Depends on:** Task 3, Task 4, Task 5

- [ ] POST /auth/login — authenticate user
- [ ] POST /auth/logout — invalidate session
- [ ] POST /auth/refresh — refresh access token
- [ ] POST /auth/mfa/verify — verify MFA code
- [ ] POST /auth/password/reset — request password reset
- [ ] POST /auth/password/confirm — confirm password reset
- [ ] GET /auth/me — get current user profile
- [ ] PUT /auth/me — update current user profile
- [ ] Add rate limiting (10 req/min for auth endpoints)
- [ ] Add request validation (Zod schemas)

**Acceptance criteria:**
- All endpoints return proper success/error responses
- Rate limiting prevents brute force
- Input validation rejects malformed requests
- Audit log generated for all auth events

---

### Task 11: Integration Tests
**Estimated effort:** Medium
**Depends on:** Task 10

- [ ] Test login flow (email/password → MFA → token)
- [ ] Test session timeout (15-min expiry)
- [ ] Test password policy enforcement
- [ ] Test account lockout (5 failed attempts)
- [ ] Test RBAC enforcement (unauthorized access blocked)
- [ ] Test break-glass workflow (request → approve → access → expiry)
- [ ] Test audit log generation
- [ ] Test concurrent session limits

**Acceptance criteria:**
- All auth flows tested end-to-end
- RBAC blocks unauthorized access
- Break-glass access expires after 1 hour
- Audit logs generated for all test events

---

### Task 12: E2E Tests
**Estimated effort:** Medium
**Depends on:** Task 9, Task 11

- [ ] Test login page (Playwright)
- [ ] Test dashboard navigation
- [ ] Test user management CRUD
- [ ] Test role assignment flow
- [ ] Test audit log search
- [ ] Test responsive layouts (mobile, tablet, desktop)
- [ ] Test dark mode toggle

**Acceptance criteria:**
- All critical user flows tested
- Tests pass in CI/CD pipeline
- No regressions on existing features

---

## Dependencies

```
Task 1 (Scaffolding)
  └── Task 2 (DB Schema)
       ├── Task 3 (Keycloak)
       │    ├── Task 4 (Password Policy)
       │    ├── Task 8 (Frontend Auth)
       │    │    └── Task 9 (Admin Dashboard)
       │    └── Task 10 (API Endpoints)
       │         └── Task 11 (Integration Tests)
       │              └── Task 12 (E2E Tests)
       ├── Task 5 (RBAC)
       │    └── Task 7 (Break-Glass)
       └── Task 6 (Audit Logging)
```

## Parallel Execution

**Wave 1:** Task 1 (no dependencies)
**Wave 2:** Task 2 (depends on Task 1)
**Wave 3:** Task 3, Task 6 (depend on Task 2)
**Wave 4:** Task 4, Task 5, Task 8 (depend on Task 3)
**Wave 5:** Task 7, Task 9, Task 10 (depend on Wave 4)
**Wave 6:** Task 11 (depends on Task 10)
**Wave 7:** Task 12 (depends on Task 9, Task 11)

## Verification

### Code Review
- All PRs reviewed before merge
- Security review for auth-related changes
- RBAC changes reviewed by compliance officer

### Testing
- Unit tests: 80% coverage for auth modules
- Integration tests: All API endpoints
- E2E tests: All critical user flows
- Security tests: OWASP Top 10 checks

### Quality Gates
- [ ] All tests pass
- [ ] Lint passes with zero errors
- [ ] TypeScript compilation succeeds
- [ ] No security vulnerabilities (npm audit)
- [ ] Audit logging verified
- [ ] RBAC enforcement verified

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Keycloak complexity | Use managed Keycloak service if self-hosted too complex |
| MFA user friction | Conditional MFA (new device only) reduces friction |
| Session timeout annoyance | Silent refresh during active use |
| RBAC approval bottleneck | Temp elevation for urgent cases |
| Audit log performance | Separate Elasticsearch cluster, async writes |

## Estimated Duration

- **Total:** 4 weeks (20 working days)
- **Parallel execution:** ~3 weeks with wave-based parallelization
- **Buffer:** 1 week for unexpected issues

## Definition of Done

- [ ] All 12 tasks completed
- [ ] AUTH-01 through AUTH-07 requirements verified
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Demo ready for stakeholders
- [ ] Production deployment verified (staging environment)
