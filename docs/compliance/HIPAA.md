# HIPAA Compliance Guide

## Overview

HMS is designed to comply with the Health Insurance Portability and Accountability Act (HIPAA) Privacy Rule, Security Rule, and Breach Notification Rule. This guide covers the technical safeguards implemented in the system.

## Technical Safeguards

### 1. Access Control (§164.312(a))

#### Unique User Identification
- Every user has a unique username/email
- No shared accounts permitted
- User IDs are immutable (never reused)

#### Emergency Access (Break-Glass)
- Admin-granted access for emergencies
- 1-hour time window
- Full audit trail maintained
- Compliance review required within 24 hours
- Frequency alerts for abuse prevention

#### Automatic Logoff
- 15-minute inactivity timeout (HIPAA strict)
- Configurable per role (doctors: 10min, admin: 15min)
- Silent refresh for active sessions
- Forced logout on password change

#### Encryption & Decryption
- AES-256 encryption at rest for all PHI
- TLS 1.3 encryption in transit
- Database-level encryption (PostgreSQL TDE)
- File-level encryption for attachments (MinIO)

### 2. Audit Controls (§164.312(b))

#### 6-Field Audit Capture
Every audited event records:
1. **Who** - User ID, name, role
2. **What** - Action performed, resource affected
3. **When** - Timestamp (UTC, millisecond precision)
4. **Where** - IP address, device, location
5. **Why** - Reason for access (if applicable)
6. **Patient** - Affected patient ID (if applicable)

#### Audit Log Storage
- Separate Elasticsearch cluster (not in primary DB)
- Hash chain integrity (tamper-evident)
- 6-year retention (HIPAA minimum)
- Immutable once written

#### Audit Alerting
- Pattern detection (unusual access frequency)
- After-hours access alerts
- Bulk data export alerts
- Failed authentication attempts
- Break-glass usage alerts

### 3. Integrity Controls (§164.312(c))

#### Data Integrity
- Database constraints (NOT NULL, UNIQUE, FK)
- Input validation (server-side, Zod schemas)
- Checksums for file uploads
- Version control for clinical notes

#### Transmission Integrity
- TLS 1.3 with forward secrecy
- HMAC for API message signing
- Certificate pinning for mobile apps

### 4. Authentication (§164.312(d))

#### Multi-Factor Authentication
- **Primary:** Push notification (HMS Authenticator)
- **Fallback:** TOTP (Time-based One-Time Password)
- **Conditional:** New device detection triggers MFA
- **Required:** For all users accessing PHI

#### Password Policy
- Minimum 12 characters
- Must include: uppercase, lowercase, number, special character
- 90-day rotation requirement
- Cannot reuse last 12 passwords
- 5 failed attempts → 30-minute lockout
- Breach password database check (HaveIBeenPwned)

### 5. Transmission Security (§164.312(e))

#### Encryption in Transit
- TLS 1.3 for all HTTP traffic
- HSTS (HTTP Strict Transport Security)
- Certificate transparency logging
- Perfect forward secrecy (ECDHE)

#### Secure API Communication
- JWT tokens with short expiry (15 min)
- Refresh token rotation (8 hour max)
- HttpOnly, Secure, SameSite cookies
- CORS whitelist enforcement

## Physical Safeguards

### Facility Access Controls
- On-premise servers in locked data centers
- Cloud infrastructure (AWS/Azure) with SOC 2
- Biometric access for server rooms

### Workstation Security
- Automatic screen lock (15 minutes)
- encrypted hard drives
- USB port restrictions (optional)
- Clean desk policy enforcement

### Device & Media Controls
- Encrypted backups (AES-256)
- Secure disposal of media
- Inventory of all devices accessing PHI
- Remote wipe capability for mobile

## Administrative Safeguards

### Risk Assessment
- Annual security risk assessment
- Vulnerability scanning (monthly)
- Penetration testing (quarterly)
- Incident response plan

### Workforce Training
- HIPAA awareness training (annual)
- Security best practices training
- Phishing awareness (quarterly)
- Role-specific training

### Business Associate Agreements
- BAAs with all third-party vendors
- Cloud provider BAAs (AWS/Azure)
- SMS/email provider BAAs (Twilio/SendGrid)

## Breach Notification

### Breach Definition
- Unauthorized access to PHI
- Unauthorized disclosure of PHI
- Loss or theft of device with PHI
- Ransomware or malware affecting PHI

### Notification Timeline
- **60 days:** HHS notification (if >500 individuals)
- **60 days:** Individual notification
- **60 days:** Media notification (if >500 in a state)
- **Immediate:** Internal incident response

### Incident Response Steps
1. Contain the breach
2. Assess the scope
3. Notify compliance officer
4. Notify affected individuals
5. Notify HHS
6. Document lessons learned

## Implementation Checklist

### Phase 1 (Foundation)
- [x] Unique user identification
- [x] Automatic logoff (15-min timeout)
- [x] MFA (push notification + TOTP)
- [x] Audit logging (6-field capture)
- [x] Role-based access control
- [x] Break-glass emergency access
- [ ] Encryption at rest (AES-256)
- [ ] Audit log integrity (hash chain)

### Phase 2-3 (Patient + EHR)
- [ ] Patient data encryption
- [ ] Clinical note versioning
- [ ] Lab result integrity checks
- [ ] Prescription audit trail

### Phase 4-5 (Billing + Compliance)
- [ ] Insurance data encryption
- [ ] Claims audit trail
- [ ] Financial report access controls
- [ ] Compliance dashboard

### Phase 6+ (Advanced)
- [ ] Penetration testing
- [ ] Vulnerability scanning automation
- [ ] Incident response automation
- [ ] Business continuity testing

## Key Metrics

| Metric | Target | Current |
|--------|--------|---------|
| MFA Adoption | 100% | TBD |
| Audit Log Coverage | 100% | TBD |
| Encryption Coverage | 100% PHI | TBD |
| Mean Time to Detect | < 1 hour | TBD |
| Mean Time to Respond | < 4 hours | TBD |
| Failed Login Detection | Real-time | TBD |
| Break-Glass Reviews | 100% within 24hr | TBD |
