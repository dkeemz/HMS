# API Overview

## Base URL

```
Production:  https://hms.com/api/v1
Staging:     https://staging.hms.com/api/v1
Development: http://localhost:3001/api/v1
```

## Authentication

All API requests require a valid JWT token obtained via Keycloak.

### Get Access Token

```http
POST /auth/realms/hms/protocol/openid-connect/token
Content-Type: application/x-www-form-urlencoded

grant_type=password
&client_id=hms-backend
&username=user@hms.com
&password=***
```

### Use Token

```http
GET /api/v1/patients
Authorization: Bearer <access_token>
```

## API Versioning

- Current version: v1
- Version in URL path: `/api/v1/`
- Breaking changes only in new versions
- Deprecation notice: 6 months before removal

## Response Format

### Success

```json
{
  "status": "success",
  "data": {
    "id": "pat_abc123",
    "name": "John Doe",
    "dateOfBirth": "1990-01-15"
  },
  "meta": {
    "timestamp": "2026-07-14T12:00:00Z",
    "requestId": "req_xyz789"
  }
}
```

### Error

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [
      {
        "field": "email",
        "message": "Must be a valid email address"
      }
    ]
  },
  "meta": {
    "timestamp": "2026-07-14T12:00:00Z",
    "requestId": "req_xyz789"
  }
}
```

## Endpoints

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/login | Authenticate user |
| POST | /auth/logout | Invalidate session |
| POST | /auth/refresh | Refresh access token |
| POST | /auth/mfa/verify | Verify MFA code |

### Patients

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /patients | List patients (paginated) |
| POST | /patients | Register new patient |
| GET | /patients/:id | Get patient details |
| PUT | /patients/:id | Update patient |
| GET | /patients/:id/history | Medical history |
| GET | /patients/search | Search patients |

### Appointments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /appointments | List appointments |
| POST | /appointments | Create appointment |
| PUT | /appointments/:id | Update appointment |
| DELETE | /appointments/:id | Cancel appointment |
| GET | /appointments/available | Available slots |

### Encounters

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /encounters | List encounters |
| POST | /encounters | Start encounter |
| PUT | /encounters/:id | Update encounter |
| POST | /encounters/:id/close | Close encounter |

### Vitals

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /encounters/:id/vitals | Get vitals |
| POST | /encounters/:id/vitals | Record vitals |

### Prescriptions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /prescriptions | List prescriptions |
| POST | /prescriptions | Create prescription |
| PUT | /prescriptions/:id | Update prescription |

### Lab Orders

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /lab-orders | List lab orders |
| POST | /lab-orders | Order lab tests |
| GET | /lab-orders/:id/results | Get results |

### Billing

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /invoices | List invoices |
| POST | /invoices | Generate invoice |
| POST | /payments | Process payment |
| GET | /claims | List claims |
| POST | /claims | Submit claim |

### Attendance

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /attendance/clock-in | Clock in |
| POST | /attendance/clock-out | Clock out |
| GET | /attendance/my-schedule | My schedule |
| POST | /attendance/leave | Request leave |
| POST | /attendance/swap | Request shift swap |

### Servicom

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /complaints | List complaints |
| POST | /complaints | File complaint |
| PUT | /complaints/:id | Update complaint |
| POST | /feedback | Submit feedback |
| GET | /surveys | List surveys |
| POST | /surveys/:id/respond | Respond to survey |

### Administration

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /admin/users | List users |
| POST | /admin/users | Create user |
| PUT | /admin/users/:id | Update user |
| GET | /admin/roles | List roles |
| POST | /admin/roles | Create role |
| GET | /admin/audit-logs | Audit logs |
| GET | /admin/reports | Generate reports |

## Pagination

```http
GET /api/v1/patients?page=1&limit=20&sort=name
```

### Response

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "totalPages": 8
  }
}
```

## Filtering

```http
GET /api/v1/patients?department=cardiology&status=active
GET /api/v1/appointments?from=2026-07-01&to=2026-07-31
GET /api/v1/appointments?doctorId=doc_abc&status=confirmed
```

## Rate Limiting

- **Standard endpoints:** 100 requests/minute
- **Search endpoints:** 30 requests/minute
- **Auth endpoints:** 10 requests/minute
- **Bulk operations:** 5 requests/minute

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1626307200
```

## Webhooks

### Event Types

| Event | Description |
|-------|-------------|
| patient.created | New patient registered |
| patient.updated | Patient info changed |
| appointment.booked | Appointment scheduled |
| appointment.cancelled | Appointment cancelled |
| encounter.completed | Encounter closed |
| lab.result.ready | Lab results available |
| payment.received | Payment processed |
| complaint.filed | New complaint |
| complaint.escalated | Complaint escalated |

### Webhook Payload

```json
{
  "event": "patient.created",
  "timestamp": "2026-07-14T12:00:00Z",
  "data": {
    "id": "pat_abc123",
    "name": "John Doe"
  }
}
```

## FHIR API

HMS exposes a FHIR R4 API for clinical data exchange.

### Base URL

```
https://hms.com/fhir
```

### Supported Resources

| Resource | Read | Search | Create | Update |
|----------|------|--------|--------|--------|
| Patient | Yes | Yes | Yes | Yes |
| Encounter | Yes | Yes | Yes | Yes |
| Observation | Yes | Yes | Yes | Yes |
| Condition | Yes | Yes | Yes | Yes |
| MedicationRequest | Yes | Yes | Yes | Yes |
| DiagnosticReport | Yes | Yes | Yes | Yes |

### Example

```http
GET /fhir/Patient?identifier=http://hms.com/patients|pat_abc123
Accept: application/fhir+json
```

```json
{
  "resourceType": "Patient",
  "id": "pat_abc123",
  "identifier": [{
    "system": "http://hms.com/patients",
    "value": "pat_abc123"
  }],
  "name": [{
    "family": "Doe",
    "given": ["John"]
  }],
  "birthDate": "1990-01-15",
  "gender": "male"
}
```

## SDKs & Libraries

### JavaScript/TypeScript

```bash
npm install @hms/sdk
```

```typescript
import { HMS } from '@hms/sdk';

const hms = new HMS({
  baseUrl: 'https://hms.com/api/v1',
  apiKey: 'your-api-key'
});

const patient = await hms.patients.get('pat_abc123');
```

### Python

```bash
pip install hms-sdk
```

```python
from hms import HMSClient

client = HMSClient(
    base_url='https://hms.com/api/v1',
    api_key='your-api-key'
)

patient = client.patients.get('pat_abc123')
```

## Postman Collection

Import the HMS API collection:
```
https://www.postman.com/hms/api/collection/hms-api-v1
```

## OpenAPI Specification

```http
GET /api/v1/openapi.json
```

Swagger UI available at:
```
https://hms.com/api/docs
```
