# NDPA & Data Protection Compliance Guide

## Overview

HMS complies with the Nigerian Data Protection Act (NDPA) 2023, Nigeria Data Protection Regulation (NDPR) 2019, and related regulations. This guide covers data protection implementation.

## Key Regulations

### Nigerian Data Protection Act (NDPA) 2023
- **Scope:** All processing of personal data of Nigerian citizens/residents
- **Authority:** Nigeria Data Protection Commission (NDPC)
- **Penalties:** Up to 2% of annual gross revenue or ₦10 million

### Nigeria Data Protection Regulation (NDPR) 2019
- **Scope:** Personal data processing
- **Requirements:** Data protection audit, DPO appointment
- **Compliance:** Annual audit filing with NDPC

### Cybercrimes (Prohibition, Prevention) Act 2015
- **Scope:** Computer systems and data
- **Requirements:** Unauthorized access prevention, data integrity
- **Penalties:** fines and imprisonment

## Data Protection Principles

### 1. Lawfulness, Fairness, Transparency
- Clear privacy notices in English + local languages
- Explicit consent for data collection
- Purpose limitation (data used only for stated purposes)
- Patient rights documentation

### 2. Purpose Limitation
- Data collected for specific, explicit purposes
- No processing incompatible with original purpose
- Documentation of purposes in data inventory

### 3. Data Minimization
- Collect only necessary data
- Regular data audits to remove excess
- Field-level access controls

### 4. Accuracy
- Patient self-service for demographics updates
- Regular data quality checks
- Version control for clinical data

### 5. Storage Limitation
- Data retention schedules defined
- Automated deletion after retention period
- Archive for legally required data

### 6. Integrity & Confidentiality
- Encryption at rest and in transit
- Access controls (RBAC + MFA)
- Audit logging for all access
- Incident response procedures

## Patient Rights

### Right to be Informed
- Privacy notice at registration
- Clear explanation of data use
- Contact details for data officer
- Available in English, Hausa, Yoruba, Igbo

### Right of Access
- Patient portal for self-service access
- Data export (FHIR/JSON format)
- Response within 72 hours
- No fee for first request

### Right to Rectification
- Patient can update demographics via portal
- Clinical corrections via authorized staff only
- Audit trail for all changes

### Right to Erasure (Right to be Forgotten)
- Patient can request data deletion
- Exceptions: legal requirements, clinical safety
- Compliance review before deletion
- Confirmation sent to patient

### Right to Restrict Processing
- Patient can limit data processing
- Flag in system for restricted records
- Staff notified of restrictions

### Right to Data Portability
- Export in machine-readable format (FHIR)
- Secure transfer to other providers
- Patient-initiated via portal

### Right to Object
- Object to marketing/communication
- Opt-out of non-essential processing
- Record objection in system

## Data Protection Officer (DPO)

### Appointment
- Required under NDPA
- Responsible for compliance oversight
- Contact published in privacy notices

### Responsibilities
- Monitor compliance
- Advise on DPIAs
- Handle data subject requests
- Liaise with NDPC
- Train staff

## Data Protection Impact Assessment (DPIA)

### When Required
- New data processing activities
- Significant changes to existing processing
- High-risk processing (health data)
- New technology implementation

### DPIA Process
1. Describe the processing
2. Assess necessity and proportionality
3. Identify and assess risks
4. Identify measures to mitigate risks
5. Document and review

### HMS DPIAs
- [ ] Patient registration and records
- [ ] Clinical documentation
- [ ] Billing and insurance
- [ ] Staff attendance tracking
- [ ] Servicom feedback system
- [ ] Analytics and reporting

## Cross-Border Data Transfer

### Restrictions
- NDPA requires adequate protection in recipient country
- Standard Contractual Clauses (SCCs) required
- Patient consent for international transfers

### HMS Implementation
- Primary storage: Nigeria (on-premise/cloud)
- Backup: Regional AWS/Azure (Africa)
- Analytics: Anonymized data only
- FHIR exports: Patient-controlled

## Data Retention Schedule

| Data Type | Retention Period | Legal Basis |
|-----------|-----------------|-------------|
| Patient Records | 6 years after last encounter | NDPA, Medical Records Act |
| Audit Logs | 6 years | HIPAA, NDPA |
| Financial Records | 7 years | Companies Income Tax Act |
| Staff Records | 6 years after termination | Labour Act |
| Consent Forms | 6 years after expiry | NDPA |
| Camera Footage | 90 days | NDPR |

## Breach Response

### Notification to NDPC
- Within 72 hours of becoming aware
- Details of the breach
- Number of individuals affected
- Measures taken to address

### Notification to Data Subjects
- Without undue delay
- Nature of the breach
- Contact details for DPO
- Recommendations for protection

### Documentation
- All breaches logged
- Root cause analysis
- Remediation steps
- Lessons learned

## Implementation Checklist

### Phase 1 (Foundation)
- [ ] Privacy notice (English + local languages)
- [ ] Consent management system
- [ ] Data inventory
- [ ] DPO appointment
- [ ] Patient rights workflow

### Phase 2-3 (Patient + EHR)
- [ ] Patient portal data access
- [ ] Data export (FHIR format)
- [ ] Clinical data retention rules
- [ ] Consent tracking for clinical data

### Phase 4-5 (Billing + Compliance)
- [ ] Financial data retention
- [ ] Insurance data handling
- [ ] Cross-border transfer controls
- [ ] DPIA completion

### Phase 6+ (Advanced)
- [ ] Annual compliance audit
- [ ] Staff training program
- [ ] Breach simulation exercises
- [ ] NDPC filing

## Key Metrics

| Metric | Target |
|--------|--------|
| Privacy Notice Availability | 4 languages |
| Data Subject Requests | <72 hours response |
| DPIA Completion | 100% high-risk |
| Staff Training | 100% annually |
| Breach Notification | <72 hours |
| Audit Filing | Annual |
| Consent Documentation | 100% patients |
