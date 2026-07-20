"""Seed script to create dummy accounts and sample data for testing."""
import asyncio
import uuid
import sys
sys.path.insert(0, ".")

from datetime import date, datetime, UTC
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import bcrypt

DATABASE_URL = "postgresql+asyncpg://hms:hms_prod_secure_2024@localhost:5432/hms"

def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

ADMIN_HASH = hash_pw("Admin123!")
DOCTOR_HASH = hash_pw("Doctor123!")
NURSE_HASH = hash_pw("Nurse123!")
PATIENT_HASH = hash_pw("Patient123!")

# Fixed UUIDs for reproducibility
ADMIN_ID = uuid.UUID("10000000-0000-0000-0000-000000000001")
DOCTOR_ID = uuid.UUID("10000000-0000-0000-0000-000000000002")
NURSE_ID = uuid.UUID("10000000-0000-0000-0000-000000000003")
PATIENT_USER_ID = uuid.UUID("10000000-0000-0000-0000-000000000004")

ADMIN_ROLE_ID = uuid.UUID("20000000-0000-0000-0000-000000000001")
DOCTOR_ROLE_ID = uuid.UUID("20000000-0000-0000-0000-000000000002")
NURSE_ROLE_ID = uuid.UUID("20000000-0000-0000-0000-000000000003")
PATIENT_ROLE_ID = uuid.UUID("20000000-0000-0000-0000-000000000004")

# Sample patient records
PATIENTS = [
    {
        "id": uuid.UUID("30000000-0000-0000-0000-000000000001"),
        "mrn": "MRN-000001",
        "first_name": "Chidinma",
        "last_name": "Okafor",
        "date_of_birth": date(1990, 3, 15),
        "gender": "female",
        "phone": "+234-801-234-5678",
        "email": "chidinma.okafor@email.com",
        "blood_group": "O+",
        "nin": "12345678901",
        "preferred_language": "English",
        "status": "active",
        "address_street": "15 Admiralty Way",
        "address_city": "Lekki",
        "address_state": "Lagos",
        "address_lga": "Eti-Osa",
    },
    {
        "id": uuid.UUID("30000000-0000-0000-0000-000000000002"),
        "mrn": "MRN-000002",
        "first_name": "Abubakar",
        "last_name": "Ibrahim",
        "date_of_birth": date(1985, 7, 22),
        "gender": "male",
        "phone": "+234-802-345-6789",
        "email": "abubakar.ibrahim@email.com",
        "blood_group": "A+",
        "nin": "23456789012",
        "preferred_language": "Hausa",
        "status": "active",
        "address_street": "42 Ahmadu Bello Way",
        "address_city": "Kaduna",
        "address_state": "Kaduna",
        "address_lga": "Kaduna North",
    },
    {
        "id": uuid.UUID("30000000-0000-0000-0000-000000000003"),
        "mrn": "MRN-000003",
        "first_name": "Adebayo",
        "last_name": "Ogundimu",
        "date_of_birth": date(1978, 11, 8),
        "gender": "male",
        "phone": "+234-803-456-7890",
        "email": "adebayo.ogundimu@email.com",
        "blood_group": "B-",
        "nin": "34567890123",
        "preferred_language": "Yoruba",
        "status": "active",
        "address_street": "7 Allen Avenue",
        "address_city": "Ikeja",
        "address_state": "Lagos",
        "address_lga": "Ikeja",
    },
]

EMERGENCY_CONTACTS = [
    {
        "id": uuid.UUID("40000000-0000-0000-0000-000000000001"),
        "patient_id": PATIENTS[0]["id"],
        "name": "Emeka Okafor",
        "phone": "+234-806-123-4567",
        "relationship": "spouse",
    },
    {
        "id": uuid.UUID("40000000-0000-0000-0000-000000000002"),
        "patient_id": PATIENTS[1]["id"],
        "name": "Fatima Ibrahim",
        "phone": "+234-807-234-5678",
        "relationship": "spouse",
    },
]

SAMPLE_ALLERGIES = [
    {
        "id": uuid.UUID("50000000-0000-0000-0000-000000000001"),
        "patient_id": PATIENTS[0]["id"],
        "name": "Penicillin",
        "reaction": "Anaphylaxis, skin rash, swelling",
        "severity": "severe",
        "verification_status": "confirmed",
        "source": "patient-reported",
    },
    {
        "id": uuid.UUID("50000000-0000-0000-0000-000000000002"),
        "patient_id": PATIENTS[0]["id"],
        "name": "Peanuts",
        "reaction": "Throat tightness, hives",
        "severity": "moderate",
        "verification_status": "confirmed",
        "source": "patient-reported",
    },
    {
        "id": uuid.UUID("50000000-0000-0000-0000-000000000003"),
        "patient_id": PATIENTS[1]["id"],
        "name": "Sulfonamides",
        "reaction": "Skin rash, fever",
        "severity": "mild",
        "verification_status": "confirmed",
        "source": "patient-reported",
    },
]

