import json
import re
import os
from dotenv import load_dotenv
from groq import Groq

# =========================
# CONFIG
# =========================
MAPPING_DIR = "mapping_folder"
MAPPING_FILE = os.path.join(MAPPING_DIR, "Objective_A.json")

RAW_INVENTORY_FILE = "raw_inventory.json"
TAXONOMY_FILE = "taxonomy.json"


# =========================
# HELPERS (UNCHANGED LOGIC)
# =========================
def normalize_source_category(cat: str) -> str:
    if not cat:
        return ""

    cat = cat.lower().strip()
    cat = cat.replace("-", " ")
    cat = cat.replace("/", " ")
    cat = cat.replace("_", " ")
    cat = " ".join(cat.split())

    return cat


# =========================
# CORE FUNCTION (OBJECT A)
# =========================
def run_object_a(input_path="raw_inventory.json"):
    """
    Objective A:
    Normalize source categories from raw inventory data and map them
    to a fixed internal taxonomy using an LLM-backed cached mapping.

    - Uses deterministic normalization to reduce category variance
    - Calls LLM only for previously unseen categories
    - Persists mappings to disk to avoid repeat API calls
    - Applies final taxonomy category to each inventory item

    Returns:
        List[dict]: inventory records with standardized `category` field added
    """
    # ---------- Load input files ----------
    with open(RAW_INVENTORY_FILE, "r", encoding="utf-8") as f:
        raw_data_json = json.load(f)

    with open(TAXONOMY_FILE, "r", encoding="utf-8") as f:
        taxonomy = json.load(f)

    taxonomy_categories = [t for t in taxonomy]

    # ---------- Load / init mapping ----------
    os.makedirs(MAPPING_DIR, exist_ok=True)

    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, "r", encoding="utf-8") as f:
            category_map = json.load(f)
    else:
        category_map = {}

    # ---------- Collect unique normalized categories ----------
    unique_categories = set()
    for item in raw_data_json:
        sc = item.get("source_category")
        if not sc:
            continue
        unique_categories.add(normalize_source_category(sc))

    unseen = [
        c for c in unique_categories
        if c not in category_map
    ]

    # ---------- Call LLM ONLY if needed ----------
    if unseen:
        prompt = f"""
You are a heavy equipment classification expert.

Map each source category to exactly ONE category from the taxonomy list.

Rules:
- Use ONLY taxonomy values
- Return valid JSON
- One-to-one mapping
- No explanations

SOURCE CATEGORIES:
{unseen}

TAXONOMY:
{taxonomy_categories}

OUTPUT FORMAT:
{{
  "normalized_source_category": "taxonomy_category"
}}
"""

        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")

        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        raw = response.choices[0].message.content
        raw = re.sub(r"```json|```", "", raw).strip()

        new_map = json.loads(raw)

        category_map.update(new_map)

        with open(MAPPING_FILE, "w", encoding="utf-8") as f:
            json.dump(category_map, f, indent=2)

    # ---------- Apply mapping to inventory ----------
    for item in raw_data_json:
        norm = normalize_source_category(item.get("source_category", ""))
        item["category"] = category_map.get(norm, "UNKNOWN")

    return raw_data_json

if __name__ == "__main__":
    result = run_object_a()

    # Optional: save output so you can inspect it
    with open("object_a_output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Object A completed. Records processed: {len(result)}")
