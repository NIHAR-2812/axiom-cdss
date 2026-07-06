import pandas as pd
from neo4j import GraphDatabase
import os

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "secure_graph_123")

def load_graph_extensions(tx, symptoms, medications):
    # 1. Load Symptoms and link to Disease
    symptom_query = """
    UNWIND $symptoms AS row
    MERGE (s:Symptom {name: row.name})
    WITH s, row
    MATCH (c:Condition {code: row.icd_10_code})
    MERGE (s)-[:INDICATES]->(c)
    """
    tx.run(symptom_query, symptoms=symptoms)
    
    # 2. Load Medications and link from Disease
    med_query = """
    UNWIND $medications AS row
    MERGE (m:Medication {name: row.name})
    WITH m, row
    MATCH (c:Condition {code: row.icd_10_code})
    MERGE (c)-[:TREATED_WITH]->(m)
    """
    tx.run(med_query, medications=medications)

def main():
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    symptoms_df = pd.read_csv(os.path.join(base_path, "synthetic_symptoms.csv"))
    medications_df = pd.read_csv(os.path.join(base_path, "synthetic_medications.csv"))
    
    print("Connecting to Neo4j to load extensions...")
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        with driver.session() as session:
            session.execute_write(load_graph_extensions, symptoms_df.to_dict("records"), medications_df.to_dict("records"))
            
    print("Graph fully constructed! Run this in Neo4j Browser:")
    print("MATCH p=(:Symptom)-[:INDICATES]->(:Condition)-[:TREATED_WITH]->(:Medication) RETURN p LIMIT 25")

if __name__ == "__main__":
    main()