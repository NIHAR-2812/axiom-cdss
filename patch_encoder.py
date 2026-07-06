import pickle
import os
from sklearn.preprocessing import LabelEncoder

def patch_encoder():
    print("[SYSTEM] Patching disease encoder to match model architecture...")
    
    # The 10 exact ICD-10 codes your model architecture was mapped for
    baseline_diseases = [
        'E78.5', 'G47.33', 'I10', 'J01.90', 'J18.9', 
        'J44.9', 'J45.909', 'K76.9', 'R73.09', 'U07.1'
    ]
    
    encoder = LabelEncoder()
    encoder.fit(baseline_diseases)
    
    # Save it directly into your backend's model folder
    path = os.path.join("ml_engine", "models", "disease_encoder.pkl")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, "wb") as f:
        pickle.dump(encoder, f)
        
    print(f"[SUCCESS] Saved encoder with {len(encoder.classes_)} classes.")
    print(f"[DEBUG] Classes: {encoder.classes_}")

if __name__ == "__main__":
    patch_encoder()