# Getting Started Guide

## For Administrators

### Initial Setup

#### 1. System Requirements
- Server: 8+ CPU cores, 32GB RAM, 500GB SSD
- Database: PostgreSQL 17+
- Cache: Redis 7+
- Auth: Keycloak 26+
- Search: Elasticsearch 8+
- OS: Ubuntu 22.04 LTS or RHEL 9

#### 2. Installation

```bash
# Clone the repository
git clone https://github.com/dkeemz/HMS.git
cd HMS

# Install dependencies
npm install

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Set up database
npx prisma migrate dev
npx prisma db seed

# Start development
npm run dev
```

#### 3. Environment Configuration

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/hms

# Redis
REDIS_URL=redis://localhost:6379

# Keycloak
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=hms
KEYCLOAK_CLIENT_ID=hms-backend

# FHIR
FHIR_SERVER_URL=http://localhost:8081/fhir

# Email (SendGrid)
SENDGRID_API_KEY=your-key
SENDGRID_FROM=noreply@hms.com

# SMS (Twilio)
TWILIO_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
```

#### 4. Keycloak Setup

```bash
# Start Keycloak
docker run -p 8080:8080 \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=admin \
  quay.io/keycloak/keycloak:26.0

# Create HMS realm
# Import HMS realm configuration from /config/keycloak/hms-realm.json
```

#### 5. Initial Admin Account

```bash
# Seed the database with initial admin
npm run seed:admin

# Default admin:
# Email: admin@hms.com
# Password: (check secure storage)
```

### User Management

#### Creating Users
1. Navigate to Administration > Users
2. Click "Add User"
3. Fill in required fields:
   - Email (becomes username)
   - First Name, Last Name
   - Role (from 15 predefined roles)
   - Department
4. Set temporary password
5. User receives welcome email with login instructions

#### Assigning Roles
1. Open user profile
2. Go to "Roles" tab
3. Click "Assign Role"
4. Select role(s) from list
5. Save changes
6. Role change is audit logged

#### Deactivating Users
1. Open user profile
2. Click "Deactivate"
3. Confirm action
4. User loses access immediately
5. Audit log preserved

### Department Setup

#### Creating Departments
1. Navigate to Administration > Departments
2. Click "Add Department"
3. Enter:
   - Department Name
   - Code (short identifier)
   - Head (assign doctor)
   - Parent Department (if sub-department)
4. Save

#### Managing Rooms & Beds
1. Navigate to Administration > Rooms
2. Add rooms by department/ward
3. Set bed capacity per room
4. Track bed status (available, occupied, maintenance)

---

## For Doctors

### First Login

1. Receive temporary credentials from admin
2. Navigate to HMS URL
3. Log in with email and temporary password
4. Change password immediately
5. Set up MFA (push notification recommended)
6. Complete profile setup

### Your Dashboard

Your personalized dashboard shows:
- **Today's Schedule:** All appointments for the day
- **Pending Tasks:** Lab results, prescriptions to sign
- **Recent Patients:** Last 10 patients seen
- **Quick Actions:** Start encounter, search patient

### Common Tasks

#### See a Patient
1. Click patient name from schedule
2. Review medical history
3. Click "Start Encounter"
4. Record vitals
5. Write clinical notes (SOAP template)
6. Add prescriptions/orders
7. Click "Complete Encounter"

#### Write a Prescription
1. In encounter, go to "Prescriptions" tab
2. Click "New Prescription"
3. Search medication
4. Set dosage, frequency, duration
5. System checks interactions/allergies
6. Send to pharmacy

#### Order Lab Tests
1. In encounter, click "Order Labs"
2. Select tests from panels
3. Add clinical notes
4. Submit order
5. Results delivered when ready

---

## For Nurses

### Your Dashboard
- Patients assigned to you today
- Vitals to record
- Medications to administer
- Tasks from doctors

### Common Tasks

#### Record Vitals
1. Open patient encounter
2. Go to "Vitals" tab
3. Enter measurements:
   - Blood Pressure (systolic/diastolic)
   - Heart Rate
   - Temperature
   - Respiratory Rate
   - Weight (kg)
   - Height (cm)
4. System calculates BMI automatically
5. Abnormal values highlighted in red

#### Administer Medication
1. View medication orders for your patients
2. Verify patient identity
3. Administer medication
4. Record administration time
5. Note any adverse reactions

---

## For Receptionists

### Your Dashboard
- Today's appointments
- Patients waiting
- Check-in queue
- Pending registrations

### Common Tasks

#### Register a Patient
1. Click "Register Patient"
2. Fill demographics:
   - Full Name, DOB, Gender
   - Phone, Email, Address
   - Next of Kin
3. Add insurance (if available)
4. System generates Patient ID
5. Print registration summary

#### Check In a Patient
1. Search for patient
2. Click "Check In"
3. Verify demographics
4. Notify assigned doctor
5. Patient waits for appointment

#### Schedule an Appointment
1. Click "New Appointment"
2. Search patient
3. Select doctor
4. Choose date/time from available slots
5. Select appointment type
6. Confirm
7. Patient receives SMS/email confirmation

---

## For Billing Staff

### Your Dashboard
- Pending invoices
- Payments to process
- Claims to submit
- Outstanding balances

### Common Tasks

#### Generate Invoice
1. Go to Billing > Pending Invoices
2. Review auto-generated charges
3. Add manual items if needed
4. Calculate total
5. Generate invoice
6. Print or email to patient

#### Process Payment
1. Select invoice
2. Choose payment method:
   - Cash
   - Card (POS)
   - Bank Transfer
   - Insurance
3. Process payment
4. Generate receipt
5. Update invoice status

#### Submit Insurance Claim
1. Go to Claims > New Claim
2. Select patient/invoice
3. Verify insurance details
4. Submit claim
5. Track status (Submitted → Under Review → Approved/Denied)

---

## For Patients (Portal)

### Accessing the Portal
1. Receive invitation email
2. Create account
3. Set up MFA
4. Log in to patient portal

### Your Portal Features
- **Appointments:** Book, view, cancel
- **Medical Records:** View history, lab results
- **Prescriptions:** View current medications
- **Billing:** View invoices, make payments
- **Messages:** Secure messaging with providers
- **Feedback:** Submit complaints, rate services

### Book an Appointment
1. Go to Appointments > Book New
2. Select department
3. Choose doctor (or let system recommend)
4. Pick date and time
5. Add reason for visit
6. Confirm
7. Receive confirmation SMS/email

### View Lab Results
1. Go to Medical Records > Lab Results
2. Select test
3. View results with reference ranges
4. Abnormal values highlighted
5. Add to favorites for tracking

---

## Keyboard Shortcuts

| Action | Windows | Mac |
|--------|---------|-----|
| Global Search | Ctrl+K | Cmd+K |
| New Patient | Ctrl+Shift+P | Cmd+Shift+P |
| New Appointment | Ctrl+Shift+A | Cmd+Shift+A |
| Save | Ctrl+S | Cmd+S |
| Cancel | Esc | Esc |
| Navigate Menu | Arrow Keys | Arrow Keys |
| Help | F1 | F1 |

---

## Support

### Internal IT Helpdesk
- Email: helpdesk@hms.com
- Phone: [Internal extension]
- Hours: 24/7

### HMS Support
- Email: support@dkeemz.com
- Phone: [Support number]
- Hours: 24/7 for critical issues

### Emergency
- Patient care issues: Call 24/7 hotline
- Security incidents: Contact compliance officer immediately
