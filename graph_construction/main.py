import os, time
from dotenv import load_dotenv
from tqdm import tqdm

from neo4j import Driver, GraphDatabase
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from neo4j_graphrag.llm import OpenAILLM

from extract_entities import extract_entities
from construct_database import clear_database, build_database


# ---------------- CONFIG ----------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ENCYKOREA_API_KEY = os.getenv("ENCYKOREA_API_KEY")
ENCYKOREA_ENDPOINT = os.getenv("ENCYKOREA_ENDPOINT")


# ---------------- NEO4J SETUP ----------------
URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "compress")

SHARED_LABEL = "__Entity__"
INDEX_NAME = "entity_index"

EMBED_MODEL = "text-embedding-3-large"
EMBED_DIMS = 3072
GENERATION_MODEL = "gpt-4o-mini"


# ---------------- UTIL ----------------
def close_driver(driver: Driver) -> None:
    if driver is not None:
        driver.close()


# ---------------- MAIN ----------------
def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    embedder = OpenAIEmbeddings(model=EMBED_MODEL, api_key=OPENAI_API_KEY)
    llm = OpenAILLM(model_name=GENERATION_MODEL, api_key=OPENAI_API_KEY)
    
    save_path = "graph_construction/extracted.json"
    srcs_path = "graph_construction/srcs_list.json"
    
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    if not os.path.exists(srcs_path):
        print(f"❗ Source file {srcs_path} not found. Please provide a valid source file.")
    else:
        print("🔄 Extracting entities and relationships...")
        extract_entities(llm, save_path, srcs_path, ENCYKOREA_API_KEY, ENCYKOREA_ENDPOINT)

        print("🧹 Clearing existing database...")
        clear_database(driver)

        print("🔄 Building database from extracted entities...")
        build_database(driver, save_path, embedder, EMBED_DIMS, SHARED_LABEL, INDEX_NAME)

        print("✅ Graph built, single vector index populated, and deduplicated.")
    
    close_driver(driver)


if __name__ == "__main__":
    main()