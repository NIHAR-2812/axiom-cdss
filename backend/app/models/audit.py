from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from datetime import datetime
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    doctor_username = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    action = Column(String, default="AI_INFERENCE_RUN")
    input_symptoms = Column(JSON)
    predicted_icd10 = Column(String)
    graph_validated = Column(String) # Storing boolean as string or bool