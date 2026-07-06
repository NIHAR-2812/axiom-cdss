from neo4j import GraphDatabase

# Your local Neo4j credentials
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "secure_graph_123")

def seed_treatments(tx):
    print("[SYSTEM] Injecting Clinical Treatment Pathways into Graph...")
    
    # Cypher query to create Disease nodes, Medication nodes, and link them
    query = """
    // 1. Liver Disease (K76.9)
    MERGE (c1:Condition {code: 'K76.9'})
    MERGE (m1:Medication {name: 'Ursodiol'})
    MERGE (m2:Medication {name: 'Lactulose'})
    MERGE (c1)-[:TREATED_WITH]->(m1)
    MERGE (c1)-[:TREATED_WITH]->(m2)

    // 2. Hypertension (I10)
    MERGE (c2:Condition {code: 'I10'})
    MERGE (m3:Medication {name: 'Lisinopril'})
    MERGE (m4:Medication {name: 'Amlodipine'})
    MERGE (c2)-[:TREATED_WITH]->(m3)
    MERGE (c2)-[:TREATED_WITH]->(m4)
    
    // 3. Asthma (J45.909)
    MERGE (c3:Condition {code: 'J45.909'})
    MERGE (m5:Medication {name: 'Albuterol Inhaler'})
    MERGE (c3)-[:TREATED_WITH]->(m5)
    """
    tx.run(query)

if __name__ == "__main__":
    try:
        driver = GraphDatabase.driver(URI, auth=AUTH)
        with driver.session() as session:
            session.execute_write(seed_treatments)
            print("[SUCCESS] Mock treatments injected! Your API will now return medications.")
        driver.close()
    except Exception as e:
        print(f"[ERROR] Could not connect to Neo4j: {e}")