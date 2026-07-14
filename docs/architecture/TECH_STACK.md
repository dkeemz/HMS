# Technology Stack

## Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.x | UI framework |
| Next.js | 15.x | SSR, routing, API routes |
| TypeScript | 5.x | Type safety |
| Material UI (MUI) | 6.x | Component library |
| Recharts | 2.x | Data visualization |
| React Query | 5.x | Server state management |
| Zustand | 5.x | Client state management |
| React Hook Form | 7.x | Form management |
| Zod | 3.x | Schema validation |

### Frontend Architecture
```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Authentication routes
│   ├── (dashboard)/       # Dashboard routes
│   ├── api/               # API routes
│   └── layout.tsx
├── components/
│   ├── ui/                # Base components (Button, Input, etc.)
│   ├── forms/             # Form components
│   ├── charts/            # Chart components
│   └── layout/            # Layout components (Sidebar, Header)
├── hooks/                 # Custom hooks
├── lib/                   # Utilities, API client
├── stores/                # Zustand stores
└── types/                 # TypeScript types
```

## Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| NestJS | 11.x | Backend framework |
| TypeScript | 5.x | Type safety |
| Prisma | 6.x | ORM |
| PostgreSQL | 17.x | Primary database |
| Redis | 7.x | Caching, sessions |
| Keycloak | 26.x | Identity & access management |
| HAPI FHIR | 8.x | FHIR server |
| Elasticsearch | 8.x | Audit log search |

### Backend Architecture
```
src/
├── modules/
│   ├── auth/              # Authentication & authorization
│   ├── patient/           # Patient management
│   ├── doctor/            # Doctor & department management
│   ├── scheduling/        # Appointment & shift scheduling
│   ├── ehr/               # Electronic health records
│   ├── billing/           # Billing & invoicing
│   ├── attendance/        # Staff attendance
│   ├── servicom/          # Customer service
│   └── analytics/         # Reporting & dashboards
├── common/
│   ├── guards/            # Auth, RBAC guards
│   ├── interceptors/      # Logging, transformation
│   ├── decorators/        # Custom decorators
│   └── filters/           # Exception filters
├── config/                # Configuration
└── main.ts
```

## Database

### PostgreSQL 17
- **Primary database** for all transactional data
- **Row-level security (RLS)** for multi-tenant isolation
- **Partitioning** for audit logs and time-series data
- **Full-text search** for patient records

### Schema Design
```sql
-- Core schemas
auth          -- Users, roles, permissions
patient       -- Patient demographics, contacts
clinical      -- Encounters, vitals, diagnoses
scheduling    -- Appointments, shifts, rooms
billing       -- Invoices, payments, claims
attendance    -- Clock records, leave, swaps
servicom      -- Complaints, feedback, surveys
audit         -- Audit logs (partitioned by month)
```

### Redis 7
- Session storage (with Keycloak)
- Rate limiting
- Real-time notifications (Pub/Sub)
- Caching (dashboard data, frequent queries)

### Elasticsearch 8
- Audit log search and analytics
- Full-text search for clinical notes
- Pattern detection for security alerts

## Authentication & Authorization

### Keycloak 26.x
- **Identity Provider (IdP)** for all users
- **MFA:** Push notification (primary), TOTP (fallback)
- **SSO:** OAuth 2.0 / OpenID Connect
- **User Federation:** LDAP/Active Directory integration
- **Custom Themes:** Branded login pages

### RBAC Implementation
- 15 predefined roles with hierarchical inheritance
- Feature-level permissions (resource:action)
- Custom role creation with admin + Dept Head approval
- Temporary role elevation for coverage situations

## Interoperability

### HAPI FHIR 8.x
- FHIR R4 compliant
- Supported resources: Patient, Encounter, Observation, Condition, MedicationRequest, DiagnosticReport
- SMART on FHIR for app authorization
- Bulk FHIR export for analytics

### HL7v2 Integration
- ADT (Admit/Discharge/Transfer) messages
- ORM (Order Messages) for lab/pharmacy
- ORU (Observation Results) for lab results

## DevOps & Infrastructure

### Containerization
```yaml
# Docker
- Multi-stage builds for optimized images
- Health checks for all services
- Non-root user execution
- Secrets management via Docker secrets

# Kubernetes
- Helm charts for deployment
- Horizontal Pod Autoscaler (HPA)
- Pod Disruption Budgets (PDB)
- Network Policies for security
```

### CI/CD Pipeline
```
GitHub Actions:
├── Lint & Type Check
├── Unit Tests
├── Integration Tests
├── Security Scan (Snyk, Trivy)
├── Build Docker Images
├── Push to Registry
├── Deploy to Staging
├── E2E Tests
└── Deploy to Production (manual approval)
```

### Monitoring & Observability
- **Metrics:** Prometheus + Grafana
- **Logs:** ELK Stack (Elasticsearch, Logstash, Kibana)
- **Traces:** Jaeger (distributed tracing)
- **Alerts:** PagerDuty / OpsGenie integration

## Development Tools

| Tool | Purpose |
|------|---------|
| ESLint | Code linting |
| Prettier | Code formatting |
| Jest | Unit testing |
| Supertest | API testing |
| Playwright | E2E testing |
| Prisma Studio | Database management |
| Storybook | Component documentation |

## Performance Targets

| Metric | Target |
|--------|--------|
| API Response Time | < 200ms (p95) |
| Page Load Time | < 2s |
| Time to Interactive | < 3s |
| Database Query Time | < 50ms (p95) |
| Concurrent Users | 1,000+ |
| Uptime | 99.9% |