SAMPLE_PROBLEMS = [
    {
        "id": uuid.UUID("55000000-0000-0000-0000-000000000001"),
        "patient_id": PATIENTS[0]["id"],
        "problem_name": "Type 2 Diabetes Mellitus",
        "icd_code": "E11",
        "status": "active",
        "onset_date": date(2020, 5, 1),
        "chronicity": "chronic",
    },
    {
        "id": uuid.UUID("55000000-0000-0000-0000-000000000002"),
        "patient_id": PATIENTS[2]["id"],
        "problem_name": "Essential Hypertension",
        "icd_code": "I10",
        "status": "active",
        "onset_date": date(2018, 1, 15),
        "chronicity": "chronic",
    },
]

SAMPLE_MEDICATIONS = [
    {
        "id": uuid.UUID("56000000-0000-0000-0000-000000000001"),
        "patient_id": PATIENTS[0]["id"],
        "medication_name": "Metformin",
        "strength": "500 mg",
        "dosage_form": "tablet",
        "frequency": "Twice daily with meals",
        "route": "oral",
        "status": "active",
        "start_date": date(2020, 5, 1),
    },
    {
        "id": uuid.UUID("56000000-0000-0000-0000-000000000002"),
        "patient_id": PATIENTS[2]["id"],
        "medication_name": "Losartan",
        "strength": "50 mg",
        "dosage_form": "tablet",
        "frequency": "Once daily",
        "route": "oral",
        "status": "active",
        "start_date": date(2018, 1, 15),
    },
]

SAMPLE_CONDITIONS = [
    {
        "id": uuid.UUID("60000000-0000-0000-0000-000000000001"),
        "patient_id": PATIENTS[0]["id"],
        "name": "Type 2 Diabetes Mellitus",
        "icd10_code": "E11",
        "clinical_status": "active",
        "verification_status": "confirmed",
        "severity": "moderate",
        "onset_date": date(2020, 5, 1),
        "source": "clinical",
    },
    {
        "id": uuid.UUID("60000000-0000-0000-0000-000000000002"),
        "patient_id": PATIENTS[2]["id"],
        "name": "Essential Hypertension",
        "icd10_code": "I10",
        "clinical_status": "active",
        "verification_status": "confirmed",
        "severity": "mild",
        "onset_date": date(2018, 1, 15),
        "source": "clinical",
    },
]

SAMPLE_SURGERIES = [
    {
        "id": uuid.UUID("70000000-0000-0000-0000-000000000001"),
        "patient_id": PATIENTS[0]["id"],
        "name": "Appendectomy",
        "procedure_date": date(2015, 8, 20),
        "surgeon": "Dr. Akinwale",
        "facility": "Lagos University Teaching Hospital",
        "outcome": "successful",
        "notes": "Laparoscopic appendectomy, no complications",
        "source": "clinical",
    },
]

SAMPLE_FAMILY_HISTORY = [
    {
        "id": uuid.UUID("80000000-0000-0000-0000-000000000001"),
        "patient_id": PATIENTS[0]["id"],
        "condition_name": "Type 2 Diabetes Mellitus",
        "relationship_type": "mother",
        "is_hereditary": True,
        "status": "living",
    },
    {
        "id": uuid.UUID("80000000-0000-0000-0000-000000000002"),
        "patient_id": PATIENTS[1]["id"],
        "condition_name": "Essential Hypertension",
        "relationship_type": "father",
        "is_hereditary": True,
        "status": "deceased",
    },
]


