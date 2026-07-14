# HMS System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │   Web    │  │  Mobile  │  │  Portal  │  │  Admin   │       │
│  │  (React) │  │ (React   │  │ (Patient)│  │  Panel   │       │
│  │          │  │  Native) │  │          │  │          │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       └──────────────┴──────────────┴──────────────┘            │
└─────────────────────────────┬───────────────────────────────────┘
                              │ HTTPS / WebSocket
┌─────────────────────────────┴───────────────────────────────────┐
│                        API GATEWAY                              │
│              (Rate Limiting, Auth, Routing)                     │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                     APPLICATION LAYER                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    NestJS Modules                        │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │   │
│  │  │  Auth   │ │ Patient │ │   EHR   │ │Scheduling│      │   │
│  │  │ Module  │ │ Module  │ │ Module  │ │ Module  │      │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘      │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │   │
│  │  │Billing  │ │Attendance│ │Servicom │ │Analytics│      │   │
│  │  │ Module  │ │ Module  │ │ Module  │ │ Module  │      │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘      │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                       DATA LAYER                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │PostgreSQL│  │   Redis  │  │Elastic-  │  │  MinIO   │       │
│  │ (Primary)│  │ (Cache)  │  │ search   │  │ (Files)  │       │
│  │          │  │          │  │ (Audit)  │  │          │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

## Architectural Patterns

### Modular Monolith (Phase 1-3)
The system starts as a modular monolith with clear module boundaries. Each module has its own:
- Domain entities
- Service layer
- Controller (REST API)
- Database schema (via schemas or separate databases)

### Strangler Fig (Phase 4+)
As the system grows, modules can be extracted into independent microservices:
- **Extract first:** Integration Hub (FHIR Gateway), Analytics
- **Extract next:** Telemedicine, AI Services
- **Keep monolith:** Core clinical modules (Patient, EHR, Scheduling)

### CQRS (Command Query Responsibility Segregation)
Used selectively for high-read modules:
- **Commands:** Patient registration, appointment booking, clinical documentation
- **Queries:** Dashboards, reports, search

### Event-Driven Architecture
Internal events for module communication:
```
PatientRegistered → AuditLog, Notification
AppointmentBooked → AuditLog, Notification, Billing
EncounterCompleted → Billing, AuditLog
LabResultReady → Notification, EHR
ComplaintFiled → Servicom, AuditLog
```

## Security Architecture

### Authentication Flow
```
User → Keycloak (MFA) → JWT Token → API Gateway → Module
                ↓
         Audit Log (every auth event)
```

### Authorization Flow
```
Request → JWT Validation → RBAC Check → Permission Check → Module Access
                ↓                    ↓                ↓
           Audit Log           Audit Log         Audit Log
```

### Data Security
- **Encryption at rest:** AES-256 for all PHI
- **Encryption in transit:** TLS 1.3
- **Database:** Row-level security (RLS) + column-level encryption for sensitive fields
- **Key management:** AWS KMS / HashiCorp Vault
- **Break-glass:** Emergency access with full audit trail

## Integration Architecture

### External Systems
```
┌─────────────────────────────────────────────────┐
│                  HMS Core                        │
└──────────────────────┬──────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────┴────┐   ┌─────┴─────┐  ┌────┴────┐
   │  FHIR   │   │  NHIS     │  │  SMS/   │
   │ Gateway │   │  Gateway  │  │  Email  │
   │(HAPI)   │   │           │  │  (Twilio│
   └─────────┘   └───────────┘  └─────────┘
```

### FHIR Integration
- **FHIR R4** for clinical data exchange
- **HAPI FHIR 8.x** as the FHIR server
- Supported resources: Patient, Encounter, Observation, Condition, MedicationRequest, DiagnosticReport

### NHIS Integration
- Nigerian Health Insurance Scheme claims submission
- Real-time eligibility verification
- Electronic claim submission and tracking

## Deployment Architecture

### Hybrid Deployment (On-Premise + Cloud)
```
┌─────────────────────────────────────────────────┐
│              Cloud (AWS/Azure)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │  App     │  │  Redis   │  │  Object  │     │
│  │  Server  │  │  Cache   │  │  Storage │     │
│  │ (K8s)    │  │          │  │  (S3)    │     │
│  └──────────┘  └──────────┘  └──────────┘     │
└─────────────────────────────────────────────────┘
                       │
              VPN / Direct Connect
                       │
┌─────────────────────────────────────────────────┐
│              On-Premise                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │PostgreSQL│  │Elastic-  │  │  Keycloak│     │
│  │ (Primary)│  │ search   │  │  (Auth)  │     │
│  └──────────┘  └──────────┘  └──────────┘     │
└─────────────────────────────────────────────────┘
```

### Container Orchestration
- **Docker** for containerization
- **Kubernetes** (K8s) for orchestration
- **Helm** for deployment configuration
- **GitHub Actions** for CI/CD

## Scalability Considerations

### Horizontal Scaling
- Stateless application servers behind load balancer
- Read replicas for PostgreSQL
- Redis cluster for caching
- Elasticsearch cluster for audit logs

### Vertical Scaling
- Database connection pooling (PgBouncer)
- Query optimization and indexing
- Materialized views for complex reports
- Background job processing (Bull queues)

## Disaster Recovery

### Backup Strategy
- **Database:** Daily full backups + hourly incremental
- **Audit logs:** Real-time replication to secondary
- **Object storage:** Cross-region replication
- **Configuration:** Git version control

### Recovery Objectives
- **RPO (Recovery Point Objective):** 1 hour
- **RTO (Recovery Time Objective):** 4 hours
- **Availability target:** 99.9% (8.76 hours downtime/year)

## Module Communication

### Synchronous (REST)
- Direct module-to-module calls for real-time operations
- Circuit breaker pattern for resilience
- Timeout and retry policies

### Asynchronous (Events)
- Event bus for cross-module communication
- Eventual consistency for non-critical operations
- Dead letter queues for failed events

### Shared Kernel
- Common entities (User, Patient, Department)
- Shared utilities (date, validation, encryption)
- Common interfaces and DTOs
