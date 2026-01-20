import re
import json
import os
from dotenv import load_dotenv
from groq import Groq

# =========================
# CONFIG
# =========================
MAPPING_DIR = "mapping_folder"
MAPPING_FILE = os.path.join(MAPPING_DIR, "manufacturer_mapping.json")


# =========================
# HELPERS (UNCHANGED LOGIC)
# =========================
def normalize_key(s):
    """
    Normalize manufacturer strings to a stable dictionary key.

    - Lowercases text
    - Removes punctuation
    - Collapses extra whitespace

    This ensures variants like:
        "J. Deere", "John-Deere", "JOHN DEERE"
    resolve to the same lookup key.
    """
    if not isinstance(s, str):
        return ""
    s = s.lower().strip()
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def parse_llm_json(text):
    """
    Extract and sanitize a JSON object from LLM output.

    Handles common LLM issues:
    - Markdown wrapping
    - Smart quotes
    - Unicode artifacts
    - Single-quote JSON

    Raises:
        ValueError if no JSON object is found.
    """
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("No JSON object found")

    raw = match.group()
    raw = raw.replace("“", '"').replace("”", '"')
    raw = raw.replace("‘", "'").replace("’", "'")
    raw = raw.replace("\u00a0", " ")
    raw = re.sub(r"\\'", "'", raw)
    raw = raw.replace("'", '"')

    return json.loads(raw)


# =========================
# OBJECT C CORE
# =========================
def run_object_c(data):
    """
    Object C:
    Normalize manufacturer names using a cached LLM-backed mapping.

    - Identifies unseen manufacturer variants
    - Uses LLM to resolve canonical names
    - Persists mapping to disk to avoid repeated calls
    - Applies canonical manufacturer names in-place

    Input:
        data: List[dict] from Object B

    Output:
        Updated list with normalized `make` field
    """
    os.makedirs(MAPPING_DIR, exist_ok=True)

    # ---------- Load / init mapping ----------
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, "r", encoding="utf-8") as f:
            manufacturer_map = json.load(f)
    else:
        manufacturer_map = {}

    # ---------- Collect raw makes ----------
    raw_makes = set(
        item["make"] for item in data
        if isinstance(item.get("make"), str)
    )

    unseen = [
        m for m in raw_makes
        if normalize_key(m) not in manufacturer_map
    ]

    # ---------- Call LLM if needed ----------
    if unseen:
        load_dotenv()
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        prompt = f"""
Normalize heavy equipment manufacturer names.

Return ONLY JSON:
{{ "<input>": "<canonical>" }}

Examples:
{{ "CAT": "Caterpillar", "J. Deere": "John Deere" }}

Rules:
- Expand abbreviations
- Remove Inc, Corp, Ltd
- Use construction equipment context
- Use double quotes (") only. Do not use single quotes it is a very strict rule.

Input:
{json.dumps(unseen)}
"""

        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        llm_map = parse_llm_json(resp.choices[0].message.content)

        for raw, canon in llm_map.items():
            manufacturer_map[normalize_key(raw)] = canon

        with open(MAPPING_FILE, "w", encoding="utf-8") as f:
            json.dump(manufacturer_map, f, indent=2)

    # ---------- Apply normalization ----------
    for item in data:
        make = item.get("make")
        if isinstance(make, str):
            item["make"] = manufacturer_map.get(
                normalize_key(make),
                make
            )

    # ✅ return fully updated JSON for Object D
    return data


# =========================
# STANDALONE RUN
# =========================
if __name__ == "__main__":
    with open("object_b_output.json", "r", encoding="utf-8") as f:
        input_data = json.load(f)

    result = run_object_c(input_data)

    with open("object_c_output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Object C completed. Records processed: {len(result)}")
