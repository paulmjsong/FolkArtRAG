import json, os, time
from dotenv import load_dotenv

from neo4j import Driver, GraphDatabase
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from neo4j_graphrag.llm import OpenAILLM

from handle_query import create_retriever, generate_response


# ---------------- CONFIG ----------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# ---------------- NEO4J SETUP ----------------
URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))

SHARED_LABEL = "__Entity__"
SHARED_INDEX = "__Entity__index"
# SEED_LABEL = "Form"
# SEED_INDEX = "Form_index"

EMBED_MODEL = "text-embedding-3-large"
EMBED_DIMS = 3072
CAPTION_MODEL = "gpt-4o-mini"
INFERENCE_MODEL = "gpt-4o"


# ---------------- UTIL ----------------
def close_driver(driver: Driver) -> None:
    if driver is not None:
        driver.close()


# ---------------- MAIN ----------------
def main():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    embedder = OpenAIEmbeddings(model=EMBED_MODEL, api_key=OPENAI_API_KEY)
    retriever = create_retriever(driver, embedder, SHARED_INDEX)
    
    # TODO: replace caption model with LLAVA
    caption_llm = OpenAILLM(model_name=CAPTION_MODEL, api_key=OPENAI_API_KEY)
    inference_llm = OpenAILLM(model_name=INFERENCE_MODEL, api_key=OPENAI_API_KEY)
    
    src_path = "example/input.json"
    dst_path = "example/output.json"
    
    if not os.path.exists(src_path):
        print(f"❗ Source file {src_path} not found. Please provide a valid source file.")
        return
    
    with open(src_path, "r", encoding="utf-8") as src_file:
        all_input = json.load(src_file)
        all_output = []

    for input in all_input:
        img_path = input["image"]
        qa_pairs = []

        for query in input["query"]:
            start_time = time.time()
            response = generate_response(inference_llm, caption_llm, embedder, retriever, [SHARED_LABEL], query, img_path)
            elapsed_time = time.time() - start_time

            qa_pairs.append({
                "query": query,
                "response": response,
                "time": elapsed_time,
            })
        
        all_output.append({
            "image": img_path,
            "output": qa_pairs,
        })
    
    with open(dst_path, "w", encoding="utf-8") as dst_file:
        json.dump(all_output, dst_file, ensure_ascii=False, indent=4)
    
    close_driver(driver)


if __name__ == "__main__":
    main()