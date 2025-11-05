import json
from tqdm import tqdm

from neo4j_graphrag.llm import OpenAILLM

from prompts import CONSTRUCTION_PROMPT


# ---------------- EXTRACT ENTITIES ----------------
def extract_data(llm: OpenAILLM, src_path: str, dst_path: str) -> None:
    with open(src_path, "r") as src_file:
        articles = json.load(src_file)

    extracted = {
        "entities": [],
        "relations": [],
    }

    for article in tqdm(articles, total=len(articles), desc="Extracting entities and relationships"):
        result = llm.invoke(
            f"Input data:\n{article}\n\n{CONSTRUCTION_PROMPT}",
        )
        # entities, relations = parse_llm_output(result.content)
        # extracted['entities'].append(entities)
        # extracted['relations'].append(relations)
        json = json.loads(result.content)
        extracted['entities'].extend(json['entities'])
        extracted['relations'].extend(json['relations'])
    
    with open(dst_path, "a", encoding="utf-8") as dst_file:
        json.dump(extracted, dst_file, ensure_ascii=False, indent=4)

# # TODO: Rewrite this function to properly parse the LLM output
# def parse_llm_output(data: str) -> tuple[list[str], list[str]]:
#     entities = []
#     relations = []
#     lines = data.split("\n")
#     current_section = None

#     for line in lines:
#         line = line.strip()
#         if line == "Entities:":
#             current_section = "entities"
#             continue
#         elif line == "Relationships:":
#             current_section = "relations"
#             continue
        
#         if current_section == "entities" and line:
#             entities.append(line)
#         elif current_section == "relations" and line:
#             relations.append(line)
    
#     return entities, relations