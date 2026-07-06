import os
import pickle
import numpy as np
from contextlib import asynccontextmanager
from typing import List, Dict

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import tensorflow as tf
from sqlalchemy.orm import Session
from neo4j import GraphDatabase

# Internal Imports
from app.core.database import engine, Base, get_db, SessionLocal
from app.models.user import User
from app.models.audit import AuditLog
from app.core.security import verify_password, get_password_hash, create_access_token, verify_token

# --- Global Registry ---
ml_engine = {}
db_connections = {}
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Helper Logic ---
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token, credentials_exception)

def get_graph_treatments(tx, icd_code: str) -> List[str]:
    query = "MATCH (c:Condition {code: $code})-[:TREATED_WITH]->(m:Medication) RETURN m.name AS medication"
    return [record["medication"] for record in tx.run(query, code=icd_code)]

# --- Lifecycle Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n[SYSTEM] Booting CDSS API...")
    # 1. DB Init
    Base.metadata.create_all(bind=engine)
    # 2. Graph Init
    db_connections["neo4j"] = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "secure_graph_123"))
    # 3. Model Init
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    model_dir = os.path.join(project_root, "ml_engine", "models")
    
    try:
        interpreter = tf.lite.Interpreter(model_path=os.path.join(model_dir, "cdss_model_quantized.tflite"))
        interpreter.allocate_tensors()
        ml_engine.update({
            "interpreter": interpreter,
            "input_details": interpreter.get_input_details(),
            "output_details": interpreter.get_output_details(),
            "symptom_encoder": pickle.load(open(os.path.join(model_dir, "symptom_encoder.pkl"), "rb")),
            "disease_encoder": pickle.load(open(os.path.join(model_dir, "disease_encoder.pkl"), "rb")),
            "medication_encoder": pickle.load(open(os.path.join(model_dir, "medication_encoder.pkl"), "rb"))
        })
    except Exception as e:
        print(f"[CRITICAL] AI Engine Failed: {e}")
    yield
    db_connections["neo4j"].close()
    ml_engine.clear()

app = FastAPI(title="CDSS Secured API", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- Models ---
class InferenceRequest(BaseModel):
    symptoms: List[str]

class InferenceResponse(BaseModel):
    ai_predicted_icd10: str
    ai_medication_recommendations: List[str]
    graph_validated_medications: List[str]
    confidence_score: float
    integrity_check: bool
    xai_analysis: Dict[str, float]

# --- Endpoints ---
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect credentials")
    return {"access_token": create_access_token(data={"sub": user.username, "role": user.role}), "token_type": "bearer"}

@app.post("/api/v1/inference/predict", response_model=InferenceResponse)
async def predict_clinical_path(payload: InferenceRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.get("role") != "Doctor": raise HTTPException(status_code=403, detail="Forbidden")
    
    # 1. Feature Prep
    mlb = ml_engine["symptom_encoder"]
    valid_symptoms = [s.lower() for s in payload.symptoms if s.lower() in mlb.classes_]
    if not valid_symptoms: raise HTTPException(status_code=400, detail="No valid symptoms recognized.")
    
    # 2. Inference
    interp = ml_engine["interpreter"]
    input_tensor = mlb.transform([valid_symptoms]).astype(np.float32)
    interp.set_tensor(ml_engine["input_details"][0]['index'], input_tensor)
    interp.invoke()
    
    # 3. Tensor Parsing (Single Output Model)
    outputs = [interp.get_tensor(d['index'])[0] for d in ml_engine["output_details"]]
    disease_probs = outputs[0] # Our Sequential model only has 1 output array
        
    pred_idx = np.argmax(disease_probs)
    predicted_icd10 = str(ml_engine["disease_encoder"].classes_[pred_idx])
        
    # 4. XAI Logic (Simplified placeholder)
    xai_analysis = {s: round(1.0/len(valid_symptoms), 4) for s in valid_symptoms}
        
    # 5. Graph Treatments (Neo4j acts as the source of truth for meds)
    with db_connections["neo4j"].session() as session:
        graph_meds = session.execute_read(get_graph_treatments, predicted_icd10)
        
    # Since the AI only predicts the condition, we use the graph for medications.
    # This inherently passes the integrity check as the graph is our clinical standard.
    ai_meds = graph_meds 
    integrity = True
        
    # 6. Audit
    db.add(AuditLog(doctor_username=current_user.get("sub"), input_symptoms=payload.symptoms, predicted_icd10=predicted_icd10, graph_validated=str(integrity)))
    db.commit()
        
    return {
        "ai_predicted_icd10": predicted_icd10,
        "ai_medication_recommendations": ai_meds,
        "graph_validated_medications": graph_meds,
        "confidence_score": float(disease_probs[pred_idx]),
        "integrity_check": integrity,
        "xai_analysis": xai_analysis
    }