async def seed():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # ── 1. Create Roles ──────────────────────────────────────────────
        roles = [
            (ADMIN_ROLE_ID, "admin", "System administrator with full access", True),
            (DOCTOR_ROLE_ID, "doctor", "Medical doctor", False),
            (NURSE_ROLE_ID, "nurse", "Nursing staff", False),
            (PATIENT_ROLE_ID, "patient", "Registered patient", False),
        ]
        for rid, name, desc, is_system in roles:
            await db.execute(
                text("""
                    INSERT INTO roles (id, name, description, is_system)
                    VALUES (:id, :name, :desc, :is_system)
                    ON CONFLICT (name) DO NOTHING
                """),
                {"id": rid, "name": name, "desc": desc, "is_system": is_system},
            )
        print("✓ Roles created")

        # ── 2. Create Users ──────────────────────────────────────────────
        users = [
            (ADMIN_ID, "admin@hms.com", "System", "Admin", ADMIN_HASH),
            (DOCTOR_ID, "doctor@hms.com", "Chioma", "Adeyemi", DOCTOR_HASH),
            (NURSE_ID, "nurse@hms.com", "Blessing", "Eze", NURSE_HASH),
            (PATIENT_USER_ID, "patient@hms.com", "Musa", "Abdullahi", PATIENT_HASH),
        ]
        for uid, email, first, last, pw in users:
            await db.execute(
                text("""
                    INSERT INTO users (id, email, first_name, last_name, password_hash, status)
                    VALUES (:id, :email, :first, :last, :pw, 'active')
                    ON CONFLICT (email) DO NOTHING
                """),
                {"id": uid, "email": email, "first": first, "last": last, "pw": pw},
            )
        print("✓ Users created")

        # ── 3. Assign Roles ──────────────────────────────────────────────
        assignments = [
            (ADMIN_ID, ADMIN_ROLE_ID),
            (DOCTOR_ID, DOCTOR_ROLE_ID),
            (NURSE_ID, NURSE_ROLE_ID),
            (PATIENT_USER_ID, PATIENT_ROLE_ID),
        ]
        for uid, rid in assignments:
            await db.execute(
                text("""
                    INSERT INTO user_roles (id, user_id, role_id, status)
                    VALUES (:id, :uid, :rid, 'approved')
                    ON CONFLICT DO NOTHING
                """),
                {"id": uuid.uuid4(), "uid": uid, "rid": rid},
            )
        print("✓ Roles assigned")

        # ── 4. Create Sample Patients ────────────────────────────────────
        for p in PATIENTS:
            await db.execute(
                text("""
                    INSERT INTO patients (id, mrn, first_name, last_name, date_of_birth, gender, phone, email, blood_group, nin, preferred_language, status, address_street, address_city, address_state, address_lga)
                    VALUES (:id, :mrn, :first_name, :last_name, :date_of_birth, :gender, :phone, :email, :blood_group, :nin, :preferred_language, :status, :address_street, :address_city, :address_state, :address_lga)
                    ON CONFLICT (mrn) DO NOTHING
                """),
                p,
            )
        print(f"✓ {len(PATIENTS)} patients created")

        # ── 5. Emergency Contacts ────────────────────────────────────────
        for ec in EMERGENCY_CONTACTS:
            await db.execute(
                text("""
                    INSERT INTO emergency_contacts (id, patient_id, name, phone, relationship)
                    VALUES (:id, :patient_id, :name, :phone, :relationship)
                    ON CONFLICT DO NOTHING
                """),
                ec,
            )
        print(f"✓ {len(EMERGENCY_CONTACTS)} emergency contacts created")

        # ── 6. Sample Allergies ──────────────────────────────────────────
        for a in SAMPLE_ALLERGIES:
            await db.execute(
                text("""
                    INSERT INTO allergies (id, patient_id, name, reaction, severity, verification_status, source)
                    VALUES (:id, :patient_id, :name, :reaction, :severity, :verification_status, :source)
                    ON CONFLICT DO NOTHING
                """),
                a,
            )
        print(f"✓ {len(SAMPLE_ALLERGIES)} allergies created")

        # ── 7. Sample Problems ───────────────────────────────────────────
        for p in SAMPLE_PROBLEMS:
            await db.execute(
                text("""
                    INSERT INTO problems (id, patient_id, problem_name, icd_code, status, onset_date, chronicity)
                    VALUES (:id, :patient_id, :problem_name, :icd_code, :status, :onset_date, :chronicity)
                    ON CONFLICT DO NOTHING
                """),
                p,
            )
        print(f"✓ {len(SAMPLE_PROBLEMS)} problems created")

        # ── 8. Sample Medications ─────────────────────────────────────────
        for m in SAMPLE_MEDICATIONS:
            await db.execute(
                text("""
                    INSERT INTO medications (id, patient_id, medication_name, strength, dosage_form, frequency, route, status, start_date)
                    VALUES (:id, :patient_id, :medication_name, :strength, :dosage_form, :frequency, :route, :status, :start_date)
                    ON CONFLICT DO NOTHING
                """),
                m,
            )
        print(f"✓ {len(SAMPLE_MEDICATIONS)} medications created")

        # ── 9. Sample Conditions ─────────────────────────────────────────
        for c in SAMPLE_CONDITIONS:
            await db.execute(
                text("""
                    INSERT INTO conditions (id, patient_id, name, icd10_code, clinical_status, verification_status, severity, onset_date, source)
                    VALUES (:id, :patient_id, :name, :icd10_code, :clinical_status, :verification_status, :severity, :onset_date, :source)
                    ON CONFLICT DO NOTHING
                """),
                c,
            )
        print(f"✓ {len(SAMPLE_CONDITIONS)} conditions created")

        # ── 8. Sample Surgeries ──────────────────────────────────────────
        for s in SAMPLE_SURGERIES:
            await db.execute(
                text("""
                    INSERT INTO surgeries (id, patient_id, name, procedure_date, surgeon, facility, outcome, notes, source)
                    VALUES (:id, :patient_id, :name, :procedure_date, :surgeon, :facility, :outcome, :notes, :source)
                    ON CONFLICT DO NOTHING
                """),
                s,
            )
        print(f"✓ {len(SAMPLE_SURGERIES)} surgeries created")

        # ── 9. Sample Family History ─────────────────────────────────────
        for fh in SAMPLE_FAMILY_HISTORY:
            await db.execute(
                text("""
                    INSERT INTO family_history (id, patient_id, condition_name, relationship_type, is_hereditary, status)
                    VALUES (:id, :patient_id, :condition_name, :relationship_type, :is_hereditary, :status)
                    ON CONFLICT DO NOTHING
                """),
                fh,
            )
        print(f"✓ {len(SAMPLE_FAMILY_HISTORY)} family history entries created")

        await db.commit()
        print("\n✅ Seed data committed successfully!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
