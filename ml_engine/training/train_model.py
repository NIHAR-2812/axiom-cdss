import os
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, Model
from sklearn.preprocessing import MultiLabelBinarizer, LabelEncoder
import pickle

def load_and_prepare_data(base_path):
    print("Loading synthetic datasets...")
    # Load the datasets generated in Phase 1
    conditions = pd.read_csv(os.path.join(base_path, "synthetic_conditions.csv"))
    symptoms = pd.read_csv(os.path.join(base_path, "synthetic_symptoms.csv"))
    medications = pd.read_csv(os.path.join(base_path, "synthetic_medications.csv"))

    # Group symptoms and medications by their ICD-10 disease code
    symp_grouped = symptoms.groupby('icd_10_code')['name'].apply(list).reset_index(name='symptoms')
    med_grouped = medications.groupby('icd_10_code')['name'].apply(list).reset_index(name='medications')

    # Merge everything together based on the condition/diagnosis
    df = conditions.merge(symp_grouped, on='icd_10_code', how='left')
    df = df.merge(med_grouped, on='icd_10_code', how='left')
    
    # Drop any rows where we might have missing synthetic mappings
    df = df.dropna()
    return df

def build_and_train_model():
    # 1. Setup paths
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_path = os.path.join(project_root, "data_pipeline")
    model_dir = os.path.join(project_root, "ml_engine", "models")
    
    # 2. Load Data
    df = load_and_prepare_data(data_path)
    
    print("Encoding medical entities...")
    # Encode Symptoms (Multi-label: Patients have multiple symptoms)
    mlb_symptoms = MultiLabelBinarizer()
    X_symptoms = mlb_symptoms.fit_transform(df['symptoms'])
    
    # Encode Diagnosis (Single-label: Primary disease prediction)
    le_disease = LabelEncoder()
    y_disease = le_disease.fit_transform(df['icd_10_code'])
    
    # Encode Medications (Multi-label: Patients get multiple meds)
    mlb_meds = MultiLabelBinarizer()
    y_meds = mlb_meds.fit_transform(df['medications'])
    
    # 3. Build the Multi-Task Neural Network Architecture
    print("Building TensorFlow Multi-Task Model...")
    input_shape = len(mlb_symptoms.classes_)
    num_diseases = len(le_disease.classes_)
    num_meds = len(mlb_meds.classes_)
    
    # Input Layer (Patient Symptoms)
    inputs = layers.Input(shape=(input_shape,), name="symptom_inputs")
    
    # Shared Representation (The "Knowledge Embedding" layers)
    x = layers.Dense(128, activation='relu')(inputs)
    x = layers.Dropout(0.3)(x)
    shared_representation = layers.Dense(64, activation='relu', name="patient_embedding")(x)
    
    # Output Task 1: Predict Disease (Softmax for categorical classification)
    disease_output = layers.Dense(num_diseases, activation='softmax', name="disease_prediction")(shared_representation)
    
    # Output Task 2: Recommend Medications (Sigmoid for multi-label classification)
    med_output = layers.Dense(num_meds, activation='sigmoid', name="medication_recommendation")(shared_representation)
    
    # Compile Model
    model = Model(inputs=inputs, outputs=[disease_output, med_output])
    
    model.compile(
        optimizer='adam',
        loss={
            "disease_prediction": "sparse_categorical_crossentropy",
            "medication_recommendation": "binary_crossentropy"
        },
        metrics={
            "disease_prediction": "accuracy",
            "medication_recommendation": "accuracy"
        }
    )
    
    # 4. Train the Model
    print("Training the neural network...")
    model.fit(
        {"symptom_inputs": X_symptoms},
        {
            "disease_prediction": y_disease,
            "medication_recommendation": y_meds
        },
        epochs=10,
        batch_size=32,
        validation_split=0.2
    )
    
    # 5. Save Model and Encoders for Production API
    print("Saving model and encoders to /ml_engine/models/...")
    model.save(os.path.join(model_dir, "cdss_multitask_model.h5"))
    
    with open(os.path.join(model_dir, "symptom_encoder.pkl"), "wb") as f:
        pickle.dump(mlb_symptoms, f)
    with open(os.path.join(model_dir, "disease_encoder.pkl"), "wb") as f:
        pickle.dump(le_disease, f)
    with open(os.path.join(model_dir, "medication_encoder.pkl"), "wb") as f:
        pickle.dump(mlb_meds, f)
        
    print("Phase 2 Complete! ML Model successfully trained and exported.")

if __name__ == "__main__":
    build_and_train_model()