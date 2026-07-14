# Technology Stack

## Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| HTMX | 2.x | Dynamic UI (HTML-over-the-wire) |
| Jinja2 | 3.x | Server-side templating |
| Tailwind CSS | 4.x | Utility-first styling |
| Heroicons | 2.x | Icon library |
| Chart.js | 4.x | Data visualization |

### Frontend Architecture
```
templates/
├── base.html                # Base template (nav, sidebar, footer)
├── auth/                    # Login, MFA, password reset
├── components/              # Reusable UI components
│   ├── buttons/
│   ├── forms/
│   ├── tables/
│   └── modals/
├── patients/                # Patient management
├── doctors/                 # Doctor management
├── scheduling/              # Appointments & shifts
├── ehr/                     # Electronic health records
├── billing/                 # Billing & invoicing
├── attendance/              # Staff attendance
├── servicom/                # Customer service
├── reports/                 # Reports & dashboards
└── static/                  # CSS, JS, images
    ├── css/
    ├── js/
    └── img/
```

## Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.115+ | Backend framework |
| Python | 3.12 | Language |
| SQLAlchemy | 2.x | ORM |
| Alembic | 1.x | Database migrations |
| Pydantic | 2.x | Data validation |
| PostgreSQL | 17.x | Primary database |
| Redis | 7.x | Caching, sessions, task queue |
| Keycloak | 26.x | Identity & access management |
| HAPI FHIR | 8.x | FHIR server |
| Elasticsearch | 8.x | Audit log search |
| Celery | 5.x | Background tasks |

### Backend Architecture
```
app/
├── main.py                 # Application entry point
├── core/                   # Core configuration
│   ├── config.py           # Settings & environment variables
│   ├── database.py         # Database connection & session
│   ├── security.py         # Auth, JWT, password hashing
│   └── deps.py             # Dependency injection
├── models/                 # SQLAlchemy models
│   ├── auth.py             # User, Role, Permission
│   ├── patient.py          # Patient, Contact, Insurance
│   ├── doctor.py           # Doctor, Department
│   ├── scheduling.py       # Appointment, Shift, Room
│   ├── ehr.py              # Encounter, Vitals, Diagnosis
│   ├── billing.py          # Invoice, Payment, Claim
│   ├── attendance.py       # Clock record, Leave, Swap
│   └── servicom.py         # Complaint, Feedback, Survey
├── schemas/                # Pydantic schemas
│   ├── auth.py
│   ├── patient.py
│   ├── doctor.py
│   ├── scheduling.py
│   ├── ehr.py
│   ├── billing.py
│   ├── attendance.py
│   └── servicom.py
├── api/                    # API routes
│   ├── v1/                 # API version 1
│   │   ├── auth.py
│   │   ├── patients.py
│   │   ├── doctors.py
│   │   ├── scheduling.py
│   │   ├── ehr.py
│   │   ├── billing.py
│   │   ├── attendance.py
│   │   └── servicom.py
│   └── deps.py             # Route dependencies
├── services/               # Business logic
│   ├── auth.py
│   ├── patient.py
│   ├── doctor.py
│   ├── scheduling.py
│   ├── ehr.py
│   ├── billing.py
│   ├── attendance.py
│   └── servicom.py
├── templates/              # Jinja2 templates (same as frontend/)
├── static/                 # Static files (CSS, JS, images)
└── tasks/                  # Celery tasks
    ├── notifications.py    # Email, SMS, push notifications
    ├── reports.py          # Scheduled report generation
    └── cleanup.py          # Data cleanup, archival
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
- Celery task queue broker

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
├── Lint & Type Check (Ruff, mypy)
├── Unit Tests (pytest)
├── Integration Tests (pytest)
├── Security Scan (Snyk, Trivy)
├── Build Docker Images
├── Push to Registry
├── Deploy to Staging
├── E2E Tests (Playwright)
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
| Ruff | Python linting |
| Black | Python formatting |
| mypy | Static type checking |
| pytest | Unit testing |
| httpx | API testing |
| Playwright | E2E testing |
| pgAdmin | Database management |

## Performance Targets

| Metric | Target |
|--------|--------|
| API Response Time | < 200ms (p95) |
| Page Load Time | < 2s |
| Time to Interactive | < 3s |
| Database Query Time | < 50ms (p95) |
| Concurrent Users | 1,000+ |
| Uptime | 99.9% |
