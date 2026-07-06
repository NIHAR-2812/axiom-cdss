import pandas as pd
from neo4j import GraphDatabase
import os

# Database Credentials
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "secure_graph_123")

def create_constraints(tx):
    """Create unique constraints to ensure data integrity and fast lookups."""
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Patient) REQUIRE p.id IS UNIQUE")
    tx.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Condition) REQUIRE c.code IS UNIQUE")

def load_patients(tx, batch):
    """Merge Patient nodes into the graph."""
    query = """
    UNWIND $batch AS row
    MERGE (p:Patient {id: row.patient_id})
    SET p.firstName = row.first_name,
        p.lastName = row.last_name,
        p.gender = row.gender,
        p.birthDate = row.birth_date
    """
    tx.run(query, batch=batch)

def load_conditions(tx, batch):
    """Merge Condition nodes and link them to Patients."""
    query = """
    UNWIND $batch AS row
    // Create or find the Condition (Diagnosis)
    MERGE (c:Condition {code: row.icd_10_code})
    ON CREATE SET c.name = row.display_name
    
    // Find the Patient
    WITH c, row
    MATCH (p:Patient {id: row.patient_id})
    
    // Create the relationship
    MERGE (p)-[r:HAS_CONDITION]->(c)
    SET r.onset = row.onset_datetime,
        r.status = row.clinical_status
    """
    tx.run(query, batch=batch)

def main():
    # 1. Load the generated data
    print("Reading synthetic data...")
    # Adjusting path to point to the data_pipeline root where the CSVs were saved
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    patients_df = pd.read_csv(os.path.join(base_path, "synthetic_patients.csv"))
    conditions_df = pd.read_csv(os.path.join(base_path, "synthetic_conditions.csv"))

    # 2. Connect to Neo4j
    print("Connecting to Neo4j...")
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        with driver.session() as session:
            # Set up database rules
            session.execute_write(create_constraints)
            
            # Load Patients
            print("Ingesting Patients...")
            patient_records = patients_df.to_dict("records")
            session.execute_write(load_patients, patient_records)
            
            # Load Conditions & Relationships
            print("Ingesting Conditions and mapping to Patients...")
            condition_records = conditions_df.to_dict("records")
            session.execute_write(load_conditions, condition_records)

    print("Graph ingestion complete! Go to http://localhost:7474 and run: MATCH (n) RETURN n LIMIT 50")

if __name__ == "__main__":
    main()