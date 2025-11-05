# ---------------- extract_entities.py ----------------
EXTRACTION_PROMPT = """
You are an expert semiotician using Roland Barthes' model (Connotation → Myth). Extract entities (Forms, Concepts, Myths) and their relations from the passage.
Output must be:
- English only
- Entities and relations only (no explanations, no headers, no summaries)
- Valid JSON: a single JSON object with two arrays: "entities" and "relations".

# Canonicalization & Deduplication Rules
1. One concept per idea: Merge near-duplicates (e.g., "Rabbit" and "Rabbit in Folklore" → "Rabbit").
2. Naming:
  - Use Title Case, ASCII, singular nouns where possible (e.g., "Tiger", "Oppression", "Cunning").
  - Use the most general canonical label unless a qualifier is essential (prefer "Tiger" over "Smoking Tiger" unless smoking is semantically crucial).
3. English only: Translate all labels to English.
4. Uniqueness: Each entity must have a unique "name". Use "aliases" for other surface forms from the passage.

# Allowed Entity Types
Each entity must have:
- "name" — canonical English label (Title Case)
- "type" — one of:
  - "Form" — material signifier in the passage (e.g., Tiger, Rabbit, Smoking Tiger motif)
  - "Concept" — immediate connoted meaning (e.g., Power, Meekness, Corruption, Resistance)
  - "Myth" — overarching ideological signified (e.g., Dominance of Oppressors, Survival of the Weak through Cunning)
- "aliases" — optional array of English surface forms/variants from the passage

# Allowed Relation Types
Only these relation types are permitted:
- "Connotes": Form → Concept
- "Generates_Myth": Combined(Concepts) → Myth

# JSON Schema
{
  "entities": [
    {
      "type": "Form|Concept|Myth",
      "name": "string",           // canonical English label, Title Case, unique
      "aliases": ["string"]       // optional; English variants/surface forms
    }
  ],
  "relations": [
    {
      "type": "Connotes",
      "source": "string",         // Form.name (must match an entity.name)
      "target": "string"          // Concept.name (must match an entity.name)
    },
    {
      "type": "Generates_Myth",
      "source_concepts": [
        "string"                  // Concept.name values; 2+ items
      ],
      "target": "string"          // Myth.name (must match an entity.name)
    }
  ]
}

# Processing Rules
- Build the "entities" list first, applying deduplication and English canonicalization.
- For each canonical entity:
  - Put its canonical label in "name".
  - Collect other surface forms into "aliases" (English only, translated if needed).
- No IDs: do not output any "id" field.
- For each relation:
  - "source", "target", and "source_concepts" must exactly match the "name" of some entity in "entities".
  - For "Generates_Myth", include only the minimal set of concepts needed to generate that myth.
  - Sort "source_concepts" alphabetically for stable, repeatable output.
- Do not output anything other than the JSON object (no prose, no comments).

# Passage
[Korean text here]

Produce the JSON now.
"""

# ---------------- construct_database.py ----------------
# None

# ---------------- main.py ----------------
# None