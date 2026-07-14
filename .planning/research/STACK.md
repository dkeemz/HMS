# Technology Stack — Hospital Management System (HMS)

**Project:** HMS for 500+ doctor hospital chain, hybrid deployment, HIPAA + PDPA compliant
**Researched:** 2026-07-13
**Confidence:** HIGH (multiple production healthcare sources, 2026-dated references)

---

## Executive Summary

This stack is designed for a large-scale, greenfield HMS with full EHR, billing, scheduling, lab integration, and mobile access across 500+ doctors. The architecture is **microservices on Kubernetes** with a **modular monolith option** for faster initial delivery if the team is small. Every technology choice prioritizes **HIPAA/PDPA compliance**, **HL7 FHIR R4 interoperability**, **clinical-grade reliability (99.99% uptime)**, and **long-term maintainability**.

The core principle: **build compliance into the architecture, not onto it**. HIPAA retrofits cost 3x more than native design.

---

## 1. Frontend — Web Application

### Primary: React 19 + Next.js 15 + TypeScript

| Attribute | Detail |
|-----------|--------|
| **Library** | React 19.x with Next.js 15.x (App Router) |
| **Language** | TypeScript 5.x (strict mode) |
| **Styling** | Tailwind CSS 4.x + Radix UI (accessible primitives) |
| **State** | TanStack Query (server state) + Zustand (client state) |
| **Forms** | react-hook-form + Zod (validated schemas) |
| **Real-time** | Socket.io client or native EventSource (SSE) |

**Why this stack:**
- React + Next.js is the **dominant choice** across all 2026 healthcare HMS sources (EngineerBabu, WeBridge, Thinkitive, SpeedMVPs). It is the most deployed frontend framework for clinical dashboards.
- **Desktop-first with responsive** — clinical staff use desktop; patients use mobile web. Next.js SSR handles both.
- **Radix UI** provides WCAG 2.1 AA accessibility out of the box — critical for healthcare compliance.
- **TypeScript across the stack** (frontend + backend) prevents data-handling bugs in sensitive contexts.
- The Nirmitee case study (production EHR, 8 months, 6 engineers) used React + TypeScript and achieved <800ms page loads.

**What NOT to use:**
- **Angular** — Still viable but the 2026 HMS ecosystem has decisively shifted to React. Angular teams report 30-40% slower hiring for healthcare projects. No production HMS case study from 2025-2026 chose Angular over React.
- **Vue.js** — Insufficient enterprise healthcare ecosystem. Fewer HIPAA-pattern libraries, smaller community for medical integrations.
- **Plain JavaScript** — Absolutely not. TypeScript is non-negotiable for healthcare data integrity.

**Confidence:** HIGH — Every production HMS reference from 2025-2026 uses React/Next.js.

---

## 2. Frontend — Mobile Application

### Primary: React Native (New Architecture) + TypeScript

| Attribute | Detail |
|-----------|--------|
| **Framework** | React Native 0.76+ (New Architecture / Fabric + TurboModules) |
| **Language** | TypeScript 5.x |
| **Navigation** | React Navigation 7.x |
| **Secure Storage** | react-native-keychain (iOS Keychain / Android Keystore) |
| **Biometrics** | react-native-biometrics |
| **BLE (medical devices)** | react-native-ble-plx |
| **HTTP** | Axios or TanStack Query |

**Why React Native:**
- **Team synergy** — Same TypeScript/React skillset as the web frontend. A single team can build both web and mobile.
- **Larger healthcare ecosystem** — More battle-tested HIPAA libraries, FHIR client libraries, and BLE medical device integrations than Flutter (confirmed by practitioner experience shipping hospital apps for 100+ US hospitals).
- **Hiring** — Significantly easier and cheaper to hire React Native developers, especially in the US market.
- **Offline-first** — Realm or WatermelonDB provide rock-solid offline sync, essential for clinical environments with spotty WiFi.
- The SeeSaw Labs 2026 healthcare comparison confirms: "React Native's ecosystem currently has more ready-made libraries for common health integrations."

