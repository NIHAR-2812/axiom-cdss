import pandas as pd
import random
import uuid
import os

# The same diagnoses from Phase 1 to ensure referential integrity
DIAGNOSES = [
    {"code": "E11.9", "disease": "Type 2 diabetes mellitus", "symptoms": ["Increased thirst", "Frequent urination", "Fatigue"], "medications": ["Metformin", "Insulin glargine"]},
    {"code": "I10", "disease": "Essential (primary) hypertension", "symptoms": ["Headache", "Shortness of breath", "Nosebleeds"], "medications": ["Lisinopril", "Amlodipine"]},
    {"code": "J45.909", "disease": "Unspecified asthma", "symptoms": ["Wheezing", "Chest tightness", "Coughing"], "medications": ["Albuterol", "Fluticasone"]},
    {"code": "E78.5", "disease": "Hyperlipidemia, unspecified", "symptoms": ["Chest pain", "Xanthomas"], "medications": ["Atorvastatin", "Simvastatin"]},
    {"code": "F32.9", "disease": "Major depressive disorder", "symptoms": ["Persistent sadness", "Loss of interest", "Insomnia"], "medications": ["Sertraline", "Fluoxetine"]},
    {"code": "I25.10", "disease": "Atherosclerotic heart disease", "symptoms": ["Angina", "Cold sweats", "Dizziness"], "medications": ["Aspirin", "Clopidogrel"]}
]

def main():
    print("Generating Symptoms and Medications...")
    symptoms_list = []
    medications_list = []
    
    for diag in DIAGNOSES:
        # Generate Symptoms
        for symp in diag["symptoms"]:
            symptoms_list.append({
                "symptom_id": str(uuid.uuid4()),
                "name": symp,
                "icd_10_code": diag["code"] # The disease it indicates
            })
            
        # Generate Medications
        for med in diag["medications"]:
            medications_list.append({
                "medication_id": str(uuid.uuid4()),
                "name": med,
                "icd_10_code": diag["code"] # The disease it treats
            })
            
    # Save to CSV in the root data_pipeline folder
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pd.DataFrame(symptoms_list).to_csv(os.path.join(base_path, "synthetic_symptoms.csv"), index=False)
    pd.DataFrame(medications_list).to_csv(os.path.join(base_path, "synthetic_medications.csv"), index=False)
    
    print("Extensions generated: synthetic_symptoms.csv, synthetic_medications.csv")

if __name__ == "__main__":
    main()