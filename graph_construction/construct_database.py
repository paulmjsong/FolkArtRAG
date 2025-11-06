import asyncio, json, re
from tqdm import tqdm
from typing import Dict, List

from neo4j import Driver
from neo4j_graphrag.indexes import create_vector_index, upsert_vectors
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.types import EntityType
from neo4j_graphrag.experimental.components.resolver import (
    SinglePropertyExactMatchResolver,
    FuzzyMatchResolver,
)


# ---------------- ADD ENTITIES TO DB ----------------
def build_database(driver: Driver, dst_path: str, embedder: OpenAILLM, EMBED_DIMS: int, SHARED_LABEL: str, INDEX_NAME: str) -> None:
    with open(dst_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    
    ensure_vector_index(driver, EMBED_DIMS, SHARED_LABEL, INDEX_NAME)
    
    # TODO: Determine whether to store edge embeddings
    node_ids: List[str] = []
    node_embeds: List[List[float]] = []
    # edge_ids: List[str] = []
    # edge_embeds: List[List[float]] = []
    
    # TODO: Batch inserts for performance
    with driver.session() as session:
        # Insert nodes
        # for entity in tqdm(data["entities"], total=len(data["entities"]), desc="Inserting entities"):
        #     node_id = session.execute_write(create_node, entity)
        #     node_ids.append(node_id)
        #     embed_text = f"Name: {entity['name']} | Description: {entity['description']}"
        #     if entity.get("aliases"):
        #         embed_text += f" | Aliases: {', '.join(entity['aliases'])}"
        #     node_embeds.append(embedder.embed_query(embed_text))

        # Insert edges
        for rel in tqdm(data["relations"], total=len(data["relations"]), desc="Inserting relationships"):
            edge_ids = session.execute_write(create_edges, rel)
            # edge_ids.extend(edge_ids)

        # One batch upsert for all nodes
        if node_ids:
            upsert_vectors(
                driver=driver,
                ids=node_ids,
                embedding_property="embedding",
                embeddings=node_embeds,
                entity_type=EntityType.NODE,
            )
    
    print("  🔍 Resolving duplicate entities...")
    asyncio.run(resolve_duplicates(driver))


# ---------------- NEO4J OPERATIONS ----------------
def ensure_vector_index(driver: Driver, EMBED_DIMS: int, SHARED_LABEL: str, INDEX_NAME: str) -> None:
    create_vector_index(
        driver=driver,
        name=INDEX_NAME,
        label=SHARED_LABEL,
        embedding_property="embedding",
        dimensions=EMBED_DIMS,
        similarity_fn="cosine",
    )

def create_node(tx, entity: Dict) -> str:
    entity_type = sanitize_label(entity["type"])
    # entity_type = entity["type"].replace(" ", "")
    if entity_type not in {"Form", "Concept", "Myth"}:
        raise ValueError(f"Unsupported entity type: {entity_type}")
    query = f"""
    MERGE (n:{entity_type} {{name: $name}})
    ON CREATE SET
        n.description = $description
    ON MATCH SET
        n.description = coalesce(n.description, $description)
    RETURN elementId(n) AS eid
    """
    print(f"Creating node: {entity['name']}")
    rec = tx.run(
        query, 
        name=entity["name"], 
        description=entity.get("description"),
    ).single()
    return rec["eid"]

def create_edges(tx, rel: Dict) -> list[str]:
    rel_type = rel["type"].upper().replace(" ", "_")
    eids = []

    def run_query(source_type: str, target_type: str, source: str, target: str):
        query = f"""
        MATCH (a:{source_type} {{name: $source}})
        MATCH (b:{target_type} {{name: $target}})
        MERGE (a)-[r:{rel_type}]->(b)
        ON CREATE SET r.description = $description
        ON MATCH  SET r.description = coalesce(r.description, $description)
        RETURN elementId(r) AS eid
        """
        print(f"Creating edge: {source} -[{rel_type}]-> {target}")
        rec = tx.run(
            query,
            source=source,
            target=target,
            description=rel.get("description"),
        ).single()
        return rec["eid"]
    
    if rel_type == "CONNOTES":
        eid = run_query(
            source_type="Form",
            target_type="Concept",
            source=rel["source"],
            target=rel["target"],
        )
        eids.append(eid)
    elif rel_type == "GENERATES_MYTH":
        for source in rel["source_concepts"]:
            eid = run_query(
                source_type="Concept",
                target_type="Myth",
                source=source,
                target=rel["target"],
            )
            eids.append(eid)
    else:
        raise ValueError(f"Unsupported relationship type: {rel_type}")
    return eids

async def resolve_duplicates(driver: Driver) -> None:
    if not apoc_available(driver):
        print("⚠️ APOC not available; skipping entity resolution.")
        return
    
    # Exact match first
    exact = SinglePropertyExactMatchResolver(driver=driver)
    await exact.run()

    # Fuzzy match on :Form, :Concept, :Myth by 'name' property
    for label in ["Form", "Concept", "Myth"]:
        fuzzy = FuzzyMatchResolver(
            driver=driver,
            filter_query=f"WHERE entity:`{label}`",
            resolve_properties=["name"],
            similarity_threshold=0.95,
        )
        await fuzzy.run()

def clear_database(driver: Driver) -> None:
    with driver.session() as session:
        # Drop constraints
        cons = session.run("SHOW CONSTRAINTS YIELD name RETURN name").value()
        for name in cons:
            session.run(f"DROP CONSTRAINT {name} IF EXISTS")
        # Drop indexes
        idxs = session.run("SHOW INDEXES YIELD name RETURN name").value()
        for name in idxs:
            session.run(f"DROP INDEX {name} IF EXISTS")
        # Delete nodes/relationships
        session.run("MATCH (n) DETACH DELETE n")
    print("🗑️  Dropped all constraints, indexes, and data.")


# ---------------- UTILS ----------------
def sanitize_label(raw: str) -> str:
    tokens = re.split(r'[^A-Za-z0-9]+', raw)
    tokens = [t for t in tokens if t]
    label = ''.join(t[:1].upper() + t[1:] for t in tokens)
    if not label or not label[0].isalpha():
        label = "Entity" + label  # ensure starts with a letter
    return label

def apoc_available(driver: Driver) -> bool:
    with driver.session() as session:
        try:
            rec = session.run("RETURN apoc.version() AS v").single()
            return rec and rec["v"]
        except Exception:
            return False