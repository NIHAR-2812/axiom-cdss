import os
import pickle
import numpy as np
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import List
import tensorflow as tf
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase
from sqlalchemy.orm import Session

# Import our Security & DB Modules
from app.core.database import engine, Base, get_db, SessionLocal
from app.models.user import User
from app.models.audit import AuditLog
from app.core.security import verify_password, get_password_hash, create_access_token, verify_token

# Global dictionaries
ml_engine = {}
db_connections = {}

# Tell FastAPI where to look for the token in requests
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Decodes the JWT on incoming requests."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token, credentials_exception)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n[SYSTEM] Booting Clinical Decision Support API...")
    
    # 1. Initialize PostgreSQL Database
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] PostgreSQL Tables Created/Verified (Including Audit Logs).")
        
        # Inject a default Doctor account for testing
        db = SessionLocal()
        default_doc = db.query(User).filter(User.username == "dr_smith").first()
        if not default_doc:
            hashed_pw = get_password_hash("secure_password_123")
            new_doc = User(username="dr_smith", hashed_password=hashed_pw, role="Doctor")
            db.add(new_doc)
            db.commit()
            print("[OK] Default test account 'dr_smith' generated.")
        db.close()
    except Exception as e:
        print(f"[ERROR] PostgreSQL Setup Failed: {e}")

    # 2. Connect to Neo4j
    try:
        URI = "bolt://localhost:7687"
        AUTH = ("neo4j", "secure_graph_123")
        db_connections["neo4j"] = GraphDatabase.driver(URI, auth=AUTH)
        print("[OK] Connected to Neo4j Graph Database.")
    except Exception as e:
        print(f"[ERROR] Neo4j Connection Failed: {e}")

    # 3. Load Optimized Machine Learning Model (TFLite)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    model_dir = os.path.join(project_root, "ml_engine", "models")
    
    try:
        print("[SYSTEM] Loading Optimized TFLite model...")
        interpreter = tf.lite.Interpreter(model_path=os.path.join(model_dir, "cdss_model_quantized.tflite"))
        interpreter.allocate_tensors()
        ml_engine["interpreter"] = interpreter
        ml_engine["input_details"] = interpreter.get_input_details()
        ml_engine["output_details"] = interpreter.get_output_details()
        
        # Load encoders
        with open(os.path.join(model_dir, "symptom_encoder.pkl"), "rb") as f:
            ml_engine["symptom_encoder"] = pickle.load(f)
        with open(os.path.join(model_dir, "disease_encoder.pkl"), "rb") as f:
            ml_engine["disease_encoder"] = pickle.load(f)
        with open(os.path.join(model_dir, "medication_encoder.pkl"), "rb") as f:
            ml_engine["medication_encoder"] = pickle.load(f)
        print("[OK] Optimized AI Engine active.")
    except Exception as e:
        print(f"[ERROR] Failed to load ML assets: {e}")
        
    print("[SYSTEM] API is live and secured.\n")
    yield
    
    print("\n[SYSTEM] Shutting down API...")
    if "neo4j" in db_connections:
        db_connections["neo4j"].close()
    ml_engine.clear()


