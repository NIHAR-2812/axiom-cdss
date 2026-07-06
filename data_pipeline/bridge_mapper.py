import pandas as pd

def bridge_snomed_to_icd10():
    print("[SYSTEM] Translating SNOMED-CT to ICD-10...")
    df = pd.read_csv("synthea/output/csv/conditions.csv")
    
    # 1. CRITICAL FIX: Ensure CODE is a string so it matches the mapping keys
    df['CODE'] = df['CODE'].astype(str)
    
    # Mapping SNOMED-CT to ICD-10
    mapping = {
        '314529007': 'I10',      # Hypertension
        '66383009': 'K76.9',     # Chronic liver disease
        '73595000': 'J45.909',   # Asthma
        '160903007': 'J44.9',    # COPD
        '160904001': 'J18.9',    # Pneumonia
        '444814009': 'J01.90',   # Viral sinusitis
        '423315002': 'E78.5',    # Hyperlipidemia
        '422650009': 'G47.33',   # Sleep apnea
        '741062008': 'U07.1',    # COVID-19
        '18718003': 'R73.09'     # Abnormal glucose tolerance
    }
    
    # 2. Map codes
    df['ICD10_CODE'] = df['CODE'].map(mapping)
    
    # 3. Filter and Save
    df_clean = df.dropna(subset=['ICD10_CODE'])
    
    if len(df_clean) == 0:
        # Debugging aid
        print("[ERROR] Mapping failed. The codes in your CSV don't match the dictionary keys.")
        print(f"Sample codes found in CSV: {df['CODE'].head().tolist()}")
    else:
        df_clean[['ICD10_CODE']].to_csv("real_conditions.csv", index=False)
        print(f"[SUCCESS] Mapped {len(df_clean)} records to real_conditions.csv.")

if __name__ == "__main__":
    bridge_snomed_to_icd10()