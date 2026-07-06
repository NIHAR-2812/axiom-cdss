import os
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, Model
from sklearn.preprocessing import MultiLabelBinarizer, LabelEncoder
import pickle
import shutil

def run_nuclear_rebuild():
    print("\n[SYSTEM] INITIATING NUCLEAR REBUILD...")

    # 1. ABSOLUTE PATHING (No more guessing where files go)
    root_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(root_dir, "data_pipeline")
    model_dir = os.path.join(root_dir, "ml_engine", "models")
    
    os.makedirs(model_dir, exist_ok=True)
    print(f"[SYSTEM] Target Directory Locked: {model_dir}")

    # 2. PURGE GHOST FILES
    print("[SYSTEM] Purging all old models and encoders...")
    for filename in os.listdir(model_dir):
        file_path = os.path.join(model_dir, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"[WARNING] Could not delete {file_path}: {e}")

    # 3. LOAD DATA
    print("[SYSTEM] Loading Data...")
    conditions = pd.read_csv(os.path.join(data_dir, "synthetic_conditions.csv"))
    symptoms = pd.read_csv(os.path.join(data_dir, "synthetic_symptoms.csv"))
    medications = pd.read_csv(os.path.join(data_dir, "synthetic_medications.csv"))

    # Force lowercase for bulletproof matching
    symptoms['name'] = symptoms['name'].str.lower()
    symp_grouped = symptoms.groupby('icd_10_code')['name'].apply(list).reset_index(name='symptoms')
    med_grouped = medications.groupby('icd_10_code')['name'].apply(list).reset_index(name='medications')

    df = conditions.merge(symp_grouped, on='icd_10_code', how='left')
    df = df.merge(med_grouped, on='icd_10_code', how='left').dropna()

    # 4. ENCODE & TRAIN
    print("[SYSTEM] Encoding & Training new architecture...")
    mlb_symptoms = MultiLabelBinarizer()
    X_symptoms = mlb_symptoms.fit_transform(df['symptoms'])
    
    le_disease = LabelEncoder()
    y_disease = le_disease.fit_transform(df['icd_10_code'])
    
    mlb_meds = MultiLabelBinarizer()
    y_meds = mlb_meds.fit_transform(df['medications'])
    
    num_classes = len(le_disease.classes_)
    print(f"[DEBUG] Model explicitly trained for {num_classes} classes.")

    inputs = layers.Input(shape=(len(mlb_symptoms.classes_),))
    x = layers.Dense(128, activation='relu')(inputs)
    x = layers.Dropout(0.3)(x)
    shared = layers.Dense(64, activation='relu')(x)
    
    disease_output = layers.Dense(num_classes, activation='softmax', name="disease")(shared)
    med_output = layers.Dense(len(mlb_meds.classes_), activation='sigmoid', name="meds")(shared)
    
    model = Model(inputs=inputs, outputs=[disease_output, med_output])
    model.compile(optimizer='adam', loss={"disease": "sparse_categorical_crossentropy", "meds": "binary_crossentropy"})
    
    # Quick train
    model.fit(X_symptoms, {"disease": y_disease, "meds": y_meds}, epochs=10, batch_size=32, verbose=0)

    # 5. DIRECT MEMORY QUANTIZATION (Bypassing .h5 completely)
    print("[SYSTEM] Converting directly to optimized TFLite (Green Computing)...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()

    # 6. SAVE PERFECTLY SYNCED BUNDLE
    with open(os.path.join(model_dir, "cdss_model_quantized.tflite"), "wb") as f:
        f.write(tflite_model)
    with open(os.path.join(model_dir, "symptom_encoder.pkl"), "wb") as f:
        pickle.dump(mlb_symptoms, f)
    with open(os.path.join(model_dir, "disease_encoder.pkl"), "wb") as f:
        pickle.dump(le_disease, f)
    with open(os.path.join(model_dir, "medication_encoder.pkl"), "wb") as f:
        pickle.dump(mlb_meds, f)

    print(f"\n[SUCCESS] NUCLEAR REBUILD COMPLETE! Files synced at exactly {num_classes} classes.")

if __name__ == "__main__":
    run_nuclear_rebuild()