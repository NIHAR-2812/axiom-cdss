import pandas as pd
import os

def extract_icd10_distribution():
    print("[SYSTEM] Reading real-world dataset...")
    
    # Construct the path relative to the script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "public_clinical_cases.csv")
    
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"[ERROR] Could not find file at: {file_path}")
        return

    # Clean headers (removes accidental leading/trailing spaces)
    df.columns = df.columns.str.strip()
    
    # Check if 'Diagnosis Code' exists
    if 'Diagnosis Code' not in df.columns:
        print(f"[ERROR] Column 'Diagnosis Code' not found. Available columns: {df.columns.tolist()}")
        return

    # Drop rows where ICD-10 is empty
    df = df.dropna(subset=['Diagnosis Code'])
    
    # Calculate the mathematical probability of each disease
    # This generates our 'statistical anchor' for the Hybrid Pipeline
    distribution_weights = df['Diagnosis Code'].value_counts(normalize=True).to_dict()
    
    # Print verification
    print("\n[SUCCESS] Extracted Base Probabilities. Top 5 Diseases:")
    top_5 = list(distribution_weights.items())[:5]
    for code, weight in top_5:
        print(f" -> ICD-10: {code} | Probability: {weight*100:.2f}%")
        
    return distribution_weights

if __name__ == "__main__":
    extract_icd10_distribution()