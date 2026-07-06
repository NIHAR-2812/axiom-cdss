import pandas as pd
import random
import uuid
from faker import Faker
from datetime import timedelta

# Initialize Faker and seed for reproducibility
fake = Faker()
Faker.seed(42)
random.seed(42)

NUM_PATIENTS = 1000
NUM_OBSERVATIONS = 5000
NUM_CONDITIONS = 1500

# Common medical diagnoses and their simplified ICD-10 codes for the simulation
DIAGNOSES = [
    {"code": "E11.9", "display": "Type 2 diabetes mellitus"},
    {"code": "I10", "display": "Essential (primary) hypertension"},
    {"code": "J45.909", "display": "Unspecified asthma"},
    {"code": "E78.5", "display": "Hyperlipidemia, unspecified"},
    {"code": "F32.9", "display": "Major depressive disorder, single episode"},
    {"code": "I25.10", "display": "Atherosclerotic heart disease"}
]

def generate_patients(n):
    """Generates FHIR-style Patient resource data."""
    print(f"Generating {n} patients...")
    patients = []
    for _ in range(n):
        patient_id = str(uuid.uuid4())
        gender = random.choice(["male", "female"])
        birth_date = fake.date_of_birth(minimum_age=18, maximum_age=90)
        
        patients.append({
            "patient_id": patient_id,
            "first_name": fake.first_name_male() if gender == "male" else fake.first_name_female(),
            "last_name": fake.last_name(),
            "gender": gender,
            "birth_date": birth_date.isoformat(),
            "city": fake.city(),
            "active": True
        })
    return pd.DataFrame(patients)

def generate_observations(patients_df, n):
    """Generates FHIR-style Observation resource data (Vitals)."""
    print(f"Generating {n} observations (vitals)...")
    observations = []
    patient_ids = patients_df['patient_id'].tolist()
    
    for _ in range(n):
        pat_id = random.choice(patient_ids)
        obs_date = fake.date_time_this_year(before_now=True, after_now=False).isoformat()
        
        # Generate realistic, slightly randomized vitals
        sys_bp = random.randint(100, 160)
        dia_bp = random.randint(60, 100)
        heart_rate = random.randint(60, 110)
        bmi = round(random.uniform(18.5, 35.0), 1)
        
        observations.append({
            "observation_id": str(uuid.uuid4()),
            "patient_id": pat_id,
            "effective_datetime": obs_date,
            "systolic_bp": sys_bp,
            "diastolic_bp": dia_bp,
            "heart_rate": heart_rate,
            "bmi": bmi,
            "status": "final"
        })
    return pd.DataFrame(observations)

def generate_conditions(patients_df, n):
    """Generates FHIR-style Condition resource data (Diagnoses)."""
    print(f"Generating {n} conditions (diagnoses)...")
    conditions = []
    patient_ids = patients_df['patient_id'].tolist()
    
    for _ in range(n):
        pat_id = random.choice(patient_ids)
        diagnosis = random.choice(DIAGNOSES)
        onset_date = fake.date_between(start_date='-5y', end_date='today').isoformat()
        
        conditions.append({
            "condition_id": str(uuid.uuid4()),
            "patient_id": pat_id,
            "clinical_status": random.choice(["active", "resolved", "remission"]),
            "verification_status": "confirmed",
            "icd_10_code": diagnosis["code"],
            "display_name": diagnosis["display"],
            "onset_datetime": onset_date
        })
    return pd.DataFrame(conditions)

def main():
    # 1. Generate Data
    patients_df = generate_patients(NUM_PATIENTS)
    observations_df = generate_observations(patients_df, NUM_OBSERVATIONS)
    conditions_df = generate_conditions(patients_df, NUM_CONDITIONS)
    
    # 2. Save to CSV for ML Training and DB Loading
    print("Saving datasets to CSV...")
    patients_df.to_csv("synthetic_patients.csv", index=False)
    observations_df.to_csv("synthetic_observations.csv", index=False)
    conditions_df.to_csv("synthetic_conditions.csv", index=False)
    
    print("Phase 1 Data Generation Complete.")
    print("Files created: synthetic_patients.csv, synthetic_observations.csv, synthetic_conditions.csv")

if __name__ == "__main__":
    main()