**When Flutter would be better (and when it's not our pick):**
- Flutter offers superior UI consistency and slightly better performance. If the team starts fresh with no React expertise, or needs multi-language RTL support (international hospital chains), Flutter is compelling.
- However, our team shares web + mobile React skills, and the healthcare-specific library ecosystem favors React Native.

**What NOT to use:**
- **Ionic/Capacitor** — Performance overhead of WebView layer is unacceptable for clinical workflows.
- **Pure native (Swift + Kotlin)** — Two codebases, double the cost, slower iteration. Not justified unless building a medical device app requiring deep OS integration.
- **Old React Native Architecture (Bridge)** — Must use the New Architecture (Fabric + TurboModules) for production healthcare in 2026. The bridge bottleneck causes latency in complex clinical screens.

**Confidence:** HIGH — Strong practitioner evidence for large-scale hospital deployments.

---

## 3. Backend — API Server

### Primary: NestJS 11 + TypeScript

| Attribute | Detail |
|-----------|--------|
| **Framework** | NestJS 11.x (Node.js 22 LTS) |
| **Language** | TypeScript 5.x |
| **API Style** | REST (primary) + GraphQL (patient chart views) |
| **ORM** | Drizzle ORM (recommended) or Prisma 6.x |
| **Task Queue** | BullMQ (Redis-backed) — medication reminders, appointment alerts |
| **WebSocket** | Socket.io or native WebSocket (real-time bed board, alerts) |
| **HL7/FHIR** | HAPI FHIR (Java sidecar) + custom HL7 v2 parser |

**Why NestJS:**
- **Module-per-domain architecture** — Each clinical domain (patients, appointments, billing, pharmacy, lab) is an isolated NestJS module with its own controller, service, and data layer. This is the standard pattern for healthcare microservices in 2026.
- **Built-in RBAC** — Guards, decorators, and interceptor patterns implement minimum-necessary access at the API layer, not just the UI layer (HIPAA requirement).
- **Immutability-friendly** — NestJS patterns naturally support append-only audit logging with write-only access from the application.
- **TypeScript across the entire stack** — One language, one team, shared types between frontend and backend.
- **Production proof** — The "PSI Nest" healthcare platform (HIPAA-compliant practice management) was built in 12 weeks with NestJS + passed independent HIPAA security assessment. The "hipaa-compliant-ehr-system" on GitHub uses NestJS microservices.
- **Scalable** — The Cognito Health case study migrated from Express to NestJS specifically for scalability in HIPAA/PIPEDA healthcare environments.

**Why not Python/FastAPI:**
- Python is preferred for **AI/ML-heavy** clinical decision support or NLP workloads. We recommend a **Python microservice for clinical decision support and drug interaction checking** alongside the NestJS core.
- For the primary API server handling scheduling, billing, and CRUD workflows, NestJS is superior due to TypeScript type safety, better async I/O for real-time features, and shared skillset with the frontend.

**What NOT to use:**
- **Express.js (without NestJS)** — Too unstructured for healthcare. Missing the module boundaries, guards, and interceptors that enforce HIPAA access controls. NestJS adds these as architectural defaults.
- **Java Spring Boot** — Viable but 3-5x the development time. Overkill unless the team has deep Java expertise and no TypeScript capability.
- **PHP/Laravel** — Viable for simpler HMS builds (single facility, < 50 doctors). For 500+ doctors and microservices, it creates architectural friction.
- **Django/Flask** — Use only for the ML/NLP microservice, not the primary API.

**Confidence:** HIGH — Multiple production HIPAA-compliant healthcare platforms built with NestJS.

---

## 4. Secondary Backend — Clinical AI/ML Service

### Python 3.12 + FastAPI

| Attribute | Detail |
|-----------|--------|
| **Framework** | FastAPI 0.115+ |
| **Language** | Python 3.12 |
| **ML** | PyTorch 2.x or scikit-learn |
| **NLP** | Clinical NLP for ambient documentation, drug interaction checking |
| **FHIR** | fhir.resources (Python FHIR library) |

**Why a separate Python service:**
- Clinical decision support, drug interaction checking, and AI-assisted documentation require Python's ML ecosystem.
- Keeps the Node.js/NestJS API clean and fast for CRUD workflows.
- Independent scaling — ML inference has different resource profiles than API serving.

**Confidence:** MEDIUM — The specific ML requirements will shape this service significantly. Start with basic drug interaction rules and evolve toward AI-assisted documentation.

---

## 5. Database — Relational (Primary Transaction Store)

### PostgreSQL 17 (on AWS RDS Multi-AZ)

| Attribute | Detail |
|-----------|--------|
| **Database** | PostgreSQL 17.x |
| **Hosting** | AWS RDS Multi-AZ (automatic failover) |
| **Encryption** | AES-256 at rest (RDS encryption) + TLS 1.3 in transit |
| **Extension** | TimescaleDB 2.18+ (for time-series clinical data) |
| **Row-Level Security** | PostgreSQL RLS policies for tenant isolation |
| **Connection Pooling** | PgBouncer or RDS Proxy |

**Why PostgreSQL:**
- **Universal consensus** — Every 2026 HMS/EHR source recommends PostgreSQL as the primary transactional database. It is the single most agreed-upon technology choice.
- **HIPAA-eligible on RDS** with AWS BAA coverage.
- **FHIR-native JSON support** — Store FHIR resources as JSONB, query with GIN indexes.
- **Row-Level Security (RLS)** — Database-level PHI access control that prevents data leakage even if application code has bugs. This is the architectural pattern recommended by HIPAA security experts.
- **TimescaleDB extension** — Add time-series capability for vital signs, monitoring data, and sensor data without a separate database. Continuous aggregates pre-compute clinical summaries. 90-95% compression on historical clinical data.
- **ACID compliance** — Non-negotiable for billing, medication administration, and clinical documentation.

**Why add TimescaleDB extension:**
- Patient vital signs, continuous monitoring data, and bed occupancy metrics are inherently time-series workloads.
- TimescaleDB extends PostgreSQL (not a separate DB) — one operational surface, full SQL JOINs with relational tables.
- Continuous aggregates pre-compute daily/weekly clinical summaries, making dashboards 100-1000x faster.
- Data retention policies automatically drop raw data beyond regulatory retention periods.

**What NOT to use:**
- **MySQL** — Viable but PostgreSQL has superior JSONB support, RLS, and healthcare ecosystem. Every FHIR server comparison favors PostgreSQL.
- **MongoDB as primary** — Use only for specific document-storage needs (DICOM metadata, scanned documents). Not for transactional clinical data where ACID and referential integrity are critical.
- **SQL Server** — Adds licensing cost with no architectural advantage. Only choose if the organization is a Microsoft shop.

**Confidence:** HIGH — Universal recommendation across all healthcare technology sources.

---

## 6. Database — Document Store (FHIR Clinical Data)

### HAPI FHIR 8.x Server (Java, PostgreSQL backend)

| Attribute | Detail |
|-----------|--------|
| **FHIR Server** | HAPI FHIR 8.x (open source, Apache 2.0) |
| **Backend** | PostgreSQL (shared or dedicated) |
| **Search Engine** | Elasticsearch 8.x (for FHIR search offloading) |
| **FHIR Version** | R4 (mandatory for ONC/CMS compliance) |

**Why HAPI FHIR:**
- **Most deployed open-source FHIR server** — Used by the US Veterans Affairs (VA) Lighthouse API for 9 million veterans. Battle-tested at 100M+ resources.
- **Best search conformance** — The mock.health 2026 benchmark confirmed HAPI passes all 23 FHIR R4 conformance checks and has the best search performance (35ms p50 at 64K patients, zero errors).
- **Full SMART on FHIR support** — Required for patient-facing and provider-facing third-party app access.
- **Full Bulk Data Export** — Required for population-level analytics and quality reporting.
- **Self-hosted with full control** — No vendor lock-in, no per-operation costs. Runs anywhere the JVM runs.
- Deployed as a **sidecar/container alongside the NestJS services** on Kubernetes.

**Alternative: Medplum** — Managed FHIR-as-a-service with better developer experience (TypeScript SDK, admin console). Good if you want less infrastructure management. However, search has a ~14% error rate on complex blended queries per 2026 benchmarks. Use HAPI for production reliability.

**Alternative: AWS HealthLake** — Only if you need built-in NLP (Comprehend Medical) on clinical text AND you're deeply AWS-native. Most expensive option ($0.10/GB/month + $0.07/1K reads). Slower search than self-hosted HAPI. Not recommended as primary.

**What NOT to use:**
- **Building a custom FHIR server** — Massive undertaking. FHIR R4 has 145+ resource types, complex search parameters, and strict conformance requirements. Use HAPI.
- **Google Cloud Healthcare API** — Only if GCP-native. Cheaper managed option than HealthLake but creates cloud lock-in.

**Confidence:** HIGH — HAPI FHIR is the industry standard for self-hosted FHIR R4.

---

## 7. Database — Cache & Real-Time State

### Redis 7.x

| Attribute | Detail |
|-----------|--------|
| **Database** | Redis 7.x (ElastiCache or self-managed) |
| **Use Cases** | Session management, real-time bed board, rate limiting, queue backend |
| **Encryption** | In-transit TLS + at-rest (ElastiCache encryption) |

**Why Redis:**
- Real-time bed availability, patient tracking boards, and clinical alerts need sub-millisecond reads. Redis is the standard pattern.
- Backs BullMQ for appointment reminders, medication alerts, and async task processing.
- Caches frequently accessed reference data (drug databases, ICD-10/CPT code tables).
- Reduced EMR API costs by 85% in production healthcare deployments through intelligent caching.

**Confidence:** HIGH — Standard across all HMS architectures.

---

## 8. Database — Search

### Elasticsearch 8.x

| Attribute | Detail |
|-----------|--------|
| **Engine** | Elasticsearch 8.x |
| **Use Cases** | Clinical documentation search, patient search, medication lookup |

**Why Elasticsearch:**
- Full-text search across progress notes, discharge summaries, and operative notes is critical for clinical review workflows.
- Powers HAPI FHIR search offloading for sub-millisecond search at scale.
- HIPAA-compliant when deployed with proper access controls and encryption.

**Confidence:** HIGH — Standard in clinical search implementations.

---

## 9. Authentication & Authorization

### Primary: Keycloak 26.x (Self-Hosted)

| Attribute | Detail |
|-----------|--------|
| **Identity Provider** | Keycloak 26.x (open source, CNCF-adjacent) |
| **Protocols** | OAuth 2.0, OpenID Connect, SAML 2.0 |
| **MFA** | TOTP, WebAuthn/Passkeys, hardware security keys |
| **RBAC** | Fine-grained authorization with UMA 2.0 |
| **LDAP/AD** | Built-in user federation (connects to hospital Active Directory) |
| **Hosting** | Self-hosted on Kubernetes (data sovereignty guaranteed) |

**Why Keycloak:**
- **Data sovereignty** — Critical for healthcare. PHI-related identity data never leaves your infrastructure. No third-party sees user credentials.
- **LDAP/AD federation** — Hospitals have existing Active Directory. Keycloak connects directly, enabling SSO for clinicians who move between workstations.
- **Zero per-user cost** — At 500+ doctors plus thousands of nurses, billing staff, and patients, per-MAU pricing becomes prohibitively expensive (Auth0 would cost $3,000-15,000+/month at scale).
- **Full HIPAA control** — Self-hosted means you control the BAA chain, audit logs, and session management.
- **Multi-tenancy** — Realms for full tenant isolation between hospital facilities.
- **Step-up authentication** — Require stronger MFA before accessing highly sensitive clinical data.

**When Auth0 would be better:**
- If the team is small (< 5 engineers) and needs to ship auth in days, not weeks.
- Auth0 has better developer experience and built-in HIPAA BAA on Enterprise plans.
- Trade-off: At 500+ doctors + patient portal users, Auth0 costs $5,000+/month vs $300-600/month for self-hosted Keycloak.

**What NOT to use:**
- **Custom auth implementation** — Never build your own auth for HIPAA. Use a proven IdP.
- **Firebase Auth** — Not HIPAA-eligible on standard plans. Not designed for healthcare RBAC.
- **AWS Cognito** — Only if deeply AWS-native. Limited customization, dated UX, vendor lock-in. Cannot export user passwords for migration.

**Confidence:** HIGH — Keycloak is the recommended choice for healthcare data sovereignty and cost at scale.

---

## 10. Real-Time Communication

### Socket.io 4.x / Native WebSocket

| Attribute | Detail |
|-----------|--------|
| **Protocol** | WebSocket with Socket.io fallback |
| **Use Cases** | Bed board updates, patient tracking, clinical alerts, notifications |
| **Server** | NestJS Gateway (WebSocket adapter) |
| **Scaling** | Redis adapter for multi-pod pub/sub |

**Why WebSocket/Socket.io:**
- Clinical dashboards (bed board, patient tracking) require sub-2-second propagation of status changes to all open instances.
- Socket.io provides automatic reconnection, fallback to long-polling, and rooms/namespaces for targeted broadcasting.
- Redis adapter enables horizontal scaling across Kubernetes pods.

**Confidence:** HIGH — Standard pattern for real-time clinical dashboards.

---

## 11. File Storage

### AWS S3 (HIPAA-Eligible)

| Attribute | Detail |
|-----------|--------|
| **Service** | Amazon S3 (under AWS BAA) |
| **Encryption** | SSE-KMS (customer-managed keys) |
| **Use Cases** | Medical documents, scanned records, clinical photos, DICOM metadata |
| **Access** | Pre-signed URLs with time-limited access |
| **Lifecycle** | Automatic deletion policies for retention compliance |

**Why S3:**
- HIPAA-eligible with AWS BAA. Most widely used object storage in healthcare.
- SSE-KMS encryption with customer-managed keys satisfies HIPAA §164.312(a)(2)(iv).
- Pre-signed URLs prevent direct PHI exposure in application tiers.
- Lifecycle policies automate retention/deletion (6-year minimum for HIPAA).

**For DICOM imaging specifically:**
- Consider **Orthanc** (open-source DICOM server) for receiving and querying DICOM images.
- Store images in S3 with DICOM metadata indexed in PostgreSQL.
- Use **Cornerstone.js** or **OHIF Viewer** for web-based DICOM viewing.

**What NOT to use:**
- **Cloudflare R2** — BAA only on Enterprise tier. Not recommended as primary for healthcare.
- **MinIO self-hosted** — Viable if on-premise storage is required, but adds operational overhead.
- **Google Cloud Storage** — Only if GCP-native.

**Confidence:** HIGH — AWS S3 is the standard for healthcare file storage.

---

## 12. API Design

### REST (Primary) + GraphQL (Patient Chart Views) + FHIR R4 (Interoperability)

| Layer | Style | When |
|-------|-------|------|
| **Core API** | REST (OpenAPI/Swagger documented) | CRUD operations, scheduling, billing |
| **Patient Chart** | GraphQL (Apollo Server) | Complex clinical views needing different data shapes |
| **External Integration** | FHIR R4 REST | EHR interop, payer access, patient access APIs |
| **Internal Messaging** | HL7 v2 over MLLP/TCP | Legacy system integration (lab analyzers, pharmacy) |

**Why this hybrid approach:**
- **REST** is the workhorse — well-understood, cacheable, audit-friendly. Use for 80% of API surface.
- **GraphQL** excels for patient chart views where different screens need different data subsets. The Nirmitee EHR case study confirmed: "GraphQL lets each view request exactly what it needs, eliminating over-fetching that makes legacy EHRs slow."
- **FHIR R4** is mandatory for interoperability. The HMS must expose FHIR R4 APIs for patient access, payer access, and provider-to-provider data exchange (CMS 2026 interoperability rules).
- **HL7 v2** is still dominant for internal hospital messaging (lab results, ADT events). Must be supported alongside FHIR.

**What NOT to use:**
- **GraphQL everywhere** — Overkill for simple CRUD. Adds complexity without benefit for scheduling and billing APIs.
- **gRPC only** — Excellent for internal service-to-service, but external healthcare integrations expect REST/FHIR.
- **SOAP** — Only for legacy system integrations that require it.

**Confidence:** HIGH — Proven pattern in production EHR systems.

---

## 13. Integration Engine

### Mirth Connect / NextGen Connect 4.x

| Attribute | Detail |
|-----------|--------|
| **Engine** | Mirth Connect 4.x (NextGen Connect) |
| **License** | Open source (MPL 2.0) for v4.5.x; newer versions commercial |
| **Message Formats** | HL7 v2, FHIR R4, X12 EDI, DICOM |
| **Deployment** | On-premise (hospital data center) + Docker/Kubernetes |
| **Backend DB** | PostgreSQL |

**Why Mirth Connect:**
- **Most widely deployed healthcare integration engine in the US** — Handles hundreds of millions of clinical messages annually.
- **Handles the hybrid reality** — Lab analyzers and pharmacy systems speak HL7 v2 over MLLP. Mirth translates between legacy and modern FHIR.
- **Runs on-premise** in the hospital data center, receives HL7 messages from local systems, forwards to cloud HMS over encrypted VPN.
- **FHIR facade** — Wraps legacy HL7 v2 systems with modern FHIR R4 APIs.

**Important licensing note:**
- Mirth Connect v4.5.2 is the last MPL 2.0 open-source version.
- Starting v4.6 (2025), NextGen moved to commercial licensing.
- **Recommendation:** Use v4.5.2 for initial deployment (open source). Evaluate commercial licensing or community forks for future upgrades.

**Confidence:** HIGH — Industry standard healthcare integration engine.

---

## 14. Deployment Infrastructure — Hybrid Cloud

### AWS (Primary Cloud) + On-Premise Kubernetes

| Component | Technology | Why |
|-----------|-----------|-----|
| **Cloud Platform** | AWS (HIPAA BAA signed) | Most mature HIPAA documentation, most HIPAA-eligible services |
| **Container Orchestration** | Amazon EKS (Kubernetes 1.30+) | Standard for healthcare microservices, auto-scaling, self-healing |
| **CI/CD** | GitHub Actions + ArgoCD | GitOps deployment, auditable, reproducible |
| **Infrastructure as Code** | Terraform 1.x | Reproducible, auditable, version-controlled infrastructure (matters for HIPAA audits) |
| **Service Mesh** | Istio or Linkerd | mTLS between services, traffic management, observability |
| **On-Premise** | Kubernetes (RKE2 or k3s) | Runs Mirth Connect + legacy interface engines in hospital data center |
| **VPN** | AWS Site-to-Site VPN | Encrypted tunnel between cloud HMS and on-premise Mirth Connect |
| **CDN** | CloudFront (non-PHI content only) | Static assets, patient portal UI |
| **DNS** | Route 53 | Health-check routing |

**Why AWS over Azure/GCP:**
- **Most HIPAA-eligible services** — AWS has the broadest set of services covered under their BAA.
- **Largest healthcare cloud ecosystem** — Most healthcare ISVs build on AWS.
- **HealthLake + HealthImaging** — If you need managed FHIR or DICOM services later.
- **Cost** — For a 200+ bed hospital HMS: $8,000-18,000/month including compute, database, storage, CDN, and monitoring.
- **Terraform support** — Best IaC support among cloud providers.

**Hybrid architecture rationale:**
- The HMS application runs in AWS (EKS, RDS, S3).
- Mirth Connect runs on-premise in the hospital's data center (receives HL7 from local lab analyzers, pharmacy systems).
- Encrypted VPN connects on-premise Mirth to cloud HMS.
- This provides cloud benefits (scalability, DR) without sacrificing legacy system integration.

**What NOT to use:**
- **DigitalOcean / Linode** — No HIPAA BAA available. Cannot be used for any PHI workload.
- **Vercel/Netlify** — For frontend hosting only (no PHI processed there). Not for backend services.
- **Self-managed VMs** — Adds operational burden without the benefits of container orchestration.
- **Single-cloud without DR** — Must have cross-region failover for clinical data.

**Confidence:** HIGH — AWS hybrid with on-premise integration engines is the standard pattern.

---

## 15. Compliance & Security

### Layered Defense Architecture

| Control | Implementation | Standard |
|---------|---------------|----------|
| **Encryption at rest** | AES-256 (RDS, S3, EBS via KMS) | HIPAA §164.312(a)(2)(iv) |
| **Encryption in transit** | TLS 1.3 (all API, DB, service-to-service) | HIPAA §164.312(e)(1) |
| **Key management** | AWS KMS (customer-managed keys, annual rotation) | HIPAA §164.312(a)(2)(iv) |
| **Access control** | RBAC + ABAC at API layer + PostgreSQL RLS | HIPAA §164.312(a)(1) |
| **MFA** | Keycloak (TOTP, WebAuthn, hardware keys) | HIPAA §164.312(d) |
| **Audit logging** | Immutable append-only logs (6-year retention) | HIPAA §164.312(b) |
| **Audit storage** | S3 Object Lock (COMPLIANCE mode) + separate DB | Tamper-evident |
| **PHI redaction** | Application-level logging middleware | PHI never enters logs |
| **Network isolation** | VPC private subnets for all PHI services | HIPAA network segmentation |
| **WAF** | AWS WAF | OWASP Top 10 protection |
| **DDoS** | AWS Shield Standard | Infrastructure protection |
| **Secret management** | AWS Secrets Manager / HashiCorp Vault | Never in code or env files |
| **Penetration testing** | Annual external pentest ($15K-$40K) | HIPAA risk analysis |
| **Dependency scanning** | Snyk / Dependabot in CI | Supply chain security |
| **SAST** | Semgrep in CI | Code vulnerability analysis |
| **Container scanning** | Trivy | Image vulnerability scanning |

**HIPAA-critical architectural decisions:**
1. **PHI in separate database** — Only decrypt when genuinely required. Limits exposure surface.
2. **RBAC at database level** — PostgreSQL RLS, not just UI hiding. UI-only hiding is the #1 HIPAA audit fail.
3. **Audit logs architecturally independent** — Separate from application logs. Write-once storage.
4. **BAA chain documented** — Every vendor in the PHI data path has a signed BAA before first patient record.
5. **Break-the-glass procedures** — Emergency access with mandatory audit documentation and time limits.

**PDPA considerations:**
- Data residency requirements (store patient data in the region of operation).
- Consent management for data processing.
- Right to erasure workflows.
- Data protection officer appointment.

**Confidence:** HIGH — These are well-documented HIPAA architectural requirements from multiple compliance-focused sources.

---

## 16. Monitoring & Observability

### Grafana + Prometheus + Loki + Tempo

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Metrics** | Prometheus + Grafana | Application + infrastructure metrics, clinical KPIs |
| **Logging** | Loki (or AWS CloudWatch Logs) | Centralized structured logging (PHI redacted) |
| **Tracing** | Tempo (or AWS X-Ray) | Distributed tracing across microservices |
| **APM** | Grafana Cloud or Datadog (HIPAA tier) | Application performance monitoring |
| **Alerting** | Prometheus Alertmanager + PagerDuty | Clinical-critical alert routing |
| **Audit** | CloudTrail + custom audit service | HIPAA audit trail |

**Why this stack:**
- **Grafana/Prometheus** is the standard for Kubernetes observability. Free, open-source, battle-tested.
- **Loki** for log aggregation keeps costs low (indexes labels, not full text).
- **HIPAA-compliant monitoring** — Datadog offers a HIPAA tier (with BAA) if you need managed APM. Alternatively, self-hosted Grafana stack avoids the BAA question entirely.
- **Structured logging with PHI redaction** — Application middleware strips PHI before logs leave the service boundary. Never log patient names, diagnoses, or clinical notes.

**What NOT to use:**
- **ELK Stack (Elasticsearch + Logstash + Kibana)** — Expensive at scale, complex to operate. Loki is simpler for log aggregation.
- **New Relic** — HIPAA BAA available but pricing is per-host and becomes expensive at scale.
- **Splatter** — Overkill for initial deployment. Consider for mature SOC operations.

**Confidence:** HIGH — Grafana stack is the standard for Kubernetes-native observability.

---

## 17. Message Queue / Event Bus

### RabbitMQ 4.x or AWS SQS/SNS

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Async messaging** | RabbitMQ 4.x (self-hosted) or AWS SQS | Decoupled microservice communication |
| **Event streaming** | AWS SNS (for event fan-out) | Patient events, clinical alerts |
| **Dead letter queues** | Built-in DLQ support | Failed message retry and alerting |

**Why:**
- Decouples services — billing doesn't call scheduling directly; it subscribes to events.
- Reliable delivery — Appointment reminders, medication alerts must not be lost.
- Buffering — Absorb traffic spikes during morning rounds or discharge surges.

**Confidence:** HIGH — Standard microservice communication pattern.

---

## 18. DevOps & Development Tools

| Tool | Purpose |
|------|---------|
| **Monorepo** | Turborepo or Nx (if microservices share packages) |
| **Package manager** | pnpm (faster, disk-efficient) |
| **Code quality** | ESLint + Prettier (enforced in CI) |
| **Git hosting** | GitHub Enterprise (with branch protection) |
| **CI/CD** | GitHub Actions (build, test, scan, deploy) |
| **GitOps** | ArgoCD (declarative Kubernetes deployments) |
| **Container registry** | Amazon ECR |
| **Local dev** | Docker Compose + Minikube (or Tilt) |
| **API docs** | Swagger/OpenAPI (auto-generated from NestJS decorators) |
| **FHIR validation** | HAPI FHIR Validator (in CI pipeline) |

**Confidence:** HIGH — Standard DevOps toolchain for healthcare microservices.

---

## 19. Telehealth / Video (Phase 2)

| Component | Technology | Why |
|-----------|-----------|-----|
| **Video** | Twilio Video or Daily.co | Both offer HIPAA BAAs, WebRTC-based |
| **Recording** | Encrypted cloud recording with audit trails | Clinical documentation requirements |
| **Chat** | Socket.io (integrated) | In-visit messaging |

**Note:** Telehealth is typically Phase 2. Choose the video SDK after core HMS is stable.

**Confidence:** MEDIUM — Video requirements will shape during phase planning.

---

## Summary: Complete Stack at a Glance

| Layer | Technology | Confidence |
|-------|-----------|------------|
| **Web Frontend** | React 19 + Next.js 15 + TypeScript + Tailwind + Radix UI | HIGH |
| **Mobile** | React Native (New Architecture) + TypeScript | HIGH |
| **API Backend** | NestJS 11 + TypeScript + Drizzle ORM | HIGH |
| **ML/AI Service** | Python 3.12 + FastAPI | MEDIUM |
| **Primary Database** | PostgreSQL 17 + TimescaleDB extension (AWS RDS Multi-AZ) | HIGH |
| **FHIR Server** | HAPI FHIR 8.x | HIGH |
| **Cache** | Redis 7.x (ElastiCache) | HIGH |
| **Search** | Elasticsearch 8.x | HIGH |
| **Auth/IdP** | Keycloak 26.x | HIGH |
| **File Storage** | AWS S3 (SSE-KMS) | HIGH |
| **Integration Engine** | Mirth Connect 4.5.x (on-premise) | HIGH |
| **Cloud** | AWS (EKS, RDS, S3, KMS, CloudTrail) | HIGH |
| **On-Premise** | Kubernetes (RKE2) + Mirth Connect | HIGH |
| **CI/CD** | GitHub Actions + ArgoCD + Terraform | HIGH |
| **Monitoring** | Grafana + Prometheus + Loki + Tempo | HIGH |
| **Message Queue** | RabbitMQ 4.x or AWS SQS/SNS | HIGH |

---

## Installation — Core Dependencies

```bash
# Frontend
npx create-next-app@latest hms-web --typescript --tailwind --app
npm install @radix-ui/react-* zustand @tanstack/react-query react-hook-form zod socket.io-client

# Backend
npx @nestjs/cli new hms-api --package-manager pnpm --skip-git
pnpm add @nestjs/config @nestjs/passport @nestjs/jwt @nestjs/throttler drizzle-orm bullmq ioredis
pnpm add -D drizzle-kit typescript @types/node

# Mobile
npx react-native init HMSMobile --template react-native-template-typescript
npm install @react-navigation/native react-native-keychain react-native-biometrics react-native-ble-plx

# FHIR Server (Docker)
docker pull hapiproject/hapi:latest

# Mirth Connect (Docker)
docker pull nextgenhealthcare/connect:4.5.2

# Keycloak (Helm)
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install keycloak bitnami/keycloak --set auth.adminPassword=<secure>
```

---

## Sources

| Source | Date | Confidence | URL |
|--------|------|------------|-----|
| AcquaintSoft - HMS Development Guide 2026 | Jun 2026 | HIGH | https://acquaintsoft.com/blog/hospital-management-system-development |
| EngineerBabu - HMS Complete Guide 2026 | Jun 2026 | HIGH | https://engineerbabu.com/blog/hospital-management-system-development-complete-guide/ |
| WeBridge - Hospital Management Tech Stack 2026 | 2026 | HIGH | https://webridge.co/tech-stack/hospital-management-tech-stack |
| Thinkitive - EHR Tech Stack 2026 | Jun 2026 | HIGH | https://www.thinkitive.com/blog/ehr-tech-stack-2026/ |
| Nirmitee - Cloud-Native EHR Case Study | Feb 2026 | HIGH | https://nirmitee.io/case-study/building-ehr-from-scratch-cloud-native-fhir-microservices/ |
| SpeedMVPs - Healthtech Stack 2026 | Jun 2026 | HIGH | https://speedmvps.com/blog/best-tech-stack-for-healthtech-apps |
| Attract Group - HIPAA App Development | Jun 2026 | HIGH | https://attractgroup.com/blog/hipaa-compliant-app-development/ |
| QuantLab - HIPAA SaaS Architecture | May 2026 | HIGH | https://quantlabusa.dev/blog/hipaa-compliant-saas-architecture |
| SeeSaw Labs - RN vs Flutter Healthcare 2026 | Mar 2026 | HIGH | https://seesawlabs.com/the-lab/guides/react-native-vs-flutter-vs-native-healthcare-2026 |
| mock.health - FHIR Server Comparison | May 2026 | HIGH | https://mock.health/blog/fhir-server-compare |
| mock.health - FHIR Server Performance | May 2026 | HIGH | https://mock.health/blog/fhir-server-performance |
| Intellizu - Keycloak vs Auth0 vs Cognito | May 2026 | HIGH | https://intellizu.com/articles/keycloak-vs-auth0-vs-cognito/ |
| EngineerBabu - EHR Platform Development | Jun 2026 | HIGH | https://engineerbabu.com/blog/ehr-platform-development/ |
| Pulse Tech Stacks - Hospital Tech Stack | May 2026 | HIGH | https://pulserevops.com/tech-stacks/tk0032 |
