# ⚡ Axiom CDSS (Clinical Decision Support System)

Axiom CDSS is an enterprise-grade, full-stack Clinical Decision Support System. It leverages a multi-task neural network to predict ICD-10 diagnoses and recommend medications based on patient symptoms. To ensure clinical safety, all AI-generated medication recommendations are cross-validated in real-time against a Neo4j medical knowledge graph—acting as the "axiom" or absolute source of truth.

## 🚀 Key Features

* **Multi-Task Neural Network:** Simultaneously predicts diseases (categorical) and maps treatments (multi-label) using TensorFlow.
* **Green Computing (Edge ML):** The core AI is quantized into an 8-bit TensorFlow Lite (`.tflite`) format, significantly reducing memory footprint and latency while maintaining accuracy.
* **Explainable AI (XAI):** Features a custom Leave-One-Out (LOO) perturbation engine to generate feature attribution, showing doctors *why* the AI made a specific prediction.
* **Graph-Validated Integrity:** AI recommendations are verified against a Neo4j medical knowledge graph to prevent AI hallucinations.
* **HIPAA-Compliant Audit Trail:** All inferences, inputs, and validation statuses are logged securely in PostgreSQL.
* **Role-Based Access Control (RBAC):** Secured via OAuth2 with JWT tokens (restricted strictly to 'Doctor' roles).

## 🛠️ Technology Stack

**Frontend:**
* React.js (Vite)
* Tailwind CSS (Dark-mode Bento Grid UI)

**Backend:**
* FastAPI (Python)
* SQLAlchemy (ORM)

**Databases:**
* PostgreSQL (User Auth & Audit Logging)
* Neo4j (Medical Knowledge Graph)

**Machine Learning Engine:**
* TensorFlow / Keras (Model Training)
* TensorFlow Lite (Production Inference)
* Scikit-Learn (Entity Encoding)

## 📂 Project Structure

    axiom-cdss/
    │
    ├── backend/                  # FastAPI Server
    │   ├── app/
    │   │   ├── core/             # Database & Security configurations
    │   │   ├── models/           # SQLAlchemy models (User, AuditLog)
    │   │   └── main.py           # Core API routing & Dynamic Tensor Mapping
    │   └── requirements.txt      
    │
    ├── frontend/                 # React UI
    │   ├── src/
    │   │   ├── App.jsx           # Main Dashboard & API Integration
    │   │   ├── main.jsx
    │   │   └── index.css         # Tailwind styles
    │   ├── package.json
    │   └── vite.config.js
    │
    ├── data_pipeline/            # Synthetic clinical datasets
    │   ├── synthetic_conditions.csv
    │   ├── synthetic_symptoms.csv
    │   └── synthetic_medications.csv
    │
    ├── ml_engine/                # AI Brain & Encoders
    │   └── models/               
    │       ├── cdss_model_quantized.tflite  # 8-bit Optimized Model
    │       ├── disease_encoder.pkl
    │       ├── medication_encoder.pkl
    │       └── symptom_encoder.pkl
    │
    ├── nuclear_rebuild.py        # Automated all-in-one model training & export script
    └── README.md

## ⚙️ Quick Start Guide

### 1. Database Setup (Docker)
Ensure Docker Desktop is running. You need both PostgreSQL and Neo4j active.
* **Neo4j:** `bolt://localhost:7687` (Auth: `neo4j` / `secure_graph_123`)
* **PostgreSQL:** Ensure your local Postgres instance is running and matches the connection string in `backend/app/core/database.py`.

### 2. Backend Initialization
Open a terminal and navigate to the `backend` folder:
    
    cd backend
    python -m venv venv
    # Activate venv (Windows: venv\Scripts\activate | Mac/Linux: source venv/bin/activate)
    pip install -r requirements.txt
    uvicorn app.main:app --reload
    
*Note: The system will automatically inject a default test user (`dr_smith` / `secure_password_123`) upon booting.*

### 3. Frontend Initialization
Open a second terminal and navigate to the `frontend` folder:
    
    cd frontend
    npm install
    npm run dev
    
Navigate to `http://localhost:5173` in your browser to access the Axiom CDSS Dashboard.

## 🧠 Model Retraining
If the underlying dataset in `/data_pipeline` is updated, you can regenerate the perfectly synced `.tflite` model and `.pkl` encoders by running the rebuild script from the root directory:
    
    python nuclear_rebuild.py
    

## 🔮 Future Scope

* **Real-World Datasets:** Scale the ML pipeline to ingest real medical datasets (e.g., MIMIC-III) to train the model on expanded ICD-10 codes.
* **FHIR Interoperability:** Update the API to accept and return JSON payloads in the official FHIR format for seamless integration with EHR systems like Epic and Cerner.
* **SHAP Integration:** Upgrade the custom LOO XAI backend to use the SHAP (SHapley Additive exPlanations) library for mathematically rigorous feature attribution.
* **Containerization:** Implement a `docker-compose.yml` file to orchestrate the frontend, backend, Neo4j, and Postgres services simultaneously.
* **Cloud Deployment:** Migrate databases to AWS RDS / AuraDB, host the FastAPI backend on AWS ECS, and deploy the Vite frontend to Vercel/Netlify for global access.

## 👨‍💻 Author
**Nihar Padave**  
Lead Developer & ML Architect