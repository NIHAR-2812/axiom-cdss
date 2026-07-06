import pickle
import os

def peek_at_encoder():
    path = os.path.join("ml_engine", "models", "symptom_encoder.pkl")
    try:
        with open(path, "rb") as f:
            encoder = pickle.load(f)
            
        print(f"[SYSTEM] Found {len(encoder.classes_)} unique symptoms.")
        print("\n--- Try copying and pasting one of these into Swagger ---")
        # Print the first 20 valid symptoms exactly as the model expects them
        for symptom in list(encoder.classes_)[:20]:
            print(f'"{symptom}"')
            
    except Exception as e:
        print(f"Error loading encoder: {e}")

if __name__ == "__main__":
    peek_at_encoder()