app = FastAPI(title="CDSS Secured API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InferenceRequest(BaseModel):
    symptoms: List[str] = Field(..., example=["Increased thirst", "Frequent urination"])

class InferenceResponse(BaseModel):
    ai_predicted_icd10: str
    ai_medication_recommendations: List[str]
    graph_validated_medications: List[str]
    confidence_score: float
    integrity_check: bool
    xai_analysis: dict

def get_graph_treatments(tx, icd_code: str) -> List[str]:
    query = "MATCH (c:Condition {code: $code})-[:TREATED_WITH]->(m:Medication) RETURN m.name AS medication"
    return [record["medication"] for record in tx.run(query, code=icd_code)]

# ==========================================
# AUTHENTICATION ENDPOINT
# ==========================================
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

# ==========================================
# SECURED INFERENCE ENDPOINT (OPTIMIZED)
# ==========================================
@app.post("/api/v1/inference/predict", response_model=InferenceResponse)
async def predict_clinical_path(
    payload: InferenceRequest, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db) 
):
    if current_user.get("role") != "Doctor":
        raise HTTPException(status_code=403, detail="Operation not permitted.")

    if "interpreter" not in ml_engine or "neo4j" not in db_connections:
        raise HTTPException(status_code=503, detail="Inference engine unavailable.")
        
    try:
        interpreter = ml_engine["interpreter"]
        input_details = ml_engine["input_details"]
        output_details = ml_engine["output_details"]
        
        mlb_symptoms = ml_engine["symptom_encoder"]
        
        # Robust lowercase matching
        lowercased_symptoms = [s.lower() for s in payload.symptoms]
        valid_symptoms = [s for s in lowercased_symptoms if s in mlb_symptoms.classes_]
        
        if not valid_symptoms:
            raise HTTPException(status_code=400, detail="Invalid symptoms provided. Please check spelling.")
            
        # --- BASELINE PREDICTION (TFLite) ---
        binary_vector = mlb_symptoms.transform([valid_symptoms]).astype(np.float32)
        
        interpreter.set_tensor(input_details[0]['index'], binary_vector)
        interpreter.invoke()
        
        # --- DYNAMIC TENSOR MAPPING ---
        # TFLite randomizes output indices. We check lengths to route them correctly.
        idx_0 = output_details[0]['index']
        idx_1 = output_details[1]['index']
        
        tensor_0 = interpreter.get_tensor(idx_0)[0]
        tensor_1 = interpreter.get_tensor(idx_1)[0]
        
        num_disease_classes = len(ml_engine["disease_encoder"].classes_)
        
        if len(tensor_0) == num_disease_classes:
            disease_tensor_idx = idx_0
            disease_probs = tensor_0
            med_probs = tensor_1
        else:
            disease_tensor_idx = idx_1
            disease_probs = tensor_1
            med_probs = tensor_0

        predicted_index = np.argmax(disease_probs)
        baseline_confidence = float(disease_probs[predicted_index])
        predicted_icd10 = str(ml_engine["disease_encoder"].classes_[predicted_index])
        
        # --- EXPLAINABLE AI (LOO Perturbation Analysis - TFLite) ---
        xai_results = {}
        if len(valid_symptoms) == 1:
            xai_results[valid_symptoms[0]] = 1.0
        else:
            for symptom in valid_symptoms:
                test_symptoms = [s for s in valid_symptoms if s != symptom]
                test_vector = mlb_symptoms.transform([test_symptoms]).astype(np.float32)
                
                interpreter.set_tensor(input_details[0]['index'], test_vector)
                interpreter.invoke()
                
                # Fetch dynamically identified disease tensor for XAI
                test_prob = float(interpreter.get_tensor(disease_tensor_idx)[0][predicted_index])
                
                drop = max(0.0, baseline_confidence - test_prob)
                xai_results[symptom] = drop
                
            total_drop = sum(xai_results.values())
            if total_drop > 0:
                xai_results = {k: round(v / total_drop, 4) for k, v in xai_results.items()}
            else:
                xai_results = {k: round(1.0 / len(valid_symptoms), 4) for k in valid_symptoms}

        # --- MEDICATION & GRAPH VALIDATION ---
        # We already grabbed the correct med_probs during the dynamic mapping
        predicted_med_indices = np.where(med_probs >= 0.5)[0]
        
        ai_med_vector = np.zeros((1, len(ml_engine["medication_encoder"].classes_)), dtype=np.float32)
        ai_med_vector[0, predicted_med_indices] = 1
        ai_meds = list(ml_engine["medication_encoder"].inverse_transform(ai_med_vector)[0])
        
        with db_connections["neo4j"].session() as session:
            graph_meds = session.execute_read(get_graph_treatments, predicted_icd10)
            
        integrity_status = sorted(ai_meds) == sorted(graph_meds)

        # --- AUDIT LOGGING ---
        audit_entry = AuditLog(
            doctor_username=current_user.get("sub"),
            input_symptoms=payload.symptoms,
            predicted_icd10=predicted_icd10,
            graph_validated=str(integrity_status)
        )
        db.add(audit_entry)
        db.commit()

        return {
            "ai_predicted_icd10": predicted_icd10,
            "ai_medication_recommendations": ai_meds,
            "graph_validated_medications": graph_meds,
            "confidence_score": round(baseline_confidence, 4),
            "integrity_check": integrity_status,
            "xai_analysis": xai_results
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
# ==========================================
# SECURE AUDIT LOG RETRIEVAL
# ==========================================
@app.get("/api/v1/audit/logs")
async def fetch_audit_logs(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.get("role") != "Doctor":
        raise HTTPException(status_code=403, detail="Operation not permitted.")
    
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(5).all()
    
    formatted_logs = []
    for log in logs:
        formatted_logs.append({
            "id": log.id,
            "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "doctor": log.doctor_username,
            "symptoms": log.input_symptoms,
            "icd10": log.predicted_icd10,
            "verified": log.graph_validated
        })
        
    return formatted_logs